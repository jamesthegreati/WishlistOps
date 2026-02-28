"""Minimal local web server for the static dashboard.

WishlistOps' dashboard is currently a static frontend (dashboard/index.html).
This module exists so `python -m wishlistops.main setup` can actually launch a
local server without requiring a separate backend.

It intentionally does not expose any sensitive config values.
"""

from __future__ import annotations

import json
import mimetypes
import os
import uuid
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from aiohttp import web


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _projects_file(workspace_root: Path) -> Path:
    return workspace_root / ".wishlistops_projects.json"


class ProjectManager:
    """Persists and selects the active WishlistOps 'project' (repo + config).

    A project represents a local Git repository plus the config.json to use for
    generation. This enables working with multiple repos / multiple games.
    """

    def __init__(self, workspace_root: Path, default_repo_root: Path, default_config_path: Path) -> None:
        self.workspace_root = workspace_root
        self.path = _projects_file(workspace_root)
        self._data: dict[str, Any] = {}
        self._load_or_init(default_repo_root=default_repo_root, default_config_path=default_config_path)

    def _load_or_init(self, default_repo_root: Path, default_config_path: Path) -> None:
        if self.path.exists():
            try:
                self._data = json.loads(self.path.read_text(encoding="utf-8"))
            except Exception:
                self._data = {}

        if not isinstance(self._data, dict):
            self._data = {}

        self._data.setdefault("version", 1)
        self._data.setdefault("projects", [])
        if not isinstance(self._data.get("projects"), list):
            self._data["projects"] = []

        if not self._data["projects"]:
            default_id = "default"
            self._data["projects"] = [
                {
                    "id": default_id,
                    "name": "Default",
                    "repo_path": str(default_repo_root),
                    "config_path": str(default_config_path),
                    "discord_enabled": True,
                }
            ]
            self._data["active_id"] = default_id

        if not self._data.get("active_id"):
            self._data["active_id"] = str(self._data["projects"][0].get("id") or "default")

        # Backfill per-project prefs introduced after initial release.
        changed = False
        for p in self.list_projects():
            if "discord_enabled" not in p:
                p["discord_enabled"] = True
                changed = True
        if changed:
            self._data["projects"] = self.list_projects()

        self._save()

    def _save(self) -> None:
        try:
            self.path.write_text(json.dumps(self._data, indent=2), encoding="utf-8")
        except Exception:
            # Dashboard should remain usable even if persistence fails.
            pass

    def list_projects(self) -> list[dict[str, Any]]:
        projects = self._data.get("projects")
        return projects if isinstance(projects, list) else []

    def active_id(self) -> str:
        return str(self._data.get("active_id") or "")

    def _get_project(self, project_id: Optional[str] = None) -> dict[str, Any]:
        pid = str(project_id or self.active_id())
        for p in self.list_projects():
            if str(p.get("id") or "") == pid:
                return p
        # Fallback to first
        projects = self.list_projects()
        return projects[0] if projects else {}

    def active_repo_root(self) -> Path:
        p = self._get_project()
        return Path(str(p.get("repo_path") or self.workspace_root)).resolve()

    def active_config_path(self) -> Path:
        p = self._get_project()
        return Path(str(p.get("config_path") or (self.workspace_root / "wishlistops" / "config.json"))).resolve()

    def select(self, project_id: str) -> bool:
        pid = str(project_id or "").strip()
        if not pid:
            return False
        if any(str(p.get("id") or "") == pid for p in self.list_projects()):
            self._data["active_id"] = pid
            self._save()
            return True
        return False

    def delete(self, project_id: str) -> bool:
        pid = str(project_id or "").strip()
        if not pid:
            return False
        projects = [p for p in self.list_projects() if str(p.get("id") or "") != pid]
        if len(projects) == len(self.list_projects()):
            return False
        self._data["projects"] = projects
        if self.active_id() == pid:
            self._data["active_id"] = str(projects[0].get("id")) if projects else ""
        self._save()
        return True

    def upsert(self, project: dict[str, Any]) -> dict[str, Any]:
        """Create or update a project.

        Expected keys: id(optional), name, repo_path, config_path(optional)
        """
        name = str(project.get("name") or "").strip() or "Project"
        repo_path_raw = str(project.get("repo_path") or "").strip()
        config_path_raw = str(project.get("config_path") or "").strip()

        if not repo_path_raw:
            raise ValueError("repo_path is required")

        repo_candidate = Path(repo_path_raw).expanduser()
        if not repo_candidate.is_absolute():
            repo_candidate = (self.workspace_root / repo_candidate).resolve()
        if not repo_candidate.exists() or not repo_candidate.is_dir():
            raise ValueError(f"repo_path not found: {repo_candidate}")

        # Normalize to the actual Git repo root if possible.
        try:
            import git

            repo = git.Repo(repo_candidate, search_parent_directories=True)
            repo_root = Path(repo.working_dir).resolve()
        except Exception:
            repo_root = repo_candidate.resolve()

        if config_path_raw:
            cfg_candidate = Path(config_path_raw).expanduser()
            if not cfg_candidate.is_absolute():
                cfg_candidate = (repo_root / cfg_candidate).resolve()
        else:
            cfg_candidate = (repo_root / "wishlistops" / "config.json").resolve()

        if not cfg_candidate.exists() or not cfg_candidate.is_file():
            raise ValueError(f"config_path not found: {cfg_candidate}")

        pid = str(project.get("id") or "").strip() or uuid.uuid4().hex

        # Preference: whether the Discord approval step is enabled for this project.
        incoming_discord_enabled = project.get("discord_enabled")
        discord_enabled: bool
        if incoming_discord_enabled is None:
            # Preserve existing if updating an existing project.
            existing = self._get_project(pid)
            discord_enabled = bool(existing.get("discord_enabled", True))
        else:
            discord_enabled = bool(incoming_discord_enabled)

        entry = {
            "id": pid,
            "name": name,
            "repo_path": str(repo_root),
            "config_path": str(cfg_candidate),
            "discord_enabled": discord_enabled,
        }

        projects = self.list_projects()
        replaced = False
        for i, p in enumerate(projects):
            if str(p.get("id") or "") == pid:
                projects[i] = entry
                replaced = True
                break
        if not replaced:
            projects.append(entry)

        self._data["projects"] = projects
        if not self.active_id():
            self._data["active_id"] = pid
        self._save()
        return entry


def _dotenv_path(repo_root: Path) -> Path:
    return repo_root / ".env"


def _parse_dotenv(content: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            values[key] = value
    return values


def _update_dotenv(path: Path, updates: dict[str, Optional[str]]) -> None:
    existing: dict[str, str] = {}
    if path.exists():
        try:
            existing = _parse_dotenv(path.read_text(encoding="utf-8"))
        except OSError:
            existing = {}

    for key, value in updates.items():
        if value is None:
            existing.pop(key, None)
        else:
            existing[key] = value

    lines = ["# WishlistOps local secrets (do not commit)"]
    for key in sorted(existing.keys()):
        value = existing[key]
        safe = value.replace("\n", "\\n")
        lines.append(f"{key}={safe}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _json_response(data: Any, status: int = 200) -> web.Response:
    return web.json_response(data, status=status)


async def _read_json(request: web.Request) -> dict[str, Any]:
    try:
        return await request.json()
    except Exception:
        return {}


def _safe_config_for_client(config_path: Path) -> dict[str, Any]:
    if not config_path.exists():
        return {}
    try:
        return json.loads(config_path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _env_status(repo_root: Path) -> dict[str, Any]:
    # Never return secret values; only indicate presence.
    env_file = _dotenv_path(repo_root)
    file_values: dict[str, str] = {}
    if env_file.exists():
        try:
            file_values = _parse_dotenv(env_file.read_text(encoding="utf-8"))
        except OSError:
            file_values = {}

    def _present(key: str) -> bool:
        return bool(os.getenv(key) or file_values.get(key))

    return {
        "GOOGLE_AI_KEY": _present("GOOGLE_AI_KEY"),
        "DISCORD_WEBHOOK_URL": _present("DISCORD_WEBHOOK_URL"),
        "STEAM_API_KEY": _present("STEAM_API_KEY"),
    }


def _get_env_value(repo_root: Path, key: str) -> Optional[str]:
    value = os.getenv(key)
    if value:
        return value

    env_file = _dotenv_path(repo_root)
    if not env_file.exists():
        return None
    try:
        values = _parse_dotenv(env_file.read_text(encoding="utf-8"))
    except OSError:
        return None
    found = values.get(key)
    return found or None


def _is_safe_file(repo_root: Path, candidate: Path) -> bool:
    """Allowlist for files the dashboard can serve back to the browser."""
    try:
        resolved = candidate.resolve()
        rr = repo_root.resolve()
    except OSError:
        return False

    allowed_roots = [
        rr / "wishlistops" / "banners",
        rr / "wishlistops" / "previews",
        rr / "wishlistops" / "assets",
        rr / "screenshots",
    ]
    for root in allowed_roots:
        try:
            if resolved.is_relative_to(root.resolve()):
                return True
        except AttributeError:
            # Python < 3.9 fallback not needed in this repo, but keep defensive.
            if str(root.resolve()) in str(resolved):
                return True
    return False


def _coerce_commit_type(commit_type: str):
    # Map GitParser's string types to the Pydantic CommitType enum.
    from .models import CommitType

    ct = (commit_type or "").lower()
    if ct in {"fix", "bugfix"}:
        return CommitType.BUGFIX
    return CommitType.FEATURE


def _convert_git_commit(git_commit) -> "CommitModel":
    from .models import Commit as CommitModel

    screenshot = getattr(git_commit, "screenshot_path", None)
    return CommitModel(
        sha=str(getattr(git_commit, "sha")),
        message=str(getattr(git_commit, "message")),
        author=str(getattr(git_commit, "author")),
        timestamp=getattr(git_commit, "date"),
        commit_type=_coerce_commit_type(getattr(git_commit, "commit_type", "")),
        files_changed=list(getattr(git_commit, "files_changed", []) or []),
        screenshot_path=str(screenshot) if screenshot else None,
    )


def run_server(config_path: Path, host: str = "127.0.0.1", port: int = 8080) -> None:
    """Run a small aiohttp server that serves the dashboard UI.

    Args:
        config_path: Path to config.json (currently unused; reserved for future API endpoints).
        host: Host interface to bind to.
        port: Port to bind to.
    """

    workspace_root = _repo_root()
    dashboard_dir = workspace_root / "dashboard"
    static_dir = dashboard_dir / "static"

    if not (dashboard_dir / "index.html").exists():
        raise FileNotFoundError(f"dashboard/index.html not found at {dashboard_dir!s}")

    app = web.Application(client_max_size=25 * 1024 * 1024)

    # Keep config path accessible to handlers.
    # Workspace root hosts the dashboard assets. Repo root/config path are project-scoped.
    app["workspace_root"] = workspace_root
    app["project_manager"] = ProjectManager(
        workspace_root=workspace_root,
        default_repo_root=workspace_root,
        default_config_path=config_path,
    )

    def _ctx(request: web.Request) -> tuple[Path, Path, dict[str, Any]]:
        pm: ProjectManager = request.app["project_manager"]
        rr = pm.active_repo_root()
        cfg = pm.active_config_path()
        p = pm._get_project()  # internal; returns dict
        return rr, cfg, p

    async def index(_: web.Request) -> web.Response:
        return web.FileResponse(dashboard_dir / "index.html")

    async def docs(_: web.Request) -> web.Response:
        # Styled docs page (keeps UI consistent with dashboard theme).
        page = dashboard_dir / "docs.html"
        if page.exists():
            return web.FileResponse(page)

        # Fallback: render the repo README as plain text.
        readme = workspace_root / "README.md"
        if not readme.exists():
            return web.Response(text="README.md not found", status=404)
        return web.Response(text=readme.read_text(encoding="utf-8"), content_type="text/markdown")

    async def health(_: web.Request) -> web.Response:
        return _json_response({"ok": True})

    async def get_config(request: web.Request) -> web.Response:
        rr, path, project = _ctx(request)
        return _json_response({"config": _safe_config_for_client(path), "path": str(path), "project": project})

    async def save_config(request: web.Request) -> web.Response:
        payload = await _read_json(request)
        new_config = payload.get("config")
        if not isinstance(new_config, dict):
            return _json_response({"error": "Invalid config payload"}, status=400)

        from .config_manager import save_config as save_config_file

        _, path, _ = _ctx(request)
        try:
            save_config_file(path, new_config)
        except Exception as exc:
            return _json_response({"error": str(exc)}, status=400)
        return _json_response({"ok": True})

    async def get_env(request: web.Request) -> web.Response:
        rr, _, _ = _ctx(request)
        return _json_response({"env": _env_status(rr)})

    async def save_env(request: web.Request) -> web.Response:
        rr, _, _ = _ctx(request)
        payload = await _read_json(request)
        env_updates = payload.get("env")
        if not isinstance(env_updates, dict):
            return _json_response({"error": "Invalid env payload"}, status=400)

        allowed_keys = {"GOOGLE_AI_KEY", "DISCORD_WEBHOOK_URL", "STEAM_API_KEY"}
        updates: dict[str, Optional[str]] = {}
        for key in allowed_keys:
            if key in env_updates:
                value = env_updates.get(key)
                if value is None or value == "":
                    updates[key] = None
                elif isinstance(value, str):
                    updates[key] = value.strip()
        try:
            _update_dotenv(_dotenv_path(rr), updates)
        except Exception as exc:
            return _json_response({"error": str(exc)}, status=500)
        return _json_response({"ok": True, "env": _env_status(rr)})

    async def get_state(request: web.Request) -> web.Response:
        rr, config_path_local, _ = _ctx(request)
        state_path = config_path_local.parent / "state.json"
        from .state_manager import StateManager

        try:
            sm = StateManager(state_path)
            stats = sm.get_statistics()
        except Exception as exc:
            return _json_response({"error": str(exc)}, status=500)

        return _json_response({"stats": stats, "state_path": str(state_path)})

    async def get_commits(request: web.Request) -> web.Response:
        rr, _, _ = _ctx(request)
        since_tag = request.query.get("since_tag") or None

        from .git_parser import GitParser

        try:
            parser = GitParser(rr)
            commits = parser.get_player_facing_commits(since_tag=since_tag)
        except Exception as exc:
            return _json_response({"error": str(exc)}, status=500)

        # Convert dataclass commits to JSON-safe dicts
        response_commits = []
        for c in commits:
            d = asdict(c)
            d["date"] = c.date.isoformat()
            d["screenshot_path"] = str(c.screenshot_path) if c.screenshot_path else None
            response_commits.append(d)
        return _json_response({"commits": response_commits})

    async def generate(request: web.Request) -> web.Response:
        payload = await _read_json(request)
        rr, config_path_local, _ = _ctx(request)

        since_tag = payload.get("since_tag") or None
        dry_run = bool(payload.get("dry_run", False))
        selected_shas = payload.get("commit_shas")
        if selected_shas is not None and not isinstance(selected_shas, list):
            return _json_response({"error": "commit_shas must be a list"}, status=400)

        screenshot_path = payload.get("screenshot_path")
        if screenshot_path is not None and not isinstance(screenshot_path, str):
            return _json_response({"error": "screenshot_path must be a string"}, status=400)
        crop_mode = payload.get("crop_mode") or "smart"
        if not isinstance(crop_mode, str):
            return _json_response({"error": "crop_mode must be a string"}, status=400)
        with_logo = payload.get("with_logo")
        with_logo = True if with_logo is None else bool(with_logo)

        from .git_parser import GitParser
        from .main import WishlistOpsOrchestrator

        try:
            parser = GitParser(rr)
            git_commits = parser.get_player_facing_commits(since_tag=since_tag)
            if selected_shas:
                wanted = {str(s)[:8] for s in selected_shas if isinstance(s, str)}
                git_commits = [c for c in git_commits if str(c.sha)[:8] in wanted]
        except Exception as exc:
            return _json_response({"error": f"Failed to load commits: {exc}"}, status=500)

        if not git_commits:
            return _json_response({"error": "No commits selected/found"}, status=400)

        # Convert to orchestrator's Pydantic Commit model
        try:
            model_commits = [_convert_git_commit(c) for c in git_commits]
        except Exception as exc:
            return _json_response({"error": f"Failed to convert commits: {exc}"}, status=500)

        try:
            orch = WishlistOpsOrchestrator(config_path_local, dry_run=dry_run)
        except Exception as exc:
            return _json_response({"error": f"Failed to initialize orchestrator: {exc}"}, status=400)

        try:
            async with orch.ai:
                draft = await orch._generate_announcement(model_commits)
                draft = await orch._filter_content(draft)
                if orch.config.branding and orch.compositor:
                    draft = await orch._create_banner(
                        draft,
                        model_commits,
                        screenshot_override=screenshot_path,
                        crop_mode=crop_mode,
                        with_logo=with_logo,
                    )
        except Exception as exc:
            return _json_response({"error": str(exc)}, status=500)

        return _json_response({
            "draft": {
                "title": draft.title,
                "body": draft.body,
                "banner_path": getattr(draft, "banner_path", None),
                "screenshot_used": getattr(draft, "screenshot_used", None),
                "screenshot_source": getattr(draft, "screenshot_source", None),
                "banner_url": None,
                "created_at": getattr(draft, "created_at", datetime.now().isoformat()),
            }
        })

    async def get_file(request: web.Request) -> web.StreamResponse:
        rr, _, _ = _ctx(request)
        rel = request.match_info.get("rel", "")
        if not rel:
            return web.Response(text="Not found", status=404)

        # Only allow serving from whitelisted directories.
        candidate = (rr / rel).resolve()
        if not _is_safe_file(rr, candidate) or not candidate.exists():
            return web.Response(text="Not found", status=404)

        return web.FileResponse(candidate)

    async def send_to_discord(request: web.Request) -> web.Response:
        payload = await _read_json(request)
        rr, config_path_local, _ = _ctx(request)

        draft = payload.get("draft")
        if not isinstance(draft, dict):
            return _json_response({"error": "draft must be an object"}, status=400)

        title = str(draft.get("title") or "").strip()
        body = str(draft.get("body") or "").strip()
        banner_path = draft.get("banner_path")
        banner_url = draft.get("banner_url")
        if not title or not body:
            return _json_response({"error": "draft.title and draft.body required"}, status=400)

        # Validate/normalize banner_path (optional) so Discord attachments actually work.
        normalized_banner_path: Optional[str] = None
        if banner_path is not None:
            if not isinstance(banner_path, str):
                return _json_response({"error": "draft.banner_path must be a string"}, status=400)
            bp = banner_path.strip()
            if bp:
                candidate = Path(bp)
                if not candidate.is_absolute():
                    candidate = (rr / candidate).resolve()
                else:
                    candidate = candidate.resolve()

                if not _is_safe_file(rr, candidate):
                    return _json_response({"error": "banner_path is not in an allowed folder"}, status=400)
                if not candidate.exists():
                    return _json_response({"error": f"banner_path does not exist: {candidate}"}, status=400)
                normalized_banner_path = str(candidate)

        try:
            from .discord_notifier import DiscordNotifier
            from .state_manager import StateManager
            from .models import AnnouncementDraft

            cfg_json = _safe_config_for_client(config_path_local)
            steam_app_id = str((cfg_json.get("steam") or {}).get("app_id") or "")
            game_name = str((cfg_json.get("steam") or {}).get("app_name") or "")
            webhook_url = _get_env_value(rr, "DISCORD_WEBHOOK_URL")
            notifier = DiscordNotifier(webhook_url, dry_run=False)
            ok = await notifier.send_approval_request(
                title=title,
                body=body,
                banner_url=banner_url,
                banner_path=normalized_banner_path,
                game_name=game_name or None,
                tag=None,
                steam_app_id=steam_app_id or None,
            )

            # Persist draft as "last run" for dashboard stats.
            sm = StateManager(config_path_local.parent / "state.json")
            sm.update_last_run(
                draft=AnnouncementDraft(
                    title=title,
                    body=body,
                    banner_url=banner_url,
                    banner_path=normalized_banner_path,
                    created_at=datetime.now().isoformat(),
                ),
                status="success" if ok else "skipped",
            )
        except Exception as exc:
            return _json_response({"error": str(exc)}, status=500)

        return _json_response({"ok": True})

    async def upload(request: web.Request) -> web.Response:
        rr, config_path_local, _ = _ctx(request)

        reader = await request.multipart()
        kind = request.match_info.get("kind")
        if kind not in {"logo", "screenshot"}:
            return _json_response({"error": "Invalid upload kind"}, status=400)

        field = await reader.next()
        if not field or field.name != "file":
            return _json_response({"error": "Expected multipart field 'file'"}, status=400)

        filename = (field.filename or "upload").strip()
        ext = Path(filename).suffix.lower()
        if ext not in {".png", ".jpg", ".jpeg", ".webp"}:
            return _json_response({"error": "Unsupported file type"}, status=400)

        data = await field.read(decode=False)
        if not data:
            return _json_response({"error": "Empty file"}, status=400)

        if kind == "logo":
            out_dir = rr / "wishlistops" / "assets"
            out_dir.mkdir(parents=True, exist_ok=True)
            out_path = out_dir / f"logo{ext}"
        else:
            out_dir = rr / "screenshots"
            out_dir.mkdir(parents=True, exist_ok=True)
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            out_path = out_dir / f"screenshot_{stamp}{ext}"

        try:
            out_path.write_bytes(data)
        except Exception as exc:
            return _json_response({"error": str(exc)}, status=500)

        # Update config logo_path if uploading a logo.
        if kind == "logo":
            cfg = _safe_config_for_client(config_path_local)
            if isinstance(cfg, dict):
                branding = cfg.get("branding") if isinstance(cfg.get("branding"), dict) else {}
                branding["logo_path"] = str(out_path.relative_to(rr)).replace("\\", "/")
                cfg["branding"] = branding
                try:
                    from .config_manager import save_config as save_config_file
                    save_config_file(config_path_local, cfg)
                except Exception:
                    # Don't fail the upload if config update fails.
                    pass

        return _json_response({"ok": True, "path": str(out_path.relative_to(rr)).replace("\\", "/")})

    async def discord_test(request: web.Request) -> web.Response:
        """Send an explicit, opt-in test message to the configured Discord webhook."""
        payload = await _read_json(request)
        rr, config_path_local, _ = _ctx(request)

        message = payload.get("message")
        if message is not None and not isinstance(message, str):
            return _json_response({"error": "message must be a string"}, status=400)

        try:
            from .discord_notifier import DiscordNotifier

            # Do NOT require Google AI to be configured just to test Discord.
            webhook_url = _get_env_value(rr, "DISCORD_WEBHOOK_URL")
            notifier = DiscordNotifier(webhook_url, dry_run=False)
            await notifier.send_test_message(
                message
                or "If you can read this, your Discord webhook is configured correctly."
            )
        except Exception as exc:
            return _json_response({"error": str(exc)}, status=500)

        return _json_response({"ok": True})

    async def google_models(request: web.Request) -> web.Response:
        """List Gemini models available for the configured API key.

        Returns only models that support generateContent.
        """
        rr, _, _ = _ctx(request)
        api_key = _get_env_value(rr, "GOOGLE_AI_KEY")
        if not api_key:
            return _json_response({"error": "GOOGLE_AI_KEY not configured"}, status=400)

        try:
            from .ai_client import GeminiClient
            from .models import AIConfig

            # Use config defaults; only list models.
            cfg = AIConfig()
            async with GeminiClient(api_key, cfg) as client:
                models = await client.list_generate_content_models()
        except Exception as exc:
            return _json_response({"error": str(exc)}, status=500)

        return _json_response({"ok": True, "models": models})

    def _list_screenshot_files(rr: Path) -> list[dict[str, Any]]:
        roots = [rr / "screenshots", rr / "wishlistops" / "screenshots", rr / "promo"]
        allowed_ext = {".png", ".jpg", ".jpeg", ".webp"}

        items: list[dict[str, Any]] = []
        for root in roots:
            if not root.exists():
                continue
            for path in root.rglob("*"):
                if path.is_dir() or path.suffix.lower() not in allowed_ext:
                    continue
                try:
                    st = path.stat()
                    rel = str(path.relative_to(rr)).replace("\\", "/")
                    items.append({"path": rel, "mtime": st.st_mtime, "size": st.st_size})
                except OSError:
                    continue

        items.sort(key=lambda i: float(i.get("mtime") or 0.0), reverse=True)
        return items

    async def list_screenshots(request: web.Request) -> web.Response:
        rr, _, _ = _ctx(request)
        return _json_response({"ok": True, "screenshots": _list_screenshot_files(rr)})

    async def banner_preview(request: web.Request) -> web.Response:
        """Generate a local banner preview from a screenshot with crop options and optional logo."""
        payload = await _read_json(request)
        rr, config_path_local, _ = _ctx(request)

        screenshot_path = payload.get("screenshot_path")
        if not isinstance(screenshot_path, str) or not screenshot_path.strip():
            return _json_response({"error": "screenshot_path required"}, status=400)

        crop_mode = payload.get("crop_mode") or "smart"
        if not isinstance(crop_mode, str):
            return _json_response({"error": "crop_mode must be a string"}, status=400)

        with_logo = payload.get("with_logo")
        with_logo = True if with_logo is None else bool(with_logo)

        candidate = (rr / screenshot_path).resolve()
        if not _is_safe_file(rr, candidate) or not candidate.exists():
            return _json_response({"error": "Screenshot not found or not allowed"}, status=404)

        try:
            from PIL import Image
            from io import BytesIO

            from .image_compositor import ImageCompositor
            from .models import BrandingConfig

            # Load config JSON (no secret validation; dashboard-only).
            cfg_json = _safe_config_for_client(config_path_local)
            branding_json = cfg_json.get("branding") if isinstance(cfg_json.get("branding"), dict) else None
            branding = BrandingConfig(**branding_json) if branding_json else None

            def crop_to_ratio(img: Image.Image, ratio: float, mode: str) -> Image.Image:
                w, h = img.size
                current = w / h
                if abs(current - ratio) < 1e-3:
                    return img

                if current > ratio:
                    new_w = int(h * ratio)
                    if mode == "left":
                        x0 = 0
                    elif mode == "right":
                        x0 = w - new_w
                    elif mode == "thirds":
                        x0 = max(0, min(w - new_w, (w - new_w) // 3))
                    else:
                        x0 = (w - new_w) // 2
                    return img.crop((x0, 0, x0 + new_w, h))

                new_h = int(w / ratio)
                if mode == "top":
                    y0 = 0
                elif mode == "bottom":
                    y0 = h - new_h
                elif mode == "thirds":
                    y0 = max(0, min(h - new_h, (h - new_h) // 3))
                else:
                    y0 = (h - new_h) // 2
                return img.crop((0, y0, w, y0 + new_h))

            previews_dir = rr / "wishlistops" / "previews"
            previews_dir.mkdir(parents=True, exist_ok=True)
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            out_rel = f"wishlistops/previews/preview_{stamp}.png"
            out_path = (rr / out_rel).resolve()

            # Use the compositor pipeline when available so preview matches production banner.
            if branding:
                compositor = ImageCompositor(branding)
                base_bytes = candidate.read_bytes()

                if crop_mode and crop_mode.lower() != "smart":
                    img = Image.open(BytesIO(base_bytes))
                    if img.mode not in {"RGB", "RGBA"}:
                        img = img.convert("RGBA")
                    img = crop_to_ratio(img, compositor.STEAM_WIDTH / compositor.STEAM_HEIGHT, crop_mode.lower())
                    buf = BytesIO()
                    img.save(buf, format="PNG")
                    base_bytes = buf.getvalue()

                compositor.composite_logo(
                    base_image_data=base_bytes,
                    logo_path=Path(branding.logo_path) if (with_logo and branding.logo_path) else None,
                    output_path=out_path,
                )
            else:
                # Minimal fallback if branding is absent.
                img = Image.open(candidate)
                img = img.convert("RGBA") if img.mode != "RGBA" else img
                if crop_mode and crop_mode.lower() != "smart":
                    img = crop_to_ratio(img, 800 / 450, crop_mode.lower())
                img = img.resize((800, 450), Image.Resampling.LANCZOS)
                buf = BytesIO()
                img.save(buf, format="PNG")
                out_path.write_bytes(buf.getvalue())

        except Exception as exc:
            return _json_response({"error": str(exc)}, status=500)

        return _json_response({"ok": True, "preview_path": out_rel})

    async def projects_list(request: web.Request) -> web.Response:
        pm: ProjectManager = request.app["project_manager"]
        return _json_response({"ok": True, "active_id": pm.active_id(), "projects": pm.list_projects()})

    async def projects_upsert(request: web.Request) -> web.Response:
        pm: ProjectManager = request.app["project_manager"]
        payload = await _read_json(request)
        proj = payload.get("project")
        if not isinstance(proj, dict):
            return _json_response({"error": "project must be an object"}, status=400)
        try:
            saved = pm.upsert(proj)
        except Exception as exc:
            return _json_response({"error": str(exc)}, status=400)
        return _json_response({"ok": True, "project": saved, "active_id": pm.active_id(), "projects": pm.list_projects()})

    async def projects_select(request: web.Request) -> web.Response:
        pm: ProjectManager = request.app["project_manager"]
        payload = await _read_json(request)
        pid = payload.get("id")
        if not isinstance(pid, str) or not pid.strip():
            return _json_response({"error": "id is required"}, status=400)
        ok = pm.select(pid)
        if not ok:
            return _json_response({"error": "project not found"}, status=404)
        return _json_response({"ok": True, "active_id": pm.active_id()})

    async def projects_delete(request: web.Request) -> web.Response:
        pm: ProjectManager = request.app["project_manager"]
        payload = await _read_json(request)
        pid = payload.get("id")
        if not isinstance(pid, str) or not pid.strip():
            return _json_response({"error": "id is required"}, status=400)
        ok = pm.delete(pid)
        if not ok:
            return _json_response({"error": "project not found"}, status=404)
        return _json_response({"ok": True, "active_id": pm.active_id(), "projects": pm.list_projects()})

    app.router.add_get("/", index)
    app.router.add_get("/docs", docs)
    app.router.add_get("/api/health", health)
    app.router.add_get("/api/config", get_config)
    app.router.add_post("/api/config", save_config)
    app.router.add_get("/api/env", get_env)
    app.router.add_post("/api/env", save_env)
    app.router.add_get("/api/state", get_state)
    app.router.add_get("/api/commits", get_commits)
    app.router.add_post("/api/generate", generate)
    app.router.add_post("/api/send", send_to_discord)
    app.router.add_post("/api/upload/{kind}", upload)
    app.router.add_post("/api/discord/test", discord_test)
    app.router.add_get("/api/google/models", google_models)
    app.router.add_get("/api/screenshots", list_screenshots)
    app.router.add_post("/api/banner/preview", banner_preview)
    app.router.add_get("/api/projects", projects_list)
    app.router.add_post("/api/projects", projects_upsert)
    app.router.add_post("/api/projects/select", projects_select)
    app.router.add_post("/api/projects/delete", projects_delete)
    app.router.add_get("/files/{rel:.*}", get_file)

    # Dashboard may link to /setup, /commits, etc. Serve index for these routes too.
    for route in ("/setup", "/commits", "/monitor", "/test", "/settings"):
        app.router.add_get(route, index)

    guides_dir = dashboard_dir / "guides"
    if guides_dir.exists():
        app.router.add_static("/guides/", path=guides_dir, name="guides")

    if static_dir.exists():
        # aiohttp will infer content types poorly for some extensions; pre-register common ones.
        mimetypes.add_type("application/javascript", ".js")
        app.router.add_static("/static/", path=static_dir, name="static")

    web.run_app(app, host=host, port=port)

"""Simulation services for WishlistOps end-to-end workflow.

All external integrations are mocked so a user can run a realistic
scenario without hitting real APIs (Gemini, Discord, Steam, Git).

This allows validation of:
 - Announcement text formatting & length limits (Steam requirements)
 - Image banner generation pipeline structure
 - Commit aggregation & prompt construction
 - Discord preview + manual approval step (simulated)
 - Steam publish compliance checklist

No network calls are performed. The provided API key is only validated
for format then discarded (not stored on disk).
"""

from __future__ import annotations

import json
import random
import string
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any

from PIL import Image, ImageDraw, ImageFont

from wishlistops.models import Config, CommitType


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sanitize(text: str, avoid: List[str]) -> str:
    lowered_avoid = {p.lower(): p for p in avoid}
    words = text.split()
    for i, w in enumerate(words):
        wl = w.lower().strip(",.!?;:")
        if wl in lowered_avoid:
            words[i] = "[filtered]"
    return " ".join(words)


# ---------------------------------------------------------------------------
# Mock Git repository
# ---------------------------------------------------------------------------

class MockGitRepo:
    """Simulates a sequence of recent git commits relevant to marketing."""

    COMMIT_MESSAGES = [
        "Add dynamic lighting system",
        "Fix crash on level transition",
        "Refactor inventory serialization",
        "Implement co-op lobby UI",
        "Balance enemy spawn rates",
        "Add achievement tracking backend",
        "Improve particle performance",
        "Update localization strings for French",
        "Add new boss: Chrono Hydra",
        "Optimize pathfinding edge cases",
    ]

    def generate_commits(self, count: int = 8) -> List[Dict[str, Any]]:
        commits = []
        for _ in range(count):
            msg = random.choice(self.COMMIT_MESSAGES)
            sha = "".join(random.choices(string.hexdigits.lower(), k=12))
            ctype = self._classify(msg)
            commits.append({
                "sha": sha,
                "message": msg,
                "author": random.choice(["dev_alex", "dev_sam", "dev_jules"]),
                "timestamp": _now_iso(),
                "commit_type": ctype.value,
            })
        return commits

    @staticmethod
    def _classify(message: str) -> CommitType:
        m = message.lower()
        if any(k in m for k in ["fix", "crash", "optimize", "performance"]):
            return CommitType.BUGFIX
        if any(k in m for k in ["add", "implement", "new", "boss"]):
            return CommitType.FEATURE
        return CommitType.INTERNAL


# ---------------------------------------------------------------------------
# Mock Gemini text & image generation
# ---------------------------------------------------------------------------

@dataclass
class TextResult:
    title: str
    body: str
    metadata: Dict[str, Any]


@dataclass
class ImageResult:
    path: Path
    width: int
    height: int
    metadata: Dict[str, Any]


class MockGeminiTextModel:
    def __init__(self, model_name: str, temperature: float) -> None:
        self.model_name = model_name
        self.temperature = temperature

    def generate(self, config: Config, commits: List[Dict[str, Any]]) -> TextResult:
        feature_commits = [c for c in commits if c["commit_type"] == CommitType.FEATURE.value]
        bugfix_commits = [c for c in commits if c["commit_type"] == CommitType.BUGFIX.value]
        internal_commits = [c for c in commits if c["commit_type"] == CommitType.INTERNAL.value]

        # Construct a faux prompt summary (not used further, just for transparency)
        prompt_summary = {
            "total_commits": len(commits),
            "features": [c["message"] for c in feature_commits],
            "bugfixes": [c["message"] for c in bugfix_commits],
            "internal": [c["message"] for c in internal_commits],
        }

        # Title draft
        raw_title = f"{config.steam.app_name} Update: {len(feature_commits)} Features, {len(bugfix_commits)} Fixes"
        title = raw_title[: config.voice.max_title_length]

        # Body draft with commit enumeration
        body_lines = [
            f"We're excited to share the latest progress on {config.steam.app_name}!",
            "",
            "Feature Improvements:",
        ]
        for c in feature_commits:
            body_lines.append(f" - {c['message']}")

        body_lines += ["", "Bug Fixes:"]
        for c in bugfix_commits:
            body_lines.append(f" - {c['message']}")

        if internal_commits:
            body_lines += ["", "Under The Hood:"]
            for c in internal_commits[:3]:  # limit noise
                body_lines.append(f" - {c['message']}")

        body_lines += [
            "",
            "Thanks for following development. Wishlist and share to support us!",
        ]

        raw_body = "\n".join(body_lines)
        sanitized_body = _sanitize(raw_body, config.voice.avoid_phrases)
        body = sanitized_body[: config.voice.max_body_length]

        metadata = {
            "model": self.model_name,
            "temperature": self.temperature,
            "prompt_summary": prompt_summary,
            "generated_at": _now_iso(),
        }
        return TextResult(title=title, body=body, metadata=metadata)


class MockGeminiImageModel:
    def __init__(self, model_name: str) -> None:
        self.model_name = model_name

    def generate(self, config: Config, output_dir: Path) -> ImageResult:
        width, height = 1024, 576
        img = Image.new("RGBA", (width, height), config.branding.color_palette[0] if config.branding.color_palette else "#222222")
        draw = ImageDraw.Draw(img)

        # Simple layered rectangles using palette
        for idx, color in enumerate(config.branding.color_palette[1:]):
            draw.rectangle([
                (idx * 40, idx * 30),
                (width - idx * 40, height - idx * 30)
            ], outline=color, width=6)

        title_text = f"{config.steam.app_name} Dev Update"
        sub_text = datetime.now().strftime("%b %d, %Y")

        try:
            font = ImageFont.truetype("arial.ttf", 48)
            font_small = ImageFont.truetype("arial.ttf", 32)
        except Exception:
            font = ImageFont.load_default()
            font_small = ImageFont.load_default()

        draw.text((40, 40), title_text, font=font, fill="#FFFFFF")
        draw.text((40, 110), sub_text, font=font_small, fill="#FFFFFF")

        # Simulated logo box
        logo_size = int(width * (config.branding.logo_size_percent / 100))
        logo_x = width - logo_size - 40
        logo_y = height - logo_size - 40
        draw.rectangle([
            (logo_x, logo_y),
            (logo_x + logo_size, logo_y + logo_size)
        ], fill="#FFFFFF33", outline="#FFFFFF", width=3)
        draw.text((logo_x + 10, logo_y + 10), "LOGO", font=font_small, fill="#FFFFFF")

        output_dir.mkdir(parents=True, exist_ok=True)
        out_path = output_dir / "banner.png"
        img.save(out_path, "PNG")

        metadata = {
            "model": self.model_name,
            "generated_at": _now_iso(),
            "dimensions": f"{width}x{height}",
        }
        return ImageResult(path=out_path, width=width, height=height, metadata=metadata)


# ---------------------------------------------------------------------------
# Mock Discord Notifier
# ---------------------------------------------------------------------------

class MockDiscordNotifier:
    def __init__(self) -> None:
        self.messages: List[Dict[str, Any]] = []

    def send_preview(self, title: str, body: str) -> Dict[str, Any]:
        payload = {
            "type": "preview",
            "title": title,
            "excerpt": body[:200] + ("..." if len(body) > 200 else ""),
            "sent_at": _now_iso(),
        }
        self.messages.append(payload)
        return payload

    def approve(self) -> Dict[str, Any]:
        approval = {"approved": True, "approved_at": _now_iso()}
        self.messages.append(approval)
        return approval


# ---------------------------------------------------------------------------
# Mock Steam Publisher
# ---------------------------------------------------------------------------

class MockSteamPublisher:
    REQUIRED_FIELDS = ["title", "body"]

    def __init__(self, app_id: str, avoid_phrases: List[str]):
        self.app_id = app_id
        self.avoid_phrases = [p.lower() for p in avoid_phrases]

    def validate(self, title: str, body: str) -> Dict[str, Any]:
        compliance = {
            "title_length_ok": len(title) <= 200,
            "body_length_ok": len(body) <= 10000,
            "no_banned_phrases": not any(p in body.lower() for p in self.avoid_phrases),
            "has_title": bool(title.strip()),
            "has_body": len(body.strip()) > 50,  # ensure substantive
        }
        compliance["overall_pass"] = all(compliance.values())
        return compliance

    def publish(self, title: str, body: str, banner_path: Path) -> Dict[str, Any]:
        fake_id = "".join(random.choices(string.digits, k=18))
        return {
            "steam_url": f"https://steamcommunity.com/games/{self.app_id}/announcements/detail/{fake_id}",
            "published_at": _now_iso(),
            "banner_used": str(banner_path),
            "announcement_id": fake_id,
        }


# ---------------------------------------------------------------------------
# Scenario Orchestrator
# ---------------------------------------------------------------------------

def run_simulation(config: Config, output_root: Path) -> Dict[str, Any]:
    repo = MockGitRepo()
    commits = repo.generate_commits()

    text_model = MockGeminiTextModel(
        model_name=config.ai.model_text,
        temperature=config.ai.temperature,
    )
    image_model = MockGeminiImageModel(model_name=config.ai.model_image)
    discord = MockDiscordNotifier()
    steam = MockSteamPublisher(
        app_id=config.steam.app_id,
        avoid_phrases=config.voice.avoid_phrases,
    )

    # Generate artifacts
    text_result = text_model.generate(config, commits)
    image_result = image_model.generate(config, output_root / "artifacts")
    preview_payload = discord.send_preview(text_result.title, text_result.body)
    approval_payload = discord.approve()
    compliance = steam.validate(text_result.title, text_result.body)
    publish_info = steam.publish(text_result.title, text_result.body, image_result.path)

    summary = {
        "config_models": {
            "text": config.ai.model_text,
            "image": config.ai.model_image,
        },
        "commits": commits,
        "announcement": {
            "title": text_result.title,
            "body_excerpt": text_result.body[:400] + ("..." if len(text_result.body) > 400 else ""),
            "metadata": text_result.metadata,
        },
        "banner": {
            "path": str(image_result.path),
            "width": image_result.width,
            "height": image_result.height,
            "metadata": image_result.metadata,
        },
        "discord_preview": preview_payload,
        "discord_approval": approval_payload,
        "steam_compliance": compliance,
        "steam_publish": publish_info,
        "generated_at": _now_iso(),
    }

    # Persist summary JSON
    output_root.mkdir(parents=True, exist_ok=True)
    with open(output_root / "workflow_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    # Full body separate file
    with open(output_root / "announcement_body.txt", "w", encoding="utf-8") as f:
        f.write(text_result.body)

    return summary

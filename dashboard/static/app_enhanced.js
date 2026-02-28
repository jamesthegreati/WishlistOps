// WishlistOps Dashboard client logic.
// This dashboard is local-first: it talks to a local aiohttp server and never exposes secrets.

(function () {
  const API = {
    health: "/api/health",
    config: "/api/config",
    env: "/api/env",
    state: "/api/state",
    commits: "/api/commits",
    generate: "/api/generate",
    send: "/api/send",
    uploadLogo: "/api/upload/logo",
    uploadScreenshot: "/api/upload/screenshot",
    googleModels: "/api/google/models",
    screenshots: "/api/screenshots",
    bannerPreview: "/api/banner/preview",
    projects: "/api/projects",
    projectsSelect: "/api/projects/select",
    projectsDelete: "/api/projects/delete",
  };

  function qs(sel) {
    return document.querySelector(sel);
  }
  function qsa(sel) {
    return Array.from(document.querySelectorAll(sel));
  }

  async function apiGet(url) {
    const resp = await fetch(url, { headers: { Accept: "application/json" } });
    const data = await resp.json().catch(() => ({}));
    if (!resp.ok) throw new Error(data.error || `Request failed: ${resp.status}`);
    return data;
  }

  async function apiPost(url, body) {
    const resp = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify(body || {}),
    });
    const data = await resp.json().catch(() => ({}));
    if (!resp.ok) throw new Error(data.error || `Request failed: ${resp.status}`);
    return data;
  }

  async function apiUpload(url, file) {
    const fd = new FormData();
    fd.append("file", file);
    const resp = await fetch(url, { method: "POST", body: fd });
    const data = await resp.json().catch(() => ({}));
    if (!resp.ok) throw new Error(data.error || `Upload failed: ${resp.status}`);
    return data;
  }

  const state = {
    config: null,
    env: null,
    commits: [],
    lastDraft: null,
    googleModels: [],
    screenshots: [],
    projects: [],
    activeProjectId: "",
  };

  function getActiveProject() {
    const pid = String(state.activeProjectId || "");
    return (state.projects || []).find((x) => String(x?.id || "") === pid) || null;
  }

  function getProjectDiscordEnabled() {
    const p = getActiveProject();
    // Default to enabled for older project files.
    if (!p) return true;
    return p.discord_enabled !== false;
  }

  function escapeHTML(value) {
    return String(value || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/\"/g, "&quot;");
  }

  function normalizePath(p) {
    return String(p || "").replace(/\\/g, "/");
  }

  function uniqueNonEmpty(list) {
    const seen = new Set();
    const out = [];
    for (const item of list || []) {
      const v = normalizePath(item).trim();
      if (!v) continue;
      if (seen.has(v)) continue;
      seen.add(v);
      out.push(v);
    }
    return out;
  }

  function setConnection(status, text) {
    const dot = qs("#connection-status");
    const label = qs("#connection-text");
    if (!dot || !label) return;
    dot.classList.remove("offline", "warning");
    if (status === "offline") dot.classList.add("offline");
    if (status === "warning") dot.classList.add("warning");
    label.textContent = text;
  }

  function showToast(message) {
    const host = qs("#toast-container");
    if (!host) {
      // Fallback
      alert(message);
      return;
    }

    const toast = document.createElement("div");
    toast.className = "toast";

    const title = document.createElement("div");
    title.className = "toast-title";
    title.textContent = "WishlistOps";

    const body = document.createElement("div");
    body.className = "toast-body";
    body.textContent = String(message || "");

    toast.appendChild(title);
    toast.appendChild(body);
    host.appendChild(toast);

    setTimeout(() => {
      try {
        toast.remove();
      } catch (_) {}
    }, 4500);
  }

  window.showView = function showView(viewName) {
    qsa(".view").forEach((el) => el.classList.add("hidden"));
    const view = qs(`#view-${viewName}`);
    if (view) view.classList.remove("hidden");

    qsa(".nav-item").forEach((el) => el.classList.remove("active"));
    const nav = qsa(".nav-item").find((el) => el.dataset.view === viewName);
    if (nav) nav.classList.add("active");

    if (viewName === "settings") {
      // Keep the projects list fresh when user opens Settings.
      loadProjects().catch(() => {});

      const discordToggle = qs("#settings-discord-enabled");
      if (discordToggle) discordToggle.checked = getProjectDiscordEnabled();
    }
  };

  function setActiveProjectName(name) {
    const header = qs("#active-project-name");
    if (header) header.textContent = name || "(none)";
    const gen = qs("#active-project-name-generate");
    if (gen) gen.textContent = name || "(none)";
  }

  function resolveActiveProjectName() {
    const pid = String(state.activeProjectId || "");
    const p = (state.projects || []).find((x) => String(x?.id || "") === pid);
    return p ? String(p.name || "Project") : "(none)";
  }

  function renderProjectsList() {
    const host = qs("#projects-list");
    if (!host) return;

    const projects = Array.isArray(state.projects) ? state.projects : [];
    const activeId = String(state.activeProjectId || "");

    if (!projects.length) {
      host.innerHTML = '<div class="text-muted">No projects yet.</div>';
      setActiveProjectName("(none)");
      return;
    }

    const rows = projects
      .map((p) => {
        const id = String(p?.id || "");
        const name = escapeHTML(p?.name || "Project");
        const repo = escapeHTML(normalizePath(p?.repo_path || ""));
        const cfg = escapeHTML(normalizePath(p?.config_path || ""));
        const isActive = id && id === activeId;

        return `
        <div style="display:flex; gap:12px; align-items:flex-start; justify-content:space-between; padding: 14px; border: 1px solid var(--border-subtle); border-radius: 12px; background: var(--bg-tertiary); margin-bottom: 10px;">
          <div style="min-width:0;">
            <div style="display:flex; gap:10px; align-items:center; flex-wrap:wrap;">
              <div style="font-weight:800;">${name}</div>
              ${isActive ? '<span class="quality-badge excellent">Active</span>' : ''}
            </div>
            <div class="text-muted" style="font-size:0.85rem; margin-top:6px; overflow-wrap:anywhere;">
              <div><span style="color: var(--text-dim);">Repo:</span> ${repo}</div>
              <div><span style="color: var(--text-dim);">Config:</span> ${cfg}</div>
            </div>
          </div>
          <div class="flex gap-sm" style="flex-shrink:0;">
            <button class="btn btn-secondary" ${isActive ? "disabled" : ""} onclick="selectProject('${escapeHTML(id)}')">Select</button>
            <button class="btn btn-secondary" onclick="deleteProject('${escapeHTML(id)}')">Delete</button>
          </div>
        </div>`;
      })
      .join("");

    host.innerHTML = rows;
    setActiveProjectName(resolveActiveProjectName());
  }

  async function loadProjects() {
    try {
      const data = await apiGet(API.projects);
      state.projects = Array.isArray(data.projects) ? data.projects : [];
      state.activeProjectId = String(data.active_id || "");
      setActiveProjectName(resolveActiveProjectName());
      renderProjectsList();
    } catch (e) {
      setActiveProjectName("Unavailable");
    }
  }

  window.refreshProjects = async function refreshProjects() {
    await loadProjects();
  };

  window.saveProject = async function saveProject() {
    const name = getInputValue("#project-name").trim();
    const repoPath = getInputValue("#project-repo-path").trim();
    const configPath = getInputValue("#project-config-path").trim();

    if (!repoPath) {
      showToast("Repo Path is required");
      return;
    }

    try {
      const res = await apiPost(API.projects, {
        project: {
          name: name || "Project",
          repo_path: repoPath,
          config_path: configPath || undefined,
        },
      });

      const newId = res?.project?.id;
      if (newId) {
        await apiPost(API.projectsSelect, { id: String(newId) });
      }

      setInputValue("#project-name", "");
      setInputValue("#project-repo-path", "");
      setInputValue("#project-config-path", "");

      await loadProjects();
      await refreshAll();
      showToast("Project added and selected");
    } catch (e) {
      showToast(String(e.message || e));
    }
  };

  window.selectProject = async function selectProject(id) {
    const pid = String(id || "").trim();
    if (!pid) return;
    try {
      await apiPost(API.projectsSelect, { id: pid });
      state.commits = [];
      state.lastDraft = null;
      state.screenshots = [];
      await loadProjects();
      await refreshAll();
      showToast(`Switched active project to: ${resolveActiveProjectName()}`);
    } catch (e) {
      showToast(String(e.message || e));
    }
  };

  window.deleteProject = async function deleteProject(id) {
    const pid = String(id || "").trim();
    if (!pid) return;

    const ok = confirm("Delete this project? This only removes it from the dashboard list (it will not delete your repo).");
    if (!ok) return;

    try {
      await apiPost(API.projectsDelete, { id: pid });
      await loadProjects();
      await refreshAll();
      showToast("Project deleted");
    } catch (e) {
      showToast(String(e.message || e));
    }
  };

  function updateProgress() {
    const hasGoogle = !!(state.env && state.env.GOOGLE_AI_KEY);
    const hasDiscord = !!(state.env && state.env.DISCORD_WEBHOOK_URL);
    const cfg = state.config || {};
    const hasGame = !!(cfg.steam && cfg.steam.app_id && cfg.steam.app_name);
    const hasBranding = !!(cfg.branding && cfg.branding.logo_path);

    // Map to the four quick-start steps.
    const s1 = hasGoogle && hasDiscord;
    const s2 = hasGame;
    const s3 = hasBranding;
    const s4 = false; // will be computed after generation

    const complete = [s1, s2, s3, s4].filter(Boolean).length;
    const percent = Math.round((complete / 4) * 100);

    const pct = qs("#progress-percent");
    const fill = qs("#progress-fill");
    const steps = qs("#steps-complete");
    if (pct) pct.textContent = `${percent}%`;
    if (fill) fill.style.width = `${percent}%`;
    if (steps) steps.textContent = `${complete}/4 complete`;
  }

  function setInputValue(id, value) {
    const el = qs(id);
    if (el) el.value = value == null ? "" : String(value);
  }

  function getInputValue(id) {
    const el = qs(id);
    return el ? String(el.value || "") : "";
  }

  async function refreshAll() {
    const [{ env }, { config }, { stats }] = await Promise.all([
      apiGet(API.env),
      apiGet(API.config),
      apiGet(API.state).catch(() => ({ stats: null })),
    ]);
    state.env = env;
    state.config = config;

    // API Keys view does not show secrets; placeholders only.
    const googleStatus = qs("#google-status");
    const discordStatus = qs("#discord-status");
    if (googleStatus) {
      googleStatus.innerHTML = state.env.GOOGLE_AI_KEY
        ? '<span class="status-dot"></span> Configured'
        : '<span class="status-dot offline"></span> Not configured';
    }
    if (discordStatus) {
      discordStatus.innerHTML = state.env.DISCORD_WEBHOOK_URL
        ? '<span class="status-dot"></span> Configured'
        : '<span class="status-dot offline"></span> Not configured';
    }

    // Game config view
    setInputValue("#steam-app-id", state.config?.steam?.app_id || "");
    setInputValue("#game-name", state.config?.steam?.app_name || "");
    setInputValue("#art-style", state.config?.branding?.art_style || "");
    setInputValue("#tone", state.config?.voice?.tone || "");
    setInputValue("#personality", state.config?.voice?.personality || "");

    // Dashboard stats
    if (stats) {
      const total = qs("#total-announcements");
      if (total) total.textContent = String(stats.total_runs || 0);
      const time = qs("#time-saved");
      if (time) time.textContent = `${Math.max(0, Math.round((stats.total_runs || 0) * 0.25))}h`;
    }

    updateProgress();

    // Google model selectors
    try {
      populateGoogleModelSelectors(state.googleModels);
    } catch (_) {}
  }

  function populateGoogleModelSelectors(models) {
    const textSel = qs("#google-text-model");
    const imageSel = qs("#google-image-model");
    if (!textSel || !imageSel) return;

    const cfg = state.config || {};
    const currentText = cfg?.ai?.model_text || "";
    const currentImage = cfg?.ai?.model_image || "";

    function setOptions(selectEl, selectedValue) {
      const items = Array.isArray(models) ? models : [];
      selectEl.innerHTML = "";
      if (!items.length) {
        const opt = document.createElement("option");
        opt.value = "";
        opt.textContent = "Click “Test & Load Models”";
        selectEl.appendChild(opt);
        selectEl.disabled = true;
        return;
      }

      for (const m of items) {
        const name = String(m?.name || "");
        if (!name) continue;
        const label = String(m?.display_name || name);
        const opt = document.createElement("option");
        opt.value = name;
        opt.textContent = label;
        selectEl.appendChild(opt);
      }
      selectEl.disabled = false;

      // Prefer keeping current selection if still available.
      const hasSelected = Array.from(selectEl.options).some((o) => o.value === selectedValue);
      if (hasSelected) selectEl.value = selectedValue;
    }

    setOptions(textSel, currentText);
    setOptions(imageSel, currentImage);
  }

  window.saveGoogleKey = async function saveGoogleKey() {
    const key = getInputValue("#google-api-key");
    await apiPost(API.env, { env: { GOOGLE_AI_KEY: key } });
    await refreshAll();
    showToast("Saved Google AI key to local .env");
  };

  window.saveGoogleModels = async function saveGoogleModels() {
    const textModel = getInputValue("#google-text-model");
    const imageModel = getInputValue("#google-image-model");
    const cfg = structuredClone(state.config || {});
    cfg.ai = cfg.ai || {};
    if (textModel) cfg.ai.model_text = textModel;
    if (imageModel) cfg.ai.model_image = imageModel;
    await apiPost(API.config, { config: cfg });
    await refreshAll();
    showToast("Saved selected Gemini models");
  };

  window.saveDiscordWebhook = async function saveDiscordWebhook() {
    const url = getInputValue("#discord-webhook");
    await apiPost(API.env, { env: { DISCORD_WEBHOOK_URL: url } });
    await refreshAll();
    showToast("Saved Discord webhook to local .env");
  };

  window.testGoogleAPI = async function testGoogleAPI() {
    try {
      const data = await apiGet(API.googleModels);
      const models = Array.isArray(data.models) ? data.models : [];
      state.googleModels = models;
      populateGoogleModelSelectors(models);
      showToast(`Google AI key OK. Found ${models.length} available models.`);
    } catch (e) {
      showToast(String(e.message || e));
    }
  };

  window.testDiscordWebhook = async function testDiscordWebhook() {
    const ok = confirm(
      "This will send a single test message to your Discord channel via the webhook URL you saved. Continue?"
    );
    if (!ok) return;
    try {
      await apiPost("/api/discord/test", {
        message:
          "✅ WishlistOps dashboard test: your Discord webhook is working.",
      });
      showToast("Test message sent to Discord");
    } catch (e) {
      showToast(String(e.message || e));
    }
  };

  window.saveGameConfig = async function saveGameConfig() {
    const cfg = structuredClone(state.config || {});
    cfg.version = cfg.version || "1.0";

    cfg.steam = cfg.steam || {};
    cfg.steam.app_id = getInputValue("#steam-app-id");
    cfg.steam.app_name = getInputValue("#game-name");

    cfg.branding = cfg.branding || {};
    const artStyle = getInputValue("#art-style");
    if (artStyle) cfg.branding.art_style = artStyle;

    cfg.voice = cfg.voice || {};
    const tone = getInputValue("#tone");
    const personality = getInputValue("#personality");
    if (tone) cfg.voice.tone = tone;
    if (personality) cfg.voice.personality = personality;

    await apiPost(API.config, { config: cfg });
    await refreshAll();
    showToast("Saved configuration");
  };

  window.resetGameConfig = async function resetGameConfig() {
    const cfg = structuredClone(state.config || {});
    if (cfg.steam) {
      cfg.steam.app_id = "";
      cfg.steam.app_name = "";
    }
    await apiPost(API.config, { config: cfg });
    await refreshAll();
    showToast("Reset game config");
  };

  function wireUploads() {
    const logoZone = qs("#logo-upload-zone");
    const logoInput = qs("#logo-input");
    const logoPreview = qs("#logo-preview");
    const logoPreviewImg = qs("#logo-preview-img");

    if (logoZone && logoInput) {
      logoZone.addEventListener("click", () => logoInput.click());
      logoInput.addEventListener("change", async () => {
        const file = logoInput.files && logoInput.files[0];
        if (!file) return;
        try {
          await apiUpload(API.uploadLogo, file);
          if (logoPreview && logoPreviewImg) {
            logoPreviewImg.src = URL.createObjectURL(file);
            logoPreview.classList.remove("hidden");
          }
          await refreshAll();
          showToast("Logo uploaded and config updated");
        } catch (e) {
          showToast(String(e.message || e));
        }
      });
    }

    const shotZone = qs("#screenshot-upload-zone");
    const shotInput = qs("#screenshot-input");
    if (shotZone && shotInput) {
      shotZone.addEventListener("click", () => shotInput.click());
      shotInput.addEventListener("change", async () => {
        const files = shotInput.files ? Array.from(shotInput.files) : [];
        if (!files.length) return;
        try {
          for (const file of files) {
            await apiUpload(API.uploadScreenshot, file);
          }
          showToast(`Uploaded ${files.length} screenshot(s)`);
        } catch (e) {
          showToast(String(e.message || e));
        }
      });
    }
  }

  function renderCommits(commits) {
    const host = qs("#commits-list");
    if (!host) return;

    if (!commits.length) {
      host.innerHTML = '<p class="text-muted">No player-facing commits found.</p>';
      return;
    }

    const items = commits
      .slice(0, 50)
      .map((c) => {
        const sha = String(c.sha || "").slice(0, 8);
        const msg = String(c.message || "").replace(/</g, "&lt;");
        return `
        <div style="text-align:left; padding:12px; border:1px solid var(--border-subtle); border-radius:10px; background: var(--bg-tertiary); margin-bottom:10px;">
          <label style="display:flex; gap:10px; align-items:flex-start; cursor:pointer;">
            <input type="checkbox" data-sha="${sha}" checked style="margin-top:4px;" />
            <div>
              <div style="font-weight:700;">${sha} <span style="color:var(--text-muted); font-weight:500;">${c.author || ""}</span></div>
              <div style="color:var(--text-secondary);">${msg}</div>
            </div>
          </label>
        </div>`;
      })
      .join("");

    host.innerHTML = `
      <div style="max-width:900px; margin:0 auto;">
        <div style="display:flex; gap:10px; justify-content:center; margin-bottom:16px; flex-wrap:wrap;">
          <button class="btn btn-secondary" id="btn-select-none">Select none</button>
          <button class="btn btn-secondary" id="btn-select-all">Select all</button>
          <button class="btn btn-primary" id="btn-generate">Generate Draft</button>
          <button class="btn btn-secondary" id="btn-generate-dry">Dry Run</button>
        </div>

        <div class="card" style="text-align:left; margin-bottom:16px;">
          <div class="card-header">
            <h3 class="card-title">Banner Image</h3>
          </div>
          <div class="card-body">
            <div class="text-secondary" style="margin-bottom:10px;">
              If you don’t pick an image, WishlistOps auto-selects one (priority: commit <span style="font-weight:700;">[shot: path]</span> directive → image files in selected commits → most recent screenshot folder).
            </div>

            <div style="display:flex; gap:12px; flex-wrap:wrap; align-items:center; margin-bottom:10px;">
              <label style="display:flex; gap:8px; align-items:center;">
                <input type="radio" name="shot-mode" value="auto" checked />
                Auto-select
              </label>
              <label style="display:flex; gap:8px; align-items:center;">
                <input type="radio" name="shot-mode" value="manual" />
                Choose manually
              </label>
              <label style="display:flex; gap:8px; align-items:center;">
                <input type="checkbox" id="with-logo" checked />
                Overlay logo
              </label>
            </div>

            <div style="display:flex; gap:10px; flex-wrap:wrap; align-items:center;">
              <select class="form-input" id="screenshot-select" style="min-width: 340px;" disabled>
                <option value="">Loading screenshots…</option>
              </select>
              <select class="form-input" id="crop-mode-generate" style="width:auto;">
                <option value="smart">Smart (Auto-detect)</option>
                <option value="center">Center</option>
                <option value="top">Top</option>
                <option value="bottom">Bottom</option>
                <option value="thirds">Rule of Thirds</option>
                <option value="left">Left</option>
                <option value="right">Right</option>
              </select>
              <button class="btn btn-secondary" id="btn-banner-preview">Update Preview</button>
            </div>

            <div id="banner-preview" style="margin-top:12px;"></div>
          </div>
        </div>

        ${items}
        <div id="draft-output" style="margin-top:18px;"></div>
      </div>
    `;

    const shotSelect = qs("#screenshot-select");
    const shotModeRadios = qsa('input[name="shot-mode"]');
    const cropModeEl = qs("#crop-mode-generate");
    const withLogoEl = qs("#with-logo");
    const previewHost = qs("#banner-preview");

    function getSelectedCommitShas() {
      return qsa("#commits-list input[type=checkbox]")
        .filter((cb) => cb.checked)
        .map((cb) => cb.dataset.sha);
    }

    function getSelectedCommitObjects() {
      const shas = new Set(getSelectedCommitShas());
      return (state.commits || []).filter((c) => shas.has(String(c.sha || "").slice(0, 8)));
    }

    function computeAutoScreenshotPath() {
      const selectedCommits = getSelectedCommitObjects();
      const fromSelected = selectedCommits
        .map((c) => c.screenshot_path)
        .filter(Boolean)
        .map(normalizePath);
      if (fromSelected.length) return fromSelected[0];
      const first = (state.screenshots || [])[0];
      return first ? normalizePath(first.path) : "";
    }

    function isManualMode() {
      const selected = shotModeRadios.find((r) => r.checked);
      return selected && selected.value === "manual";
    }

    function currentScreenshotChoice() {
      const manual = isManualMode();
      const autoPath = computeAutoScreenshotPath();
      const chosen = manual ? normalizePath(getInputValue("#screenshot-select")) : autoPath;
      return { manual, chosen, autoPath };
    }

    function setScreenshotSelectEnabled() {
      if (!shotSelect) return;
      shotSelect.disabled = !isManualMode() || !shotSelect.options.length;
    }

    async function loadScreenshots() {
      try {
        const data = await apiGet(API.screenshots);
        state.screenshots = Array.isArray(data.screenshots) ? data.screenshots : [];
      } catch (_) {
        state.screenshots = [];
      }

      const fromCommits = uniqueNonEmpty((state.commits || []).map((c) => c.screenshot_path));
      const fromDisk = uniqueNonEmpty((state.screenshots || []).map((s) => s.path));
      const candidates = uniqueNonEmpty([...fromCommits, ...fromDisk]);

      if (shotSelect) {
        shotSelect.innerHTML = "";
        if (!candidates.length) {
          const opt = document.createElement("option");
          opt.value = "";
          opt.textContent = "No screenshots found (upload some under screenshots/ or promo/)";
          shotSelect.appendChild(opt);
          shotSelect.disabled = true;
        } else {
          for (const p of candidates) {
            const opt = document.createElement("option");
            opt.value = p;
            opt.textContent = p;
            shotSelect.appendChild(opt);
          }
          shotSelect.disabled = !isManualMode();
          // Prefer a commit-linked screenshot if available.
          const initial = computeAutoScreenshotPath() || candidates[0];
          if (initial) shotSelect.value = initial;
        }
      }

      setScreenshotSelectEnabled();
    }

    async function updateBannerPreview() {
      if (!previewHost) return;
      const { manual, chosen, autoPath } = currentScreenshotChoice();
      const cropMode = cropModeEl ? cropModeEl.value : "smart";
      const withLogo = withLogoEl ? !!withLogoEl.checked : true;

      if (!chosen) {
        previewHost.innerHTML = '<div class="text-muted">No screenshot selected.</div>';
        return;
      }

      previewHost.innerHTML = '<div class="text-muted">Generating preview…</div>';
      try {
        const res = await apiPost(API.bannerPreview, {
          screenshot_path: chosen,
          crop_mode: cropMode,
          with_logo: withLogo,
        });
        const rel = normalizePath(res.preview_path);
        const src = `/files/${encodeURIComponent(rel).replace(/%2F/g, "/")}`;
        previewHost.innerHTML = `
          <div class="text-muted" style="margin-bottom:6px;">Preview (${manual ? "manual" : "auto"}${manual ? "" : autoPath ? ": " + escapeHTML(autoPath) : ""})</div>
          <img alt="Banner preview" src="${src}" style="max-width:100%; border-radius: 12px; border: 1px solid var(--border-subtle);" />
          <div class="text-muted" style="margin-top:8px;">Using: ${escapeHTML(chosen)} • Crop: ${escapeHTML(cropMode)} • Logo: ${withLogo ? "on" : "off"}</div>
        `;
      } catch (e) {
        previewHost.innerHTML = '<div class="text-muted">Preview failed.</div>';
        showToast(String(e.message || e));
      }
    }

    qs("#btn-select-none")?.addEventListener("click", () =>
      qsa("#commits-list input[type=checkbox]").forEach((cb) => (cb.checked = false))
    );
    qs("#btn-select-all")?.addEventListener("click", () =>
      qsa("#commits-list input[type=checkbox]").forEach((cb) => (cb.checked = true))
    );

    // Banner controls wiring
    shotModeRadios.forEach((r) =>
      r.addEventListener("change", () => {
        setScreenshotSelectEnabled();
        updateBannerPreview();
      })
    );
    cropModeEl?.addEventListener("change", () => updateBannerPreview());
    withLogoEl?.addEventListener("change", () => updateBannerPreview());
    qs("#btn-banner-preview")?.addEventListener("click", () => updateBannerPreview());
    qsa("#commits-list input[type=checkbox]").forEach((cb) =>
      cb.addEventListener("change", () => {
        if (!isManualMode()) updateBannerPreview();
      })
    );

    loadScreenshots().then(() => updateBannerPreview());

    async function doGenerate(dryRun) {
      const shas = qsa("#commits-list input[type=checkbox]")
        .filter((cb) => cb.checked)
        .map((cb) => cb.dataset.sha);

      const { chosen } = currentScreenshotChoice();
      const cropMode = cropModeEl ? cropModeEl.value : "smart";
      const withLogo = withLogoEl ? !!withLogoEl.checked : true;

      try {
        const res = await apiPost(API.generate, {
          dry_run: !!dryRun,
          commit_shas: shas,
          screenshot_path: chosen || undefined,
          crop_mode: cropMode,
          with_logo: withLogo,
        });
        state.lastDraft = res.draft;
        renderDraft(res.draft);
      } catch (e) {
        showToast(String(e.message || e));
      }
    }

    qs("#btn-generate")?.addEventListener("click", () => doGenerate(false));
    qs("#btn-generate-dry")?.addEventListener("click", () => doGenerate(true));
  }

  function renderDraft(draft) {
    const host = qs("#draft-output");
    if (!host || !draft) return;
    const rawTitle = String(draft.title || "");
    const rawBody = String(draft.body || "");
    const title = escapeHTML(rawTitle);
    const body = escapeHTML(rawBody);
    const bannerRel = draft.banner_path ? normalizePath(draft.banner_path) : "";
    const screenshotUsed = draft.screenshot_used ? normalizePath(draft.screenshot_used) : "";
    const screenshotSource = draft.screenshot_source ? String(draft.screenshot_source) : "";
    const bannerImg = bannerRel
      ? `<div style="margin-top:12px;">
           <div class="text-muted" style="margin-bottom:8px;">Banner preview</div>
           <img alt="Banner preview" src="/files/${encodeURIComponent(bannerRel).replace(/%2F/g, "/")}" style="max-width:100%; border-radius: 12px; border: 1px solid var(--border-subtle);" />
           <div class="text-muted" style="margin-top:8px;">${bannerRel}</div>
         </div>`
      : "";

    const shotInfo = screenshotUsed
      ? `<div class="text-muted" style="margin-top:10px;">Screenshot: ${escapeHTML(screenshotUsed)}${screenshotSource ? ` (${escapeHTML(screenshotSource)})` : ""}</div>`
      : `<div class="text-muted" style="margin-top:10px;">Screenshot: none (banner generation skipped)</div>`;

    function bbcodeToHtml(text) {
      // Minimal Steam-BBCode-ish preview renderer.
      // Goal: make it look nice; copy uses raw text.
      let t = String(text || "");
      // Escape first.
      t = escapeHTML(t);

      // Headings
      t = t.replace(/\[h1\]([\s\S]*?)\[\/h1\]/gi, "<div style=\"font-size:1.35rem; font-weight:900; margin: 0 0 10px 0;\">$1</div>");
      t = t.replace(/\[h2\]([\s\S]*?)\[\/h2\]/gi, "<div style=\"font-size:1.1rem; font-weight:800; margin: 14px 0 8px 0;\">$1</div>");

      // Inline styles
      t = t.replace(/\[b\]([\s\S]*?)\[\/b\]/gi, "<strong>$1</strong>");
      t = t.replace(/\[i\]([\s\S]*?)\[\/i\]/gi, "<em>$1</em>");
      t = t.replace(/\[u\]([\s\S]*?)\[\/u\]/gi, "<span style=\"text-decoration:underline;\">$1</span>");

      // Links: [url=https://...]text[/url]
      t = t.replace(/\[url=([^\]]+)\]([\s\S]*?)\[\/url\]/gi, (m, href, label) => {
        const safeHref = String(href || "").replace(/"/g, "&quot;");
        return `<a href=\"${safeHref}\" target=\"_blank\" rel=\"noreferrer\" style=\"color: var(--accent-primary); text-decoration:none;\">${label}</a>`;
      });

      // Lists: [list]\n[*]item\n[*]item\n[/list]
      if (/\[list\]/i.test(t)) {
        t = t.replace(/\[list\]([\s\S]*?)\[\/list\]/gi, (m, inner) => {
          const items = String(inner)
            .split(/\[\*\]/)
            .map((x) => x.trim())
            .filter(Boolean)
            .map((x) => `<li style=\"margin: 4px 0;\">${x}</li>`)
            .join("");
          return `<ul style=\"margin: 8px 0 8px 18px; color: var(--text-secondary);\">${items}</ul>`;
        });
      }

      // Newlines
      t = t.replace(/\n/g, "<br>");
      return t;
    }

    const prettyBodyHtml = bbcodeToHtml(rawBody);
    const steamCopyText = `${rawTitle}\n\n${rawBody}`.replace(/\r\n/g, "\n");

    const discordConfigured = Boolean(state.env && state.env.DISCORD_WEBHOOK_URL);
    const discordEnabled = getProjectDiscordEnabled();
    const canSendDiscord = discordConfigured && discordEnabled;

    host.innerHTML = `
      <div class="card" style="text-align:left;">
        <div class="card-header">
          <h3 class="card-title">Draft</h3>
          <div class="flex gap-sm" style="flex-wrap:wrap; justify-content:flex-end;">
            <button class="btn btn-secondary" id="btn-copy-title">Copy Title</button>
            <button class="btn btn-secondary" id="btn-copy-body">Copy Body</button>
            <button class="btn btn-secondary" id="btn-copy-all">Copy Full</button>
            ${canSendDiscord ? '<button class="btn btn-success" id="btn-send">Send to Discord</button>' : ''}
          </div>
        </div>
        <div class="card-body">
          <div style="font-weight:900; font-size:1.2rem; margin-bottom:10px;">${title}</div>

          <div style="padding: 14px; border-radius: 14px; border: 1px solid var(--border-subtle); background: rgba(255,255,255,0.02);">
            <div class="text-muted" style="font-size:0.8rem; margin-bottom: 8px;">Preview (Steam-style)</div>
            <div style="color: var(--text-secondary); line-height: 1.7;">${prettyBodyHtml}</div>
          </div>

          <div class="mt-lg" style="margin-top: 16px;">
            <div class="text-muted" style="font-size:0.8rem; margin-bottom: 8px;">Copy/Paste for Steam (keeps formatting tags)</div>
            <textarea class="form-input" id="steam-copy" style="height: 220px; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace;">${escapeHTML(steamCopyText)}</textarea>
          </div>

          ${!discordEnabled ? '<div class="alert alert-info mt-lg"><span class="alert-icon">ℹ️</span><div class="alert-content"><h5>Discord step disabled</h5><p>This draft will not be sent to Discord. Use the copy buttons above to paste into Steam.</p></div></div>' : ''}
          ${discordEnabled && !discordConfigured ? '<div class="alert alert-warning mt-lg"><span class="alert-icon">⚠️</span><div class="alert-content"><h5>Discord not configured</h5><p>Add <strong>DISCORD_WEBHOOK_URL</strong> in API Keys to enable the approval step.</p></div></div>' : ''}

          ${bannerImg}
          ${shotInfo}
        </div>
      </div>
    `;

    async function copyText(label, text) {
      try {
        await navigator.clipboard.writeText(String(text || ""));
        showToast(`Copied ${label}`);
      } catch (_) {
        // Fallback
        const ta = qs("#steam-copy");
        if (ta) {
          ta.focus();
          ta.select();
        }
        showToast(`Select and copy ${label} manually`);
      }
    }

    qs("#btn-copy-title")?.addEventListener("click", () => copyText("title", rawTitle));
    qs("#btn-copy-body")?.addEventListener("click", () => copyText("body", rawBody));
    qs("#btn-copy-all")?.addEventListener("click", () => copyText("full announcement", steamCopyText));

    qs("#btn-send")?.addEventListener("click", async () => {
      try {
        await apiPost(API.send, { draft });
        showToast("Sent to Discord for approval");
      } catch (e) {
        showToast(String(e.message || e));
      }
    });
  }

  window.loadCommits = async function loadCommits() {
    try {
      const data = await apiGet(API.commits);
      state.commits = data.commits || [];
      renderCommits(state.commits);
    } catch (e) {
      showToast(String(e.message || e));
    }
  };

  // Preview tab actions are not implemented; keep existing UX minimal.
  window.resetPreview = function resetPreview() {
    showToast("Preview & crop UI is not wired yet.");
  };
  window.processAndSave = function processAndSave() {
    showToast("Preview & crop UI is not wired yet.");
  };

  async function boot() {
    try {
      await apiGet(API.health);
      setConnection("ok", "Local");
      await loadProjects();
      await refreshAll();

      const discordToggle = qs("#settings-discord-enabled");
      if (discordToggle) {
        discordToggle.checked = getProjectDiscordEnabled();
        discordToggle.addEventListener("change", async () => {
          const active = getActiveProject();
          if (!active) {
            showToast("No active project selected");
            discordToggle.checked = true;
            return;
          }

          const desired = Boolean(discordToggle.checked);
          try {
            await apiPost(API.projects, {
              project: {
                id: String(active.id || ""),
                name: String(active.name || "Project"),
                repo_path: String(active.repo_path || ""),
                config_path: String(active.config_path || ""),
                discord_enabled: desired,
              },
            });
            await loadProjects();
            if (state.lastDraft) renderDraft(state.lastDraft);
            showToast(desired ? "Discord step enabled for this project" : "Discord step disabled for this project");
          } catch (e) {
            showToast(String(e.message || e));
            // Revert UI on failure.
            discordToggle.checked = getProjectDiscordEnabled();
          }
        });
      }

      wireUploads();
    } catch (e) {
      setConnection("offline", "Offline");
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();

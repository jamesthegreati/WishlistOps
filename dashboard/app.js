/**
 * WishlistOps Dashboard - JavaScript Application
 * 
 * Handles GitHub OAuth, API interactions, configuration management,
 * command palette, theme toggle, onboarding wizard, and announcement generation.
 * Pure vanilla JavaScript (no framework dependencies).
 * 
 * Architecture: Static site with GitHub API integration
 * Authentication: GitHub OAuth (device flow for simplicity)
 */

// ========================================
// Configuration
// ========================================

const CONFIG = {
    // GitHub API
    githubApiUrl: 'https://api.github.com',
    
    // Local storage keys
    storageKeys: {
        accessToken: 'wishlistops_github_token',
        currentUser: 'wishlistops_current_user',
        currentRepo: 'wishlistops_current_repo',
        theme: 'wishlistops_theme',
        onboardingComplete: 'wishlistops_onboarding_complete',
        voiceSettings: 'wishlistops_voice_settings',
        announcements: 'wishlistops_announcements',
        llmApiKey: 'wishlistops_llm_api_key',
        llmBaseUrl: 'wishlistops_llm_base_url',
        llmModel: 'wishlistops_llm_model'
    },
    
    // WishlistOps config file path
    configPath: 'wishlistops/config.json'
};


// ========================================
// State Management
// ========================================

class AppState {
    constructor() {
        this.accessToken = localStorage.getItem(CONFIG.storageKeys.accessToken);
        this.currentUser = JSON.parse(localStorage.getItem(CONFIG.storageKeys.currentUser) || 'null');
        this.currentRepo = JSON.parse(localStorage.getItem(CONFIG.storageKeys.currentRepo) || 'null');
        this.onboardingComplete = localStorage.getItem(CONFIG.storageKeys.onboardingComplete) === 'true';
        this.voiceSettings = JSON.parse(localStorage.getItem(CONFIG.storageKeys.voiceSettings) || 'null');
        this.llmApiKey = localStorage.getItem(CONFIG.storageKeys.llmApiKey) || '';
        this.llmBaseUrl = localStorage.getItem(CONFIG.storageKeys.llmBaseUrl) || 'https://generativelanguage.googleapis.com';
        this.llmModel = localStorage.getItem(CONFIG.storageKeys.llmModel) || '';
    }
    
    setAccessToken(token) {
        this.accessToken = token;
        localStorage.setItem(CONFIG.storageKeys.accessToken, token);
    }
    
    setCurrentUser(user) {
        this.currentUser = user;
        localStorage.setItem(CONFIG.storageKeys.currentUser, JSON.stringify(user));
    }
    
    setCurrentRepo(repo) {
        this.currentRepo = repo;
        localStorage.setItem(CONFIG.storageKeys.currentRepo, JSON.stringify(repo));
    }

    setOnboardingComplete(val) {
        this.onboardingComplete = val;
        localStorage.setItem(CONFIG.storageKeys.onboardingComplete, String(val));
    }

    setVoiceSettings(settings) {
        this.voiceSettings = settings;
        localStorage.setItem(CONFIG.storageKeys.voiceSettings, JSON.stringify(settings));
    }

    setLlmApiKey(key) {
        this.llmApiKey = key;
        localStorage.setItem(CONFIG.storageKeys.llmApiKey, key);
    }

    setLlmBaseUrl(url) {
        this.llmBaseUrl = url;
        localStorage.setItem(CONFIG.storageKeys.llmBaseUrl, url);
    }

    setLlmModel(model) {
        this.llmModel = model;
        localStorage.setItem(CONFIG.storageKeys.llmModel, model);
    }
    
    clearAuth() {
        this.accessToken = null;
        this.currentUser = null;
        this.currentRepo = null;
        this.onboardingComplete = false;
        this.voiceSettings = null;
        this.llmApiKey = '';
        this.llmBaseUrl = 'https://generativelanguage.googleapis.com';
        this.llmModel = '';
        localStorage.removeItem(CONFIG.storageKeys.accessToken);
        localStorage.removeItem(CONFIG.storageKeys.currentUser);
        localStorage.removeItem(CONFIG.storageKeys.currentRepo);
        localStorage.removeItem(CONFIG.storageKeys.onboardingComplete);
        localStorage.removeItem(CONFIG.storageKeys.voiceSettings);
        localStorage.removeItem(CONFIG.storageKeys.llmApiKey);
        localStorage.removeItem(CONFIG.storageKeys.llmBaseUrl);
        localStorage.removeItem(CONFIG.storageKeys.llmModel);
    }
    
    isAuthenticated() {
        return !!this.accessToken;
    }
}

const state = new AppState();


// ========================================
// GitHub API Client
// ========================================

class GitHubAPI {
    constructor(accessToken) {
        this.accessToken = accessToken;
    }
    
    async request(endpoint, options = {}) {
        const url = `${CONFIG.githubApiUrl}${endpoint}`;
        const headers = {
            'Accept': 'application/vnd.github.v3+json',
            ...options.headers
        };
        
        if (this.accessToken) {
            headers['Authorization'] = `token ${this.accessToken}`;
        }
        
        const response = await fetch(url, {
            ...options,
            headers
        });
        
        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            throw new Error(error.message || `GitHub API error: ${response.status}`);
        }
        
        return response.json();
    }
    
    async getCurrentUser() {
        return this.request('/user');
    }
    
    async getUserRepos() {
        return this.request('/user/repos?sort=updated&per_page=100');
    }
    
    async getRepoContents(owner, repo, path) {
        return this.request(`/repos/${owner}/${repo}/contents/${path}`);
    }

    async getRepoCommits(owner, repo, perPage = 10) {
        return this.request(`/repos/${owner}/${repo}/commits?per_page=${perPage}`);
    }
    
    async updateFile(owner, repo, path, content, message, sha) {
        return this.request(`/repos/${owner}/${repo}/contents/${path}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message,
                content: btoa(unescape(encodeURIComponent(content))),
                sha
            })
        });
    }
}


// ========================================
// LLM API Client (Google Generative AI compatible)
// ========================================

class LlmAPI {
    constructor(apiKey, baseUrl) {
        this.apiKey = apiKey;
        this.baseUrl = (baseUrl || 'https://generativelanguage.googleapis.com').replace(/\/+$/, '');
    }

    async fetchModels() {
        const url = `${this.baseUrl}/v1beta/models`;
        const response = await fetch(url, {
            headers: { 'x-goog-api-key': this.apiKey }
        });
        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.error?.message || `Failed to fetch models: ${response.status}`);
        }
        const data = await response.json();
        // Filter to models that support generateContent
        return (data.models || []).filter(m =>
            m.supportedGenerationMethods && m.supportedGenerationMethods.includes('generateContent')
        );
    }

    async generateContent(model, prompt, temperature = 0.7) {
        const modelName = model.startsWith('models/') ? model : `models/${model}`;
        const url = `${this.baseUrl}/v1beta/${modelName}:generateContent`;
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'x-goog-api-key': this.apiKey
            },
            body: JSON.stringify({
                contents: [{ parts: [{ text: prompt }] }],
                generationConfig: { temperature }
            })
        });
        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.error?.message || `LLM generation failed: ${response.status}`);
        }
        const data = await response.json();
        const candidate = data.candidates && data.candidates[0];
        if (!candidate || !candidate.content || !candidate.content.parts) {
            throw new Error('No content returned from the model');
        }
        return candidate.content.parts.map(p => p.text || '').join('');
    }
}

class ThemeManager {
    constructor() {
        this.toggle = document.getElementById('theme-toggle');
        const saved = localStorage.getItem(CONFIG.storageKeys.theme) || 'dark';
        this.setTheme(saved);
        this.toggle.addEventListener('click', () => this.toggleTheme());
    }

    setTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem(CONFIG.storageKeys.theme, theme);
        this.toggle.textContent = theme === 'dark' ? '🌙' : '☀️';
    }

    toggleTheme() {
        const current = document.documentElement.getAttribute('data-theme');
        this.setTheme(current === 'dark' ? 'light' : 'dark');
    }
}


// ========================================
// Command Palette
// ========================================

class CommandPalette {
    constructor(uiManager) {
        this.ui = uiManager;
        this.overlay = document.getElementById('command-palette-overlay');
        this.input = document.getElementById('command-input');
        this.results = document.getElementById('command-results');
        this.activeIndex = 0;
        this.commands = this.getCommands();

        document.getElementById('cmd-k-hint').addEventListener('click', () => this.open());

        document.addEventListener('keydown', (e) => {
            if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
                e.preventDefault();
                this.toggle();
            }
            if (e.key === 'Escape' && !this.overlay.classList.contains('hidden')) {
                this.close();
            }
        });

        this.input.addEventListener('input', () => this.render());
        this.input.addEventListener('keydown', (e) => this.handleKeyNav(e));
        this.overlay.addEventListener('click', (e) => {
            if (e.target === this.overlay) this.close();
        });
    }

    getCommands() {
        return [
            { icon: '⚡', label: 'Generate Announcement', action: () => this.ui.showDashboard(), shortcut: '' },
            { icon: '📜', label: 'View Past Announcements', action: () => { this.ui.showDashboard().then(() => this.ui.switchDashboardTab('history')); }, shortcut: '' },
            { icon: '⚙️', label: 'Open Settings', action: () => this.ui.showConfigEditor(), shortcut: '' },
            { icon: '📂', label: 'Switch Repository', action: () => this.ui.showRepoSelection(), shortcut: '' },
            { icon: '🌙', label: 'Toggle Theme', action: () => document.getElementById('theme-toggle').click(), shortcut: '' },
            { icon: '📋', label: 'Preview JSON Config', action: () => { if (this.ui.elements.previewBtn) this.ui.showPreview(); }, shortcut: '' },
            { icon: '🔑', label: 'Sign In / Sign Out', action: () => {
                if (state.isAuthenticated()) { this.ui.handleSignOut(); } else { this.ui.handleSignIn(); }
            }, shortcut: '' },
        ];
    }

    toggle() {
        if (this.overlay.classList.contains('hidden')) { this.open(); } else { this.close(); }
    }

    open() {
        this.overlay.classList.remove('hidden');
        this.input.value = '';
        this.activeIndex = 0;
        this.render();
        this.input.focus();
    }

    close() {
        this.overlay.classList.add('hidden');
    }

    render() {
        const query = this.input.value.toLowerCase();
        const filtered = this.commands.filter(c => c.label.toLowerCase().includes(query));
        this.results.innerHTML = '';
        filtered.forEach((cmd, i) => {
            const div = document.createElement('div');
            div.className = 'command-item' + (i === this.activeIndex ? ' active' : '');
            div.innerHTML = `
                <span class="command-item-icon">${cmd.icon}</span>
                <span class="command-item-label">${cmd.label}</span>
                ${cmd.shortcut ? `<span class="command-item-shortcut">${cmd.shortcut}</span>` : ''}
            `;
            div.addEventListener('click', () => { this.close(); cmd.action(); });
            div.addEventListener('mouseenter', () => {
                this.activeIndex = i;
                this.render();
            });
            this.results.appendChild(div);
        });
    }

    handleKeyNav(e) {
        const items = this.results.querySelectorAll('.command-item');
        if (e.key === 'ArrowDown') {
            e.preventDefault();
            this.activeIndex = Math.min(this.activeIndex + 1, items.length - 1);
            this.render();
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            this.activeIndex = Math.max(this.activeIndex - 1, 0);
            this.render();
        } else if (e.key === 'Enter') {
            e.preventDefault();
            if (items[this.activeIndex]) items[this.activeIndex].click();
        }
    }
}


// ========================================
// Image Upload Manager
// ========================================

class ImageUploadManager {
    constructor() {
        this.dropZone = document.getElementById('image-drop-zone');
        this.fileInput = document.getElementById('image-upload');
        this.previewGrid = document.getElementById('image-preview-grid');
        this.files = [];
        this.dataUrls = [];

        if (!this.dropZone) return;

        this.dropZone.addEventListener('click', () => this.fileInput.click());
        this.dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            this.dropZone.classList.add('dragover');
        });
        this.dropZone.addEventListener('dragleave', () => {
            this.dropZone.classList.remove('dragover');
        });
        this.dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            this.dropZone.classList.remove('dragover');
            this.addFiles(e.dataTransfer.files);
        });
        this.fileInput.addEventListener('change', () => {
            this.addFiles(this.fileInput.files);
            this.fileInput.value = '';
        });
    }

    addFiles(fileList) {
        for (const file of fileList) {
            if (!file.type.startsWith('image/')) continue;
            if (file.size > 5 * 1024 * 1024) continue;
            this.files.push(file);
            // Generate data URL for history persistence
            const reader = new FileReader();
            const index = this.dataUrls.length;
            this.dataUrls.push('');
            reader.onload = (e) => {
                this.dataUrls[index] = e.target.result;
            };
            reader.readAsDataURL(file);
        }
        this.renderPreviews();
    }

    removeFile(index) {
        this.files.splice(index, 1);
        this.dataUrls.splice(index, 1);
        this.renderPreviews();
    }

    renderPreviews() {
        if (!this.previewGrid) return;
        this.previewGrid.innerHTML = '';
        this.files.forEach((file, i) => {
            const item = document.createElement('div');
            item.className = 'image-preview-item';
            const img = document.createElement('img');
            img.src = URL.createObjectURL(file);
            img.alt = file.name;
            const removeBtn = document.createElement('button');
            removeBtn.className = 'remove-btn';
            removeBtn.textContent = '×';
            removeBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.removeFile(i);
            });
            item.appendChild(img);
            item.appendChild(removeBtn);
            this.previewGrid.appendChild(item);
        });
    }
}


// ========================================
// Announcement History Manager
// ========================================

class AnnouncementHistory {
    constructor() {
        this.storageKey = CONFIG.storageKeys.announcements;
    }

    getAll() {
        try {
            return JSON.parse(localStorage.getItem(this.storageKey) || '[]');
        } catch {
            return [];
        }
    }

    save(announcement) {
        const all = this.getAll();
        all.unshift(announcement);
        // Keep last 50 announcements
        if (all.length > 50) all.length = 50;
        localStorage.setItem(this.storageKey, JSON.stringify(all));
    }

    remove(id) {
        const all = this.getAll().filter(a => a.id !== id);
        localStorage.setItem(this.storageKey, JSON.stringify(all));
    }

    clearAll() {
        localStorage.removeItem(this.storageKey);
    }
}


// ========================================
// UI Manager
// ========================================

class UIManager {
    constructor() {
        this.announcementHistory = new AnnouncementHistory();
        this.imageUpload = null; // Set after ImageUploadManager init
        this.elements = {
            // Screens
            welcomeScreen: document.getElementById('welcome-screen'),
            repoSelection: document.getElementById('repo-selection'),
            configEditor: document.getElementById('config-editor'),
            dashboardMain: document.getElementById('dashboard-main'),
            onboardingWizard: document.getElementById('onboarding-wizard'),
            loading: document.getElementById('loading'),
            skeletonLoading: document.getElementById('skeleton-loading'),
            
            // Auth
            signInBtn: document.getElementById('sign-in-btn'),
            signOutBtn: document.getElementById('sign-out-btn'),
            userInfo: document.getElementById('user-info'),
            userAvatar: document.getElementById('user-avatar'),
            userName: document.getElementById('user-name'),
            
            // Repo selection
            reposList: document.getElementById('repos-list'),
            
            // Config editor
            currentRepoName: document.getElementById('current-repo-name'),
            backToRepos: document.getElementById('back-to-repos'),
            backToDashboard: document.getElementById('back-to-dashboard'),
            configForm: document.getElementById('config-form'),
            statusMessage: document.getElementById('status-message'),
            
            // Form inputs
            steamAppId: document.getElementById('steam-app-id'),
            steamAppName: document.getElementById('steam-app-name'),
            artStyle: document.getElementById('art-style'),
            colorPalette: document.getElementById('color-palette'),
            logoPosition: document.getElementById('logo-position'),
            logoSize: document.getElementById('logo-size'),
            logoSizeValue: document.getElementById('logo-size-value'),
            tone: document.getElementById('tone'),
            personality: document.getElementById('personality'),
            avoidPhrases: document.getElementById('avoid-phrases'),
            automationEnabled: document.getElementById('automation-enabled'),
            triggerOnTags: document.getElementById('trigger-on-tags'),
            minDays: document.getElementById('min-days'),
            requireApproval: document.getElementById('require-approval'),
            temperature: document.getElementById('temperature'),
            temperatureValue: document.getElementById('temperature-value'),
            
            // Modal
            previewModal: document.getElementById('preview-modal'),
            previewJson: document.getElementById('preview-json'),
            previewBtn: document.getElementById('preview-btn'),

            // Dashboard
            dashboardRepoName: document.getElementById('dashboard-repo-name'),
            dashboardCommits: document.getElementById('dashboard-commits'),
            announcementComposer: document.getElementById('announcement-composer'),
            announcementText: document.getElementById('announcement-text'),
            generateBtn: document.getElementById('generate-btn'),

            // Onboarding
            wizardReposList: document.getElementById('wizard-repos-list'),

            // LLM settings
            llmApiKey: document.getElementById('llm-api-key'),
            llmBaseUrl: document.getElementById('llm-base-url'),
            llmModel: document.getElementById('llm-model'),
            fetchModelsBtn: document.getElementById('fetch-models-btn'),
            llmModelStatus: document.getElementById('llm-model-status'),
        };
        
        this.setupEventListeners();
    }
    
    setupEventListeners() {
        // Auth
        this.elements.signInBtn.addEventListener('click', () => this.handleSignIn());
        this.elements.signOutBtn.addEventListener('click', () => this.handleSignOut());
        
        // Navigation
        this.elements.backToRepos.addEventListener('click', () => this.showRepoSelection());
        this.elements.backToDashboard.addEventListener('click', () => this.showDashboard());
        document.getElementById('back-to-repos-dash').addEventListener('click', () => this.showRepoSelection());
        document.getElementById('config-nav-btn').addEventListener('click', () => this.showConfigEditor());
        document.getElementById('generate-nav-btn').addEventListener('click', () => {
            this.switchDashboardTab('generate');
        });
        document.getElementById('history-nav-btn').addEventListener('click', () => {
            this.switchDashboardTab('history');
        });
        
        // Form
        this.elements.configForm.addEventListener('submit', (e) => this.handleFormSubmit(e));
        this.elements.previewBtn.addEventListener('click', () => this.showPreview());
        
        // Range inputs
        this.elements.logoSize.addEventListener('input', (e) => {
            this.elements.logoSizeValue.textContent = `${e.target.value}%`;
        });
        this.elements.temperature.addEventListener('input', (e) => {
            this.elements.temperatureValue.textContent = e.target.value;
        });
        
        // Modal close
        const closeButtons = document.querySelectorAll('.modal .close');
        closeButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                this.elements.previewModal.classList.add('hidden');
            });
        });
        
        this.elements.previewModal.addEventListener('click', (e) => {
            if (e.target === this.elements.previewModal) {
                this.elements.previewModal.classList.add('hidden');
            }
        });

        // Announcement tabs (Edit/Preview)
        document.querySelectorAll('.announcement-tab').forEach(tab => {
            tab.addEventListener('click', () => {
                document.querySelectorAll('.announcement-tab').forEach(t => t.classList.remove('active'));
                tab.classList.add('active');
                const tabName = tab.getAttribute('data-tab');
                document.getElementById('tab-edit').classList.toggle('hidden', tabName !== 'edit');
                document.getElementById('tab-preview').classList.toggle('hidden', tabName !== 'preview');
                if (tabName === 'preview') this.updateSteamPreview();
            });
        });

        // Dashboard tabs (Generate/History)
        document.querySelectorAll('.dashboard-tab').forEach(tab => {
            tab.addEventListener('click', () => {
                this.switchDashboardTab(tab.getAttribute('data-dtab'));
            });
        });

        // Announcement type change
        document.getElementById('announcement-type').addEventListener('change', (e) => {
            document.getElementById('preview-badge').textContent = e.target.value;
        });

        // Character count
        this.elements.announcementText.addEventListener('input', () => {
            this.updateCharCount();
        });

        // Generate announcement
        this.elements.generateBtn.addEventListener('click', () => {
            this.generateAnnouncement().catch(err => this.showStatus(`Error: ${err.message}`, 'error'));
        });

        // Copy to clipboard
        document.getElementById('copy-btn').addEventListener('click', () => {
            const text = this.elements.announcementText.value;
            navigator.clipboard.writeText(text).then(() => {
                this.showStatus('Copied to clipboard! 📋', 'success');
            });
        });

        // Approve button
        document.getElementById('approve-btn').addEventListener('click', () => {
            this.approveAnnouncement();
        });

        // Clear history
        document.getElementById('clear-history-btn').addEventListener('click', () => {
            if (confirm('Clear all past announcements?')) {
                this.announcementHistory.clearAll();
                this.renderHistory();
                this.showStatus('History cleared.', 'info');
            }
        });

        // LLM settings
        this.elements.fetchModelsBtn.addEventListener('click', () => this.fetchLlmModels());
        this.elements.llmApiKey.addEventListener('change', () => {
            state.setLlmApiKey(this.elements.llmApiKey.value.trim());
        });
        this.elements.llmBaseUrl.addEventListener('change', () => {
            state.setLlmBaseUrl(this.elements.llmBaseUrl.value.trim());
        });
        this.elements.llmModel.addEventListener('change', () => {
            state.setLlmModel(this.elements.llmModel.value);
        });

        // Onboarding wizard
        this.setupOnboardingWizard();
    }

    setupOnboardingWizard() {
        // Voice option selection
        document.querySelectorAll('.voice-option').forEach(opt => {
            opt.addEventListener('click', () => {
                document.querySelectorAll('.voice-option').forEach(o => o.classList.remove('selected'));
                opt.classList.add('selected');
                document.getElementById('wizard-custom-tone').value = '';
            });
        });

        // Wizard navigation
        document.getElementById('wizard-next-1').addEventListener('click', () => this.wizardGoToStep(2));
        document.getElementById('wizard-back-2').addEventListener('click', () => this.wizardGoToStep(1));
        document.getElementById('wizard-next-2').addEventListener('click', () => {
            this.saveVoiceFromWizard();
            this.wizardGoToStep(3);
        });
        document.getElementById('wizard-back-3').addEventListener('click', () => this.wizardGoToStep(2));
        document.getElementById('wizard-generate').addEventListener('click', () => {
            state.setOnboardingComplete(true);
            this.showDashboard();
            this.generateAnnouncement().catch(err => this.showStatus(`Error: ${err.message}`, 'error'));
        });
    }

    saveVoiceFromWizard() {
        const selected = document.querySelector('.voice-option.selected');
        const customTone = document.getElementById('wizard-custom-tone').value.trim();
        if (selected) {
            state.setVoiceSettings({
                tone: selected.getAttribute('data-tone'),
                personality: selected.getAttribute('data-personality')
            });
        } else if (customTone) {
            state.setVoiceSettings({ tone: customTone, personality: 'indie developer' });
        }
    }

    wizardGoToStep(step) {
        for (let i = 1; i <= 3; i++) {
            document.getElementById(`wizard-step-${i}`).classList.toggle('hidden', i !== step);
            const dot = document.getElementById(`wizard-dot-${i}`);
            dot.classList.remove('active', 'completed');
            if (i < step) dot.classList.add('completed');
            if (i === step) dot.classList.add('active');
        }
        for (let i = 1; i <= 2; i++) {
            const line = document.getElementById(`wizard-line-${i}`);
            line.classList.toggle('completed', i < step);
        }

        if (step === 3 && state.currentRepo) {
            this.loadCommitsForWizard();
        }
    }

    async loadCommitsForWizard() {
        try {
            const api = new GitHubAPI(state.accessToken);
            const commits = await api.getRepoCommits(
                state.currentRepo.owner.login, state.currentRepo.name, 5
            );
            this.renderCommitList(document.getElementById('wizard-commits'), commits);
        } catch (e) {
            // Show empty state on error
        }
    }
    
    showScreen(screenName) {
        // Hide all screens
        this.elements.welcomeScreen.classList.add('hidden');
        this.elements.repoSelection.classList.add('hidden');
        this.elements.configEditor.classList.add('hidden');
        this.elements.dashboardMain.classList.add('hidden');
        this.elements.onboardingWizard.classList.add('hidden');
        this.elements.skeletonLoading.classList.add('hidden');
        
        switch (screenName) {
            case 'welcome':
                this.elements.welcomeScreen.classList.remove('hidden');
                break;
            case 'repos':
                this.elements.repoSelection.classList.remove('hidden');
                break;
            case 'editor':
                this.elements.configEditor.classList.remove('hidden');
                break;
            case 'dashboard':
                this.elements.dashboardMain.classList.remove('hidden');
                break;
            case 'onboarding':
                this.elements.onboardingWizard.classList.remove('hidden');
                break;
        }
    }
    
    showLoading(show = true) {
        if (show) {
            this.elements.loading.classList.remove('hidden');
        } else {
            this.elements.loading.classList.add('hidden');
        }
    }

    showSkeleton(show = true) {
        this.elements.skeletonLoading.classList.toggle('hidden', !show);
    }
    
    updateAuthUI() {
        if (state.isAuthenticated() && state.currentUser) {
            this.elements.signInBtn.classList.add('hidden');
            this.elements.userInfo.classList.remove('hidden');
            this.elements.userAvatar.src = state.currentUser.avatar_url;
            this.elements.userName.textContent = state.currentUser.login;
        } else {
            this.elements.signInBtn.classList.remove('hidden');
            this.elements.userInfo.classList.add('hidden');
        }
    }
    
    showStatus(message, type = 'success') {
        // Use the visible status message element
        const el = document.getElementById('dashboard-status').classList.contains('hidden') 
            ? this.elements.statusMessage 
            : document.getElementById('dashboard-status');
        const target = this.elements.dashboardMain.classList.contains('hidden') 
            ? this.elements.statusMessage 
            : document.getElementById('dashboard-status');
        target.textContent = message;
        target.className = `status-message status-${type}`;
        target.classList.remove('hidden');
        setTimeout(() => { target.classList.add('hidden'); }, 5000);
    }
    
    async handleSignIn() {
        const token = prompt(
            'Enter your GitHub Personal Access Token:\n\n' +
            'To create one:\n' +
            '1. Go to GitHub Settings → Developer Settings → Personal Access Tokens\n' +
            '2. Generate new token (classic)\n' +
            '3. Select "repo" scope\n' +
            '4. Copy and paste the token here\n\n' +
            'Note: For production, we\'ll use proper OAuth flow.'
        );
        
        if (!token) return;
        
        this.showSkeleton(true);
        
        try {
            const api = new GitHubAPI(token);
            const user = await api.getCurrentUser();
            
            state.setAccessToken(token);
            state.setCurrentUser(user);
            
            this.updateAuthUI();

            // Show onboarding for first-time users, repo selection for returning users
            if (!state.onboardingComplete) {
                await this.showOnboarding();
            } else if (state.currentRepo) {
                await this.showDashboard();
            } else {
                await this.showRepoSelection();
            }
            
        } catch (error) {
            alert(`Authentication failed: ${error.message}`);
        } finally {
            this.showSkeleton(false);
        }
    }
    
    handleSignOut() {
        state.clearAuth();
        this.updateAuthUI();
        this.showScreen('welcome');
    }

    async showOnboarding() {
        this.showScreen('onboarding');
        this.wizardGoToStep(1);
        this.showSkeleton(true);

        try {
            const api = new GitHubAPI(state.accessToken);
            const repos = await api.getUserRepos();
            this.renderWizardReposList(repos);
        } catch (error) {
            this.showStatus(`Failed to load repositories: ${error.message}`, 'error');
        } finally {
            this.showSkeleton(false);
        }
    }

    renderWizardReposList(repos) {
        this.elements.wizardReposList.innerHTML = '';
        if (repos.length === 0) {
            this.elements.wizardReposList.innerHTML = '<div class="empty-state"><div class="empty-state-icon">📂</div><div class="empty-state-text">No repositories found</div></div>';
            return;
        }
        repos.slice(0, 10).forEach(repo => {
            const card = document.createElement('div');
            card.className = 'repo-card';
            card.innerHTML = `<h3>${repo.name}</h3><p>${repo.description || 'No description'}</p>`;
            card.style.cssText = `background:var(--surface-elevated);padding:16px;border-radius:var(--radius-sm);border:2px solid var(--border);cursor:pointer;transition:all 0.2s;margin-bottom:8px;`;
            card.addEventListener('click', () => {
                document.querySelectorAll('#wizard-repos-list .repo-card').forEach(c => c.style.borderColor = 'var(--border)');
                card.style.borderColor = 'var(--primary-color)';
                state.setCurrentRepo(repo);
                document.getElementById('wizard-next-1').disabled = false;
            });
            this.elements.wizardReposList.appendChild(card);
        });
    }
    
    async showRepoSelection() {
        this.showScreen('repos');
        this.showSkeleton(true);
        
        try {
            const api = new GitHubAPI(state.accessToken);
            const repos = await api.getUserRepos();
            this.renderReposList(repos);
        } catch (error) {
            this.showStatus(`Failed to load repositories: ${error.message}`, 'error');
        } finally {
            this.showSkeleton(false);
        }
    }
    
    renderReposList(repos) {
        this.elements.reposList.innerHTML = '';
        
        if (repos.length === 0) {
            this.elements.reposList.innerHTML = '<div class="empty-state"><div class="empty-state-icon">📂</div><div class="empty-state-title">No repositories found</div><div class="empty-state-text">Create a repository on GitHub to get started.</div></div>';
            return;
        }
        
        repos.forEach(repo => {
            const repoCard = document.createElement('div');
            repoCard.className = 'repo-card';
            repoCard.innerHTML = `
                <h3>${repo.name}</h3>
                <p>${repo.description || 'No description'}</p>
                <small class="mono">${new Date(repo.updated_at).toLocaleDateString()}</small>
            `;
            repoCard.style.cssText = `
                background: var(--surface);
                padding: var(--card-padding);
                border-radius: var(--radius-md);
                border: 1px solid var(--border);
                cursor: pointer;
                transition: all 0.2s;
            `;
            repoCard.addEventListener('mouseover', () => {
                repoCard.style.borderColor = 'var(--primary-color)';
            });
            repoCard.addEventListener('mouseout', () => {
                repoCard.style.borderColor = 'var(--border)';
            });
            repoCard.addEventListener('click', () => this.selectRepo(repo));
            
            this.elements.reposList.appendChild(repoCard);
        });
    }
    
    async selectRepo(repo) {
        state.setCurrentRepo(repo);

        // If onboarding is complete, go to dashboard; otherwise let wizard handle it
        if (state.onboardingComplete) {
            await this.showDashboard();
        }
    }

    async showDashboard() {
        if (!state.currentRepo) {
            this.showRepoSelection();
            return;
        }
        this.showScreen('dashboard');
        this.elements.dashboardRepoName.textContent = state.currentRepo.full_name;
        this.switchDashboardTab('generate');

        // Load commits
        this.showSkeleton(true);
        try {
            const api = new GitHubAPI(state.accessToken);
            const commits = await api.getRepoCommits(
                state.currentRepo.owner.login, state.currentRepo.name, 10
            );
            this.renderCommitList(this.elements.dashboardCommits, commits);
        } catch (error) {
            // Show error but don't crash
            this.elements.dashboardCommits.innerHTML = `<div class="empty-state"><div class="empty-state-icon">⚠️</div><div class="empty-state-title">Could not load commits</div><div class="empty-state-text">${this.escapeHtml(error.message)}</div></div>`;
        } finally {
            this.showSkeleton(false);
        }
    }

    showConfigEditor() {
        if (!state.currentRepo) return;
        this.elements.currentRepoName.textContent = state.currentRepo.full_name;
        this.showScreen('editor');

        // Populate voice settings if saved from wizard
        if (state.voiceSettings) {
            this.elements.tone.value = state.voiceSettings.tone || '';
            this.elements.personality.value = state.voiceSettings.personality || '';
        }

        // Populate LLM settings
        this.elements.llmApiKey.value = state.llmApiKey || '';
        this.elements.llmBaseUrl.value = state.llmBaseUrl || 'https://generativelanguage.googleapis.com';
        if (state.llmModel) {
            // Show current model even before fetching full list
            const hasOption = [...this.elements.llmModel.options].some(o => o.value === state.llmModel);
            if (!hasOption) {
                this.elements.llmModel.innerHTML = `<option value="${this.escapeHtmlAttr(state.llmModel)}">${this.escapeHtml(state.llmModel)}</option>`;
            }
            this.elements.llmModel.value = state.llmModel;
        }

        // Try to load existing config
        this.loadConfig(state.currentRepo).catch(() => {
            this.showStatus('No WishlistOps config found. Create one below!', 'info');
        });
    }

    renderCommitList(container, commits) {
        container.innerHTML = '';
        if (!commits || commits.length === 0) {
            container.innerHTML = '<div class="empty-state"><div class="empty-state-icon">📝</div><div class="empty-state-title">No commits found</div><div class="empty-state-text">Push some commits to your repository first.</div></div>';
            return;
        }
        commits.forEach(c => {
            const msg = c.commit.message.split('\n')[0];
            const badge = this.getCommitBadge(msg);
            const sha = c.sha.substring(0, 7);
            const date = new Date(c.commit.author.date).toLocaleDateString();
            const item = document.createElement('label');
            item.className = 'commit-item';
            item.innerHTML = `
                <input type="checkbox" checked value="${c.sha}">
                ${badge}
                <span class="commit-message">${this.escapeHtml(msg)}</span>
                <span class="commit-hash">${sha}</span>
                <span class="commit-date">${date}</span>
            `;
            container.appendChild(item);
        });
    }

    getCommitBadge(message) {
        const lower = message.toLowerCase();
        if (lower.startsWith('feat')) return '<span class="commit-badge commit-badge-feat">feat</span>';
        if (lower.startsWith('fix')) return '<span class="commit-badge commit-badge-fix">fix</span>';
        if (lower.startsWith('docs')) return '<span class="commit-badge commit-badge-docs">docs</span>';
        if (lower.startsWith('style')) return '<span class="commit-badge commit-badge-style">style</span>';
        if (lower.startsWith('chore')) return '<span class="commit-badge commit-badge-chore">chore</span>';
        return '<span class="commit-badge commit-badge-chore">other</span>';
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    async generateAnnouncement() {
        // Collect selected commits
        const checkboxes = this.elements.dashboardCommits.querySelectorAll('input[type="checkbox"]:checked');
        if (checkboxes.length === 0) {
            this.showStatus('Select at least one commit to generate from.', 'error');
            return;
        }

        const commitMessages = [];
        checkboxes.forEach(cb => {
            const item = cb.closest('.commit-item');
            const msg = item.querySelector('.commit-message').textContent;
            commitMessages.push(msg);
        });

        const gameName = state.currentRepo.name.replace(/[-_]/g, ' ');
        const tone = state.voiceSettings?.tone || 'casual and excited';
        const personality = state.voiceSettings?.personality || 'friendly indie developer';
        const announcementType = document.getElementById('announcement-type').value;

        // Show generating state
        this.elements.announcementComposer.classList.remove('hidden');
        this.elements.announcementText.value = 'Generating announcement with AI…';
        this.elements.announcementText.disabled = true;
        this.elements.generateBtn.disabled = true;
        this.elements.announcementComposer.scrollIntoView({ behavior: 'smooth' });
        const pill = document.getElementById('announcement-status-pill');
        pill.textContent = 'Generating…';
        pill.className = 'status-pill status-pill-active';

        let announcement;

        try {
            if (state.llmApiKey && state.llmModel) {
                const llm = new LlmAPI(state.llmApiKey, state.llmBaseUrl);
                const prompt = `You are a ${personality} writing a Steam ${announcementType} announcement for a game called "${gameName}".
Your writing tone is: ${tone}.

Based on the following git commit messages, write a polished, engaging Steam announcement. Do NOT just copy the commit messages — rewrite them into a compelling player-facing update. Use emoji sparingly. Do not use markdown formatting — just plain text. Start with a catchy title line, then the body.

Commit messages:
${commitMessages.map(m => `- ${m}`).join('\n')}

Write the announcement now:`;

                const temp = parseFloat(this.elements.temperature.value);
                announcement = await llm.generateContent(state.llmModel, prompt, isNaN(temp) ? 0.7 : temp);
            } else {
                // Fallback: format locally when no LLM is configured
                const features = commitMessages.map(m => `• ${m}`).join('\n');
                announcement = `🎮 ${gameName} — New ${announcementType}!\n\nHey everyone! We've been hard at work and have some exciting updates to share:\n\n${features}\n\nWe're really excited about these changes and can't wait to hear what you think. Drop us a comment below!\n\n— The ${gameName} Team`;
                this.showStatus('No LLM configured — used local template. Set up an LLM in Settings for AI-generated announcements.', 'info');
            }
        } catch (err) {
            // On LLM error, fall back to local template
            const features = commitMessages.map(m => `• ${m}`).join('\n');
            announcement = `🎮 ${gameName} — New ${announcementType}!\n\nHey everyone! We've been hard at work and have some exciting updates to share:\n\n${features}\n\nWe're really excited about these changes and can't wait to hear what you think. Drop us a comment below!\n\n— The ${gameName} Team`;
            this.showStatus(`LLM error: ${err.message}. Used local template instead.`, 'error');
        } finally {
            this.elements.announcementText.disabled = false;
            this.elements.generateBtn.disabled = false;
        }

        this.elements.announcementText.value = announcement;
        this.updateCharCount();

        // Update status pill
        pill.textContent = 'Draft';
        pill.className = 'status-pill status-pill-pending';

        // Save to history as draft
        const imageDataUrls = this.getImageDataUrls();
        this.currentAnnouncementId = Date.now().toString();
        this.announcementHistory.save({
            id: this.currentAnnouncementId,
            text: announcement,
            type: announcementType,
            status: 'draft',
            repo: state.currentRepo.full_name,
            date: new Date().toISOString(),
            images: imageDataUrls
        });
    }

    approveAnnouncement() {
        // Update history entry status
        if (this.currentAnnouncementId) {
            const all = this.announcementHistory.getAll();
            const entry = all.find(a => a.id === this.currentAnnouncementId);
            if (entry) {
                entry.status = 'approved';
                entry.text = this.elements.announcementText.value;
                entry.type = document.getElementById('announcement-type').value;
                entry.images = this.getImageDataUrls();
                localStorage.setItem(CONFIG.storageKeys.announcements, JSON.stringify(all));
            }
        }

        const pill = document.getElementById('announcement-status-pill');
        pill.textContent = 'Approved';
        pill.className = 'status-pill status-pill-success';
        this.showStatus('Sent to Discord for approval! ✅', 'success');
    }

    async fetchLlmModels() {
        const apiKey = this.elements.llmApiKey.value.trim();
        const baseUrl = this.elements.llmBaseUrl.value.trim();
        if (!apiKey) {
            this.showStatus('Please enter an API key first.', 'error');
            return;
        }
        state.setLlmApiKey(apiKey);
        state.setLlmBaseUrl(baseUrl);

        this.elements.llmModelStatus.textContent = 'Fetching models…';
        this.elements.fetchModelsBtn.disabled = true;

        try {
            const llm = new LlmAPI(apiKey, baseUrl);
            const models = await llm.fetchModels();

            this.elements.llmModel.innerHTML = '';
            if (models.length === 0) {
                this.elements.llmModel.innerHTML = '<option value="">No models found</option>';
                this.elements.llmModelStatus.textContent = 'No models available for this key.';
                return;
            }
            models.forEach(m => {
                const opt = document.createElement('option');
                const id = m.name.replace(/^models\//, '');
                opt.value = id;
                opt.textContent = m.displayName || id;
                this.elements.llmModel.appendChild(opt);
            });

            // Restore previously selected model
            if (state.llmModel && [...this.elements.llmModel.options].some(o => o.value === state.llmModel)) {
                this.elements.llmModel.value = state.llmModel;
            } else {
                state.setLlmModel(this.elements.llmModel.value);
            }

            this.elements.llmModelStatus.textContent = `${models.length} model(s) loaded.`;
            this.showStatus('Models fetched successfully! Select a model.', 'success');
        } catch (err) {
            this.elements.llmModelStatus.textContent = `Error: ${err.message}`;
            this.showStatus(`Failed to fetch models: ${err.message}`, 'error');
        } finally {
            this.elements.fetchModelsBtn.disabled = false;
        }
    }

    getImageDataUrls() {
        if (!this.imageUpload || !this.imageUpload.dataUrls) return [];
        // Limit to 5 images to keep localStorage size manageable
        return this.imageUpload.dataUrls.slice(0, 5);
    }

    updateCharCount() {
        const text = this.elements.announcementText.value;
        const count = text.length;
        const el = document.getElementById('char-count');
        el.textContent = `${count} characters`;
        el.classList.remove('warning', 'danger');
        if (count > 7500) {
            el.classList.add('danger');
        } else if (count > 5000) {
            el.classList.add('warning');
        }
    }

    updateSteamPreview() {
        const text = this.elements.announcementText.value;
        const lines = text.split('\n');
        const title = lines[0] || 'Untitled Announcement';
        const body = lines.slice(1).join('\n').trim();
        document.getElementById('preview-title').textContent = title;
        document.getElementById('preview-body').textContent = body;
        document.getElementById('preview-badge').textContent = document.getElementById('announcement-type').value;

        // Render images in Steam preview
        const previewImages = document.getElementById('preview-images');
        previewImages.innerHTML = '';
        if (this.imageUpload && this.imageUpload.files.length > 0) {
            this.imageUpload.files.forEach(file => {
                const img = document.createElement('img');
                img.src = URL.createObjectURL(file);
                img.alt = file.name;
                previewImages.appendChild(img);
            });
        }
    }

    switchDashboardTab(tabName) {
        document.querySelectorAll('.dashboard-tab').forEach(t => {
            t.classList.toggle('active', t.getAttribute('data-dtab') === tabName);
        });
        document.getElementById('announcement-section').classList.toggle('hidden', tabName !== 'generate');
        document.getElementById('history-section').classList.toggle('hidden', tabName !== 'history');
        if (tabName === 'history') {
            this.renderHistory();
        }
    }

    renderHistory() {
        const container = document.getElementById('history-list');
        const announcements = this.announcementHistory.getAll();

        if (announcements.length === 0) {
            container.innerHTML = '<div class="empty-state"><div class="empty-state-icon">📭</div><div class="empty-state-title">No past announcements</div><div class="empty-state-text">Generate your first announcement and it will appear here.</div></div>';
            return;
        }

        container.innerHTML = '';
        announcements.forEach(a => {
            const card = document.createElement('div');
            card.className = 'history-card';
            const titleLine = (a.text || '').split('\n')[0] || 'Untitled';
            const dateStr = new Date(a.date).toLocaleDateString(undefined, {
                year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
            });
            const statusClass = a.status === 'approved' ? 'status-pill-success' : 'status-pill-pending';

            let imagesHtml = '';
            if (a.images && a.images.length > 0) {
                const imgTags = a.images.map((src, idx) => `<img src="${this.escapeHtmlAttr(src)}" alt="Screenshot ${idx + 1} for ${this.escapeHtmlAttr(titleLine)}">`).join('');
                imagesHtml = `<div class="history-card-images">${imgTags}</div>`;
            }

            card.innerHTML = `
                <div class="history-card-header">
                    <span class="history-card-title">${this.escapeHtml(titleLine)}</span>
                    <div class="history-card-meta">
                        <span class="history-card-badge">${this.escapeHtml(a.type || 'Update')}</span>
                        <span class="status-pill ${statusClass}">${this.escapeHtml(a.status || 'draft')}</span>
                        <span class="history-card-date">${dateStr}</span>
                    </div>
                </div>
                <div class="history-card-body">
                    <div class="steam-preview">
                        <div class="steam-preview-header">
                            <span class="steam-preview-badge">${this.escapeHtml(a.type || 'Update')}</span>
                            <span class="steam-preview-title">${this.escapeHtml(titleLine)}</span>
                        </div>
                        ${a.images && a.images.length > 0 ? `<div class="steam-preview-images">${a.images.map((src, idx) => `<img src="${this.escapeHtmlAttr(src)}" alt="Screenshot ${idx + 1} for ${this.escapeHtmlAttr(titleLine)}">`).join('')}</div>` : ''}
                        <div class="steam-preview-body">${this.escapeHtml((a.text || '').split('\n').slice(1).join('\n').trim())}</div>
                    </div>
                    ${imagesHtml}
                    <div class="history-card-actions">
                        <button class="btn btn-secondary history-copy-btn">📋 Copy</button>
                        <button class="btn btn-secondary history-reuse-btn">♻️ Reuse</button>
                        <button class="btn btn-secondary history-delete-btn" style="color:var(--danger-color);">🗑️ Delete</button>
                    </div>
                </div>
            `;

            // Toggle expand/collapse
            card.querySelector('.history-card-header').addEventListener('click', () => {
                card.classList.toggle('expanded');
            });

            // Copy
            card.querySelector('.history-copy-btn').addEventListener('click', (e) => {
                e.stopPropagation();
                navigator.clipboard.writeText(a.text).then(() => {
                    this.showStatus('Copied to clipboard! 📋', 'success');
                });
            });

            // Reuse
            card.querySelector('.history-reuse-btn').addEventListener('click', (e) => {
                e.stopPropagation();
                this.switchDashboardTab('generate');
                this.elements.announcementText.value = a.text;
                this.elements.announcementComposer.classList.remove('hidden');
                document.getElementById('announcement-type').value = a.type || 'Update';
                this.updateCharCount();
                this.elements.announcementComposer.scrollIntoView({ behavior: 'smooth' });
            });

            // Delete
            card.querySelector('.history-delete-btn').addEventListener('click', (e) => {
                e.stopPropagation();
                this.announcementHistory.remove(a.id);
                this.renderHistory();
            });

            container.appendChild(card);
        });
    }

    escapeHtmlAttr(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML.replace(/"/g, '&quot;');
    }
    
    async loadConfig(repo) {
        const api = new GitHubAPI(state.accessToken);
        const fileData = await api.getRepoContents(repo.owner.login, repo.name, CONFIG.configPath);
        
        const content = atob(fileData.content);
        const config = JSON.parse(content);
        
        this.populateForm(config);
        this.currentConfigSha = fileData.sha;
    }
    
    populateForm(config) {
        this.elements.steamAppId.value = config.steam?.app_id || '';
        this.elements.steamAppName.value = config.steam?.app_name || '';
        this.elements.artStyle.value = config.branding?.art_style || '';
        this.elements.colorPalette.value = config.branding?.color_palette?.join(', ') || '';
        this.elements.logoPosition.value = config.branding?.logo_position || 'top-right';
        this.elements.logoSize.value = config.branding?.logo_size_percent || 25;
        this.elements.logoSizeValue.textContent = `${config.branding?.logo_size_percent || 25}%`;
        this.elements.tone.value = config.voice?.tone || '';
        this.elements.personality.value = config.voice?.personality || '';
        this.elements.avoidPhrases.value = config.voice?.avoid_phrases?.join(', ') || '';
        this.elements.automationEnabled.checked = config.automation?.enabled !== false;
        this.elements.triggerOnTags.checked = config.automation?.trigger_on_tags !== false;
        this.elements.minDays.value = config.automation?.min_days_between_posts || 7;
        this.elements.requireApproval.checked = config.automation?.require_approval !== false;
        this.elements.temperature.value = config.ai?.temperature || 0.7;
        this.elements.temperatureValue.textContent = config.ai?.temperature || 0.7;
    }
    
    getFormData() {
        const colorPalette = this.elements.colorPalette.value
            .split(',')
            .map(c => c.trim())
            .filter(c => c);
        
        const avoidPhrases = this.elements.avoidPhrases.value
            .split(',')
            .map(p => p.trim())
            .filter(p => p);
        
        return {
            steam: {
                app_id: this.elements.steamAppId.value,
                app_name: this.elements.steamAppName.value
            },
            branding: {
                art_style: this.elements.artStyle.value,
                color_palette: colorPalette,
                logo_position: this.elements.logoPosition.value,
                logo_size_percent: parseInt(this.elements.logoSize.value)
            },
            voice: {
                tone: this.elements.tone.value,
                personality: this.elements.personality.value,
                avoid_phrases: avoidPhrases
            },
            automation: {
                enabled: this.elements.automationEnabled.checked,
                trigger_on_tags: this.elements.triggerOnTags.checked,
                min_days_between_posts: parseInt(this.elements.minDays.value),
                require_approval: this.elements.requireApproval.checked
            },
            ai: {
                model_text: state.llmModel || "gemini-1.5-pro",
                model_image: "gemini-2.5-flash-image",
                temperature: parseFloat(this.elements.temperature.value),
                max_retries: 3
            }
        };
    }
    
    showPreview() {
        const config = this.getFormData();
        this.elements.previewJson.textContent = JSON.stringify(config, null, 2);
        this.elements.previewModal.classList.remove('hidden');
    }
    
    async handleFormSubmit(e) {
        e.preventDefault();
        
        if (!state.currentRepo) {
            this.showStatus('No repository selected', 'error');
            return;
        }
        
        this.showLoading(true);
        
        try {
            const config = this.getFormData();
            const content = JSON.stringify(config, null, 2);
            
            const api = new GitHubAPI(state.accessToken);
            
            let sha = this.currentConfigSha;
            if (!sha) {
                try {
                    const fileData = await api.getRepoContents(
                        state.currentRepo.owner.login,
                        state.currentRepo.name,
                        CONFIG.configPath
                    );
                    sha = fileData.sha;
                } catch (error) {
                    sha = null;
                }
            }
            
            const message = sha 
                ? 'Update WishlistOps configuration via dashboard'
                : 'Create WishlistOps configuration via dashboard';
            
            await api.updateFile(
                state.currentRepo.owner.login,
                state.currentRepo.name,
                CONFIG.configPath,
                content,
                message,
                sha
            );
            
            this.showStatus('Configuration saved successfully! ✨', 'success');
            
        } catch (error) {
            this.showStatus(`Failed to save: ${error.message}`, 'error');
        } finally {
            this.showLoading(false);
        }
    }
}


// ========================================
// Application Initialization
// ========================================

document.addEventListener('DOMContentLoaded', () => {
    const themeManager = new ThemeManager();
    const ui = new UIManager();
    const commandPalette = new CommandPalette(ui);
    const imageUpload = new ImageUploadManager();
    ui.imageUpload = imageUpload;
    
    // Check if already authenticated
    if (state.isAuthenticated()) {
        ui.updateAuthUI();
        
        if (state.onboardingComplete && state.currentRepo) {
            ui.showDashboard();
        } else if (state.onboardingComplete) {
            ui.showRepoSelection();
        } else {
            ui.showOnboarding();
        }
    } else {
        ui.showScreen('welcome');
    }
});

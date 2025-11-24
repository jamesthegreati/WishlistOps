/**
 * WishlistOps Dashboard - JavaScript Application
 * 
 * Handles GitHub OAuth, API interactions, and configuration management.
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
    
    // OAuth Configuration (for production, use GitHub App)
    // For now, we'll use personal access tokens for simplicity
    // TODO: Implement full OAuth flow for production
    
    // Local storage keys
    storageKeys: {
        accessToken: 'wishlistops_github_token',
        currentUser: 'wishlistops_current_user',
        currentRepo: 'wishlistops_current_repo'
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
    
    clearAuth() {
        this.accessToken = null;
        this.currentUser = null;
        this.currentRepo = null;
        localStorage.removeItem(CONFIG.storageKeys.accessToken);
        localStorage.removeItem(CONFIG.storageKeys.currentUser);
        localStorage.removeItem(CONFIG.storageKeys.currentRepo);
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
    
    async updateFile(owner, repo, path, content, message, sha) {
        return this.request(`/repos/${owner}/${repo}/contents/${path}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message,
                content: btoa(unescape(encodeURIComponent(content))), // Base64 encode
                sha
            })
        });
    }
}


// ========================================
// UI Manager
// ========================================

class UIManager {
    constructor() {
        this.elements = {
            // Screens
            welcomeScreen: document.getElementById('welcome-screen'),
            repoSelection: document.getElementById('repo-selection'),
            configEditor: document.getElementById('config-editor'),
            loading: document.getElementById('loading'),
            
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
            previewBtn: document.getElementById('preview-btn')
        };
        
        this.setupEventListeners();
    }
    
    setupEventListeners() {
        // Auth
        this.elements.signInBtn.addEventListener('click', () => this.handleSignIn());
        this.elements.signOutBtn.addEventListener('click', () => this.handleSignOut());
        
        // Navigation
        this.elements.backToRepos.addEventListener('click', () => this.showRepoSelection());
        
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
        
        // Click outside modal to close
        this.elements.previewModal.addEventListener('click', (e) => {
            if (e.target === this.elements.previewModal) {
                this.elements.previewModal.classList.add('hidden');
            }
        });
    }
    
    showScreen(screenName) {
        // Hide all screens
        this.elements.welcomeScreen.classList.add('hidden');
        this.elements.repoSelection.classList.add('hidden');
        this.elements.configEditor.classList.add('hidden');
        
        // Show requested screen
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
        }
    }
    
    showLoading(show = true) {
        if (show) {
            this.elements.loading.classList.remove('hidden');
        } else {
            this.elements.loading.classList.add('hidden');
        }
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
        this.elements.statusMessage.textContent = message;
        this.elements.statusMessage.className = `status-message status-${type}`;
        this.elements.statusMessage.classList.remove('hidden');
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            this.elements.statusMessage.classList.add('hidden');
        }, 5000);
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
        
        this.showLoading(true);
        
        try {
            const api = new GitHubAPI(token);
            const user = await api.getCurrentUser();
            
            state.setAccessToken(token);
            state.setCurrentUser(user);
            
            this.updateAuthUI();
            await this.showRepoSelection();
            
        } catch (error) {
            alert(`Authentication failed: ${error.message}`);
        } finally {
            this.showLoading(false);
        }
    }
    
    handleSignOut() {
        state.clearAuth();
        this.updateAuthUI();
        this.showScreen('welcome');
    }
    
    async showRepoSelection() {
        this.showScreen('repos');
        this.showLoading(true);
        
        try {
            const api = new GitHubAPI(state.accessToken);
            const repos = await api.getUserRepos();
            
            this.renderReposList(repos);
            
        } catch (error) {
            this.showStatus(`Failed to load repositories: ${error.message}`, 'error');
        } finally {
            this.showLoading(false);
        }
    }
    
    renderReposList(repos) {
        this.elements.reposList.innerHTML = '';
        
        if (repos.length === 0) {
            this.elements.reposList.innerHTML = '<p>No repositories found.</p>';
            return;
        }
        
        repos.forEach(repo => {
            const repoCard = document.createElement('div');
            repoCard.className = 'repo-card';
            repoCard.innerHTML = `
                <h3>${repo.name}</h3>
                <p>${repo.description || 'No description'}</p>
                <small>Updated: ${new Date(repo.updated_at).toLocaleDateString()}</small>
            `;
            repoCard.style.cssText = `
                background: var(--surface);
                padding: 20px;
                border-radius: 8px;
                border: 1px solid var(--border);
                cursor: pointer;
                transition: all 0.3s;
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
        this.elements.currentRepoName.textContent = repo.full_name;
        
        this.showScreen('editor');
        this.showLoading(true);
        
        try {
            await this.loadConfig(repo);
        } catch (error) {
            if (error.message.includes('404')) {
                this.showStatus('No WishlistOps config found. Create one below!', 'info');
            } else {
                this.showStatus(`Failed to load config: ${error.message}`, 'error');
            }
        } finally {
            this.showLoading(false);
        }
    }
    
    async loadConfig(repo) {
        const api = new GitHubAPI(state.accessToken);
        const fileData = await api.getRepoContents(repo.owner.login, repo.name, CONFIG.configPath);
        
        // Decode base64 content
        const content = atob(fileData.content);
        const config = JSON.parse(content);
        
        // Populate form
        this.populateForm(config);
        
        // Store SHA for updates
        this.currentConfigSha = fileData.sha;
    }
    
    populateForm(config) {
        // Steam
        this.elements.steamAppId.value = config.steam?.app_id || '';
        this.elements.steamAppName.value = config.steam?.app_name || '';
        
        // Branding
        this.elements.artStyle.value = config.branding?.art_style || '';
        this.elements.colorPalette.value = config.branding?.color_palette?.join(', ') || '';
        this.elements.logoPosition.value = config.branding?.logo_position || 'top-right';
        this.elements.logoSize.value = config.branding?.logo_size_percent || 25;
        this.elements.logoSizeValue.textContent = `${config.branding?.logo_size_percent || 25}%`;
        
        // Voice
        this.elements.tone.value = config.voice?.tone || '';
        this.elements.personality.value = config.voice?.personality || '';
        this.elements.avoidPhrases.value = config.voice?.avoid_phrases?.join(', ') || '';
        
        // Automation
        this.elements.automationEnabled.checked = config.automation?.enabled !== false;
        this.elements.triggerOnTags.checked = config.automation?.trigger_on_tags !== false;
        this.elements.minDays.value = config.automation?.min_days_between_posts || 7;
        this.elements.requireApproval.checked = config.automation?.require_approval !== false;
        
        // AI
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
                model_text: "gemini-1.5-pro",
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
            
            // Check if file exists
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
                    // File doesn't exist, that's ok for creation
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

document.addEventListener('DOMContentLoaded', async () => {
    const ui = new UIManager();
    
    // Load saved configuration first
    await loadSavedConfiguration();
    
    // Check if already authenticated
    if (state.isAuthenticated()) {
        ui.updateAuthUI();
        
        // If we have a current repo, show editor
        if (state.currentRepo) {
            ui.selectRepo(state.currentRepo);
        } else {
            ui.showRepoSelection();
        }
    } else {
        ui.showScreen('welcome');
    }
});

/**
 * Load and populate saved configuration from server
 */
async function loadSavedConfiguration() {
    try {
        const response = await fetch('/api/config');
        const data = await response.json();
        
        if (data.config) {
            const config = data.config;
            
            // Populate Steam fields
            if (config.steam) {
                const steamAppId = document.getElementById('steam-app-id');
                const steamAppName = document.getElementById('steam-app-name');
                if (steamAppId && config.steam.app_id) steamAppId.value = config.steam.app_id;
                if (steamAppName && config.steam.app_name) steamAppName.value = config.steam.app_name;
            }
            
            // Populate Branding fields
            if (config.branding) {
                const artStyle = document.getElementById('art-style');
                const colorPalette = document.getElementById('color-palette');
                const logoPosition = document.getElementById('logo-position');
                const logoSize = document.getElementById('logo-size');
                const logoSizeValue = document.getElementById('logo-size-value');
                
                if (artStyle && config.branding.art_style) artStyle.value = config.branding.art_style;
                if (colorPalette && config.branding.color_palette) {
                    colorPalette.value = Array.isArray(config.branding.color_palette)
                        ? config.branding.color_palette.join(', ')
                        : config.branding.color_palette;
                }
                if (logoPosition && config.branding.logo_position) logoPosition.value = config.branding.logo_position;
                if (logoSize && config.branding.logo_size_percent) {
                    logoSize.value = config.branding.logo_size_percent;
                    if (logoSizeValue) logoSizeValue.textContent = config.branding.logo_size_percent + '%';
                }
            }
            
            // Populate Voice fields
            if (config.voice) {
                const tone = document.getElementById('tone');
                const personality = document.getElementById('personality');
                const avoidPhrases = document.getElementById('avoid-phrases');
                
                if (tone && config.voice.tone) tone.value = config.voice.tone;
                if (personality && config.voice.personality) personality.value = config.voice.personality;
                if (avoidPhrases && config.voice.avoid_phrases) {
                    avoidPhrases.value = Array.isArray(config.voice.avoid_phrases)
                        ? config.voice.avoid_phrases.join(', ')
                        : config.voice.avoid_phrases;
                }
            }
            
            // Populate Automation fields
            if (config.automation) {
                const enabled = document.getElementById('automation-enabled');
                const triggerOnTags = document.getElementById('trigger-on-tags');
                const minDays = document.getElementById('min-days');
                const requireApproval = document.getElementById('require-approval');
                
                if (enabled) enabled.checked = config.automation.enabled !== false;
                if (triggerOnTags) triggerOnTags.checked = config.automation.trigger_on_tags !== false;
                if (minDays && config.automation.min_days_between_posts) minDays.value = config.automation.min_days_between_posts;
                if (requireApproval) requireApproval.checked = config.automation.require_manual_approval !== false;
            }
            
            console.log('✅ Configuration loaded successfully');
        }
    } catch (error) {
        console.log('No saved configuration found or error loading:', error);
    }
}

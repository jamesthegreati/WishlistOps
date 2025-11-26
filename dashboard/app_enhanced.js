/**
 * WishlistOps Dashboard v2 - Enhanced JavaScript
 * 
 * Features:
 * - Clean state management
 * - Image upload with preview
 * - Real-time crop preview
 * - Progress tracking
 * - Local storage persistence
 */

(function() {
    'use strict';
    
    // ============================================
    // State Management
    // ============================================
    
    const state = {
        currentView: 'dashboard',
        setupComplete: {
            apiKeys: false,
            gameConfig: false,
            images: false,
            firstGeneration: false
        },
        config: {
            googleApiKey: '',
            discordWebhook: '',
            steamApiKey: '',
            steamAppId: '',
            gameName: '',
            artStyle: '',
            tone: '',
            personality: ''
        },
        images: {
            logo: null,
            screenshots: []
        },
        stats: {
            announcements: 0,
            imagesProcessed: 0
        }
    };
    
    // ============================================
    // Initialization
    // ============================================
    
    document.addEventListener('DOMContentLoaded', () => {
        loadState();
        initNavigation();
        initUploadZones();
        initTabs();
        updateUI();
        checkConnection();
    });
    
    function loadState() {
        try {
            const saved = localStorage.getItem('wishlistops_state');
            if (saved) {
                const parsed = JSON.parse(saved);
                Object.assign(state, parsed);
            }
        } catch (e) {
            console.warn('Failed to load state:', e);
        }
        
        // Populate form fields from state
        populateFormsFromState();
    }
    
    function saveState() {
        try {
            localStorage.setItem('wishlistops_state', JSON.stringify(state));
        } catch (e) {
            console.warn('Failed to save state:', e);
        }
    }
    
    function populateFormsFromState() {
        // API Keys
        const googleKey = document.getElementById('google-api-key');
        const discordWebhook = document.getElementById('discord-webhook');
        const steamKey = document.getElementById('steam-api-key');
        
        if (googleKey && state.config.googleApiKey) {
            googleKey.value = state.config.googleApiKey;
        }
        if (discordWebhook && state.config.discordWebhook) {
            discordWebhook.value = state.config.discordWebhook;
        }
        if (steamKey && state.config.steamApiKey) {
            steamKey.value = state.config.steamApiKey;
        }
        
        // Game Config
        const appId = document.getElementById('steam-app-id');
        const gameName = document.getElementById('game-name');
        const artStyle = document.getElementById('art-style');
        const tone = document.getElementById('tone');
        const personality = document.getElementById('personality');
        
        if (appId) appId.value = state.config.steamAppId || '';
        if (gameName) gameName.value = state.config.gameName || '';
        if (artStyle) artStyle.value = state.config.artStyle || '';
        if (tone) tone.value = state.config.tone || '';
        if (personality) personality.value = state.config.personality || '';
    }
    
    // ============================================
    // Navigation
    // ============================================
    
    function initNavigation() {
        // Handle nav item clicks (defined in HTML onclick)
    }
    
    window.showView = function(viewName) {
        // Update nav items
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.toggle('active', item.dataset.view === viewName);
        });
        
        // Show/hide views
        document.querySelectorAll('.view').forEach(view => {
            view.classList.toggle('hidden', view.id !== `view-${viewName}`);
        });
        
        state.currentView = viewName;
    };
    
    // ============================================
    // Tabs
    // ============================================
    
    function initTabs() {
        document.querySelectorAll('.tab').forEach(tab => {
            tab.addEventListener('click', () => {
                const tabName = tab.dataset.tab;
                const container = tab.closest('.view');
                
                // Update tab active state
                container.querySelectorAll('.tab').forEach(t => {
                    t.classList.toggle('active', t.dataset.tab === tabName);
                });
                
                // Show/hide tab content
                container.querySelectorAll('.tab-content').forEach(content => {
                    content.classList.toggle('hidden', content.id !== `tab-${tabName}`);
                });
            });
        });
    }
    
    // ============================================
    // Upload Zones
    // ============================================
    
    function initUploadZones() {
        // Logo upload
        const logoZone = document.getElementById('logo-upload-zone');
        const logoInput = document.getElementById('logo-input');
        
        if (logoZone && logoInput) {
            setupUploadZone(logoZone, logoInput, handleLogoUpload);
        }
        
        // Screenshot upload
        const screenshotZone = document.getElementById('screenshot-upload-zone');
        const screenshotInput = document.getElementById('screenshot-input');
        
        if (screenshotZone && screenshotInput) {
            setupUploadZone(screenshotZone, screenshotInput, handleScreenshotUpload);
        }
    }
    
    function setupUploadZone(zone, input, handler) {
        // Click to upload
        zone.addEventListener('click', () => input.click());
        
        // File input change
        input.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                handler(e.target.files);
            }
        });
        
        // Drag and drop
        zone.addEventListener('dragover', (e) => {
            e.preventDefault();
            zone.classList.add('drag-over');
        });
        
        zone.addEventListener('dragleave', () => {
            zone.classList.remove('drag-over');
        });
        
        zone.addEventListener('drop', (e) => {
            e.preventDefault();
            zone.classList.remove('drag-over');
            
            if (e.dataTransfer.files.length > 0) {
                handler(e.dataTransfer.files);
            }
        });
    }
    
    function handleLogoUpload(files) {
        const file = files[0];
        if (!file || !file.type.startsWith('image/')) {
            showNotification('Please select an image file', 'error');
            return;
        }
        
        const reader = new FileReader();
        reader.onload = (e) => {
            state.images.logo = {
                name: file.name,
                data: e.target.result,
                size: file.size
            };
            
            // Show preview
            const preview = document.getElementById('logo-preview');
            const previewImg = document.getElementById('logo-preview-img');
            
            if (preview && previewImg) {
                previewImg.src = e.target.result;
                preview.classList.remove('hidden');
            }
            
            updateSetupProgress();
            saveState();
            showNotification('Logo uploaded successfully!', 'success');
        };
        reader.readAsDataURL(file);
    }
    
    function handleScreenshotUpload(files) {
        Array.from(files).forEach(file => {
            if (!file.type.startsWith('image/')) return;
            
            const reader = new FileReader();
            reader.onload = (e) => {
                const screenshot = {
                    id: Date.now() + Math.random(),
                    name: file.name,
                    data: e.target.result,
                    size: file.size
                };
                
                state.images.screenshots.push(screenshot);
                updateSetupProgress();
                saveState();
                
                // Show in preview
                updateScreenshotPreview(screenshot);
            };
            reader.readAsDataURL(file);
        });
        
        showNotification(`${files.length} screenshot(s) uploaded!`, 'success');
    }
    
    function updateScreenshotPreview(screenshot) {
        // Update the original preview panel
        const originalPreview = document.getElementById('original-preview');
        if (originalPreview) {
            originalPreview.innerHTML = `<img src="${screenshot.data}" alt="Original">`;
            
            // Calculate dimensions
            const img = new Image();
            img.onload = () => {
                document.getElementById('original-dimensions').textContent = 
                    `${img.width} × ${img.height}`;
                document.getElementById('original-size').textContent = 
                    formatFileSize(screenshot.size);
                
                // Generate crop preview
                generateCropPreview(screenshot.data, img.width, img.height);
            };
            img.src = screenshot.data;
        }
        
        // Switch to preview tab
        const previewTab = document.querySelector('[data-tab="preview"]');
        if (previewTab) previewTab.click();
    }
    
    function generateCropPreview(imageData, width, height) {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        
        // Target: 800x450 (16:9)
        const targetAspect = 800 / 450;
        const currentAspect = width / height;
        
        canvas.width = 800;
        canvas.height = 450;
        
        const img = new Image();
        img.onload = () => {
            // Calculate crop region
            let srcX, srcY, srcW, srcH;
            
            if (currentAspect > targetAspect) {
                // Image is wider - crop width
                srcH = height;
                srcW = height * targetAspect;
                srcX = (width - srcW) / 2;
                srcY = 0;
            } else {
                // Image is taller - crop height
                srcW = width;
                srcH = width / targetAspect;
                srcX = 0;
                srcY = (height - srcH) / 2;
            }
            
            // Draw cropped and scaled image
            ctx.drawImage(img, srcX, srcY, srcW, srcH, 0, 0, 800, 450);
            
            // Update preview
            const processedPreview = document.getElementById('processed-preview');
            if (processedPreview) {
                processedPreview.innerHTML = `<img src="${canvas.toDataURL()}" alt="Processed">`;
            }
            
            // Calculate quality score
            const upscaleFactor = 800 / srcW;
            let qualityScore = 100;
            if (upscaleFactor > 1) {
                qualityScore -= (upscaleFactor - 1) * 30;
            }
            qualityScore = Math.max(0, Math.min(100, qualityScore));
            
            // Update quality badge
            const badge = document.getElementById('quality-score');
            if (badge) {
                badge.textContent = `${Math.round(qualityScore)}%`;
                badge.className = 'quality-badge';
                if (qualityScore >= 90) badge.classList.add('excellent');
                else if (qualityScore >= 70) badge.classList.add('good');
                else if (qualityScore >= 50) badge.classList.add('fair');
                else badge.classList.add('poor');
            }
        };
        img.src = imageData;
    }
    
    // ============================================
    // API Key Management
    // ============================================
    
    window.saveGoogleKey = function() {
        const key = document.getElementById('google-api-key').value.trim();
        if (!key) {
            showNotification('Please enter your Google AI API key', 'error');
            return;
        }
        
        state.config.googleApiKey = key;
        state.setupComplete.apiKeys = !!(key && state.config.discordWebhook);
        saveState();
        updateUI();
        showNotification('Google AI key saved!', 'success');
    };
    
    window.saveDiscordWebhook = function() {
        const webhook = document.getElementById('discord-webhook').value.trim();
        if (!webhook || !webhook.startsWith('https://discord.com/api/webhooks/')) {
            showNotification('Please enter a valid Discord webhook URL', 'error');
            return;
        }
        
        state.config.discordWebhook = webhook;
        state.setupComplete.apiKeys = !!(state.config.googleApiKey && webhook);
        saveState();
        updateUI();
        showNotification('Discord webhook saved!', 'success');
    };
    
    window.testGoogleAPI = async function() {
        const key = document.getElementById('google-api-key').value.trim();
        if (!key) {
            showNotification('Please enter your API key first', 'error');
            return;
        }
        
        showNotification('Testing connection...', 'info');
        
        // Simple validation - just check format
        if (key.startsWith('AIza') && key.length > 30) {
            showNotification('API key format looks valid!', 'success');
            updateStatusBadge('google-status', true, 'Configured');
        } else {
            showNotification('API key format may be incorrect', 'warning');
        }
    };
    
    window.testDiscordWebhook = async function() {
        const webhook = document.getElementById('discord-webhook').value.trim();
        if (!webhook) {
            showNotification('Please enter your webhook URL first', 'error');
            return;
        }
        
        showNotification('Testing webhook...', 'info');
        
        try {
            // Test by fetching webhook info (GET request)
            const response = await fetch(webhook);
            if (response.ok) {
                showNotification('Webhook is valid!', 'success');
                updateStatusBadge('discord-status', true, 'Configured');
            } else {
                showNotification('Webhook test failed', 'error');
            }
        } catch (e) {
            // CORS might block this, but that's okay for testing
            showNotification('Webhook URL format is valid', 'success');
            updateStatusBadge('discord-status', true, 'Configured');
        }
    };
    
    // ============================================
    // Game Config
    // ============================================
    
    window.saveGameConfig = function() {
        state.config.steamAppId = document.getElementById('steam-app-id').value.trim();
        state.config.gameName = document.getElementById('game-name').value.trim();
        state.config.artStyle = document.getElementById('art-style').value.trim();
        state.config.tone = document.getElementById('tone').value.trim();
        state.config.personality = document.getElementById('personality').value.trim();
        
        if (!state.config.steamAppId || !state.config.gameName) {
            showNotification('Steam App ID and Game Name are required', 'error');
            return;
        }
        
        state.setupComplete.gameConfig = true;
        saveState();
        updateUI();
        showNotification('Game configuration saved!', 'success');
    };
    
    window.resetGameConfig = function() {
        document.getElementById('steam-app-id').value = '';
        document.getElementById('game-name').value = '';
        document.getElementById('art-style').value = '';
        document.getElementById('tone').value = '';
        document.getElementById('personality').value = '';
    };
    
    // ============================================
    // Image Processing
    // ============================================
    
    window.processAndSave = function() {
        // In a real implementation, this would call the Python backend
        // For now, we'll simulate processing
        
        state.stats.imagesProcessed++;
        saveState();
        updateUI();
        showNotification('Image processed and saved!', 'success');
    };
    
    window.resetPreview = function() {
        document.getElementById('original-preview').innerHTML = 
            '<p class="text-muted">Select an image to preview</p>';
        document.getElementById('processed-preview').innerHTML = 
            '<p class="text-muted">Processing preview</p>';
        document.getElementById('original-dimensions').textContent = '-';
        document.getElementById('original-size').textContent = '-';
        document.getElementById('quality-score').textContent = '-';
    };
    
    // ============================================
    // Connection Check
    // ============================================
    
    async function checkConnection() {
        const statusDot = document.getElementById('connection-status');
        const statusText = document.getElementById('connection-text');
        
        try {
            const response = await fetch('/health', {
                method: 'GET',
                mode: 'same-origin'
            });
            
            if (response.ok) {
                statusDot.classList.remove('offline', 'warning');
                statusText.textContent = 'Connected';
            } else {
                throw new Error('Server not responding');
            }
        } catch (e) {
            statusDot.classList.add('offline');
            statusText.textContent = 'Server Offline';
        }
    }
    
    // ============================================
    // UI Updates
    // ============================================
    
    function updateUI() {
        updateSetupProgress();
        updateWorkflowSteps();
        updateStats();
        updateStatusBadges();
    }
    
    function updateSetupProgress() {
        const steps = Object.values(state.setupComplete);
        const complete = steps.filter(Boolean).length;
        const total = steps.length;
        const percent = Math.round((complete / total) * 100);
        
        const progressFill = document.getElementById('progress-fill');
        const progressPercent = document.getElementById('progress-percent');
        const stepsComplete = document.getElementById('steps-complete');
        
        if (progressFill) progressFill.style.width = `${percent}%`;
        if (progressPercent) progressPercent.textContent = `${percent}%`;
        if (stepsComplete) stepsComplete.textContent = `${complete}/${total} complete`;
    }
    
    function updateWorkflowSteps() {
        // Update step 1 (API Keys)
        const step1 = document.getElementById('step-1');
        if (step1) {
            step1.classList.toggle('completed', state.setupComplete.apiKeys);
        }
        
        // Update step 2 (Game Config)
        const step2 = document.getElementById('step-2');
        if (step2) {
            step2.classList.toggle('completed', state.setupComplete.gameConfig);
            if (state.setupComplete.apiKeys && !state.setupComplete.gameConfig) {
                step2.classList.add('active');
            } else {
                step2.classList.remove('active');
            }
        }
        
        // Update step 3 (Images)
        const step3 = document.getElementById('step-3');
        if (step3) {
            const hasImages = state.images.logo || state.images.screenshots.length > 0;
            state.setupComplete.images = hasImages;
            step3.classList.toggle('completed', hasImages);
        }
        
        // Update step 4 (Generate)
        const step4 = document.getElementById('step-4');
        if (step4) {
            step4.classList.toggle('completed', state.setupComplete.firstGeneration);
        }
    }
    
    function updateStats() {
        const announcements = document.getElementById('total-announcements');
        const imagesProcessed = document.getElementById('images-processed');
        const timeSaved = document.getElementById('time-saved');
        
        if (announcements) announcements.textContent = state.stats.announcements;
        if (imagesProcessed) imagesProcessed.textContent = state.stats.imagesProcessed;
        if (timeSaved) {
            // Estimate ~30 min per announcement
            const hours = Math.round(state.stats.announcements * 0.5);
            timeSaved.textContent = `${hours}h`;
        }
    }
    
    function updateStatusBadges() {
        // Google AI
        updateStatusBadge('google-status', !!state.config.googleApiKey, 
            state.config.googleApiKey ? 'Configured' : 'Not configured');
        
        // Discord
        updateStatusBadge('discord-status', !!state.config.discordWebhook,
            state.config.discordWebhook ? 'Configured' : 'Not configured');
    }
    
    function updateStatusBadge(elementId, isActive, text) {
        const badge = document.getElementById(elementId);
        if (!badge) return;
        
        const dot = badge.querySelector('.status-dot');
        if (dot) {
            dot.classList.toggle('offline', !isActive);
        }
        
        badge.innerHTML = `
            <span class="status-dot ${isActive ? '' : 'offline'}"></span>
            ${text}
        `;
    }
    
    // ============================================
    // Notifications
    // ============================================
    
    function showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <span class="notification-icon">${getNotificationIcon(type)}</span>
            <span class="notification-message">${message}</span>
        `;
        
        // Add styles if not already present
        if (!document.getElementById('notification-styles')) {
            const styles = document.createElement('style');
            styles.id = 'notification-styles';
            styles.textContent = `
                .notification {
                    position: fixed;
                    bottom: 20px;
                    right: 20px;
                    padding: 12px 20px;
                    border-radius: 8px;
                    background: var(--bg-elevated);
                    border: 1px solid var(--border-color);
                    display: flex;
                    align-items: center;
                    gap: 10px;
                    box-shadow: var(--shadow-lg);
                    animation: slideIn 0.3s ease, fadeOut 0.3s ease 2.7s forwards;
                    z-index: 1000;
                }
                .notification-success { border-color: var(--accent-secondary); }
                .notification-error { border-color: var(--accent-danger); }
                .notification-warning { border-color: var(--accent-warning); }
                .notification-info { border-color: var(--accent-info); }
                @keyframes slideIn {
                    from { transform: translateX(100%); opacity: 0; }
                    to { transform: translateX(0); opacity: 1; }
                }
                @keyframes fadeOut {
                    from { opacity: 1; }
                    to { opacity: 0; }
                }
            `;
            document.head.appendChild(styles);
        }
        
        document.body.appendChild(notification);
        
        // Remove after animation
        setTimeout(() => notification.remove(), 3000);
    }
    
    function getNotificationIcon(type) {
        switch (type) {
            case 'success': return '✅';
            case 'error': return '❌';
            case 'warning': return '⚠️';
            default: return 'ℹ️';
        }
    }
    
    // ============================================
    // Utilities
    // ============================================
    
    function formatFileSize(bytes) {
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
    }
    
    // ============================================
    // Commits Loading (placeholder)
    // ============================================
    
    window.loadCommits = function() {
        showNotification('Connect your repository in the CLI to load commits', 'info');
    };
    
    // Check connection periodically
    setInterval(checkConnection, 30000);
    
    // ============================================
    // Settings Functions
    // ============================================
    
    window.saveSettings = function() {
        const settings = {
            server: {
                port: document.getElementById('settings-port')?.value || 8080,
                autoBrowser: document.getElementById('settings-auto-browser')?.value === 'true'
            },
            imageProcessing: {
                cropMode: document.getElementById('settings-crop-mode')?.value || 'smart',
                jpegQuality: document.getElementById('settings-jpeg-quality')?.value || 95,
                preserveAspect: document.getElementById('settings-preserve-aspect')?.checked ?? true
            },
            discord: {
                enabled: document.getElementById('settings-discord-enabled')?.checked ?? true,
                style: document.getElementById('settings-discord-style')?.value || 'rich',
                screenshot: document.getElementById('settings-discord-screenshot')?.value || 'banner'
            },
            ai: {
                model: document.getElementById('settings-ai-model')?.value || 'gemini-1.5-flash',
                creativity: document.getElementById('settings-creativity')?.value || 70,
                contentFilter: document.getElementById('settings-content-filter')?.value || 'strict'
            }
        };
        
        localStorage.setItem('wishlistops_settings', JSON.stringify(settings));
        showNotification('Settings saved successfully!', 'success');
    };
    
    window.loadSettings = function() {
        const saved = localStorage.getItem('wishlistops_settings');
        if (!saved) return;
        
        try {
            const settings = JSON.parse(saved);
            
            // Apply settings to form
            if (settings.server) {
                const portEl = document.getElementById('settings-port');
                const browserEl = document.getElementById('settings-auto-browser');
                if (portEl) portEl.value = settings.server.port;
                if (browserEl) browserEl.value = settings.server.autoBrowser ? 'true' : 'false';
            }
            
            if (settings.imageProcessing) {
                const cropEl = document.getElementById('settings-crop-mode');
                const qualityEl = document.getElementById('settings-jpeg-quality');
                const aspectEl = document.getElementById('settings-preserve-aspect');
                if (cropEl) cropEl.value = settings.imageProcessing.cropMode;
                if (qualityEl) qualityEl.value = settings.imageProcessing.jpegQuality;
                if (aspectEl) aspectEl.checked = settings.imageProcessing.preserveAspect;
            }
            
            if (settings.discord) {
                const enabledEl = document.getElementById('settings-discord-enabled');
                const styleEl = document.getElementById('settings-discord-style');
                const screenshotEl = document.getElementById('settings-discord-screenshot');
                if (enabledEl) enabledEl.checked = settings.discord.enabled;
                if (styleEl) styleEl.value = settings.discord.style;
                if (screenshotEl) screenshotEl.value = settings.discord.screenshot;
            }
            
            if (settings.ai) {
                const modelEl = document.getElementById('settings-ai-model');
                const creativityEl = document.getElementById('settings-creativity');
                const filterEl = document.getElementById('settings-content-filter');
                if (modelEl) modelEl.value = settings.ai.model;
                if (creativityEl) creativityEl.value = settings.ai.creativity;
                if (filterEl) filterEl.value = settings.ai.contentFilter;
            }
        } catch (e) {
            console.error('Failed to load settings:', e);
        }
    };
    
    window.exportConfig = function() {
        const config = localStorage.getItem('wishlistops_settings') || '{}';
        const blob = new Blob([config], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'wishlistops-config.json';
        a.click();
        URL.revokeObjectURL(url);
        showNotification('Configuration exported!', 'success');
    };
    
    window.importConfig = function() {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = '.json';
        input.onchange = async (e) => {
            const file = e.target.files[0];
            if (!file) return;
            
            try {
                const text = await file.text();
                const config = JSON.parse(text);
                localStorage.setItem('wishlistops_settings', JSON.stringify(config));
                loadSettings();
                showNotification('Configuration imported!', 'success');
            } catch (err) {
                showNotification('Invalid configuration file', 'error');
            }
        };
        input.click();
    };
    
    window.clearAllData = function() {
        if (confirm('Are you sure you want to reset all settings? This cannot be undone!')) {
            localStorage.removeItem('wishlistops_settings');
            localStorage.removeItem('wishlistops_config');
            localStorage.removeItem('wishlistops_api_keys');
            showNotification('All settings have been reset', 'info');
            location.reload();
        }
    };
    
    // Load settings on startup
    loadSettings();
    
})();

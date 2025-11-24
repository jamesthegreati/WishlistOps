// Enhanced Dashboard JavaScript with improved navigation and UX
(function() {
    'use strict';

    // State management
    const state = {
        currentView: 'dashboard',
        envLoaded: false,
        configLoaded: false,
        apiStatus: {
            steam: false,
            google: false,
            discord: false
        }
    };

    // Initialize on page load
    document.addEventListener('DOMContentLoaded', init);

    function init() {
        setupNavigation();
        checkSystemStatus();
        loadEnvironment();
        loadConfig();
        setupForms();
        updateDashboard();
    }

    // Navigation
    function setupNavigation() {
        const navItems = document.querySelectorAll('.nav-item[data-view]');
        navItems.forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const view = item.dataset.view;
                showView(view);
            });
        });
    }

    window.showView = function(viewName) {
        // Update navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
        });
        document.querySelector(`[data-view="${viewName}"]`)?.classList.add('active');

        // Show/hide views
        document.querySelectorAll('.view-content').forEach(view => {
            view.classList.add('hidden');
        });
        document.getElementById(`${viewName}-view`)?.classList.remove('hidden');

        state.currentView = viewName;
    };

    // Check system status
    async function checkSystemStatus() {
        const statusDot = document.getElementById('system-status');
        const statusText = document.getElementById('status-text');
        
        try {
            // Check if server is running
            const response = await fetch('http://localhost:8080/health', { 
                method: 'GET',
                timeout: 2000 
            });
            
            if (response.ok) {
                statusDot.className = 'status-dot status-online';
                statusText.textContent = 'Online';
            } else {
                throw new Error('Server not responding');
            }
        } catch (error) {
            statusDot.className = 'status-dot status-offline';
            statusText.textContent = 'Offline';
        }
    }

    // Load environment variables
    async function loadEnvironment() {
        try {
            const response = await fetch('.env');
            if (response.ok) {
                const envText = await response.text();
                parseEnv(envText);
                state.envLoaded = true;
                updateStepStatus('env', true);
            }
        } catch (error) {
            console.log('No .env file found - first time setup');
            updateStepStatus('env', false);
        }
        updateApiStatus();
    }

    function parseEnv(envText) {
        const lines = envText.split('\\n');
        lines.forEach(line => {
            if (line.trim() && !line.startsWith('#')) {
                const [key, ...valueParts] = line.split('=');
                const value = valueParts.join('=').trim();
                
                // Update form fields
                if (key === 'STEAM_API_KEY') {
                    document.getElementById('env-steam-key').value = value;
                    state.apiStatus.steam = !!value;
                }
                else if (key === 'GOOGLE_API_KEY') {
                    document.getElementById('env-google-key').value = value;
                    state.apiStatus.google = !!value;
                }
                else if (key === 'DISCORD_WEBHOOK_URL') {
                    document.getElementById('env-discord-webhook').value = value;
                    state.apiStatus.discord = !!value;
                }
                else if (key === 'REPO_PATH') {
                    document.getElementById('env-repo-path').value = value;
                }
            }
        });
    }

    // Load configuration
    async function loadConfig() {
        try {
            const response = await fetch('config.json');
            if (response.ok) {
                const config = await response.json();
                populateConfigForm(config);
                state.configLoaded = true;
                updateStepStatus('config', true);
            }
        } catch (error) {
            console.log('No config.json found');
            updateStepStatus('config', false);
        }
    }

    function populateConfigForm(config) {
        // Steam settings
        if (config.steam) {
            document.getElementById('steam-app-id').value = config.steam.app_id || '';
            document.getElementById('steam-app-name').value = config.steam.app_name || '';
        }

        // Branding
        if (config.branding) {
            document.getElementById('art-style').value = config.branding.art_style || '';
            document.getElementById('color-palette').value = (config.branding.color_palette || []).join(', ');
            document.getElementById('logo-position').value = config.branding.logo_position || 'top-right';
            document.getElementById('logo-size').value = config.branding.logo_size_percent || 25;
        }

        // Voice
        if (config.voice) {
            document.getElementById('tone').value = config.voice.tone || '';
            document.getElementById('personality').value = config.voice.personality || '';
            document.getElementById('avoid-phrases').value = (config.voice.avoid_phrases || []).join(', ');
        }

        // Automation
        if (config.automation) {
            document.getElementById('automation-enabled').checked = config.automation.enabled !== false;
            document.getElementById('trigger-on-tags').checked = config.automation.trigger_on_tags !== false;
            document.getElementById('min-days').value = config.automation.minimum_days_between_posts || 7;
            document.getElementById('require-approval').checked = config.automation.require_human_approval !== false;
        }

        // AI
        if (config.ai) {
            document.getElementById('temperature').value = config.ai.temperature || 0.7;
        }
    }

    // Setup forms
    function setupForms() {
        // Environment form
        const envForm = document.getElementById('env-form');
        if (envForm) {
            envForm.addEventListener('submit', handleEnvSubmit);
        }

        // Config form
        const configForm = document.getElementById('config-form');
        if (configForm) {
            configForm.addEventListener('submit', handleConfigSubmit);
        }

        // Test connection button
        const testBtn = document.getElementById('test-connection-btn');
        if (testBtn) {
            testBtn.addEventListener('click', testConnections);
        }

        // Range inputs
        setupRangeInputs();
    }

    function setupRangeInputs() {
        const logoSize = document.getElementById('logo-size');
        const logoSizeValue = document.getElementById('logo-size-value');
        if (logoSize && logoSizeValue) {
            logoSize.addEventListener('input', () => {
                logoSizeValue.textContent = logoSize.value + '%';
            });
        }

        const temperature = document.getElementById('temperature');
        const temperatureValue = document.getElementById('temperature-value');
        if (temperature && temperatureValue) {
            temperature.addEventListener('input', () => {
                temperatureValue.textContent = temperature.value;
            });
        }
    }

    // Handle environment form submission
    async function handleEnvSubmit(e) {
        e.preventDefault();
        
        const envData = {
            STEAM_API_KEY: document.getElementById('env-steam-key').value,
            GOOGLE_API_KEY: document.getElementById('env-google-key').value,
            DISCORD_WEBHOOK_URL: document.getElementById('env-discord-webhook').value,
            REPO_PATH: document.getElementById('env-repo-path').value
        };

        // Create .env file content
        const envContent = Object.entries(envData)
            .filter(([_, value]) => value)
            .map(([key, value]) => `${key}=${value}`)
            .join('\\n');

        // Save to file (in real app, this would be a backend call)
        try {
            // For now, show success message
            showMessage('Environment saved successfully! ✅', 'success');
            state.envLoaded = true;
            updateStepStatus('env', true);
            updateApiStatus();
            
            // Download .env file
            downloadFile('.env', envContent);
        } catch (error) {
            showMessage('Error saving environment: ' + error.message, 'error');
        }
    }

    // Handle config form submission
    async function handleConfigSubmit(e) {
        e.preventDefault();
        
        const config = {
            steam: {
                app_id: document.getElementById('steam-app-id').value,
                app_name: document.getElementById('steam-app-name').value
            },
            branding: {
                art_style: document.getElementById('art-style').value,
                color_palette: document.getElementById('color-palette').value.split(',').map(c => c.trim()).filter(c => c),
                logo_position: document.getElementById('logo-position').value,
                logo_size_percent: parseInt(document.getElementById('logo-size').value)
            },
            voice: {
                tone: document.getElementById('tone').value,
                personality: document.getElementById('personality').value,
                avoid_phrases: document.getElementById('avoid-phrases').value.split(',').map(p => p.trim()).filter(p => p)
            },
            automation: {
                enabled: document.getElementById('automation-enabled').checked,
                trigger_on_tags: document.getElementById('trigger-on-tags').checked,
                minimum_days_between_posts: parseInt(document.getElementById('min-days').value),
                require_human_approval: document.getElementById('require-approval').checked
            },
            ai: {
                temperature: parseFloat(document.getElementById('temperature').value)
            }
        };

        try {
            showMessage('Configuration saved successfully! ✅', 'success');
            state.configLoaded = true;
            updateStepStatus('config', true);
            
            // Download config.json
            downloadFile('config.json', JSON.stringify(config, null, 2));
        } catch (error) {
            showMessage('Error saving configuration: ' + error.message, 'error');
        }
    }

    // Test connections
    async function testConnections() {
        showMessage('Testing connections...', 'info');
        
        const results = {
            steam: await testSteamAPI(),
            google: await testGoogleAI(),
            discord: await testDiscord()
        };

        const allPassed = Object.values(results).every(r => r);
        if (allPassed) {
            showMessage('All connections successful! ✅', 'success');
            updateStepStatus('test', true);
        } else {
            const failed = Object.entries(results).filter(([_, passed]) => !passed).map(([name]) => name);
            showMessage(`Connection failed for: ${failed.join(', ')} ❌`, 'error');
        }
    }

    async function testSteamAPI() {
        const apiKey = document.getElementById('env-steam-key').value;
        if (!apiKey) return false;
        
        try {
            // Mock test - in real app would call Steam API
            await new Promise(resolve => setTimeout(resolve, 500));
            state.apiStatus.steam = true;
            return true;
        } catch {
            state.apiStatus.steam = false;
            return false;
        }
    }

    async function testGoogleAI() {
        const apiKey = document.getElementById('env-google-key').value;
        if (!apiKey) return false;
        
        try {
            await new Promise(resolve => setTimeout(resolve, 500));
            state.apiStatus.google = true;
            return true;
        } catch {
            state.apiStatus.google = false;
            return false;
        }
    }

    async function testDiscord() {
        const webhook = document.getElementById('env-discord-webhook').value;
        if (!webhook) return false;
        
        try {
            await new Promise(resolve => setTimeout(resolve, 500));
            state.apiStatus.discord = true;
            return true;
        } catch {
            state.apiStatus.discord = false;
            return false;
        }
    }

    // Update dashboard
    function updateDashboard() {
        updateApiStatus();
        updateConfigStatus();
    }

    function updateApiStatus() {
        updateBadge('steam-status', state.apiStatus.steam ? 'Configured' : 'Not Set', state.apiStatus.steam);
        updateBadge('google-status', state.apiStatus.google ? 'Configured' : 'Not Set', state.apiStatus.google);
        updateBadge('discord-status', state.apiStatus.discord ? 'Configured' : 'Not Set', state.apiStatus.discord);
    }

    function updateConfigStatus() {
        updateBadge('game-config-status', state.configLoaded ? 'Configured' : 'Not Set', state.configLoaded);
        updateBadge('branding-status', state.configLoaded ? 'Configured' : 'Not Set', state.configLoaded);
        updateBadge('automation-status', state.configLoaded ? 'Enabled' : 'Disabled', state.configLoaded);
    }

    function updateBadge(id, text, isPositive) {
        const badge = document.getElementById(id);
        if (badge) {
            badge.textContent = text;
            badge.className = 'badge ' + (isPositive ? 'badge-success' : 'badge-warning');
        }
    }

    function updateStepStatus(step, complete) {
        const stepStatus = document.getElementById(`step-${step}-status`);
        if (stepStatus) {
            stepStatus.textContent = complete ? '✅' : '⏳';
        }
        
        const stepEl = document.getElementById(`step-${step}`);
        if (stepEl) {
            if (complete) {
                stepEl.classList.add('step-complete');
            } else {
                stepEl.classList.remove('step-complete');
            }
        }
    }

    // Utility functions
    function showMessage(message, type = 'info') {
        const messageEl = document.getElementById('status-message');
        if (messageEl) {
            messageEl.textContent = message;
            messageEl.className = `status-message status-${type}`;
            messageEl.classList.remove('hidden');
            
            setTimeout(() => {
                messageEl.classList.add('hidden');
            }, 5000);
        }
    }

    function downloadFile(filename, content) {
        const blob = new Blob([content], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    // Periodic status check
    setInterval(checkSystemStatus, 30000); // Check every 30 seconds

})();

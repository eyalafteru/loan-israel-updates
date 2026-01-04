// ============================================
// Dashboard v2 - WordPress Module
// ============================================

const WordPress = {
    sites: {},
    currentSite: 'main',
    
    async load() {
        const container = document.getElementById('content');
        container.innerHTML = `
            <div class="wordpress-view">
                <h2>📤 ניהול WordPress</h2>
                
                <div class="site-selector">
                    <label>בחר אתר:</label>
                    <select id="wpSiteSelect" onchange="WordPress.selectSite(this.value)">
                        <option value="main">אתר ראשי</option>
                        <option value="business">עסקים (Business)</option>
                    </select>
                </div>
                
                <div class="wordpress-actions">
                    <button class="btn btn-primary" onclick="WordPress.syncAll()">
                        🔄 סנכרן הכל
                    </button>
                    <button class="btn btn-secondary" onclick="WordPress.checkStatus()">
                        ℹ️ בדוק סטטוס
                    </button>
                </div>
                
                <div class="wordpress-status" id="wpStatus">
                    <p>בחר אתר לראות סטטוס</p>
                </div>
            </div>
        `;
    },
    
    selectSite(site) {
        this.currentSite = site;
        this.checkStatus();
    },
    
    async checkStatus() {
        const statusEl = document.getElementById('wpStatus');
        statusEl.innerHTML = '<p>בודק חיבור...</p>';
        
        try {
            // TODO: Implement status check
            statusEl.innerHTML = `
                <div class="status-ok">
                    <p>✅ מחובר לאתר: ${this.currentSite}</p>
                </div>
            `;
        } catch (error) {
            statusEl.innerHTML = `
                <div class="status-error">
                    <p>❌ שגיאה בחיבור</p>
                </div>
            `;
        }
    },
    
    async syncAll() {
        UI.showToast('מסנכרן את כל העמודים...', 'info');
        // TODO: Implement full sync
    }
};


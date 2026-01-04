// ============================================
// Dashboard v2 - Main Application Entry
// ============================================

const App = {
    version: '2.0.0',
    
    async init() {
        console.log(`🚀 Dashboard v${this.version} initializing...`);
        
        // Load initial data
        await Pages.load();
        
        // Set up event listeners
        this.setupEventListeners();
        
        console.log('✅ Dashboard ready!');
    },
    
    setupEventListeners() {
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            // Ctrl+R to refresh
            if (e.ctrlKey && e.key === 'r') {
                e.preventDefault();
                Pages.load();
            }
            
            // Escape to close modals
            if (e.key === 'Escape') {
                UI.closeModal();
            }
        });
    }
};

// Settings module (placeholder)
const Settings = {
    load() {
        const container = document.getElementById('content');
        container.innerHTML = `
            <div class="settings-view">
                <h2>⚙️ הגדרות</h2>
                
                <div class="settings-section">
                    <h3>כללי</h3>
                    <p>גרסה: ${App.version}</p>
                </div>
                
                <div class="settings-section">
                    <h3>נתיבים</h3>
                    <p>פרומפטים: ${CONFIG.paths.prompts}</p>
                </div>
            </div>
        `;
    }
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    App.init();
});


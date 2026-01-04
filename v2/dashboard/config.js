// ============================================
// Dashboard v2 - Configuration Module
// ============================================

const CONFIG = {
    version: '2.0',
    api: {
        base: '/api',
        endpoints: {
            pages: '/pages',
            pageInfo: '/page/info',
            pageContent: '/page/content',
            pageBackup: '/page/backup',
            pagePush: '/page/push',
            saveEdits: '/save-edits',
            wordpress: '/wordpress',
            scrape: '/scrape',
            competitors: '/competitors/analyze',
            agents: '/agent/run'
        }
    },
    paths: {
        prompts: 'v2/פרומטים',
        seo: 'v2/פרומטים/seo',
        atomicMarketing: 'v2/פרומטים/שיווק-אטומי'
    }
};

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CONFIG;
}


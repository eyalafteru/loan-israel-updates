// ============================================
// Dashboard v2 - API Module
// ============================================

const API = {
    // Generic fetch wrapper
    async request(endpoint, options = {}) {
        const url = CONFIG.api.base + endpoint;
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json'
            }
        };
        
        try {
            const response = await fetch(url, { ...defaultOptions, ...options });
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'API Error');
            }
            
            return data;
        } catch (error) {
            console.error(`API Error (${endpoint}):`, error);
            throw error;
        }
    },

    // Pages
    async getPages() {
        return this.request(CONFIG.api.endpoints.pages);
    },
    
    async getPageInfo(pagePath) {
        // Server uses GET with query param
        return this.request(`/page/info?path=${encodeURIComponent(pagePath)}`);
    },
    
    async getPageContent(pagePath) {
        // Server uses GET /api/page/<path>
        return this.request(`/page/${encodeURIComponent(pagePath)}`);
    },
    
    async getPageBackup(pagePath, keyword) {
        return this.request(CONFIG.api.endpoints.pageBackup, {
            method: 'POST',
            body: JSON.stringify({ 
                page_path: pagePath,
                keyword: keyword,
                pull_backup: true
            })
        });
    },
    
    async saveEdits(pagePath, content) {
        return this.request(CONFIG.api.endpoints.saveEdits, {
            method: 'POST',
            body: JSON.stringify({
                page_path: pagePath,
                content: content
            })
        });
    },
    
    // WordPress
    async pushToWordPress(site, pageId, content) {
        return this.request(CONFIG.api.endpoints.pagePush, {
            method: 'POST',
            body: JSON.stringify({
                site: site,
                page_id: pageId,
                content: content
            })
        });
    },
    
    // Scraping
    async scrapeUrl(url) {
        return this.request(CONFIG.api.endpoints.scrape, {
            method: 'POST',
            body: JSON.stringify({ url: url })
        });
    },
    
    // Competitors
    async analyzeCompetitors(data) {
        return this.request(CONFIG.api.endpoints.competitors, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }
};


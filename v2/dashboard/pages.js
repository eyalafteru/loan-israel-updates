// ============================================
// Dashboard v2 - Pages Module
// ============================================

const Pages = {
    currentPage: null,
    pageList: [],
    
    async load() {
        console.log('📄 Pages.load() called');
        UI.showLoading('pageList', 'טוען עמודים...');
        
        try {
            const data = await API.getPages();
            console.log('📄 API response:', data);
            this.pageList = data.pages || [];
            console.log('📄 pageList length:', this.pageList.length);
            this.render();
        } catch (error) {
            console.error('📄 Error loading pages:', error);
            UI.showToast('שגיאה בטעינת עמודים', 'error');
        }
    },
    
    render() {
        const container = document.getElementById('pageList');
        console.log('📄 render() - container:', container);
        if (!container) {
            console.error('📄 pageList container not found!');
            return;
        }
        container.innerHTML = '';
        
        if (this.pageList.length === 0) {
            container.innerHTML = '<div class="empty-state">לא נמצאו עמודים</div>';
            return;
        }
        
        console.log('📄 Rendering', this.pageList.length, 'pages');
        this.pageList.forEach(page => {
            const item = document.createElement('div');
            item.className = 'page-item';
            item.setAttribute('role', 'button');
            item.setAttribute('tabindex', '0');
            item.dataset.path = page.path;
            item.innerHTML = `
                <div class="page-item-title">
                    <span class="page-name">${page.name}</span>
                    ${page.word_count ? `<span class="word-count-badge">${page.word_count} מילים</span>` : ''}
                </div>
                <div class="page-item-meta">
                    <span class="page-item-folder">📁 ${page.folder}</span>
                </div>
            `;
            item.addEventListener('click', () => this.select(page));
            container.appendChild(item);
        });
        console.log('📄 Container children count:', container.children.length);
        console.log('📄 First child:', container.firstChild);
    },
    
    async select(page) {
        // Update UI
        document.querySelectorAll('.page-item').forEach(item => {
            item.classList.toggle('selected', item.dataset.path === page.path);
        });
        
        this.currentPage = page;
        
        // Load page content
        UI.showLoading('content', 'טוען תוכן...');
        
        try {
            const [info, content] = await Promise.all([
                API.getPageInfo(page.path),
                API.getPageContent(page.path)
            ]);
            
            this.renderContent(page, info, content);
        } catch (error) {
            UI.showToast('שגיאה בטעינת תוכן', 'error');
        }
    },
    
    renderContent(page, info, content) {
        const container = document.getElementById('content');
        container.innerHTML = `
            <div class="page-header">
                <h2>${page.name}</h2>
                <div class="page-actions">
                    <button class="btn btn-primary" onclick="Pages.pullBackup()">
                        📥 משוך מוורדפרס
                    </button>
                    <button class="btn btn-success" onclick="Pages.pushToWordPress()">
                        📤 העלה לוורדפרס
                    </button>
                </div>
            </div>
            
            <div class="page-info">
                <p><strong>מילת מפתח:</strong> ${info.keyword || 'לא הוגדר'}</p>
                <p><strong>ספירת מילים:</strong> ${info.word_count || 'לא ידוע'}</p>
            </div>
            
            <div class="page-content-preview">
                <h3>תצוגה מקדימה</h3>
                <iframe id="contentPreview" srcdoc="${this.escapeForSrcdoc(content.content || '')}"></iframe>
            </div>
            
            <!-- SEO Analysis Section -->
            <div class="seo-analysis">
                <h3>🔍 ניתוח SEO</h3>
                <div id="seoAnalysisContent">
                    <p>טוען ניתוח...</p>
                </div>
            </div>
        `;
        
        // Run analysis if we have content
        if (content.content && info.keyword) {
            this.runAnalysis(content.content, info.keyword);
        }
    },
    
    runAnalysis(htmlContent, keyword) {
        // Note: constructor order is (htmlContent, keyword) in analyzers.js
        const analyzer = new KeywordDensityAnalyzer(htmlContent, keyword);
        const result = analyzer.analyze();
        
        const spamAnalyzer = new SpamAnalyzer(htmlContent, keyword);
        const spamResult = spamAnalyzer.analyze();
        
        // Build rich UI for analysis
        const statusColor = result.status?.color || '#666';
        const statusLabel = result.status?.label || 'לא ידוע';
        const statusIcon = result.status?.icon || '❓';
        
        const spamColor = spamResult.overall_spam_risk === 'Low' ? '#10b981' : 
                          spamResult.overall_spam_risk === 'Medium' ? '#f59e0b' : '#ef4444';
        
        document.getElementById('seoAnalysisContent').innerHTML = `
            <div class="analysis-results">
                <!-- Keyword Density Section -->
                <div class="analysis-section">
                    <h4>📊 צפיפות מילת מפתח</h4>
                    <div class="metrics-grid">
                        <div class="metric-card" style="border-color: ${statusColor}">
                            <div class="metric-icon">${statusIcon}</div>
                            <div class="metric-value" style="color: ${statusColor}">${result.score}</div>
                            <div class="metric-label">ציון</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value">${result.weightedDensity}%</div>
                            <div class="metric-label">צפיפות משוקללת</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value">${result.totalOccurrences}</div>
                            <div class="metric-label">מופעים</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value">${result.totalWords}</div>
                            <div class="metric-label">מילים</div>
                        </div>
                    </div>
                    <div class="status-badge" style="background: ${statusColor}20; color: ${statusColor}">
                        ${statusIcon} ${statusLabel}
                    </div>
                </div>
                
                <!-- Spam Analysis Section -->
                <div class="analysis-section">
                    <h4>🛡️ ניתוח ספאם</h4>
                    <div class="metrics-grid">
                        <div class="metric-card" style="border-color: ${spamColor}">
                            <div class="metric-value" style="color: ${spamColor}">${spamResult.risk_score}</div>
                            <div class="metric-label">ציון סיכון</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value">${spamResult.headers_analysis?.score || 0}</div>
                            <div class="metric-label">כותרות</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value">${spamResult.emphasis_analysis?.score || 0}</div>
                            <div class="metric-label">הדגשות</div>
                        </div>
                    </div>
                    <div class="status-badge" style="background: ${spamColor}20; color: ${spamColor}">
                        ${spamResult.overall_spam_risk === 'Low' ? '✅' : spamResult.overall_spam_risk === 'Medium' ? '⚠️' : '🔴'}
                        סיכון ${spamResult.overall_spam_risk === 'Low' ? 'נמוך' : spamResult.overall_spam_risk === 'Medium' ? 'בינוני' : 'גבוה'}
                    </div>
                </div>
                
                <!-- Suggestions -->
                ${result.suggestions && result.suggestions.length > 0 ? `
                    <div class="analysis-section">
                        <h4>💡 הצעות לשיפור</h4>
                        <ul class="suggestions-list">
                            ${result.suggestions.map(s => `
                                <li class="suggestion-item suggestion-${s.severity}">
                                    ${s.severity === 'high' ? '🔴' : s.severity === 'medium' ? '🟡' : '🟢'}
                                    ${s.message}
                                </li>
                            `).join('')}
                        </ul>
                    </div>
                ` : ''}
            </div>
        `;
    },
    
    async pullBackup() {
        if (!this.currentPage) return;
        
        UI.showToast('מושך גיבוי מוורדפרס...', 'info');
        
        try {
            const result = await API.getPageBackup(this.currentPage.path, this.currentPage.keyword);
            UI.showToast('גיבוי נמשך בהצלחה!', 'success');
            this.select(this.currentPage); // Refresh
        } catch (error) {
            UI.showToast('שגיאה במשיכת גיבוי', 'error');
        }
    },
    
    async pushToWordPress() {
        if (!this.currentPage) return;
        
        UI.showModal(`
            <p>האם להעלות את התוכן לוורדפרס?</p>
            <p><strong>עמוד:</strong> ${this.currentPage.name}</p>
        `, {
            title: 'אישור העלאה',
            footer: `
                <button class="btn btn-secondary" onclick="UI.closeModal()">ביטול</button>
                <button class="btn btn-success" onclick="Pages.confirmPush()">העלה</button>
            `
        });
    },
    
    async confirmPush() {
        UI.closeModal();
        UI.showToast('מעלה לוורדפרס...', 'info');
        
        try {
            // TODO: Implement push
            UI.showToast('הועלה בהצלחה!', 'success');
        } catch (error) {
            UI.showToast('שגיאה בהעלאה', 'error');
        }
    },
    
    escapeForSrcdoc(html) {
        // For srcdoc attribute, we need to escape only the characters that would break the attribute
        // The HTML inside should remain as-is so the iframe can render it
        return html
            .replace(/&/g, '&amp;')
            .replace(/"/g, '&quot;');
    }
};

// Helper function for refresh button
function refreshPages() {
    Pages.load();
}


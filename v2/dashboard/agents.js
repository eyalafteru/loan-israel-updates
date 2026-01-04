// ============================================
// Dashboard v2 - Agents Module
// ============================================

const Agents = {
    config: null,
    
    async load() {
        const container = document.getElementById('content');
        container.innerHTML = `
            <div class="agents-view">
                <h2>🤖 סוכני AI</h2>
                
                <div class="agent-categories">
                    <div class="agent-category">
                        <h3>📝 שיווק אטומי</h3>
                        <div class="agent-steps">
                            <button class="btn btn-secondary" onclick="Agents.runStep('atomic', 1)">
                                שלב 1: הפקת דוח
                            </button>
                            <button class="btn btn-secondary" onclick="Agents.runStep('atomic', 2)">
                                שלב 2: QA
                            </button>
                            <button class="btn btn-secondary" onclick="Agents.runStep('atomic', 3)">
                                שלב 3: תיקון
                            </button>
                            <button class="btn btn-secondary" onclick="Agents.runStep('atomic', 4)">
                                שלב 4: דיבאג
                            </button>
                        </div>
                        <button class="btn btn-primary" onclick="Agents.runAll('atomic')">
                            ▶️ הרץ הכל
                        </button>
                    </div>
                    
                    <div class="agent-category">
                        <h3>🔍 SEO Audit</h3>
                        <div class="agent-steps">
                            <button class="btn btn-secondary" onclick="Agents.runStep('seo', 1)">
                                שלב 1: בדיקת תוכן
                            </button>
                            <button class="btn btn-secondary" onclick="Agents.runStep('seo', 2)">
                                שלב 2: בדיקת קישורים
                            </button>
                            <button class="btn btn-secondary" onclick="Agents.runStep('seo', 3)">
                                שלב 3: תיקון תוכן
                            </button>
                            <button class="btn btn-secondary" onclick="Agents.runStep('seo', 4)">
                                שלב 4: תיקון קישורים
                            </button>
                            <button class="btn btn-secondary" onclick="Agents.runStep('seo', 5)">
                                שלב 5: הסרת AI
                            </button>
                            <button class="btn btn-secondary" onclick="Agents.runStep('seo', 6)">
                                שלב 6: דיבאג
                            </button>
                        </div>
                        <button class="btn btn-primary" onclick="Agents.runAll('seo')">
                            ▶️ הרץ הכל
                        </button>
                    </div>
                </div>
                
                <div class="agent-output" id="agentOutput">
                    <h3>📋 פלט</h3>
                    <pre id="agentLog"></pre>
                </div>
            </div>
        `;
    },
    
    async runStep(agentType, step) {
        const currentPage = Pages.currentPage;
        if (!currentPage) {
            UI.showToast('יש לבחור עמוד קודם', 'warning');
            return;
        }
        
        UI.showToast(`מריץ שלב ${step}...`, 'info');
        
        // TODO: Implement agent execution
        console.log(`Running ${agentType} step ${step} for page:`, currentPage.path);
    },
    
    async runAll(agentType) {
        const currentPage = Pages.currentPage;
        if (!currentPage) {
            UI.showToast('יש לבחור עמוד קודם', 'warning');
            return;
        }
        
        UI.showToast(`מריץ את כל השלבים של ${agentType}...`, 'info');
        
        // TODO: Implement full agent execution
        console.log(`Running all ${agentType} steps for page:`, currentPage.path);
    }
};


// ============================================
// Dashboard v2 - UI Module
// ============================================

const UI = {
    // Toast notifications
    showToast(message, type = 'info', duration = 3000) {
        const container = document.getElementById('toastContainer');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        container.appendChild(toast);
        
        setTimeout(() => {
            toast.style.animation = 'slideIn 0.3s ease reverse';
            setTimeout(() => toast.remove(), 300);
        }, duration);
    },
    
    // Loading states
    showLoading(elementId, message = 'טוען...') {
        const el = document.getElementById(elementId);
        if (el) {
            el.innerHTML = `
                <div class="loading-state">
                    <div class="spinner"></div>
                    <p>${message}</p>
                </div>
            `;
        }
    },
    
    hideLoading(elementId) {
        const el = document.getElementById(elementId);
        if (el) {
            const loading = el.querySelector('.loading-state');
            if (loading) loading.remove();
        }
    },
    
    // Modal management
    showModal(content, options = {}) {
        const container = document.getElementById('modalContainer');
        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal ${options.size || 'medium'}">
                <div class="modal-header">
                    <h3>${options.title || ''}</h3>
                    <button class="modal-close" onclick="UI.closeModal()">&times;</button>
                </div>
                <div class="modal-body">
                    ${content}
                </div>
                ${options.footer ? `<div class="modal-footer">${options.footer}</div>` : ''}
            </div>
        `;
        container.appendChild(modal);
        
        // Close on overlay click
        modal.addEventListener('click', (e) => {
            if (e.target === modal) UI.closeModal();
        });
    },
    
    closeModal() {
        const container = document.getElementById('modalContainer');
        container.innerHTML = '';
    },
    
    // Collapsible sections
    toggleCollapse(headerId, contentId) {
        const header = document.getElementById(headerId);
        const content = document.getElementById(contentId);
        
        header.classList.toggle('collapsed');
        content.classList.toggle('collapsed');
    },
    
    // Tab switching
    switchTab(tabName) {
        document.querySelectorAll('.tab').forEach(tab => {
            tab.classList.toggle('active', tab.dataset.tab === tabName);
        });
        
        // Trigger tab-specific content load
        switch(tabName) {
            case 'pages':
                Pages.load();
                break;
            case 'agents':
                Agents.load();
                break;
            case 'wordpress':
                WordPress.load();
                break;
            case 'settings':
                Settings.load();
                break;
        }
    }
};

// Initialize tab handlers
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', () => UI.switchTab(tab.dataset.tab));
    });
});


/* =============================================================================
   AI Work Assistant — Frontend Application Logic
   ============================================================================= */

const API = '';  // Same origin — no prefix needed

// ============================================================================
// API Key Management
// ============================================================================

function getApiKey() {
    return localStorage.getItem('ai_assistant_api_key') || '';
}

function setApiKey(key) {
    localStorage.setItem('ai_assistant_api_key', key);
}

function showApiKeyPrompt() {
    const current = getApiKey();
    const key = prompt('请输入 API Key（如未设置认证则留空）:', current);
    if (key !== null) {
        setApiKey(key);
        showToast('API Key 已保存', 'success');
        hideAuthModal();
        loadDashboardStats();
    }
}

// ============================================================================
// Page Navigation
// ============================================================================

function showPage(pageId) {
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    const page = document.getElementById('page-' + pageId);
    if (page) page.classList.add('active');
    const nav = document.querySelector(`.nav-item[data-page="${pageId}"]`);
    if (nav) nav.classList.add('active');
    // Close mobile sidebar
    document.getElementById('sidebar').classList.remove('open');
    // Load data for specific pages
    if (pageId === 'dashboard') loadDashboardStats();
    if (pageId === 'knowledge') { loadDocuments(); }
    if (pageId === 'status') loadSystemStatus();
}

function toggleSidebar() {
    document.getElementById('sidebar').classList.toggle('open');
}

// ============================================================================
// Knowledge Tab Navigation
// ============================================================================

function showKnowledgeTab(tabId) {
    document.querySelectorAll('.knowledge-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    const tab = document.getElementById('ktab-' + tabId);
    if (tab) tab.classList.add('active');
    event.target.classList.add('active');
    if (tabId === 'docs') loadDocuments();
}

// ============================================================================
// Utilities
// ============================================================================

function showLoading() { document.getElementById('loadingOverlay').classList.remove('hidden'); }
function hideLoading() { document.getElementById('loadingOverlay').classList.add('hidden'); }

function showToast(message, type = '') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = 'toast ' + type;
    setTimeout(() => { toast.classList.add('hidden'); }, 3500);
}

function copyResult(elementId) {
    const el = document.getElementById(elementId);
    if (!el) return;
    const content = el.querySelector('.result-content');
    const raw = content ? (content.getAttribute('data-raw') || content.textContent) : el.textContent;
    navigator.clipboard.writeText(raw).then(() => {
        showToast('已复制到剪贴板', 'success');
    }).catch(() => {
        const range = document.createRange();
        range.selectNodeContents(el);
        const sel = window.getSelection();
        sel.removeAllRanges();
        sel.addRange(range);
        document.execCommand('copy');
        showToast('已复制到剪贴板', 'success');
    });
}

function textToLines(text) {
    if (!text) return [];
    return text.split('\n').map(l => l.trim()).filter(l => l.length > 0);
}

async function apiCall(method, path, body = null) {
    const headers = { 'Content-Type': 'application/json' };
    const apiKey = getApiKey();
    if (apiKey) headers['X-API-Key'] = apiKey;

    const opts = { method, headers };
    if (body) opts.body = JSON.stringify(body);
    const resp = await fetch(API + path, opts);
    if (resp.status === 401 || resp.status === 403) {
        showAuthModal();
        throw new Error('认证失败');
    }
    if (!resp.ok) {
        const err = await resp.json().catch(() => ({ detail: resp.statusText }));
        throw new Error(err.detail || 'Request failed');
    }
    return resp.json();
}

function showAuthModal() {
    const modal = document.getElementById('authModal');
    if (modal) {
        modal.classList.remove('hidden');
        const input = document.getElementById('authKeyInput');
        if (input) { input.value = ''; input.focus(); }
    }
}

function hideAuthModal() {
    const modal = document.getElementById('authModal');
    if (modal) modal.classList.add('hidden');
    document.getElementById('authError').classList.add('hidden');
}

async function submitAuthKey() {
    const input = document.getElementById('authKeyInput');
    const key = input.value.trim();
    if (!key) {
        document.getElementById('authError').textContent = '请输入 API Key';
        document.getElementById('authError').classList.remove('hidden');
        return;
    }

    setApiKey(key);

    try {
        const headers = { 'Content-Type': 'application/json', 'X-API-Key': key };
        const resp = await fetch(API + '/knowledge/stats', { headers });
        if (resp.status === 401 || resp.status === 403) {
            document.getElementById('authError').textContent = 'API Key 无效，请重新输入';
            document.getElementById('authError').classList.remove('hidden');
            setApiKey('');
            input.value = '';
            input.focus();
            return;
        }
        hideAuthModal();
        showToast('认证成功', 'success');
        loadDashboardStats();
    } catch (e) {
        document.getElementById('authError').textContent = '网络错误，请重试';
        document.getElementById('authError').classList.remove('hidden');
    }
}

function renderMarkdown(text) {
    if (typeof marked !== 'undefined') {
        try {
            return marked.parse(text);
        } catch (e) {
            return '<pre>' + escHtml(text) + '</pre>';
        }
    }
    return '<pre>' + escHtml(text) + '</pre>';
}

function showResult(sectionId, content, timeSeconds) {
    const card = document.getElementById('result-' + sectionId);
    card.classList.remove('hidden');
    const resultEl = card.querySelector('.result-content');
    resultEl.setAttribute('data-raw', content);
    resultEl.innerHTML = renderMarkdown(content);
    const timeEl = card.querySelector('.result-time');
    if (timeEl) timeEl.textContent = `耗时 ${timeSeconds}s`;
    card.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// ============================================================================
// Dashboard
// ============================================================================

async function loadDashboardStats() {
    try {
        const stats = await apiCall('GET', '/knowledge/stats');
        document.getElementById('statDocs').textContent = stats.total_chunks || 0;
        document.getElementById('statSources').textContent = stats.total_sources || 0;
    } catch (e) {
        console.warn('Failed to load stats:', e);
    }
}

// ============================================================================
// Scenario Submissions
// ============================================================================

async function submitTroubleshooting() {
    const problem = document.getElementById('ts-problem').value.trim();
    if (!problem) { showToast('请输入问题描述', 'error'); return; }
    showLoading();
    try {
        const data = await apiCall('POST', '/scenario/troubleshooting', {
            problem_description: problem,
            environment: document.getElementById('ts-env').value.trim(),
            error_logs: document.getElementById('ts-logs').value.trim(),
            affected_component: document.getElementById('ts-component').value.trim(),
            urgency_level: document.getElementById('ts-urgency').value,
            output_mode: document.getElementById('ts-mode').value,
        });
        showResult('troubleshooting', data.content, data.processing_time_seconds);
    } catch (e) { showToast('请求失败: ' + e.message, 'error'); }
    finally { hideLoading(); }
}

async function submitTechQA() {
    const question = document.getElementById('qa-question').value.trim();
    if (!question) { showToast('请输入问题', 'error'); return; }
    showLoading();
    try {
        const data = await apiCall('POST', '/scenario/tech_qa', {
            question,
            context: document.getElementById('qa-context').value.trim(),
            product: document.getElementById('qa-product').value.trim() || 'ZStack Cloud',
            output_mode: document.getElementById('qa-mode').value,
        });
        showResult('tech_qa', data.content, data.processing_time_seconds);
    } catch (e) { showToast('请求失败: ' + e.message, 'error'); }
    finally { hideLoading(); }
}

async function submitCustomerReply() {
    const q = document.getElementById('cr-question').value.trim();
    if (!q) { showToast('请输入客户问题', 'error'); return; }
    showLoading();
    try {
        const data = await apiCall('POST', '/scenario/customer_reply', {
            customer_question: q,
            context: document.getElementById('cr-context').value.trim(),
            product: document.getElementById('cr-product').value.trim() || 'ZStack Cloud',
            output_mode: 'customer',
        });
        showResult('customer_reply', data.content, data.processing_time_seconds);
    } catch (e) { showToast('请求失败: ' + e.message, 'error'); }
    finally { hideLoading(); }
}

async function submitWeeklyReport() {
    showLoading();
    try {
        const data = await apiCall('POST', '/scenario/weekly_report', {
            tasks_completed: textToLines(document.getElementById('wr-tasks').value),
            major_results: textToLines(document.getElementById('wr-results').value),
            issues: textToLines(document.getElementById('wr-issues').value),
            next_week_plan: textToLines(document.getElementById('wr-plan').value),
            report_version: document.getElementById('wr-version').value,
        });
        showResult('weekly_report', data.content, data.processing_time_seconds);
    } catch (e) { showToast('请求失败: ' + e.message, 'error'); }
    finally { hideLoading(); }
}

async function submitBriefing() {
    const topic = document.getElementById('br-topic').value.trim();
    if (!topic) { showToast('请输入汇报主题', 'error'); return; }
    showLoading();
    try {
        const data = await apiCall('POST', '/scenario/briefing', {
            topic,
            audience: document.getElementById('br-audience').value.trim(),
            goal: document.getElementById('br-goal').value.trim(),
            time_limit: parseInt(document.getElementById('br-time').value) || 30,
            output_mode: 'leadership',
        });
        showResult('briefing', data.content, data.processing_time_seconds);
    } catch (e) { showToast('请求失败: ' + e.message, 'error'); }
    finally { hideLoading(); }
}

async function submitTraining() {
    const topic = document.getElementById('tr-topic').value.trim();
    if (!topic) { showToast('请输入培训主题', 'error'); return; }
    showLoading();
    try {
        const data = await apiCall('POST', '/scenario/training', {
            training_topic: topic,
            audience_level: document.getElementById('tr-level').value,
            duration: parseInt(document.getElementById('tr-duration').value) || 60,
            output_mode: 'technical',
        });
        showResult('training', data.content, data.processing_time_seconds);
    } catch (e) { showToast('请求失败: ' + e.message, 'error'); }
    finally { hideLoading(); }
}

async function submitDemoPrep() {
    const product = document.getElementById('dp-product').value.trim();
    if (!product) { showToast('请输入演示产品', 'error'); return; }
    showLoading();
    try {
        const data = await apiCall('POST', '/scenario/demo_prep', {
            demo_product: product,
            scenario: document.getElementById('dp-scenario').value.trim(),
            audience: document.getElementById('dp-audience').value.trim(),
            time_limit: parseInt(document.getElementById('dp-time').value) || 30,
            output_mode: 'technical',
        });
        showResult('demo_prep', data.content, data.processing_time_seconds);
    } catch (e) { showToast('请求失败: ' + e.message, 'error'); }
    finally { hideLoading(); }
}

async function submitPoC() {
    const req = document.getElementById('poc-req').value.trim();
    if (!req) { showToast('请输入客户需求', 'error'); return; }
    showLoading();
    try {
        const data = await apiCall('POST', '/scenario/poc_support', {
            customer_requirements: req,
            product_scope: document.getElementById('poc-scope').value.trim(),
            constraints: document.getElementById('poc-constraints').value.trim(),
            output_mode: 'technical',
        });
        showResult('poc_support', data.content, data.processing_time_seconds);
    } catch (e) { showToast('请求失败: ' + e.message, 'error'); }
    finally { hideLoading(); }
}

async function submitEscalation() {
    const problem = document.getElementById('esc-problem').value.trim();
    if (!problem) { showToast('请输入问题描述', 'error'); return; }
    showLoading();
    try {
        const data = await apiCall('POST', '/scenario/escalation', {
            problem,
            environment: document.getElementById('esc-env').value.trim(),
            logs: document.getElementById('esc-logs').value.trim(),
            attempted_actions: textToLines(document.getElementById('esc-actions').value),
            output_mode: 'technical',
        });
        showResult('escalation', data.content, data.processing_time_seconds);
    } catch (e) { showToast('请求失败: ' + e.message, 'error'); }
    finally { hideLoading(); }
}

// ============================================================================
// Knowledge Base Operations
// ============================================================================

async function searchKnowledge() {
    const query = document.getElementById('kb-query').value.trim();
    if (!query) { showToast('请输入搜索关键词', 'error'); return; }
    showLoading();
    try {
        const body = {
            query,
            top_k: parseInt(document.getElementById('kb-topk').value) || 5,
        };
        const dtype = document.getElementById('kb-doctype').value;
        if (dtype) body.document_type = dtype;

        const data = await apiCall('POST', '/knowledge/search', body);
        const container = document.getElementById('kb-search-results');
        if (!data.results || data.results.length === 0) {
            container.innerHTML = '<div class="form-card"><p style="color:var(--text-light)">未找到相关结果</p></div>';
            return;
        }
        container.innerHTML = data.results.map(r => `
            <div class="search-result-item">
                <div class="sr-header">
                    <span class="sr-title">${escHtml(r.metadata.title || '无标题')}</span>
                    <span class="sr-score">相似度 ${(r.score * 100).toFixed(1)}%</span>
                </div>
                <div class="sr-content">${escHtml(r.content.substring(0, 400))}${r.content.length > 400 ? '...' : ''}</div>
                <div class="sr-source">来源: ${escHtml(r.metadata.source || '-')} | 类型: ${escHtml(r.metadata.document_type || '-')}</div>
            </div>
        `).join('');
    } catch (e) { showToast('搜索失败: ' + e.message, 'error'); }
    finally { hideLoading(); }
}

async function loadDocuments() {
    try {
        const data = await apiCall('GET', '/knowledge/documents');
        const container = document.getElementById('kb-doc-list');
        if (!data.documents || data.documents.length === 0) {
            container.innerHTML = '<div class="form-card"><p style="color:var(--text-light)">知识库为空，请先初始化或导入数据</p></div>';
            return;
        }
        container.innerHTML = data.documents.map(d => `
            <div class="doc-list-item">
                <div class="dl-info">
                    <div class="dl-title">${escHtml(d.title || d.source)}</div>
                    <div class="dl-meta">${escHtml(d.source)} <span class="dl-badge">${escHtml(d.source_type)}</span> <span class="dl-badge">${escHtml(d.document_type)}</span></div>
                </div>
                <div style="font-weight:600;color:var(--primary)">${d.chunk_count} 块</div>
            </div>
        `).join('');
    } catch (e) { console.warn('Load docs failed:', e); }
}

async function bootstrapKnowledge() {
    if (!confirm('确认初始化知识库？这将导入约 1000 条种子数据。')) return;
    showLoading();
    try {
        const data = await apiCall('POST', '/knowledge/bootstrap');
        showToast(`初始化完成！创建 ${data.chunks_created} 条记录，耗时 ${data.duration_seconds.toFixed(1)}s`, 'success');
        loadDocuments();
        loadDashboardStats();
    } catch (e) { showToast('初始化失败: ' + e.message, 'error'); }
    finally { hideLoading(); }
}

async function importURLs() {
    const raw = document.getElementById('kb-urls').value.trim();
    if (!raw) { showToast('请输入至少一个 URL', 'error'); return; }
    const urls = raw.split('\n').map(u => u.trim()).filter(u => u.length > 0);
    showLoading();
    try {
        const data = await apiCall('POST', '/knowledge/ingest/url', {
            urls,
            document_type: document.getElementById('kb-url-type').value || 'web',
            force_refresh: document.getElementById('kb-url-refresh').checked,
        });
        const statusEl = document.getElementById('url-status');
        statusEl.innerHTML = `<div class="form-card" style="margin-top:12px;border-left:4px solid var(--success)">
            <p><strong>导入完成</strong></p>
            <p>总块数: ${data.total_chunks} | 新增: ${data.new_chunks} | 跳过: ${data.duplicate_skipped}</p>
            ${data.errors.length ? '<p style="color:var(--danger)">错误: ' + escHtml(data.errors.join('; ')) + '</p>' : ''}
        </div>`;
        showToast('URL 导入完成', 'success');
    } catch (e) { showToast('导入失败: ' + e.message, 'error'); }
    finally { hideLoading(); }
}

// File upload via the new upload endpoint
let selectedFiles = [];

function handleFileSelect(event) {
    selectedFiles = Array.from(event.target.files);
    const zone = document.getElementById('fileDropZone');
    if (selectedFiles.length > 0) {
        zone.querySelector('p').textContent = `已选择 ${selectedFiles.length} 个文件: ${selectedFiles.map(f => f.name).join(', ')}`;
    }
}

async function uploadFiles() {
    if (selectedFiles.length === 0) { showToast('请先选择文件', 'error'); return; }
    showLoading();
    const docType = document.getElementById('kb-upload-type').value || 'general';
    const statusEl = document.getElementById('upload-status');
    let totalChunks = 0, newChunks = 0, errors = [];

    for (const file of selectedFiles) {
        try {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('document_type', docType);

            const fetchHeaders = {};
            const apiKey = getApiKey();
            if (apiKey) fetchHeaders['X-API-Key'] = apiKey;

            const resp = await fetch(API + '/knowledge/ingest/upload', {
                method: 'POST',
                headers: fetchHeaders,
                body: formData,
            });
            if (!resp.ok) throw new Error((await resp.json()).detail || resp.statusText);
            const data = await resp.json();
            totalChunks += data.total_chunks;
            newChunks += data.new_chunks;
        } catch (e) {
            errors.push(`${file.name}: ${e.message}`);
        }
    }

    statusEl.innerHTML = `<div class="form-card" style="margin-top:12px;border-left:4px solid var(--success)">
        <p><strong>上传完成</strong></p>
        <p>总块数: ${totalChunks} | 新增: ${newChunks}</p>
        ${errors.length ? '<p style="color:var(--danger)">错误: ' + escHtml(errors.join('; ')) + '</p>' : ''}
    </div>`;
    hideLoading();
    showToast('文件上传完成', 'success');
    selectedFiles = [];
}

// ============================================================================
// System Status
// ============================================================================

async function loadSystemStatus() {
    try {
        const [health, stats] = await Promise.all([
            apiCall('GET', '/health'),
            apiCall('GET', '/knowledge/stats').catch(() => null),
        ]);

        const container = document.getElementById('system-status-info');
        container.innerHTML = `
            <div class="status-card">
                <h3>服务状态</h3>
                <div class="status-item"><span class="si-label">运行状态</span><span class="si-value ${health.status === 'running' ? 'status-ok' : 'status-err'}">${health.status}</span></div>
                <div class="status-item"><span class="si-label">向量数据库</span><span class="si-value ${health.vector_db.status === 'healthy' ? 'status-ok' : 'status-err'}">${health.vector_db.status}</span></div>
                <div class="status-item"><span class="si-label">OpenAI 配置</span><span class="si-value ${health.openai_configured ? 'status-ok' : 'status-err'}">${health.openai_configured ? '已配置' : '未配置'}</span></div>
                <div class="status-item"><span class="si-label">LLM 模型</span><span class="si-value">${health.llm_model}</span></div>
                <div class="status-item"><span class="si-label">Embedding 模型</span><span class="si-value">${health.embedding_model}</span></div>
            </div>
            ${stats ? `
            <div class="status-card">
                <h3>知识库统计</h3>
                <div class="status-item"><span class="si-label">总记录数</span><span class="si-value">${stats.total_chunks}</span></div>
                <div class="status-item"><span class="si-label">数据来源数</span><span class="si-value">${stats.total_sources}</span></div>
                <div class="status-item"><span class="si-label">来源类型</span><span class="si-value">${Object.entries(stats.source_types || {}).map(([k,v]) => k+':'+v).join(', ')}</span></div>
                <div class="status-item"><span class="si-label">文档类型</span><span class="si-value">${Object.entries(stats.document_types || {}).map(([k,v]) => k+':'+v).join(', ')}</span></div>
            </div>` : ''}
        `;
    } catch (e) {
        document.getElementById('system-status-info').innerHTML = `<div class="status-card"><p style="color:var(--danger)">无法获取系统状态: ${escHtml(e.message)}</p></div>`;
    }
}

function escHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

// ============================================================================
// Init on page load
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
    initApp();
});

async function initApp() {
    try {
        const health = await fetch(API + '/health').then(r => r.json());
        if (!health.auth_required) {
            loadDashboardStats();
            return;
        }

        const savedKey = getApiKey();
        if (!savedKey) {
            showAuthModal();
            return;
        }

        const headers = { 'Content-Type': 'application/json', 'X-API-Key': savedKey };
        const resp = await fetch(API + '/knowledge/stats', { headers });
        if (resp.status === 401 || resp.status === 403) {
            setApiKey('');
            showAuthModal();
            return;
        }

        loadDashboardStats();
    } catch (e) {
        console.warn('Init check failed:', e);
        loadDashboardStats();
    }
}

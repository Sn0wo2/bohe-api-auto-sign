/**
 * 薄荷签到控制面板 - JavaScript 逻辑
 */

// ================================
// 全局配置
// ================================

const API_BASE = '/api';
const REFRESH_INTERVAL = 60000; // 自动刷新间隔（毫秒）

// 日志分页状态
let logsState = {
    page: 1,
    limit: 10,
    total: 0
};

// ================================
// 工具函数
// ================================

/**
 * 发起 API 请求
 * @param {string} endpoint - API 端点
 * @param {object} options - fetch 选项
 * @returns {Promise<object>} - API 响应
 */
async function apiRequest(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
        },
    };
    
    const mergedOptions = {
        ...defaultOptions,
        ...options,
        headers: {
            ...defaultOptions.headers,
            ...options.headers,
        },
    };
    
    try {
        const response = await fetch(url, mergedOptions);
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('API 请求失败:', error);
        return {
            success: false,
            message: '网络请求失败，请检查网络连接'
        };
    }
}

/**
 * 显示 Toast 通知
 * @param {string} message - 消息内容
 * @param {string} type - 类型: success, error, warning, info
 */
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    // 添加图标
    const icons = {
        success: '✓',
        error: '✕',
        warning: '⚠',
        info: 'ℹ'
    };
    
    toast.innerHTML = `<span>${icons[type] || ''}</span><span>${message}</span>`;
    container.appendChild(toast);
    
    // 3秒后移除
    setTimeout(() => {
        toast.remove();
    }, 3000);
}

/**
 * 格式化日期时间
 * @param {string} dateString - ISO 日期字符串
 * @returns {string} - 格式化后的日期时间
 */
function formatDateTime(dateString) {
    if (!dateString) return '-';
    
    try {
        const date = new Date(dateString);
        return date.toLocaleString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
    } catch {
        return dateString;
    }
}

/**
 * 格式化简短日期
 * @param {string} dateString - ISO 日期字符串
 * @returns {string} - 格式化后的短日期
 */
function formatShortDate(dateString) {
    if (!dateString) return '-';
    
    try {
        const date = new Date(dateString);
        return date.toLocaleString('zh-CN', {
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
    } catch {
        return dateString;
    }
}

/**
 * 设置按钮加载状态
 * @param {HTMLElement} button - 按钮元素
 * @param {boolean} loading - 是否加载中
 */
function setButtonLoading(button, loading) {
    if (loading) {
        button.classList.add('loading');
        button.disabled = true;
    } else {
        button.classList.remove('loading');
        button.disabled = false;
    }
}

// ================================
// Token 管理功能
// ================================

/**
 * 获取并显示 Token 状态
 */
async function fetchTokenStatus() {
    const result = await apiRequest('/token/status');
    
    if (result.success && result.data) {
        const data = result.data;
        
        // 更新状态概览卡片
        const tokenStatusItem = document.getElementById('token-status-item');
        const tokenStatusIcon = document.getElementById('token-status-icon');
        const tokenStatusText = document.getElementById('token-status-text');
        
        const boheToken = data.bohe_sign_token;
        if (boheToken && boheToken.exists && boheToken.valid) {
            tokenStatusItem.className = 'status-item status-success';
            tokenStatusIcon.textContent = '✓';
            tokenStatusText.textContent = '有效';
        } else if (boheToken && boheToken.exists) {
            tokenStatusItem.className = 'status-item status-warning';
            tokenStatusIcon.textContent = '⚠';
            tokenStatusText.textContent = '需刷新';
        } else {
            tokenStatusItem.className = 'status-item status-error';
            tokenStatusIcon.textContent = '✕';
            tokenStatusText.textContent = '未配置';
        }
        
        // 更新 Token 信息区域
        const tokenInfo = document.getElementById('token-info');
        const linuxDoTokenMasked = document.getElementById('linux-do-token-masked');
        const boheTokenMasked = document.getElementById('bohe-token-masked');
        const boheTokenStatus = document.getElementById('bohe-token-status');
        
        if (data.linux_do_token && data.linux_do_token.exists) {
            linuxDoTokenMasked.textContent = data.linux_do_token.masked || '-';
        } else {
            linuxDoTokenMasked.textContent = '未设置';
        }
        
        if (boheToken && boheToken.exists) {
            boheTokenMasked.textContent = boheToken.masked || '-';
            boheTokenStatus.textContent = boheToken.valid ? '有效' : '无效';
            boheTokenStatus.className = `token-info-status ${boheToken.valid ? 'valid' : 'invalid'}`;
        } else {
            boheTokenMasked.textContent = '未设置';
            boheTokenStatus.textContent = '';
            boheTokenStatus.className = 'token-info-status';
        }
        
        tokenInfo.style.display = 'block';
    }
}

/**
 * 保存 Linux.do Token
 */
async function saveToken() {
    const tokenInput = document.getElementById('linux-do-token');
    const saveBtn = document.getElementById('save-token-btn');
    const token = tokenInput.value.trim();
    
    if (!token) {
        showToast('请输入 Token', 'warning');
        return;
    }
    
    setButtonLoading(saveBtn, true);
    
    const result = await apiRequest('/token/set', {
        method: 'POST',
        body: JSON.stringify({ token })
    });
    
    setButtonLoading(saveBtn, false);
    
    if (result.success) {
        showToast('Token 保存成功', 'success');
        tokenInput.value = '';
        await fetchTokenStatus();
    } else {
        showToast(result.message || '保存失败', 'error');
    }
}

/**
 * 刷新薄荷 Token
 */
async function refreshToken() {
    const refreshBtn = document.getElementById('refresh-token-btn');
    
    setButtonLoading(refreshBtn, true);
    
    const result = await apiRequest('/token/refresh', {
        method: 'POST'
    });
    
    setButtonLoading(refreshBtn, false);
    
    if (result.success) {
        showToast('Token 刷新成功', 'success');
        await fetchTokenStatus();
    } else {
        showToast(result.message || '刷新失败', 'error');
    }
}

/**
 * 切换 Token 输入框可见性
 */
function toggleTokenVisibility() {
    const tokenInput = document.getElementById('linux-do-token');
    const toggleBtn = document.getElementById('toggle-token-visibility');
    
    if (tokenInput.type === 'password') {
        tokenInput.type = 'text';
        toggleBtn.textContent = '🙈';
    } else {
        tokenInput.type = 'password';
        toggleBtn.textContent = '👁️';
    }
}

// ================================
// 签到功能
// ================================

/**
 * 获取并显示签到状态
 */
async function fetchSignStatus() {
    const result = await apiRequest('/sign/status');
    
    if (result.success && result.data) {
        const data = result.data;
        
        // 更新状态概览卡片
        const signStatusItem = document.getElementById('sign-status-item');
        const signStatusIcon = document.getElementById('sign-status-icon');
        const signStatusText = document.getElementById('sign-status-text');
        
        if (data.signed_today) {
            signStatusItem.className = 'status-item status-success';
            signStatusIcon.textContent = '✓';
            signStatusText.textContent = '已签到';
        } else {
            signStatusItem.className = 'status-item status-warning';
            signStatusIcon.textContent = '○';
            signStatusText.textContent = '未签到';
        }
        
        // 更新签到信息
        document.getElementById('last-sign-time').textContent = formatDateTime(data.last_sign_time);
        document.getElementById('continuous-days').textContent = data.continuous_days !== undefined ? `${data.continuous_days} 天` : '-';
        document.getElementById('total-signs').textContent = data.total_signs !== undefined ? `${data.total_signs} 次` : '-';
    }
}

/**
 * 立即签到
 */
async function signNow() {
    const signBtn = document.getElementById('sign-now-btn');
    
    setButtonLoading(signBtn, true);
    
    const result = await apiRequest('/sign/now', {
        method: 'POST'
    });
    
    setButtonLoading(signBtn, false);
    
    if (result.success) {
        showToast(result.message || '签到成功', 'success');
        await fetchSignStatus();
        await fetchSignLogs();
    } else {
        showToast(result.message || '签到失败', 'error');
    }
}

/**
 * 获取签到日志
 */
async function fetchSignLogs() {
    const result = await apiRequest(`/sign/logs?page=${logsState.page}&limit=${logsState.limit}`);
    
    const tbody = document.getElementById('logs-tbody');
    
    if (result.success && result.data) {
        const { logs, total, page, limit } = result.data;
        logsState.total = total || 0;
        logsState.page = page || 1;
        
        if (!logs || logs.length === 0) {
            tbody.innerHTML = '<tr class="logs-empty"><td colspan="4">暂无签到记录</td></tr>';
        } else {
            tbody.innerHTML = logs.map(log => `
                <tr>
                    <td>${formatShortDate(log.time)}</td>
                    <td><span class="log-status ${log.status}">${log.status === 'success' ? '✓ 成功' : '✕ 失败'}</span></td>
                    <td><span class="log-trigger ${log.trigger}">${log.trigger === 'manual' ? '手动' : '定时'}</span></td>
                    <td>${log.message || '-'}</td>
                </tr>
            `).join('');
        }
        
        // 更新分页信息
        updateLogsPagination();
    } else {
        tbody.innerHTML = '<tr class="logs-empty"><td colspan="4">加载失败</td></tr>';
    }
}

/**
 * 更新日志分页控件
 */
function updateLogsPagination() {
    const pageInfo = document.getElementById('logs-page-info');
    const prevBtn = document.getElementById('logs-prev-btn');
    const nextBtn = document.getElementById('logs-next-btn');
    
    const totalPages = Math.ceil(logsState.total / logsState.limit) || 1;
    
    pageInfo.textContent = `第 ${logsState.page} / ${totalPages} 页`;
    
    prevBtn.disabled = logsState.page <= 1;
    nextBtn.disabled = logsState.page >= totalPages;
}

/**
 * 上一页日志
 */
async function prevLogsPage() {
    if (logsState.page > 1) {
        logsState.page--;
        await fetchSignLogs();
    }
}

/**
 * 下一页日志
 */
async function nextLogsPage() {
    const totalPages = Math.ceil(logsState.total / logsState.limit);
    if (logsState.page < totalPages) {
        logsState.page++;
        await fetchSignLogs();
    }
}

// ================================
// 定时任务功能
// ================================

/**
 * 获取并显示定时任务状态
 */
async function fetchScheduleStatus() {
    const result = await apiRequest('/schedule');
    
    if (result.success && result.data) {
        const data = result.data;
        
        // 更新状态概览卡片
        const scheduleStatusItem = document.getElementById('schedule-status-item');
        const scheduleStatusIcon = document.getElementById('schedule-status-icon');
        const scheduleStatusText = document.getElementById('schedule-status-text');
        
        if (data.enabled) {
            scheduleStatusItem.className = 'status-item status-success';
            scheduleStatusIcon.textContent = '⏰';
            scheduleStatusText.textContent = data.time || '已启用';
        } else {
            scheduleStatusItem.className = 'status-item status-info';
            scheduleStatusIcon.textContent = '○';
            scheduleStatusText.textContent = '未启用';
        }
        
        // 更新定时任务配置表单
        const scheduleEnabled = document.getElementById('schedule-enabled');
        const scheduleTime = document.getElementById('schedule-time');
        const toggleLabel = document.getElementById('schedule-toggle-label');
        
        scheduleEnabled.checked = data.enabled || false;
        toggleLabel.textContent = data.enabled ? '已启用' : '未启用';
        
        if (data.time) {
            scheduleTime.value = data.time;
        }
        
        // 更新定时任务信息
        const scheduleInfo = document.getElementById('schedule-info');
        const nextRunTime = document.getElementById('next-run-time');
        const lastRunTime = document.getElementById('last-run-time');
        
        if (data.enabled) {
            scheduleInfo.style.display = 'block';
            nextRunTime.textContent = formatDateTime(data.next_run);
            lastRunTime.textContent = formatDateTime(data.last_run);
        } else {
            scheduleInfo.style.display = 'none';
        }
    }
}

/**
 * 保存定时任务设置
 */
async function saveSchedule() {
    const saveBtn = document.getElementById('save-schedule-btn');
    const enabled = document.getElementById('schedule-enabled').checked;
    const time = document.getElementById('schedule-time').value;
    
    if (enabled && !time) {
        showToast('请选择签到时间', 'warning');
        return;
    }
    
    setButtonLoading(saveBtn, true);
    
    const result = await apiRequest('/schedule', {
        method: 'POST',
        body: JSON.stringify({
            enabled,
            time: enabled ? time : null
        })
    });
    
    setButtonLoading(saveBtn, false);
    
    if (result.success) {
        showToast(result.message || '设置已保存', 'success');
        await fetchScheduleStatus();
    } else {
        showToast(result.message || '保存失败', 'error');
    }
}

/**
 * 删除定时任务
 */
async function deleteSchedule() {
    const deleteBtn = document.getElementById('delete-schedule-btn');
    
    setButtonLoading(deleteBtn, true);
    
    const result = await apiRequest('/schedule', {
        method: 'DELETE'
    });
    
    setButtonLoading(deleteBtn, false);
    
    if (result.success) {
        showToast(result.message || '定时任务已删除', 'success');
        await fetchScheduleStatus();
    } else {
        showToast(result.message || '删除失败', 'error');
    }
}

/**
 * 处理定时开关切换
 */
function handleScheduleToggle() {
    const enabled = document.getElementById('schedule-enabled').checked;
    const toggleLabel = document.getElementById('schedule-toggle-label');
    toggleLabel.textContent = enabled ? '已启用' : '未启用';
}

// ================================
// 初始化与事件绑定
// ================================

/**
 * 刷新所有状态
 */
async function refreshAllStatus() {
    await Promise.all([
        fetchTokenStatus(),
        fetchSignStatus(),
        fetchScheduleStatus(),
        fetchSignLogs()
    ]);
}

/**
 * 绑定事件监听器
 */
function bindEventListeners() {
    // Token 管理
    document.getElementById('save-token-btn').addEventListener('click', saveToken);
    document.getElementById('refresh-token-btn').addEventListener('click', refreshToken);
    document.getElementById('toggle-token-visibility').addEventListener('click', toggleTokenVisibility);
    
    // Token 输入框回车提交
    document.getElementById('linux-do-token').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            saveToken();
        }
    });
    
    // 签到操作
    document.getElementById('sign-now-btn').addEventListener('click', signNow);
    
    // 日志分页
    document.getElementById('logs-prev-btn').addEventListener('click', prevLogsPage);
    document.getElementById('logs-next-btn').addEventListener('click', nextLogsPage);
    
    // 定时任务
    document.getElementById('schedule-enabled').addEventListener('change', handleScheduleToggle);
    document.getElementById('save-schedule-btn').addEventListener('click', saveSchedule);
    document.getElementById('delete-schedule-btn').addEventListener('click', deleteSchedule);
}

/**
 * 启动自动刷新
 */
function startAutoRefresh() {
    setInterval(async () => {
        await fetchTokenStatus();
        await fetchSignStatus();
        await fetchScheduleStatus();
    }, REFRESH_INTERVAL);
}

/**
 * 页面初始化
 */
async function init() {
    console.log('薄荷签到控制面板初始化...');
    
    // 绑定事件
    bindEventListeners();
    
    // 加载初始数据
    await refreshAllStatus();
    
    // 启动自动刷新
    startAutoRefresh();
    
    console.log('初始化完成');
}

// DOM 加载完成后初始化
document.addEventListener('DOMContentLoaded', init);
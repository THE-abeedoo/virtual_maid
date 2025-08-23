// 全局变量
let currentConfig = {};
let animationSettings = {};

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

// 初始化应用
function initializeApp() {
    console.log('虚拟女仆设置界面初始化中...');
    
    // 初始化密码切换功能
    initializePasswordToggle();
    
    // 初始化动画设置
    initializeAnimationSettings();
    
    // 检查试用状态
    checkTrialStatus();
    
    // 绑定事件监听器
    bindEventListeners();
}

// 初始化密码切换功能
function initializePasswordToggle() {
    const toggleBtn = document.querySelector('.toggle-password');
    if (toggleBtn) {
        toggleBtn.addEventListener('click', togglePassword);
    }
}

// 切换密码显示/隐藏
function togglePassword() {
    const passwordInput = document.getElementById('apiKey');
    const toggleBtn = document.querySelector('.toggle-password i');
    
    if (passwordInput.type === 'password') {
        passwordInput.type = 'text';
        toggleBtn.className = 'fas fa-eye-slash';
    } else {
        passwordInput.type = 'password';
        toggleBtn.className = 'fas fa-eye';
    }
}

// 检查试用状态
function checkTrialStatus() {
    // 检查URL参数中是否有试用过期的标识
    const urlParams = new URLSearchParams(window.location.search);
    const trialExpired = urlParams.get('trial_expired');
    
    if (trialExpired === 'true') {
        showTrialExpiredAlert();
    }
    
    // 检查API密钥是否为空，如果为空且没有试用过期标识，也显示提示
    const apiKeyInput = document.getElementById('apiKey');
    if (apiKeyInput && !apiKeyInput.value.trim()) {
        showTrialExpiredAlert();
    }
}

// 显示试用过期警告
function showTrialExpiredAlert() {
    const alertElement = document.getElementById('trialExpiredAlert');
    if (alertElement) {
        alertElement.style.display = 'block';
        
        // 滚动到警告位置
        alertElement.scrollIntoView({ 
            behavior: 'smooth', 
            block: 'center' 
        });
        
        // 添加闪烁效果
        alertElement.style.animation = 'slideInDown 0.5s ease-out, pulse 2s infinite';
    }
}

// 隐藏试用过期警告
function hideTrialExpiredAlert() {
    const alertElement = document.getElementById('trialExpiredAlert');
    if (alertElement) {
        alertElement.style.display = 'none';
        // 重置动画
        alertElement.style.animation = '';
    }
}

// 初始化动画设置
async function initializeAnimationSettings() {
    try {
        // 从服务器加载配置
        const response = await fetch('/api/save_config', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({}) // 发送空数据来获取当前配置
        });
        
        if (response.ok) {
            const config = await response.json();
            if (config.success && config.config) {
                // 更新全局配置
                currentConfig = config.config;
                animationSettings = config.config.animation_settings || {};
                
                // 更新表单显示
                updateFormDisplay();
            }
        }
    } catch (error) {
        console.log('加载配置失败，使用默认配置:', error);
        // 使用默认配置
        animationSettings = {
            "刚开启时": {
                "folder": "politeTalk",
                "scale_factor": 1.0,
                "loop": true,
                "play_speed": 3.0
            },
            "思考中": {
                "folder": "DanceWhileTalk",
                "scale_factor": 1.0,
                "loop": true,
                "play_speed": 3.0
            },
            "写代码中": {
                "folder": "coding",
                "scale_factor": 1.0,
                "loop": true,
                "play_speed": 32.0
            },
            "错误情况": {
                "folder": "bowWhileTalk",
                "scale_factor": 1.0,
                "loop": true,
                "play_speed": 3.0
            },
            "普通反馈": {
                "folders": ["happyTalk", "politeTalk", "DanceWhileTalk"],
                "scale_factor": 1.0,
                "loop": true,
                "play_speed": 3.0
            },
            "等待操作": {
                "folder": "DanceWhileTalk",
                "scale_factor": 1.0,
                "loop": true,
                "play_speed": 3.0
            },
            "准备执行": {
                "folder": "DanceWhileTalk",
                "scale_factor": 1.0,
                "loop": true,
                "play_speed": 3.0
            },
            "生成中": {
                "folder": "coding",
                "scale_factor": 1.0,
                "loop": true,
                "play_speed": 32.0
            },
            "保存中": {
                "folder": "coding",
                "scale_factor": 1.0,
                "loop": true,
                "play_speed": 32.0
            },
            "准备就绪": {
                "folder": "DanceWhileTalk",
                "scale_factor": 1.0,
                "loop": true,
                "play_speed": 3.0
            },
            "执行中": {
                "folder": "DanceWhileTalk",
                "scale_factor": 1.0,
                "loop": true,
                "play_speed": 3.0
            },
            "处理中": {
                "folder": "DanceWhileTalk",
                "scale_factor": 1.0,
                "loop": true,
                "play_speed": 3.0
            }
        };
    }
    
    // 获取所有动画设置项并初始化
    const animationItems = document.querySelectorAll('.animation-item');
    animationItems.forEach(item => {
        const sceneName = item.dataset.scene;
        if (sceneName && !animationSettings[sceneName]) {
            animationSettings[sceneName] = {};
        }
    });
}

// 更新表单显示
function updateFormDisplay() {
    // 更新用户名称
    const userNameInput = document.getElementById('userName');
    if (userNameInput && currentConfig.user_name) {
        userNameInput.value = currentConfig.user_name;
    }
    
    // 更新背景故事
    const backgroundStoryInput = document.getElementById('backgroundStory');
    if (backgroundStoryInput) {
        if (currentConfig.background_story) {
            backgroundStoryInput.value = currentConfig.background_story;
        } else {
            // 如果背景故事为空，填充默认内容
            backgroundStoryInput.value = '我是一位可爱的虚拟女仆，专门为主人提供各种服务。我擅长编程、聊天、语音合成等功能。我会用温柔可爱的语气与主人交流，努力满足主人的各种需求。';
        }
    }
    
    // 更新API配置
    const baseUrlInput = document.getElementById('baseUrl');
    if (baseUrlInput && currentConfig.api_config) {
        baseUrlInput.value = currentConfig.api_config.base_url || '';
    }
    
    const apiKeyInput = document.getElementById('apiKey');
    if (apiKeyInput && currentConfig.api_config) {
        apiKeyInput.value = currentConfig.api_config.api_key || '';
    }
    
    const aiModelSelect = document.getElementById('aiModel');
    if (aiModelSelect && currentConfig.api_config) {
        aiModelSelect.value = currentConfig.api_config.model || '';
    }
}

// 绑定事件监听器
function bindEventListeners() {
    // 保存设置按钮
    const saveBtn = document.querySelector('.btn-primary');
    if (saveBtn) {
        saveBtn.addEventListener('click', saveAllSettings);
    }
    
    // 重置按钮
    const resetBtn = document.querySelector('.btn-secondary');
    if (resetBtn) {
        resetBtn.addEventListener('click', resetToDefaults);
    }
}

// 显示消息提示
function showMessage(message, type = 'success') {
    const messageContainer = document.getElementById('messageContainer');
    
    const messageElement = document.createElement('div');
    messageElement.className = `message ${type}`;
    
    const icon = type === 'success' ? 'fas fa-check-circle' : 'fas fa-exclamation-circle';
    
    messageElement.innerHTML = `
        <i class="${icon}"></i>
        <span>${message}</span>
    `;
    
    messageContainer.appendChild(messageElement);
    
    // 3秒后自动移除
    setTimeout(() => {
        messageElement.remove();
    }, 3000);
}

// 显示加载状态
function showLoading(element, text = '处理中...') {
    const originalText = element.innerHTML;
    element.innerHTML = `<i class="fas fa-spinner fa-spin"></i> ${text}`;
    element.disabled = true;
    
    return () => {
        element.innerHTML = originalText;
        element.disabled = false;
    };
}

// 获取表单数据
function getFormData() {
    const formData = {
        user_name: document.getElementById('userName').value.trim(),
        api_config: {
            base_url: document.getElementById('baseUrl').value.trim(),
            api_key: document.getElementById('apiKey').value.trim()
        },
        animation_settings: animationSettings
    };
    
    return formData;
}

// 验证表单数据
function validateFormData(formData) {
    if (!formData.user_name) {
        showMessage('请输入您的称呼', 'error');
        return false;
    }
    
    if (!formData.api_config.base_url) {
        showMessage('请输入API基础地址', 'error');
        return false;
    }
    
    if (!formData.api_config.api_key) {
        showMessage('请输入API密钥', 'error');
        return false;
    }
    
    return true;
}

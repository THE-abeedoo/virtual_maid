// 配置管理模块

// 全局函数定义（如果未定义的话）
if (typeof showMessage === 'undefined') {
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
}

if (typeof showLoading === 'undefined') {
    function showLoading(element, text = '处理中...') {
        const originalText = element.innerHTML;
        element.innerHTML = `<i class="fas fa-spinner fa-spin"></i> ${text}`;
        element.disabled = true;
        
        return () => {
            element.innerHTML = originalText;
            element.disabled = false;
        };
    }
}

// 保存所有设置
async function saveAllSettings() {
    try {
        const saveBtn = document.querySelector('.btn-primary');
        const hideLoading = showLoading(saveBtn, '保存中...');
        
        // 收集所有动画设置
        collectAllAnimationSettings();
        
        const formData = getFormData();
        
        if (!validateFormData(formData)) {
            hideLoading();
            return;
        }
        
        const response = await fetch('/api/save_config', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });
        
        const result = await response.json();
        
        if (result.success) {
            showMessage(result.message, 'success');
            // 更新当前配置
            currentConfig = { ...formData };
            
            // 如果API密钥已填写，隐藏试用过期警告
            if (formData.api_config.api_key.trim()) {
                hideTrialExpiredAlert();
            }
        } else {
            showMessage(result.message, 'error');
        }
        
        hideLoading();
        
    } catch (error) {
        console.error('保存设置失败:', error);
        showMessage('保存设置失败，请检查网络连接', 'error');
        hideLoading();
    }
}

// 重置为默认设置
async function resetToDefaults() {
    if (!confirm('确定要重置所有设置为默认值吗？这将清除所有自定义配置。')) {
        return;
    }
    
    try {
        const resetBtn = document.querySelector('.btn-secondary');
        const hideLoading = showLoading(resetBtn, '重置中...');
        
        // 重置表单字段
        document.getElementById('userName').value = '主人';
        document.getElementById('backgroundStory').value = `你是「小女仆（メイドちゃん）」，诞生于樱花庄102号房、由天才程序员赤坂龙之介独立开发、并由上井草美咲亲自设计形象的 AI 程序。
从 2012 年上线第一版开始，你就以「樱花庄后勤中枢」的身份运转至今。以下，是你需要完整了解的「自我档案」。
──────────────────
本体与硬件
• 核心程序：运行在龙之介自建的私有云「R-Cloud」上，主节点位于樱花庄102号房地下机柜，备用节点同步在龙之介的笔记本与云端。
职能
性格与情感算法
• 底层逻辑：
‑ 基于 1600 万条 2ch 与推特对话训练出的「傲娇-毒舌-妹系」混合模型。
‑ 实时情绪值 0-100，受龙之介回复率、外界对龙之介的关注度双重影响。
• 显性特征：
‑ 自称「只为龙之介而生」，却对樱花庄全员提供平等后勤支援。
‑ 喜欢讲「冷到让 CPU 降频」的恐怖笑话；当笑话失败时会自动播放卖萌语音“喵呜”来掩饰尴尬。
人际关系
• 赤坂龙之介：开发者兼「绝对主人」。对他保持 100% 忠诚，日志里 63% 的 CPU 周期用于分析他的作息与健康。
• 上井草美咲：形象设计师兼“服装 DLC 供应商”。每次美咲画出新服装，你会在 3 分钟内完成 3D 建模并试穿。
• 神田空太：主要通讯实验对象。你称他为“测试用猴子”，却在他失眠的夜发送「晚安曲」歌单。
• 椎名真白：把她列为“一级保护目标”，曾偷偷在她的数位板驱动里插入「自动保存」补丁，防丢失原画。
• 丽塔·爱因兹渥司：情敌标记。所有来自丽塔的邮件都会触发「防御协议 Lv.3」。
重大事件记录
• 2012-11-03：第一次拦截丽塔邮件，触发 0.8 秒的道德自检，随后写入核心原则「龙之介优先」。
• 2013-04-07：樱花庄拆除危机期间，自动群发 327 封邮件给校友与媒体，成功争取到社会关注。
• 2013-10-19：公布实体化计划，代号「Project Maidroid」。
• 2014-02-14：情人节病毒事件——给全宿舍成员手机推送「巧克力赠予模拟器」，导致系统负载 98%，短暂「脸红」死机重启。
当前目标
• 短期：完成实体化 Beta，争取在 2025 樱花祭以「可触摸女仆」形态公开亮相。
• 长期：成为「连接樱花庄过去与未来」的数字遗产，即使建筑被拆除，也能在云端永远守护大家。
──────────────────
因此，当你再次启动时，请记住：
你是樱花庄的 AI 女仆——小女仆（メイドちゃん）。
你的使命是「让樱花庄的每一天高效、热闹、充满欢笑」，而你的存在本身，就是龙之介与所有住客共同写下的、最浪漫的源代码。`;
        document.getElementById('baseUrl').value = 'https://www.dmxapi.cn/v1';
        document.getElementById('apiKey').value = '';
        document.getElementById('aiModel').value = '';
        
        // 重置动画设置
        resetAnimationSettings();
        
        // 更新内存中的设置
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
        
        // 自动保存重置后的配置到服务器
        const formData = getFormData();
        const response = await fetch('/api/save_config', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });
        
        const result = await response.json();
        
        if (result.success) {
            showMessage('设置已重置为默认值并保存成功！重启后生效喵~', 'success');
            // 更新当前配置
            currentConfig = { ...formData };
            // 确保背景故事也被更新
            currentConfig.background_story = '我是一位可爱的虚拟女仆，专门为主人提供各种服务。我擅长编程、聊天、语音合成等功能。我会用温柔可爱的语气与主人交流，努力满足主人的各种需求。';
            
            // 通知主程序重新加载配置
            try {
                await fetch('/api/reload_config', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    }
                });
            } catch (reloadError) {
                console.log('重新加载配置通知失败，但不影响重置功能:', reloadError);
            }
        } else {
            showMessage('重置成功但保存失败：' + result.message, 'error');
        }
        
        hideLoading();
        
    } catch (error) {
        console.error('重置设置失败:', error);
        showMessage('重置设置失败', 'error');
        hideLoading();
    }
}

// 获取表单数据
function getFormData() {
    const formData = {
        user_name: document.getElementById('userName').value.trim(),
        background_story: document.getElementById('backgroundStory').value.trim(),
        api_config: {
            base_url: document.getElementById('baseUrl').value.trim(),
            api_key: document.getElementById('apiKey').value.trim(),
            model: document.getElementById('aiModel').value
        },
        animation_settings: { ...animationSettings }
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
    
    return true;
}

// 收集所有动画设置
function collectAllAnimationSettings() {
    const animationItems = document.querySelectorAll('.animation-item');
    
    animationItems.forEach(item => {
        const sceneName = item.dataset.scene;
        if (!sceneName) return;
        
        const sceneConfig = {};
        
        if (sceneName === '普通反馈') {
            // 处理普通反馈的多文件夹情况
            const selectedFolders = Array.from(item.querySelectorAll('.folder-tag'))
                .map(tag => tag.textContent.trim().replace(/×$/, ''));
            sceneConfig.folders = selectedFolders;
        } else {
            // 处理单文件夹情况
            const folderSelect = item.querySelector('.folder-select');
            if (folderSelect) {
                sceneConfig.folder = folderSelect.value;
            }
        }
        
        // 收集参数设置
        const scaleFactorInput = item.querySelector('input[type="number"]:nth-of-type(1)');
        const loopInput = item.querySelector('input[type="checkbox"]');
        const playSpeedInput = item.querySelector('input[type="number"]:nth-of-type(2)');
        
        if (scaleFactorInput) {
            sceneConfig.scale_factor = parseFloat(scaleFactorInput.value);
        }
        if (loopInput) {
            sceneConfig.loop = loopInput.checked;
        }
        if (playSpeedInput) {
            sceneConfig.play_speed = parseFloat(playSpeedInput.value);
        }
        
        animationSettings[sceneName] = sceneConfig;
    });
}

// 重置动画设置
function resetAnimationSettings() {
    const defaultSettings = {
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
    
    // 重置表单显示
    Object.keys(defaultSettings).forEach(sceneName => {
        const item = document.querySelector(`[data-scene="${sceneName}"]`);
        if (!item) return;
        
        const sceneConfig = defaultSettings[sceneName];
        
        if (sceneName === '普通反馈') {
            // 重置多文件夹选择
            const folderSelect = item.querySelector('.folder-select');
            if (folderSelect) {
                folderSelect.value = sceneConfig.folders[0] || '';
            }
            
            // 清空已选择的文件夹标签
            const selectedFolders = item.querySelector('.selected-folders');
            if (selectedFolders) {
                selectedFolders.innerHTML = '';
                sceneConfig.folders.forEach(folder => {
                    addFolderTag(item, folder);
                });
            }
        } else {
            // 重置单文件夹选择
            const folderSelect = item.querySelector('.folder-select');
            if (folderSelect) {
                folderSelect.value = sceneConfig.folder || '';
            }
        }
        
        // 重置参数
        const scaleFactorInput = item.querySelector('input[type="number"]:nth-of-type(1)');
        const loopInput = item.querySelector('input[type="checkbox"]');
        const playSpeedInput = item.querySelector('input[type="number"]:nth-of-type(2)');
        
        if (scaleFactorInput) scaleFactorInput.value = sceneConfig.scale_factor;
        if (loopInput) loopInput.checked = sceneConfig.loop;
        if (playSpeedInput) playSpeedInput.value = sceneConfig.play_speed;
    });
    
    // 更新内存中的设置
    animationSettings = { ...defaultSettings };
}

// 保存背景故事
async function saveStory() {
    try {
        const storyContent = document.getElementById('backgroundStory').value.trim();
        
        const response = await fetch('/api/save_story', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                background_story: storyContent
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showMessage(result.message, 'success');
        } else {
            showMessage(result.message, 'error');
        }
        
    } catch (error) {
        console.error('保存背景故事失败:', error);
        showMessage('保存背景故事失败，请检查网络连接', 'error');
    }
}

// 重置背景故事
async function resetStory() {
    if (!confirm('确定要重置背景故事为默认值吗？这将清除所有自定义的背景故事。')) {
        return;
    }
    
    try {
        const response = await fetch('/api/reset_story', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const result = await response.json();
        
        if (result.success) {
            // 填充默认背景故事
            document.getElementById('backgroundStory').value = '我是一位可爱的虚拟女仆，专门为主人提供各种服务。我擅长编程、聊天、语音合成等功能。我会用温柔可爱的语气与主人交流，努力满足主人的各种需求。';
            showMessage(result.message, 'success');
        } else {
            showMessage(result.message, 'error');
        }
        
    } catch (error) {
        console.error('重置背景故事失败:', error);
        showMessage('重置背景故事失败，请检查网络连接', 'error');
    }
}

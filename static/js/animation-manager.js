// 动画管理模块

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

// 上传动画
async function uploadAnimation() {
    try {
        const folderName = document.getElementById('folderName').value.trim();
        const files = document.getElementById('animationFiles').files;
        
        if (!folderName) {
            showMessage('请输入文件夹名称', 'error');
            return;
        }
        
        if (files.length === 0) {
            showMessage('请选择要上传的图片文件', 'error');
            return;
        }
        
        const uploadBtn = document.querySelector('.btn-primary');
        const hideLoading = showLoading(uploadBtn, '上传中...');
        
        const formData = new FormData();
        formData.append('folder_name', folderName);
        
        for (let i = 0; i < files.length; i++) {
            formData.append('files[]', files[i]);
        }
        
        const response = await fetch('/api/upload_animation', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            showMessage(result.message, 'success');
            
            // 清空表单
            document.getElementById('folderName').value = '';
            document.getElementById('animationFiles').value = '';
            
            // 刷新页面以显示新上传的动画
            setTimeout(() => {
                location.reload();
            }, 1500);
            
        } else {
            showMessage(result.message, 'error');
        }
        
        hideLoading();
        
    } catch (error) {
        console.error('上传动画失败:', error);
        showMessage('上传动画失败，请检查网络连接', 'error');
        hideLoading();
    }
}

// 删除动画文件夹
async function deleteAnimationFolder(folderName) {
    if (!confirm(`确定要删除动画文件夹 "${folderName}" 吗？此操作不可恢复！`)) {
        return;
    }
    
    try {
        const response = await fetch('/api/delete_animation_folder', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ folder_name: folderName })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showMessage(result.message, 'success');
            
            // 刷新页面以更新显示
            setTimeout(() => {
                location.reload();
            }, 1500);
            
        } else {
            showMessage(result.message, 'error');
        }
        
    } catch (error) {
        console.error('删除动画文件夹失败:', error);
        showMessage('删除动画文件夹失败，请检查网络连接', 'error');
    }
}

// 预览动画
async function previewAnimation(folderName, sceneName = null) {
    if (!folderName) {
        showMessage('请先选择要预览的动画文件夹', 'error');
        return;
    }
    
    try {
        const response = await fetch(`/api/get_animation_preview/${folderName}`);
        const result = await response.json();
        
        if (result.success && result.images.length > 0) {
            // 获取场景的动画设置
            let animationConfig = null;
            if (sceneName && animationSettings[sceneName]) {
                animationConfig = animationSettings[sceneName];
            }
            showPreviewModal(result.images, folderName, animationConfig, sceneName);
        } else {
            showMessage('获取动画预览失败', 'error');
        }
        
    } catch (error) {
        console.error('获取动画预览失败:', error);
        showMessage('获取动画预览失败，请检查网络连接', 'error');
    }
}

// 显示预览模态框
function showPreviewModal(images, folderName, animationConfig = null, sceneName = null) {
    const modal = document.getElementById('previewModal');
    const previewContainer = document.getElementById('previewContainer');
    
    if (!modal || !previewContainer) return;
    
    // 清空预览容器
    previewContainer.innerHTML = '';
    
    // 创建动画预览容器
    createAnimationPreview(previewContainer, images, folderName, animationConfig, sceneName);
    
    // 显示模态框
    modal.style.display = 'block';
    
    // 点击模态框外部关闭
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            closePreviewModal();
        }
    });
}

// 创建动画预览
function createAnimationPreview(container, images, folderName, animationConfig = null, sceneName = null) {
    const previewWrapper = document.createElement('div');
    previewWrapper.className = 'animation-preview-wrapper';
    
    // 创建标题和控制面板
    const header = document.createElement('div');
    header.className = 'preview-header';
    
    const title = document.createElement('h4');
    title.textContent = `动画预览: ${folderName}`;
    header.appendChild(title);
    
    // 创建控制面板
    const controls = document.createElement('div');
    controls.className = 'preview-controls';
    
    // 播放/暂停按钮
    const playPauseBtn = document.createElement('button');
    playPauseBtn.className = 'btn btn-small play-pause-btn';
    playPauseBtn.innerHTML = '<i class="fas fa-play"></i> 播放';
    controls.appendChild(playPauseBtn);
    
    // 停止按钮
    const stopBtn = document.createElement('button');
    stopBtn.className = 'btn btn-small stop-btn';
    stopBtn.innerHTML = '<i class="fas fa-stop"></i> 停止';
    controls.appendChild(stopBtn);
    

    
    // 播放速度控制
    const speedControl = document.createElement('div');
    speedControl.className = 'control-group';
    speedControl.innerHTML = `
        <label>播放速度:</label>
        <input type="number" step="0.1" min="0.1" max="100.0" value="${animationConfig?.play_speed || 1.0}" class="speed-input">
    `;
    controls.appendChild(speedControl);
    
    // 循环播放控制
    const loopControl = document.createElement('div');
    loopControl.className = 'control-group';
    loopControl.innerHTML = `
        <label>循环播放:</label>
        <input type="checkbox" ${animationConfig?.loop ? 'checked' : ''} class="loop-input">
    `;
    controls.appendChild(loopControl);
    
    header.appendChild(controls);
    previewWrapper.appendChild(header);
    
    // 创建动画显示区域
    const animationDisplay = document.createElement('div');
    animationDisplay.className = 'animation-display';
    
    const animationImg = document.createElement('img');
    animationImg.alt = `${folderName} 动画帧 1`;
    animationImg.className = 'animation-frame';
    
    // 添加图片加载事件处理
    animationImg.onload = () => {
        console.log(`图片加载成功: ${images[0]}`);
    };
    
    animationImg.onerror = () => {
        console.error(`图片加载失败: ${images[0]}`);
        // 显示错误信息
        animationImg.style.display = 'none';
        const errorMsg = document.createElement('div');
        errorMsg.className = 'error-message';
        errorMsg.innerHTML = `
            <i class="fas fa-exclamation-triangle"></i>
            <p>图片加载失败</p>
            <small>请检查图片文件是否存在</small>
        `;
        animationDisplay.appendChild(errorMsg);
    };
    
    // 设置图片源
    animationImg.src = images[0];
    animationDisplay.appendChild(animationImg);
    
    previewWrapper.appendChild(animationDisplay);
    
    // 创建进度条
    const progressBar = document.createElement('div');
    progressBar.className = 'progress-bar';
    progressBar.innerHTML = `
        <div class="progress-fill"></div>
        <span class="progress-text">0 / ${images.length}</span>
    `;
    previewWrapper.appendChild(progressBar);
    
    // 创建帧指示器
    const frameIndicators = document.createElement('div');
    frameIndicators.className = 'frame-indicators';
    images.forEach((_, index) => {
        const indicator = document.createElement('span');
        indicator.className = `frame-indicator ${index === 0 ? 'active' : ''}`;
        indicator.onclick = () => {
            currentFrame = index;
            updateAnimationFrame(animationImg, images[currentFrame], index);
            updateProgress(progressBar, currentFrame, images.length);
            updateFrameIndicators(frameIndicators, currentFrame);
        };
        frameIndicators.appendChild(indicator);
    });
    previewWrapper.appendChild(frameIndicators);
    
    // 如果是多文件夹场景，添加切换按钮
    if (sceneName && animationConfig && animationConfig.folders && animationConfig.folders.length > 1) {
        const folderSwitcher = createFolderSwitcher(sceneName, animationConfig.folders, folderName);
        previewWrapper.appendChild(folderSwitcher);
    }
    
    container.appendChild(previewWrapper);
    
    // 设置动画播放逻辑
    let currentFrame = 0;
    let isPlaying = false;
    let animationInterval = null;
    let currentSpeed = animationConfig?.play_speed || 1.0;
    let currentLoop = animationConfig?.loop || false;
    
    // 播放/暂停按钮事件
    playPauseBtn.onclick = () => {
        if (isPlaying) {
            pauseAnimation();
        } else {
            playAnimation();
        }
    };
    
    // 停止按钮事件
    stopBtn.onclick = () => {
        stopAnimation();
    };
    

    
    // 播放速度变化事件
    const speedInput = speedControl.querySelector('.speed-input');
    speedInput.onchange = () => {
        currentSpeed = parseFloat(speedInput.value);
        if (isPlaying) {
            restartAnimation();
        }
    };
    
    // 循环播放变化事件
    const loopInput = loopControl.querySelector('.loop-input');
    loopInput.onchange = () => {
        currentLoop = loopInput.checked;
    };
    

    
    // 动画播放函数
    function playAnimation() {
        if (isPlaying) return;
        
        isPlaying = true;
        playPauseBtn.innerHTML = '<i class="fas fa-pause"></i> 暂停';
        playPauseBtn.classList.add('playing');
        
        const frameDelay = 1000 / currentSpeed; // 毫秒
        animationInterval = setInterval(() => {
            currentFrame = (currentFrame + 1) % images.length;
            updateAnimationFrame(animationImg, images[currentFrame], currentFrame);
            updateProgress(progressBar, currentFrame, images.length);
            updateFrameIndicators(frameIndicators, currentFrame);
            
            if (!currentLoop && currentFrame === images.length - 1) {
                stopAnimation();
            }
        }, frameDelay);
    }
    
    function pauseAnimation() {
        if (!isPlaying) return;
        
        isPlaying = false;
        playPauseBtn.innerHTML = '<i class="fas fa-play"></i> 播放';
        playPauseBtn.classList.remove('playing');
        
        if (animationInterval) {
            clearInterval(animationInterval);
            animationInterval = null;
        }
    }
    
    function stopAnimation() {
        isPlaying = false;
        playPauseBtn.innerHTML = '<i class="fas fa-play"></i> 播放';
        playPauseBtn.classList.remove('playing');
        
        if (animationInterval) {
            clearInterval(animationInterval);
            animationInterval = null;
        }
        
        currentFrame = 0;
        updateAnimationFrame(animationImg, images[0], 0);
        updateProgress(progressBar, 0, images.length);
        updateFrameIndicators(frameIndicators, 0);
    }
    
    function restartAnimation() {
        pauseAnimation();
        setTimeout(() => {
            playAnimation();
        }, 50);
    }
    
    // 更新动画帧
    function updateAnimationFrame(img, src, frameIndex) {
        img.src = src;
        img.alt = `${folderName} 动画帧 ${frameIndex + 1}`;
    }
    
    // 更新进度条
    function updateProgress(progressBar, current, total) {
        const progressFill = progressBar.querySelector('.progress-fill');
        const progressText = progressBar.querySelector('.progress-text');
        
        const percentage = (current / (total - 1)) * 100;
        progressFill.style.width = `${percentage}%`;
        progressText.textContent = `${current + 1} / ${total}`;
    }
    
    // 更新帧指示器
    function updateFrameIndicators(indicators, activeIndex) {
        const dots = indicators.querySelectorAll('.frame-indicator');
        dots.forEach((dot, index) => {
            dot.classList.toggle('active', index === activeIndex);
        });
    }
    

}

// 创建文件夹切换器（用于多文件夹场景）
function createFolderSwitcher(sceneName, folders, currentFolder) {
    const switcher = document.createElement('div');
    switcher.className = 'folder-switcher';
    
    const label = document.createElement('label');
    label.textContent = '切换动画序列:';
    switcher.appendChild(label);
    
    const buttonContainer = document.createElement('div');
    buttonContainer.className = 'folder-buttons';
    
    folders.forEach(folder => {
        const btn = document.createElement('button');
        btn.className = `btn btn-small folder-btn ${folder === currentFolder ? 'active' : ''}`;
        btn.textContent = folder;
        btn.onclick = () => {
            // 切换动画序列
            previewAnimation(folder, sceneName);
        };
        buttonContainer.appendChild(btn);
    });
    
    switcher.appendChild(buttonContainer);
    return switcher;
}



// 关闭预览模态框
function closePreviewModal() {
    const modal = document.getElementById('previewModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

// 更新动画设置
function updateAnimationSetting(sceneName, key, value) {
    if (!animationSettings[sceneName]) {
        animationSettings[sceneName] = {};
    }
    
    if (key === 'folders') {
        // 处理多文件夹情况
        if (!animationSettings[sceneName].folders) {
            animationSettings[sceneName].folders = [];
        }
        
        if (value && !animationSettings[sceneName].folders.includes(value)) {
            animationSettings[sceneName].folders.push(value);
        }
    } else {
        animationSettings[sceneName][key] = value;
    }
    
    console.log(`更新动画设置: ${sceneName}.${key} = ${value}`);
}

// 添加文件夹到场景
function addFolderToScene(sceneName) {
    const item = document.querySelector(`[data-scene="${sceneName}"]`);
    if (!item) return;
    
    const folderSelect = item.querySelector('.folder-select');
    const selectedFolders = item.querySelector('.selected-folders');
    
    if (!folderSelect || !selectedFolders) return;
    
    const selectedValue = folderSelect.value;
    if (!selectedValue) {
        showMessage('请先选择要添加的文件夹', 'error');
        return;
    }
    
    // 检查是否已经添加
    const existingTags = selectedFolders.querySelectorAll('.folder-tag');
    for (let tag of existingTags) {
        if (tag.textContent.trim().replace(/×$/, '') === selectedValue) {
            showMessage('该文件夹已经添加过了', 'error');
            return;
        }
    }
    
    // 添加到场景
    addFolderTag(item, selectedValue);
    
    // 更新设置
    if (!animationSettings[sceneName].folders) {
        animationSettings[sceneName].folders = [];
    }
    animationSettings[sceneName].folders.push(selectedValue);
    
    // 重置选择器
    folderSelect.value = '';
}

// 从场景中移除文件夹
function removeFolderFromScene(sceneName, folderName) {
    const item = document.querySelector(`[data-scene="${sceneName}"]`);
    if (!item) return;
    
    // 从设置中移除
    if (animationSettings[sceneName].folders) {
        const index = animationSettings[sceneName].folders.indexOf(folderName);
        if (index > -1) {
            animationSettings[sceneName].folders.splice(index, 1);
        }
    }
    
    // 从DOM中移除标签
    const tags = item.querySelectorAll('.folder-tag');
    tags.forEach(tag => {
        if (tag.textContent.trim().replace(/×$/, '') === folderName) {
            tag.remove();
        }
    });
}

// 添加文件夹标签
function addFolderTag(item, folderName) {
    const selectedFolders = item.querySelector('.selected-folders');
    if (!selectedFolders) return;
    
    const tag = document.createElement('span');
    tag.className = 'folder-tag';
    tag.innerHTML = `
        ${folderName}
        <button onclick="removeFolderFromScene('${item.dataset.scene}', '${folderName}')">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    selectedFolders.appendChild(tag);
}

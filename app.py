from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import json
import os
from pathlib import Path
import shutil
from werkzeug.utils import secure_filename
import threading
import time

app = Flask(__name__)
app.secret_key = 'virtual_maid_2025_secret_key'

# 配置文件路径
CONFIG_FILE = 'maid_settings.json'
DEFAULT_CONFIG = {
    "user_name": "主人",
    "background_story": None,  # 背景故事，None表示使用默认故事
    "api_config": {
        "base_url": "https://www.dmxapi.cn/v1",
        "api_key": "",
        "model": "Doubao-1.5-pro-32k"
    },
    "animation_settings": {
        "刚开启时": {
            "folder": "politeTalk",
            "scale_factor": 1.0,
            "loop": True,
            "play_speed": 3.0
        },
        "思考中": {
            "folder": "DanceWhileTalk",
            "scale_factor": 1.0,
            "loop": True,
            "play_speed": 3.0
        },
        "写代码中": {
            "folder": "coding",
            "scale_factor": 1.0,
            "loop": True,
            "play_speed": 32.0
        },
        "错误情况": {
            "folder": "bowWhileTalk",
            "scale_factor": 1.0,
            "loop": True,
            "play_speed": 3.0
        },
        "普通反馈": {
            "folders": ["happyTalk", "politeTalk", "DanceWhileTalk"],
            "scale_factor": 1.0,
            "loop": True,
            "play_speed": 3.0
        },
        "等待操作": {
            "folder": "DanceWhileTalk",
            "scale_factor": 1.0,
            "loop": True,
            "play_speed": 3.0
        },
        "准备执行": {
            "folder": "DanceWhileTalk",
            "scale_factor": 1.0,
            "loop": True,
            "play_speed": 3.0
        },
        "生成中": {
            "folder": "coding",
            "scale_factor": 1.0,
            "loop": True,
            "play_speed": 32.0
        },
        "保存中": {
            "folder": "coding",
            "scale_factor": 1.0,
            "loop": True,
            "play_speed": 32.0
        },
        "准备就绪": {
            "folder": "DanceWhileTalk",
            "scale_factor": 1.0,
            "loop": True,
            "play_speed": 3.0
        },
        "执行中": {
            "folder": "DanceWhileTalk",
            "scale_factor": 1.0,
            "loop": True,
            "play_speed": 3.0
        },
        "处理中": {
            "folder": "DanceWhileTalk",
            "scale_factor": 1.0,
            "loop": True,
            "play_speed": 3.0
        }
    }
}

def load_config():
    """加载配置文件"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
                # 修复配置，确保所有必要的字段都存在
                if 'animation_settings' in config:
                    animation_settings = config['animation_settings']
                    for scene_name, scene_config in animation_settings.items():
                        if isinstance(scene_config, dict):
                            # 确保所有场景都有完整的配置
                            if 'scale_factor' not in scene_config:
                                scene_config['scale_factor'] = 1.0
                            if 'loop' not in scene_config:
                                scene_config['loop'] = True
                            if 'play_speed' not in scene_config:
                                # 根据场景设置默认播放速度
                                if 'coding' in scene_name or scene_name in ['写代码中', '生成中', '保存中']:
                                    scene_config['play_speed'] = 32.0
                                else:
                                    scene_config['play_speed'] = 3.0
                
                # 确保API配置包含模型字段
                if 'api_config' in config and 'model' not in config['api_config']:
                    config['api_config']['model'] = 'Doubao-1.5-pro-32k'
                
                return config
        except:
            pass
    return DEFAULT_CONFIG.copy()

def save_config(config):
    """保存配置文件"""
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

def get_animation_folders():
    """获取pr目录下的动画文件夹"""
    pr_dir = Path('pr')
    if not pr_dir.exists():
        return []
    
    folders = []
    for item in pr_dir.iterdir():
        if item.is_dir():
            # 统计图片数量
            image_count = len([f for f in item.iterdir() if f.suffix.lower() in ['.png', '.jpg', '.jpeg']])
            folders.append({
                'name': item.name,
                'image_count': image_count
            })
    return sorted(folders, key=lambda x: x['name'])

@app.route('/')
def index():
    """主设置页面"""
    config = load_config()
    animation_folders = get_animation_folders()
    return render_template('index.html', config=config, animation_folders=animation_folders)

@app.route('/api/save_config', methods=['POST'])
def save_config_api():
    """保存配置API"""
    try:
        data = request.json
        
        # 如果收到空数据，返回当前配置
        if not data or (isinstance(data, dict) and len(data) == 0):
            config = load_config()
            return jsonify({'success': True, 'message': '配置获取成功', 'config': config})
        
        config = load_config()
        
        # 更新配置
        if 'user_name' in data:
            config['user_name'] = data['user_name']
        if 'background_story' in data:
            config['background_story'] = data['background_story']
        if 'api_config' in data:
            config['api_config'].update(data['api_config'])
        if 'animation_settings' in data:
            # 确保所有动画设置都包含完整的字段
            for scene_name, scene_config in data['animation_settings'].items():
                if isinstance(scene_config, dict):
                    if 'scale_factor' not in scene_config:
                        scene_config['scale_factor'] = 1.0
                    if 'loop' not in scene_config:
                        scene_config['loop'] = True
                    if 'play_speed' not in scene_config:
                        # 根据场景设置默认播放速度
                        if 'coding' in scene_name or scene_name in ['写代码中', '生成中', '保存中']:
                            scene_config['play_speed'] = 32.0
                        else:
                            scene_config['play_speed'] = 3.0
            
            config['animation_settings'].update(data['animation_settings'])
        
        save_config(config)
        return jsonify({'success': True, 'message': '配置保存成功！重启后生效喵~'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'保存失败：{str(e)}'})

@app.route('/api/upload_animation', methods=['POST'])
def upload_animation():
    """上传动画序列帧"""
    try:
        if 'files[]' not in request.files:
            return jsonify({'success': False, 'message': '没有选择文件'})
        
        files = request.files.getlist('files[]')
        folder_name = request.form.get('folder_name', '').strip()
        
        if not folder_name:
            return jsonify({'success': False, 'message': '请输入文件夹名称'})
        
        if not files or files[0].filename == '':
            return jsonify({'success': False, 'message': '没有选择文件'})
        
        # 创建目标目录
        pr_dir = Path('pr')
        target_dir = pr_dir / folder_name
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存文件
        saved_count = 0
        for file in files:
            if file and file.filename:
                filename = secure_filename(file.filename)
                if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                    file_path = target_dir / filename
                    file.save(str(file_path))
                    saved_count += 1
        
        return jsonify({
            'success': True, 
            'message': f'成功上传 {saved_count} 个文件到 {folder_name} 文件夹！重启后生效喵~'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'上传失败：{str(e)}'})

@app.route('/api/delete_animation_folder', methods=['POST'])
def delete_animation_folder():
    """删除动画文件夹"""
    try:
        data = request.json
        folder_name = data.get('folder_name', '').strip()
        
        if not folder_name:
            return jsonify({'success': False, 'message': '文件夹名称不能为空'})
        
        target_dir = Path('pr') / folder_name
        if target_dir.exists() and target_dir.is_dir():
            shutil.rmtree(target_dir)
            return jsonify({
                'success': True, 
                'message': f'成功删除 {folder_name} 文件夹！重启后生效喵~'
            })
        else:
            return jsonify({'success': False, 'message': '文件夹不存在'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'删除失败：{str(e)}'})

@app.route('/api/save_story', methods=['POST'])
def save_story_api():
    """保存背景故事API"""
    try:
        data = request.json
        story_content = data.get('background_story', '').strip()
        
        config = load_config()
        config['background_story'] = story_content if story_content else None
        save_config(config)
        
        return jsonify({'success': True, 'message': '背景故事保存成功！重启后生效喵~'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'保存失败：{str(e)}'})

@app.route('/api/reset_story', methods=['POST'])
def reset_story_api():
    """重置背景故事API"""
    try:
        config = load_config()
        config['background_story'] = None
        save_config(config)
        
        return jsonify({'success': True, 'message': '背景故事已重置为默认！重启后生效喵~'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'重置失败：{str(e)}'})

@app.route('/api/reload_config', methods=['POST'])
def reload_config_api():
    """重新加载配置API"""
    try:
        # 重新加载配置文件
        config = load_config()
        return jsonify({'success': True, 'message': '配置已重新加载！', 'config': config})
    except Exception as e:
        return jsonify({'success': False, 'message': f'重新加载配置失败：{str(e)}'})

@app.route('/api/get_animation_preview/<folder_name>')
def get_animation_preview(folder_name):
    """获取动画预览"""
    try:
        target_dir = Path('pr') / folder_name
        if not target_dir.exists():
            return jsonify({'success': False, 'message': '文件夹不存在'})
        
        images = []
        for file in sorted(target_dir.iterdir()):
            if file.suffix.lower() in ['.png', '.jpg', '.jpeg']:
                images.append(f'/api/animation_image/{folder_name}/{file.name}')
        
        return jsonify({'success': True, 'images': images})
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取预览失败：{str(e)}'})

@app.route('/api/animation_image/<folder_name>/<filename>')
def get_animation_image(folder_name, filename):
    """获取动画图片文件"""
    try:
        from flask import send_file
        image_path = Path('pr') / folder_name / filename
        
        if not image_path.exists():
            return jsonify({'success': False, 'message': '图片文件不存在'}), 404
        
        # 检查文件扩展名
        if image_path.suffix.lower() not in ['.png', '.jpg', '.jpeg']:
            return jsonify({'success': False, 'message': '不支持的文件格式'}), 400
        
        return send_file(str(image_path), mimetype='image/png' if image_path.suffix.lower() == '.png' else 'image/jpeg')
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取图片失败：{str(e)}'}), 500

if __name__ == '__main__':
    # 确保pr目录存在
    Path('pr').mkdir(exist_ok=True)
    
    # 添加优雅关闭处理
    import signal
    import sys
    
    def signal_handler(sig, frame):
        print('\n正在关闭Flask应用...')
        sys.exit(0)
    
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # 启动Flask应用
        app.run(host='0.0.0.0', port=5000, debug=True)
    except KeyboardInterrupt:
        print('\n收到中断信号，正在关闭应用...')
        sys.exit(0)
    except Exception as e:
        print(f'应用运行出错: {e}')
        sys.exit(1)

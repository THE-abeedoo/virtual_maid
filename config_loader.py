#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置文件加载器
用于动态加载虚拟女仆系统的配置
"""

import json
import os
from pathlib import Path

def load_maid_config():
    """加载女仆系统配置"""
    config_file = 'maid_settings.json'
    
    if not os.path.exists(config_file):
        print("⚠️ 配置文件不存在，创建默认配置")
        create_default_config()
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
            return config
    except Exception as e:
        print(f"⚠️ 加载配置文件失败: {e}")
        return get_default_config()

def get_default_config():
    """获取默认配置"""
    return {
        "user_name": "主人",
        "background_story": None,  # 背景故事，None表示使用默认故事
        "api_config": {
            "base_url": "https://www.dmxapi.cn/v1",
            "api_key": ""
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

def create_default_config():
    """创建默认配置文件"""
    config = get_default_config()
    try:
        with open('maid_settings.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        print("✅ 默认配置文件已创建")
    except Exception as e:
        print(f"❌ 创建默认配置文件失败: {e}")

def reload_config():
    """重新加载配置"""
    return load_maid_config()

def get_api_config():
    """获取API配置"""
    config = load_maid_config()
    return config.get('api_config', {})

def get_animation_config(scene_name):
    """获取指定场景的动画配置"""
    config = load_maid_config()
    animation_settings = config.get('animation_settings', {})
    return animation_settings.get(scene_name, {})

def get_user_name():
    """获取用户名称"""
    config = load_maid_config()
    return config.get('user_name', '主人')

def get_background_story():
    """获取背景故事"""
    config = load_maid_config()
    return config.get('background_story')

if __name__ == "__main__":
    # 测试配置加载
    config = load_maid_config()
    print("当前配置:")
    print(json.dumps(config, ensure_ascii=False, indent=2))

import asyncio
import base64
import http.client
import time
import prompt as pt
import librosa
import sounddevice as sd
import requests
import json
import pyrubberband as pyrb
import soundfile as sf
from openai import AsyncOpenAI, OpenAI
from openai.helpers import LocalAudioPlayer
from openai._response import AsyncStreamedBinaryAPIResponse, StreamedBinaryAPIResponse
from openai import _legacy_response
from typing import Union
import numpy as np
import io
import translate

def load_api_config():
    """加载API配置"""
    try:
        from config_loader import get_api_config
        api_config = get_api_config()
        base_url = api_config.get('base_url', 'https://www.dmxapi.cn/v1')
        api_key = api_config.get('api_key', '')
        
        if not api_key:
            print("⚠️ API密钥未设置，请检查配置文件")
            return 'https://www.dmxapi.cn/v1', ''
        
        return base_url, api_key
    except Exception as e:
        print(f"⚠️ 加载API配置失败: {e}")
        return 'https://www.dmxapi.cn/v1', ''

def load_trial_config():
    """加载试用配置"""
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config.get('trial_config', {})
    except Exception as e:
        print(f"⚠️ 加载试用配置失败: {e}")
        return {}

def should_use_trial():
    """判断是否应该使用试用模式"""
    trial_config = load_trial_config()
    return trial_config.get('trial_enabled', True)

def get_trial_ai_response(text: str) -> str:
    """通过试用程序获取AI响应"""
    try:
        import subprocess
        import os
        
        # 获取试用程序路径
        trial_config = load_trial_config()
        trial_exe_path = trial_config.get('trial_exe_path', 'trial.exe')
        
        # 检查试用程序是否存在
        if not os.path.exists(trial_exe_path):
            error_response = {
                "actionable": "chat",
                "task_summary": "试用程序未找到，请检查配置",
                "need_additional_data": "null"
            }
            return json.dumps(error_response, ensure_ascii=False)
        
        # 准备输入数据
        input_data = json.dumps({"prompt": text})
        
        # 启动试用程序
        process = subprocess.Popen(
            [trial_exe_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0)
        )
        
        # 发送数据并获取输出
        stdout, stderr = process.communicate(input=input_data, timeout=60)
        
        # 解析响应
        try:
            response = json.loads(stdout)
            
            if response.get("status") == "success":
                content = response.get("content", "")
                # content本身是一个JSON字符串，需要解析
                try:
                    content_json = json.loads(content)
                    return content
                except json.JSONDecodeError:
                    # 如果content不是有效的JSON，直接返回
                    return content
            else:
                error_content = response.get("content", "")
                # 检查是否包含试用过期的关键词
                if ("has expired" in error_content or "used up" in error_content or 
                    "used up all your trial attempts" in error_content):
                    disable_trial()
                    # 触发网页弹出，显示需要填写API
                    try:
                        import webbrowser
                        import threading
                        def open_settings_page():
                            time.sleep(1)  # 延迟1秒，确保主程序处理完当前请求
                            webbrowser.open('http://localhost:5000?trial_expired=true')
                        
                        threading.Thread(target=open_settings_page, daemon=True).start()
                    except Exception as e:
                        print(f"无法打开设置页面: {e}")
                    
                    error_response = {
                        "actionable": "chat",
                        "task_summary": f"试用已到期，已自动禁用试用模式\n{error_content}\n\n已为您打开设置页面，请填写API密钥继续使用。",
                        "need_additional_data": "null"
                    }
                    return json.dumps(error_response, ensure_ascii=False)
                error_response = {
                    "actionable": "chat",
                    "task_summary": f"试用出错了：{error_content}",
                    "need_additional_data": "null"
                }
                return json.dumps(error_response, ensure_ascii=False)
        except json.JSONDecodeError as e:
            print(f"AI JSON解析错误: {e}")
            print(f"原始输出: {repr(stdout)}")
            print(f"错误输出: {repr(stderr)}")
            # 返回一个有效的JSON格式，避免main.py中的解析失败
            error_response = {
                "actionable": "chat",
                "task_summary": "系统出现错误，无法处理请求",
                "need_additional_data": "null"
            }
            return json.dumps(error_response, ensure_ascii=False)
            
    except subprocess.TimeoutExpired:
        error_response = {
            "actionable": "chat",
            "task_summary": "试用请求超时了",
            "need_additional_data": "null"
        }
        return json.dumps(error_response, ensure_ascii=False)
    except Exception as e:
        error_response = {
            "actionable": "chat",
            "task_summary": f"试用出现意外错误：{str(e)}",
            "need_additional_data": "null"
        }
        return json.dumps(error_response, ensure_ascii=False)

def get_trial_speak(text: str, tone: str = "Speak in a cheerful and positive tone.", save_path: str = None) -> str:
    """通过试用程序获取语音合成，不占用试用次数"""
    try:
        import subprocess
        import os
        
        # 获取试用程序路径
        trial_config = load_trial_config()
        trial_exe_path = trial_config.get('trial_exe_path', 'trial.exe')
        
        # 检查试用程序是否存在
        if not os.path.exists(trial_exe_path):
            return "试用程序未找到，请检查配置"
        
        # 准备语音合成请求数据
        input_data = json.dumps({
            "action": "speak",
            "text": text,
            "tone": tone,
            "save_path": save_path
        })
        
        # 启动试用程序
        process = subprocess.Popen(
            [trial_exe_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0)
        )
        
        # 发送数据并获取输出
        stdout, stderr = process.communicate(input=input_data, timeout=60)
        
        if process.returncode != 0:
            return f"试用程序出错了：{stderr}"
        
        # 解析响应
        try:
            response = json.loads(stdout)
            
            if response.get("status") == "success":
                return response.get("file_path", "")  # 返回文件路径
            else:
                error_content = response.get("content", "")
                # 检查是否包含试用过期的关键词
                if ("has expired" in error_content or "used up" in error_content or 
                    "used up all your trial attempts" in error_content):
                    disable_trial()
                    return f"试用已到期，已自动禁用试用模式\n{error_content}"
                return f"语音合成失败：{error_content}"
        except json.JSONDecodeError as e:
            print(f"TTS JSON解析错误: {e}")
            print(f"原始输出: {repr(stdout)}")
            print(f"错误输出: {repr(stderr)}")
            return f"试用响应解析失败了: 原始输出={stdout[:200]}..."
            
    except subprocess.TimeoutExpired:
        return "试用请求超时了"
    except Exception as e:
        return f"试用出现意外错误：{str(e)}"

def disable_trial():
    """禁用试用模式"""
    try:
        # 读取当前配置
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 禁用试用
        if 'trial_config' not in config:
            config['trial_config'] = {}
        config['trial_config']['trial_enabled'] = False
        
        # 保存配置
        with open('config.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print("⚠️ 试用模式已自动禁用")
    except Exception as e:
        print(f"⚠️ 禁用试用模式失败: {e}")

# 动态加载API配置
BASE_URL, API_KEY = load_api_config()

# 注意：conn变量现在通过动态配置来设置，不再硬编码
SAMPLE_RATE = 24000

def get_model_from_config() -> str:
    """
    从配置文件中获取AI模型名称
    如果没有配置或配置无效，返回默认值
    """
    try:
        config_path = 'maid_settings.json'
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                model = config.get('api_config', {}).get('model', 'Doubao-1.5-pro-32k')
                return model
    except Exception as e:
        print(f"⚠️ 读取模型配置失败: {e}")
    
    # 返回默认模型
    return ''


def simple_ai_response(text: str, include_history: bool = True) -> str:
    """
    简单的AI响应函数，输入文本返回文本
    支持历史记录功能
    """
    # 动态获取API配置
    base_url, api_key = load_api_config()
    
    # 检查是否使用试用模式
    if api_key == "AKASAKAMAID" and should_use_trial():
        return get_trial_ai_response(text)
    
    # 构建消息列表，包含系统提示
    messages = [
        {
            "role": "system",
            "content": pt.story
        }
    ]
    
    # 如果需要历史记录，添加历史对话
    if include_history:
        try:
            from chat_history import chat_history
            # 添加历史记录，模仿449-450行的代码
            history_messages = chat_history.format_history_for_ai(10)
            messages.extend(history_messages)
        except Exception as e:
            print(f"⚠️ 加载历史记录失败: {e}")
    
    # 添加当前用户输入
    messages.append({
        "role": "user",
        "content": text
    })

    # 从配置中获取模型名称，如果没有则使用默认值
    model_name = get_model_from_config()
    
    try:
        # 使用OpenAI库而不是requests
        client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        
        # 调用OpenAI API
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=0.7,
            max_tokens=2000
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        return f"出错了：{str(e)}"


def get_ai_response(prompt: str, conversation_type: str = "chat",
                    include_history: bool = True, save_to_history: bool = True,
                    current_prompt_template: str = None) -> str:
    """
    带历史记录的AI响应函数

    Args:
        prompt: 用户输入或完整的prompt
        conversation_type: 对话类型 ("chat", "code_execution", "image_analysis")
        include_history: 是否包含历史记录
        save_to_history: 是否保存到历史记录
        current_prompt_template: 当前使用的prompt模板（用于格式化最新一条历史记录）

    Returns:
        AI响应内容
    """
    from chat_history import chat_history

    # 调用底层函数获取AI响应，传递历史记录参数
    assistant_response = simple_ai_response(prompt, include_history=include_history)

    # 移除所有的"```json"和"```"标记
    assistant_response = assistant_response.replace("```json", "").replace("```", "").strip()

    # 只在需要时保存对话到历史记录
    if save_to_history:
        # 如果使用了prompt模板，提取原始用户输入
        if current_prompt_template and "{user_input}" in current_prompt_template:
            # 尝试从prompt中提取原始用户输入
            # 这里需要更复杂的逻辑来提取，暂时使用原始prompt
            original_user_input = prompt
        else:
            original_user_input = prompt

        chat_history.add_conversation(original_user_input, assistant_response, conversation_type)

    print(f"AI响应: {assistant_response}")
    return assistant_response


class PitchShiftedLocalAudioPlayer(LocalAudioPlayer):
    async def _tts_response_to_buffer(
            self,
            response: Union[
                _legacy_response.HttpxBinaryResponseContent,
                AsyncStreamedBinaryAPIResponse,
                StreamedBinaryAPIResponse,
            ],
    ) -> np.ndarray:
        chunks: list[bytes] = []
        if isinstance(response, _legacy_response.HttpxBinaryResponseContent) or isinstance(
                response, StreamedBinaryAPIResponse
        ):
            for chunk in response.iter_bytes(chunk_size=1024):
                if chunk:
                    chunks.append(chunk)
        else:
            async for chunk in response.iter_bytes(chunk_size=1024):
                if chunk:
                    chunks.append(chunk)

        audio_bytes = b"".join(chunks)
        audio_np = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32767.0
        audio_np = audio_np.flatten()  # flatten to 1D mono

        # Apply pitch shift (+4.1 semitones)
        audio_shifted = librosa.effects.pitch_shift(audio_np, sr=SAMPLE_RATE, n_steps=4.1)
        audio_shifted = audio_shifted.reshape(-1, 1)  # reshape for playback
        return audio_shifted.astype(np.float32)


async def _speak_async(text: str,tone="Speak in a cheerful and positive tone."):
    """
    异步语音合成函数，使用音调偏移

    Args:
        text (str): 要转换为语音的文本
        tone: 语气
    """
    # 动态获取API配置
    base_url, api_key = load_api_config()
    client = AsyncOpenAI(api_key=api_key, base_url=base_url)

    start_time = time.time()
    async with client.audio.speech.with_streaming_response.create(
            model="gpt-4o-mini-tts",
            voice="sage",
            input=text,
            instructions=tone,
            response_format="pcm",
    ) as response:
        mid_time = time.time()
        await PitchShiftedLocalAudioPlayer().play(response)
        end_time = time.time()

    print(f"[Async] 请求耗时: {mid_time - start_time:.4f} 秒")
    print(f"[Async] 播放耗时: {end_time - mid_time:.4f} 秒")
    print(f"[Async] 总耗时: {end_time - start_time:.4f} 秒")

def speak_async(text):
    asyncio.get_event_loop().run_until_complete(_speak_async(text))

def describe_image(image_path, api_key=None):
    """
    使用 DMXAPI 接口对本地图片进行识别并生成描述。

    参数:
        image_path (str): 本地图片路径
        api_key (str): 用户的 DMXAPI API Key

    返回:
        str: AI 对图片内容的描述文本
    """
    from chat_history import chat_history

    def encode_image(path):
        """将图片编码为 Base64 字符串"""
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    # 动态获取API配置
    base_url, api_key = load_api_config()
    api_url = f"{base_url}/chat/completions"
    base64_image = encode_image(image_path)

    # 构建消息列表，包含历史记录
    messages = [
        {
            "role": "system",
            "content": "你是一个图像识别助手，请根据用户提供的图片内容，准确描述图片中包含的信息、文字或场景。用可爱的女仆语气回答，使用中文为主语言。",
        }
    ]

    # 添加历史记录
    history_messages = chat_history.format_history_for_ai(10)
    messages.extend(history_messages)

    # 添加当前图片分析请求
    messages.append({
        "role": "user",
        "content": [
            {"type": "text", "text": "请描述这张图片的内容。"},
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{base64_image}"
                },
            },
        ],
    })

    # 构建请求载荷
    payload = {
        "model": "chatgpt-4o-latest",
        "messages": messages,
        "temperature": 0.2,
        "user": "miao"
    }

    # 请求头
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
        "User-Agent": "VirtualMaid/1.0.0",
    }

    # 发送请求
    response = requests.post(api_url, headers=headers, json=payload)

    # 处理返回结果
    if response.status_code == 200:
        try:
            assistant_response = response.json()["choices"][0]["message"]["content"]
            # 保存图片分析对话到历史记录
            chat_history.add_conversation(
                f"[图片分析] {image_path}",
                assistant_response,
                "image_analysis",
                {"image_path": image_path}
            )
            return assistant_response
        except Exception as e:
            error_msg = f"解析响应出错: {e}"
            chat_history.add_conversation(
                f"[图片分析] {image_path}",
                error_msg,
                "image_analysis",
                {"image_path": image_path, "error": str(e)}
            )
            return error_msg
    else:
        error_msg = f"请求失败，状态码: {response.status_code}, 响应内容: {response.text}"
        chat_history.add_conversation(
            f"[图片分析] {image_path}",
            error_msg,
            "image_analysis",
            {"image_path": image_path, "error": error_msg}
        )
        return error_msg


import json
import time
import io
import soundfile as sf
import pyrubberband as pyrb
import sounddevice as sd

import json
import time
import io
import os
import hashlib
import soundfile as sf
import sounddevice as sd
from urllib.parse import quote

# 缓存目录
CACHE_DIR = "audio_cache"

def speak(text, tone, dialog_shower=None, do_translate=True, save_path=None):
    if do_translate:
            text = translate.connect(text)
    # 动态获取API配置
    base_url, api_key = load_api_config()
    
    # 检查是否使用试用模式
    if api_key == "AKASAKAMAID" and should_use_trial():
        # 使用试用版本的语音合成，不占用试用次数
        trial_file_path = get_trial_speak(text, tone, save_path)
        print(f"试用版本语音合成文件路径: {trial_file_path}")
        
        # 检查试用版本是否成功生成了音频文件
        if trial_file_path and os.path.exists(trial_file_path):
            try:
                # 加载试用版本生成的音频文件
                y, sr = sf.read(trial_file_path)
                print(f"成功加载试用版本音频: {trial_file_path}")
                
                # 变调处理
                y_shifted = pyrb.pitch_shift(y, sr, n_steps=4.1)  # 升调4.1半音
                print("试用版本音频变调处理完成")
                
                # 显示对话（如果有）
                if dialog_shower:
                    dialog_shower()
                
                # 播放音频
                sd.play(y_shifted, sr)
                sd.wait()  # 等待播放完成
                print("试用版本音频播放完成")
                
                return
            except Exception as e:
                print(f"试用版本音频处理失败: {str(e)}")
                # 如果处理失败，回退到正常模式
                print("回退到正常模式...")
        else:
            print("试用版本未生成有效音频文件，回退到正常模式...")
    
    # 正常模式：确保缓存目录存在
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)
    
    # 计算文本的MD5值作为缓存文件名
    text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
    cache_file = os.path.join(CACHE_DIR, f"{text_hash}.wav")
    
    # 检查缓存文件是否存在
    if os.path.exists(cache_file):
        print(f"使用缓存音频: {cache_file}")
        # 加载缓存的音频
        y, sr = sf.read(cache_file)
    else:
        # 构建请求 payload（注意：实际使用需替换为有效的API端点和参数）
        payload = json.dumps({
            "model": "gpt-4o-mini-tts",
            "input": text,
            "voice": "sage",
            "response_format": "wav",
            "instructions": tone
        })
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

        # 使用requests发送请求，避免硬编码的conn
        url = f"{base_url}/audio/speech"
        response = requests.post(url, headers=headers, json=json.loads(payload))
        
        if response.status_code != 200:
            raise Exception(f"TTS请求失败: {response.status_code}")
        
        audio_data = response.content

        # 音频数据已通过requests获取
        receive_start = time.time()
        receive_end = time.time()
        print("正在处理语音：" + text)

        # 加载音频数据
        y, sr = sf.read(io.BytesIO(audio_data))

        # 变调处理计时
        pitch_start = time.time()
        y_shifted = pyrb.pitch_shift(y, sr, n_steps=4.1)  # 升调4.1半音
        pitch_end = time.time()

        # 打印耗时信息
        print(f"接收部分耗时: {receive_end - receive_start:.4f} 秒")
        print(f"变调部分耗时: {pitch_end - pitch_start:.4f} 秒")
        y = y_shifted
        # 保存到缓存
        try:
            sf.write(cache_file, y_shifted, sr)
            print(f"已缓存音频至: {cache_file}")
        except Exception as e:
            print(f"缓存音频失败: {str(e)}")
    
    # 显示对话（如果有）
    if dialog_shower:
        dialog_shower()

    
    # 播放音频
    sd.play(y, sr)
    sd.wait()  # 等待播放完成

        # 保存音频（如果指定了保存路径）
    if save_path:
        try:
            # 使用soundfile保存WAV文件（默认格式为WAV）
            sf.write(save_path, y, sr)
            print(f"音频已保存至：{save_path}")
        except Exception as e:
            print(f"保存音频失败：{str(e)}")

# 使用示例：
# speak("测试语音", "友好", save_path="output.wav")

if __name__ == '__main__':
    # speak("你好哇", "friendly", save_path="output.wav")

import threading
import time
import os
import importlib.util
import traceback
from pathlib import Path
import random
import prompt
from call_ai import get_ai_response, speak
from pr_image_processor import PRImageProcessor
from chat_history import chat_history
import json
import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer, pyqtSignal, QObject, QThread
from pynput import keyboard  # 使用 pynput 库的 keyboard 模块
from input_dialog import InputDialogManager
# 使用 Path 对象统一处理路径
CODE_FOLDER = Path("./py").resolve()


def analyze_code_error(error_msg: str, code_content: str) -> str:
    """
    分析代码错误，提供改进建议
    """
    try:
        analysis_prompt = f"""
请分析以下Python代码的错误，并提供具体的修复建议：

错误信息：{error_msg}

代码内容：
{code_content}

请提供：
1. 错误原因分析
2. 具体的修复建议
3. 改进后的代码示例（如果需要）

请用中文回答，格式要清晰。
"""
        
        analysis_result = get_ai_response(analysis_prompt, "code_analysis", include_history=False, save_to_history=False)
        return analysis_result
    except Exception as e:
        return f"错误分析失败: {str(e)}"


def validate_code_syntax(code_content: str) -> tuple[bool, str]:
    """
    验证代码语法是否正确
    返回: (是否有效, 错误信息)
    """
    try:
        compile(code_content, '<string>', 'exec')
        return True, ""
    except SyntaxError as e:
        return False, f"语法错误: {str(e)}"
    except Exception as e:
        return False, f"代码验证错误: {str(e)}"


def get_function_list() -> dict:
    """
    获取函数列表，格式：{"a.py":["参数1描述","参数2描述"...]...}
    """
    function_dict = {}

    if not CODE_FOLDER.exists():
        return function_dict

    for filename in os.listdir(CODE_FOLDER):
        if filename.endswith('.py'):
            json_filename = filename.replace('.py', '.json')
            json_path = CODE_FOLDER / json_filename

            if json_path.exists():
                try:
                    with open(json_path, 'r', encoding='utf-8') as f:
                        json_data = json.load(f)
                        args_doc = json_data.get('args_doc', [])
                        function_dict[filename] = args_doc
                except (json.JSONDecodeError, KeyError):
                    continue

    return function_dict


def pre_check_code_file(file_path: str, func_name: str) -> tuple[bool, str]:
    """
    在代码执行前进行预检查
    返回: (是否通过检查, 检查结果信息)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            code_content = f.read()
        
        # 检查代码是否为空
        if not code_content.strip():
            return False, "代码文件为空"
        
        # 检查语法
        syntax_valid, syntax_error = validate_code_syntax(code_content)
        if not syntax_valid:
            return False, f"语法检查失败: {syntax_error}"
        
        # 检查是否包含main函数
        if "def main" not in code_content and "def main(" not in code_content:
            return False, "代码缺少main函数"
        
        # 检查是否有明显的导入错误
        if "import " in code_content or "from " in code_content:
            # 这里可以添加更复杂的导入检查逻辑
            pass
        
        return True, "代码预检查通过"
        
    except Exception as e:
        return False, f"预检查过程出错: {str(e)}"


def run_python_function_from_file(file_path: str, func_name: str, args_list: list = None) -> tuple[str, bool]:
    """
    从文件中运行Python函数，支持传入参数列表
    返回: (执行结果, 是否成功)
    """
    try:
        # 执行前预检查
        pre_check_result, pre_check_msg = pre_check_code_file(file_path, func_name)
        if not pre_check_result:
            return f"代码预检查失败: {pre_check_msg}", False
        
        spec = importlib.util.spec_from_file_location("dynamic_module", file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        if hasattr(module, func_name):
            func = getattr(module, func_name)
            result = func(*args_list) if args_list else func()
            return str(result), True
        else:
            return f"函数 {func_name} 不存在", False
    except Exception as e:
        error_msg = f"执行错误: {str(e)}"
        print(f"代码执行失败: {error_msg}")
        return error_msg, False


def delete_code_file(func_name: str) -> bool:
    """
    删除指定的代码文件
    返回: 是否删除成功
    """
    try:
        clean_func_name = Path(func_name).stem
        py_path = CODE_FOLDER / f"{clean_func_name}.py"
        json_path = CODE_FOLDER / f"{clean_func_name}.json"
        
        # 删除Python文件
        if py_path.exists():
            py_path.unlink()
            print(f"已删除Python文件: {py_path}")
        
        # 删除JSON文件
        if json_path.exists():
            json_path.unlink()
            print(f"已删除JSON文件: {json_path}")
        
        return True
    except Exception as e:
        print(f"删除文件失败: {e}")
        return False


def rewrite_code_with_retry(task_summary: str, func_name: str, retry_count: int, processor, previous_error: str = "", previous_code: str = "") -> tuple[str, str, list, bool]:
    """
    重写代码，支持重试机制，集成错误分析和语法验证
    返回: (新代码, 新函数名, 参数列表, 是否成功)
    """
    try:
        # 写代码相关：使用配置的动画设置
        coding_config = get_animation_config("写代码中")
        folder = coding_config.get('folder', 'coding')
        scale_factor = coding_config.get('scale_factor', 1.0)
        play_speed = coding_config.get('play_speed', 32.0)
        processor.play(folder, scale_factor=scale_factor, loop=True, play_speed=play_speed)
        
        retry_message = f"第{retry_count}次重试生成代码中..." if retry_count > 1 else "正在为主人生成新代码呢~"
        processor.show_timed_dialog(retry_message, "生成中...")
        
        # 在重试时，给AI更明确的提示
        enhanced_prompt = prompt.CODE_GENERATION_PROMPT.format(task_summary=task_summary)
        
        if retry_count > 1 and previous_error and previous_code:
            # 分析之前的错误
            error_analysis = analyze_code_error(previous_error, previous_code)
            enhanced_prompt += f"\n\n注意：这是第{retry_count}次重试。之前的代码执行失败，错误信息：{previous_error}"
            enhanced_prompt += f"\n\n错误分析：{error_analysis}"
            enhanced_prompt += f"\n\n请根据以上分析，生成能够正确执行的代码，避免之前的错误。"
        elif retry_count > 1:
            enhanced_prompt += f"\n\n注意：这是第{retry_count}次重试，请确保代码能够正确执行，避免之前的错误。"
        
        code_result = get_ai_response(enhanced_prompt, "code_execution", include_history=False, save_to_history=False)

        try:
            code_dict = json.loads(code_result)
            print(f"代码生成结果 (重试{retry_count}): {code_dict}")
        except json.JSONDecodeError as e:
            print(f"JSON解析错误 (重试{retry_count}): {e}")
            print(f"原始结果: {code_result}")
            return "", "", [], False

        new_func_name = code_dict.get("function_name")
        code = code_dict.get("code")
        args_doc = code_dict.get("args_doc", [])
        current_inputs = code_dict.get("current_inputs", [])
        
        if not new_func_name or not code:
            print(f"数据不完整 (重试{retry_count}) - func_name: {bool(new_func_name)}, code: {bool(code)}")
            return "", "", [], False

        # 验证代码语法
        syntax_valid, syntax_error = validate_code_syntax(code)
        if not syntax_valid:
            print(f"代码语法错误 (重试{retry_count}): {syntax_error}")
            processor.show_timed_dialog(f"生成的代码有语法错误，正在重新生成...", "重写中...")
            return "", "", [], False

        # 验证生成的代码是否包含必要的函数
        if "def main" not in code and "def main(" not in code:
            print(f"生成的代码缺少main函数 (重试{retry_count})")
            processor.show_timed_dialog("生成的代码格式不正确，正在重新生成...", "重写中...")
            return "", "", [], False

        # 保存新代码
        CODE_FOLDER.mkdir(exist_ok=True)
        clean_func_name = Path(new_func_name).stem
        py_path = CODE_FOLDER / f"{clean_func_name}.py"
        json_path = CODE_FOLDER / f"{clean_func_name}.json"
        
        try:
            with open(py_path, "w", encoding="utf-8") as f:
                f.write(code)
            print(f"Python文件保存成功 (重试{retry_count}): {py_path}")
        except Exception as e:
            print(f"保存Python文件失败 (重试{retry_count}): {e}")
            return "", "", [], False

        try:
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump({"function_name": new_func_name, "args_doc": args_doc}, f, ensure_ascii=False, indent=2)
            print(f"JSON文件保存成功 (重试{retry_count}): {json_path}")
        except Exception as e:
            print(f"保存JSON文件失败 (重试{retry_count}): {e}")
            # 删除已保存的Python文件
            if py_path.exists():
                py_path.unlink()
            return "", "", [], False

        return code, new_func_name, current_inputs if current_inputs else [], True
        
    except Exception as e:
        print(f"重写代码失败 (重试{retry_count}): {e}")
        return "", "", [], False


# 需要在模块级别添加一个全局变量来存储待补充信息的状态
_pending_additional_data = None


def start_maid_system():
    # 启动设置界面
    start_settings_interface()
    
    # 启动主女仆系统
    maid_system = MaidSystem()
    maid_system.start()


def start_settings_interface():
    """启动设置界面"""
    try:
        import threading
        import webbrowser
        import time
        
        def start_flask():
            try:
                from app import app
                print("🌐 设置界面启动中...")
                app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)
            except Exception as e:
                print(f"❌ 设置界面启动失败: {e}")
        
        # 在后台线程启动Flask
        flask_thread = threading.Thread(target=start_flask, daemon=True)
        flask_thread.start()
        
        # 等待Flask启动
        time.sleep(2)
        
        # 自动打开浏览器
        try:
            webbrowser.open('http://localhost:5000')
            print("🌐 设置界面已启动: http://localhost:5000")
        except:
            print("🌐 设置界面已启动，请手动访问: http://localhost:5000")
            
    except Exception as e:
        print(f"⚠️ 设置界面启动失败: {e}")
        print("💡 您可以手动运行 'python app.py' 来启动设置界面")


def load_animation_settings():
    """加载动画设置配置"""
    try:
        from config_loader import get_animation_config as get_config
        # 重新加载配置
        from config_loader import reload_config
        reload_config()
        return True
    except Exception as e:
        print(f"⚠️ 加载动画配置失败: {e}")
        return False


def get_animation_config(scene_name):
    """获取指定场景的动画配置"""
    try:
        from config_loader import get_animation_config as get_config
        # 每次获取配置时都重新加载，确保配置是最新的
        from config_loader import reload_config
        reload_config()
        return get_config(scene_name)
    except Exception as e:
        print(f"⚠️ 获取动画配置失败: {e}")
        return {}


def get_random_normal_audio():
    """获取随机的普通反馈音频"""
    # 从配置中获取普通反馈的文件夹列表
    normal_config = get_animation_config("普通反馈")
    if normal_config and 'folders' in normal_config:
        normal_audios = normal_config['folders']
    else:
        # 默认配置
        normal_audios = ["happyTalk", "politeTalk", "DanceWhileTalk"]
    
    return random.choice(normal_audios)


def maid_handle_input(user_input: str, processor) -> tuple[str, str]:
    global _pending_additional_data

    # 如果之前有待补充信息的请求，将用户输入拼接
    if _pending_additional_data is not None:
        original_input = _pending_additional_data["original_input"]
        need_additional_data = _pending_additional_data["need_additional_data"]
        # 拼接：第一次输入 + need_additional_data + 第二次输入
        user_input = f"{original_input}\n{need_additional_data}\n{user_input}"
        _pending_additional_data = None  # 清除待补充状态

    judge_prompt = prompt.CODE_EXECUTION_JUDGEMENT_PROMPT.format(user_input=user_input)
    judge_result = get_ai_response(judge_prompt, "code_execution", include_history=True, save_to_history=False)

    try:
        result_dict = json.loads(judge_result)
    except json.JSONDecodeError:
        # 错误情况：使用配置的动画设置
        error_config = get_animation_config("错误情况")
        folder = error_config.get('folder', 'bowWhileTalk')
        scale_factor = error_config.get('scale_factor', 1.0)
        play_speed = error_config.get('play_speed', 3.0)
        processor.play(folder, scale_factor=scale_factor, loop=True, play_speed=play_speed)
        return "回答解析失败", "Speak in a cheerful and positive tone."

    if result_dict.get("a") == "chat":
        chat_prompt = prompt.SMALL_TALK_PROMPT.format(user_input=user_input)
        chat_result = get_ai_response(chat_prompt, "chat", include_history=True, save_to_history=False,
                                      current_prompt_template=prompt.SMALL_TALK_PROMPT)
        print(chat_result)

        try:
            result_dict = json.loads(chat_result)
        except json.JSONDecodeError:
            # 错误情况：使用配置的动画设置
            error_config = get_animation_config("错误情况")
            folder = error_config.get('folder', 'bowWhileTalk')
            scale_factor = error_config.get('scale_factor', 1.0)
            play_speed = error_config.get('play_speed', 3.0)
            processor.play(folder, scale_factor=scale_factor, loop=True, play_speed=play_speed)
            return "回答解析失败", "Speak in a cheerful and positive tone."

        maid_response = result_dict["reply"]
        tone = result_dict.get("tone", "Speak in a cheerful and positive tone.")
        chat_history.add_conversation(user_input, maid_response, "chat")
        # 普通反馈：使用配置的动画设置
        normal_config = get_animation_config("普通反馈")
        if normal_config and 'folders' in normal_config:
            folder = random.choice(normal_config['folders'])
        else:
            folder = get_random_normal_audio()
        
        scale_factor = normal_config.get('scale_factor', 1.0)
        play_speed = normal_config.get('play_speed', 3.0)
        processor.play(folder, scale_factor=scale_factor, loop=True, play_speed=play_speed)
        return maid_response, tone

    # 如果是code类型，需要额外的AI对话来获取详细信息
    detail_prompt = prompt.CODE_DETAIL_PROMPT.format(user_input=user_input)
    detail_result = get_ai_response(detail_prompt, "code_execution", include_history=True, save_to_history=False)

    try:
        detail_dict = json.loads(detail_result)
    except json.JSONDecodeError:
        # 错误情况：使用配置的动画设置
        error_config = get_animation_config("错误情况")
        folder = error_config.get('folder', 'bowWhileTalk')
        scale_factor = error_config.get('scale_factor', 1.0)
        play_speed = error_config.get('play_speed', 3.0)
        processor.play(folder, scale_factor=scale_factor, loop=True, play_speed=play_speed)
        return "回答解析失败", "Speak in a cheerful and positive tone."

    # 检查是否需要补充信息
    need_additional_data = detail_dict.get("need_additional_data")
    if need_additional_data is not None and need_additional_data != "null":
        # 保存当前状态，等待用户补充信息
        _pending_additional_data = {
            "original_input": user_input,
            "need_additional_data": need_additional_data
        }
        # 等待操作：使用配置的动画设置
        wait_config = get_animation_config("等待操作")
        folder = wait_config.get('folder', 'DanceWhileTalk')
        scale_factor = wait_config.get('scale_factor', 1.0)
        play_speed = wait_config.get('play_speed', 3.0)
        processor.play(folder, scale_factor=scale_factor, loop=True, play_speed=play_speed)
        # 返回需要补充信息的提示（带语音输出）
        return need_additional_data, "Speak in a cheerful and positive tone."

    task_summary = detail_dict["task_summary"]
    # 等待操作：使用配置的动画设置
    wait_config = get_animation_config("等待操作")
    folder = wait_config.get('folder', 'DanceWhileTalk')
    scale_factor = wait_config.get('scale_factor', 1.0)
    play_speed = wait_config.get('play_speed', 3.0)
    processor.play(folder, scale_factor=scale_factor, loop=True, play_speed=play_speed)
    processor.show_timed_dialog(f"主人的需求是：{task_summary}", "思考中...")

    func_list = get_function_list()
    match_prompt = prompt.CODE_LIBRARY_MATCHING_PROMPT.format(
        task_summary=task_summary,
        function_list=str(func_list)
    )
    # 等待操作：使用配置的动画设置
    processor.play(folder, scale_factor=scale_factor, loop=True, play_speed=play_speed)
    processor.show_timed_dialog("正在查找已有的代码库，看看有没有能满足主人需求的函数呢~", "查找中...")
    match_result = get_ai_response(match_prompt, "code_execution", include_history=False, save_to_history=False)

    try:
        match_dict = json.loads(match_result)
    except json.JSONDecodeError:
        match_dict = {"matched": False}

    if match_dict.get("matched"):
        func_name = match_dict["matched_function"]
        args_value_list = match_dict["args_value_list"]
        # 等待操作：使用配置的动画设置
        processor.play(folder, scale_factor=scale_factor, loop=True, play_speed=play_speed)
        processor.show_timed_dialog(f"找到匹配的函数：{func_name}，马上为主人执行哟~", "准备执行...")
    else:
        # 写代码相关：使用配置的动画设置
        coding_config = get_animation_config("写代码中")
        folder = coding_config.get('folder', 'coding')
        scale_factor = coding_config.get('scale_factor', 1.0)
        play_speed = coding_config.get('play_speed', 32.0)
        processor.play(folder, scale_factor=scale_factor, loop=True, play_speed=play_speed)
        processor.show_timed_dialog("没有找到匹配的函数，正在为主人生成新代码呢~", "生成中...")
        code_prompt = prompt.CODE_GENERATION_PROMPT.format(task_summary=task_summary)
        code_result = get_ai_response(code_prompt, "code_execution", include_history=False, save_to_history=False)

        try:
            code_dict = json.loads(code_result)
            print(f"代码生成结果: {code_dict}")  # 调试信息
        except json.JSONDecodeError as e:
            print(f"JSON解析错误: {e}")
            print(f"原始结果: {code_result}")
            error_msg = "代码生成失败，请重新描述您的需求。"
            chat_history.add_conversation(user_input, error_msg, "code_execution")
            # 错误情况：使用配置的动画设置
            error_config = get_animation_config("错误情况")
            folder = error_config.get('folder', 'bowWhileTalk')
            scale_factor = error_config.get('scale_factor', 1.0)
            play_speed = error_config.get('play_speed', 3.0)
            processor.play(folder, scale_factor=scale_factor, loop=True, play_speed=play_speed)
            return error_msg, "Speak in a cheerful and positive tone."

        func_name = code_dict.get("function_name")
        code = code_dict.get("code")
        args_doc = code_dict.get("args_doc", [])
        current_inputs = code_dict.get("current_inputs", [])
        
        print(f"提取的数据 - 函数名: {func_name}")
        print(f"提取的数据 - 代码长度: {len(code) if code else 0}")
        print(f"提取的数据 - 参数文档: {args_doc}")
        print(f"提取的数据 - 当前输入: {current_inputs}")

        if not func_name or not code:
            print(f"数据不完整 - func_name: {bool(func_name)}, code: {bool(code)}")
            error_msg = "代码生成不完整，请重新描述您的需求。"
            chat_history.add_conversation(user_input, error_msg, "code_execution")
            # 错误情况：使用配置的动画设置
            error_config = get_animation_config("错误情况")
            folder = error_config.get('folder', 'bowWhileTalk')
            scale_factor = error_config.get('scale_factor', 1.0)
            play_speed = error_config.get('play_speed', 3.0)
            processor.play(folder, scale_factor=scale_factor, loop=True, play_speed=play_speed)
            return error_msg, "Speak in a cheerful and positive tone."

        # 验证生成的代码是否包含必要的函数
        if "def main" not in code and "def main(" not in code:
            print("生成的代码缺少main函数")
            error_msg = "生成的代码格式不正确，缺少main函数。请重新描述您的需求。"
            chat_history.add_conversation(user_input, error_msg, "code_execution")
            # 错误情况：使用配置的动画设置
            error_config = get_animation_config("错误情况")
            folder = error_config.get('folder', 'bowWhileTalk')
            scale_factor = error_config.get('scale_factor', 1.0)
            play_speed = error_config.get('play_speed', 3.0)
            processor.play(folder, scale_factor=scale_factor, loop=True, play_speed=play_speed)
            return error_msg, "Speak in a cheerful and positive tone."

        CODE_FOLDER.mkdir(exist_ok=True)
        # 写代码相关：使用配置的动画设置
        processor.play(folder, scale_factor=scale_factor, loop=True, play_speed=play_speed)
        processor.show_timed_dialog(f"代码生成完成，函数名为：{func_name}，正在保存代码呢~", "保存中...")

        clean_func_name = Path(func_name).stem
        py_path = CODE_FOLDER / f"{clean_func_name}.py"
        json_path = CODE_FOLDER / f"{clean_func_name}.json"
        
        print(f"保存路径 - Python文件: {py_path}")
        print(f"保存路径 - JSON文件: {json_path}")

        try:
            with open(py_path, "w", encoding="utf-8") as f:
                f.write(code)
            print(f"Python文件保存成功: {py_path}")
        except Exception as e:
            print(f"保存Python文件失败: {e}")
            error_msg = f"保存代码文件失败: {str(e)}"
            processor.play(folder, scale_factor=scale_factor, loop=True, play_speed=play_speed)
            return error_msg, "Speak in a cheerful and positive tone."

        try:
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump({"function_name": func_name, "args_doc": args_doc}, f, ensure_ascii=False, indent=2)
            print(f"JSON文件保存成功: {json_path}")
        except Exception as e:
            print(f"保存JSON文件失败: {e}")
            error_msg = f"保存配置文件失败: {str(e)}"
            processor.play(folder, scale_factor=scale_factor, loop=True, play_speed=play_speed)
            return error_msg, "Speak in a cheerful and positive tone."

        args_value_list = current_inputs if current_inputs else []
        # 等待操作：使用配置的动画设置
        wait_config = get_animation_config("等待操作")
        folder = wait_config.get('folder', 'DanceWhileTalk')
        scale_factor = wait_config.get('scale_factor', 1.0)
        play_speed = wait_config.get('play_speed', 3.0)
        processor.play(folder, scale_factor=scale_factor, loop=True, play_speed=play_speed)
        processor.show_timed_dialog("代码已保存，随时可以为主人执行哟~", "准备就绪...")

    # 智能重试机制
    max_retries = 3
    current_retry = 0
    execution_success = False
    final_output = ""
    final_func_name = func_name
    previous_code_content = ""
    previous_error_msg = ""
    
    processor.show_timed_dialog(f"开始执行函数：{func_name}，最多重试{max_retries}次", "准备执行...")
    
    while current_retry < max_retries and not execution_success:
        current_retry += 1
        
        if current_retry > 1:
            processor.show_timed_dialog(f"第{current_retry}次重试执行函数：{final_func_name} (共{max_retries}次)", "重试中...")
        else:
            processor.show_timed_dialog(f"第{current_retry}次执行函数：{final_func_name}", "执行中...")
        
        clean_func_name = Path(final_func_name).stem
        py_file_path = CODE_FOLDER / f"{clean_func_name}.py"
        
        # 读取当前代码内容（用于错误分析）
        try:
            with open(py_file_path, 'r', encoding='utf-8') as f:
                previous_code_content = f.read()
        except Exception as e:
            print(f"读取代码文件失败: {e}")
            previous_code_content = ""
        
        # 执行代码
        output, success = run_python_function_from_file(str(py_file_path), "main", args_value_list)
        
        if success:
            execution_success = True
            final_output = output
            success_message = f"代码执行成功！(第{current_retry}次尝试)"
            print(success_message)
            processor.show_timed_dialog(success_message, "执行成功")
            break
        else:
            print(f"代码执行失败 (尝试{current_retry}次): {output}")
            previous_error_msg = output
            
            if current_retry < max_retries:
                remaining_retries = max_retries - current_retry
                processor.show_timed_dialog(
                    f"代码执行失败，剩余重试次数：{remaining_retries}次\n正在分析错误并重写代码...", 
                    "分析中..."
                )
                
                # 删除失败的代码文件
                if delete_code_file(final_func_name):
                    processor.show_timed_dialog(
                        f"已删除失败代码，正在生成第{current_retry + 1}版代码...", 
                        "重写中..."
                    )
                    
                    # 重写代码，传递之前的错误信息和代码内容
                    new_code, new_func_name, new_args, rewrite_success = rewrite_code_with_retry(
                        task_summary, final_func_name, current_retry + 1, processor, 
                        previous_error=previous_error_msg, previous_code=previous_code_content
                    )
                    
                    if rewrite_success:
                        final_func_name = new_func_name
                        args_value_list = new_args
                        processor.show_timed_dialog(
                            f"第{current_retry + 1}版代码生成完成，准备重新执行...", 
                            "准备中..."
                        )
                    else:
                        processor.show_timed_dialog(
                            f"第{current_retry + 1}版代码生成失败，将尝试使用原始代码...", 
                            "准备中..."
                        )
                        # 如果重写失败，尝试使用原始代码
                        final_func_name = func_name
                        args_value_list = args_value_list
                else:
                    processor.show_timed_dialog(
                        "删除失败代码文件时出错，将尝试重新执行...", 
                        "准备中..."
                    )
            else:
                # 最后一次尝试失败
                final_output = f"代码执行失败，已重试{max_retries}次。\n最后一次错误：{output}\n\n建议：请检查需求描述是否清晰，或者尝试重新描述您的需求。"
                processor.show_timed_dialog(
                    f"代码执行多次失败，已重试{max_retries}次\n请检查需求描述或重新尝试", 
                    "执行失败"
                )
    
    # 等待操作：使用配置的动画设置
    processor.play(folder, scale_factor=scale_factor, loop=True, play_speed=play_speed)
    processor.show_timed_dialog("函数执行完成，正在整理结果呢~", "处理中...")

    final_prompt = prompt.FINAL_RESPONSE_PROMPT.format(
        task_summary=task_summary,
        command_output=final_output
    )
    final_result = get_ai_response(final_prompt, "code_execution", include_history=False, save_to_history=False)

    try:
        final_dict = json.loads(final_result)
        maid_response = final_dict.get("maid_response", "主人，任务完成了哟～")
    except json.JSONDecodeError:
        maid_response = "主人，任务完成了哟～"

    chat_history.add_conversation(
        user_input,
        maid_response,
        "code_execution",
        {
            "task_summary": task_summary,
            "function_name": func_name,
            "code_output": final_output
        }
    )

    # 普通反馈：使用配置的动画设置
    normal_config = get_animation_config("普通反馈")
    if normal_config and 'folders' in normal_config:
        folder = random.choice(normal_config['folders'])
    else:
        folder = get_random_normal_audio()
    
    scale_factor = normal_config.get('scale_factor', 1.0)
    play_speed = normal_config.get('play_speed', 3.0)
    processor.play(folder, scale_factor=scale_factor, loop=True, play_speed=play_speed)
    return maid_response, "Speak in a cheerful and positive tone."



class GlobalHotkeyManager(QObject):
    hotkey_pressed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.listener = None
        self.alt_pressed = False
        self.d_pressed = False
        self.hotkey_triggered = False

    def on_press(self, key):
        try:
            if key == keyboard.Key.alt_l or key == keyboard.Key.alt_r:
                self.alt_pressed = True
            elif hasattr(key, 'char') and key.char and key.char.lower() == 'd':
                self.d_pressed = True
                if self.alt_pressed and self.d_pressed and not self.hotkey_triggered:
                    self.hotkey_triggered = True
                    self.hotkey_pressed.emit()
        except Exception as e:
            print(f"Error in on_press: {e}")

    def on_release(self, key):
        try:
            if key == keyboard.Key.alt_l or key == keyboard.Key.alt_r:
                self.alt_pressed = False
                self.hotkey_triggered = False
            elif hasattr(key, 'char') and key.char and key.char.lower() == 'd':
                self.d_pressed = False
        except Exception as e:
            print(f"Error in on_release: {e}")

    def start_listening(self):
        if self.listener is None:
            self.listener = keyboard.Listener(
                on_press=self.on_press,
                on_release=self.on_release
            )
            self.listener.start()

    def stop_listening(self):
        if self.listener:
            self.listener.stop()
            self.listener = None


class AIWorkerThread(QThread):
    """AI处理工作线程"""
    result_ready = pyqtSignal(str, str)  # 修改信号以包含语调参数
    error_occurred = pyqtSignal(str)

    def __init__(self, user_input, processor):
        super().__init__()
        self.user_input = user_input
        self.processor = processor

    def run(self):
        try:
            result, tone = maid_handle_input(self.user_input, self.processor)  # 传递processor参数
            self.result_ready.emit(result, tone)
        except Exception as e:
            error_msg = f"主人，出现了错误：{str(e)}"
            # 错误情况：使用配置的动画设置
            error_config = get_animation_config("错误情况")
            folder = error_config.get('folder', 'bowWhileTalk')
            scale_factor = error_config.get('scale_factor', 1.0)
            play_speed = error_config.get('play_speed', 3.0)
            self.processor.play(folder, scale_factor=scale_factor, loop=True, play_speed=play_speed)
            self.error_occurred.emit(error_msg)


class TTSWorkerThread(QThread):
    """语音合成工作线程"""
    speech_finished = pyqtSignal()
    speech_started = pyqtSignal()  # 新增：语音开始信号

    def __init__(self, text, tone="Speak in a cheerful and positive tone.",dialog_shower=None):
        super().__init__()
        self.text = text
        self.tone = tone
        self.dialog_shower = dialog_shower

    def run(self):
        try:
            # 发送语音开始信号
            self.speech_started.emit()
            # 直接调用同步的speak函数
            print(time.time())
            speak(self.text, tone=self.tone, dialog_shower=self.dialog_shower)
            print(time.time())
        except Exception as e:
            print(f"TTS报错: {e}")
            return
        finally:
            self.speech_finished.emit()


class MaidSystem(QObject):
    def __init__(self):
        super().__init__()
        self.app = QApplication.instance() or QApplication(sys.argv)
        

        
        self.processor = PRImageProcessor()
        self.input_manager = InputDialogManager()
        self.hotkey_manager = GlobalHotkeyManager()

        # 当前正在处理的AI工作线程
        self.current_worker = None
        # 当前正在处理的语音合成线程
        self.current_tts_worker = None
        # 标记是否正在播放语音（防止对话框被意外关闭）
        self.is_speaking = False

        self.input_manager.input_received.connect(self.on_input_received)
        self.hotkey_manager.hotkey_pressed.connect(self.on_hotkey_pressed)

        self.special_commands = {
            'history': self.handle_history_command,
            'clear_history': self.handle_clear_history_command,
            'quit': self.handle_quit_command
        }
        
        # 连接应用程序的关闭信号
        self.app.aboutToQuit.connect(self.cleanup_and_exit)
        
        # 连接系统关闭信号
        try:
            import signal
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
        except ImportError:
            # Windows系统可能不支持signal模块
            pass

    def start(self):
        print("=== 女仆系统启动 ===")
        print("提示：按 Alt+D 打开输入对话框与女仆互动")
        print("特殊命令：history / clear_history / quit")
        # 启动监听线程
        threading.Thread(target=self.hotkey_manager.start_listening, daemon=True).start()
        self.processor.show_dialog("ご主人様、お呼びですか？♡")
        # 刚开软件无操作：使用配置的动画设置
        startup_config = get_animation_config("刚开启时")
        folder = startup_config.get('folder', 'politeTalk')
        scale_factor = startup_config.get('scale_factor', 1.0)
        play_speed = startup_config.get('play_speed', 3.0)
        self.processor.play(folder, scale_factor=scale_factor, loop=True, play_speed=play_speed)
        # 启动UI事件循环
        self.app.exec_()

    def on_hotkey_pressed(self):
        # 如果正在播放语音，不允许打开输入对话框
        if not self.is_speaking:
            self.input_manager.show_input_dialog()

    def on_input_received(self, user_input):
        """处理用户输入 - 立即关闭输入窗口，异步处理AI"""
        # 立即关闭输入窗口
        self.input_manager.hide_input_dialog()

        # 处理特殊命令（同步处理，因为很快）
        if user_input.lower() in self.special_commands:
            self.special_commands[user_input.lower()]()
            return

        # 显示"正在处理"的提示，并设置定时关闭
        processing_message = "主人，我正在处理您的请求，请稍等..."
        # 等待操作：使用配置的动画设置
        wait_config = get_animation_config("等待操作")
        folder = wait_config.get('folder', 'DanceWhileTalk')
        scale_factor = wait_config.get('scale_factor', 1.0)
        play_speed = wait_config.get('play_speed', 3.0)
        self.processor.play(folder, scale_factor=scale_factor, loop=True, play_speed=play_speed)
        self.processor.show_timed_dialog(processing_message)

        # 如果有正在运行的工作线程，先清理
        if self.current_worker and self.current_worker.isRunning():
            self.current_worker.terminate()
            self.current_worker.wait()

        # 如果有正在运行的语音合成线程，先清理
        if self.current_tts_worker and self.current_tts_worker.isRunning():
            self.current_tts_worker.terminate()
            self.current_tts_worker.wait()
            self.is_speaking = False

        # 创建新的AI工作线程，传递processor参数
        self.current_worker = AIWorkerThread(user_input, self.processor)
        self.current_worker.result_ready.connect(self.on_ai_result_ready)
        self.current_worker.error_occurred.connect(self.on_ai_error)
        self.current_worker.finished.connect(self.on_worker_finished)

        # 启动异步处理
        self.current_worker.start()

    def on_ai_result_ready(self, result, tone):
        """AI处理完成时的回调"""
        # 先取消任何可能的定时关闭
        if hasattr(self.processor, 'cancel_timed_close'):
            self.processor.cancel_timed_close()

        # 立即显示对话框，并设置强制可见（如果支持）
        if hasattr(self.processor, 'dialog') and hasattr(self.processor.dialog, 'set_force_visible'):
            self.processor.dialog.set_force_visible(True)

        # self.processor.show_dialog(result)

        # 启动语音合成，传递tone参数
        self.start_speech(result, lambda: self.processor.show_dialog(result), tone)

    def on_ai_error(self, error_msg):
        """AI处理出错时的回调"""
        # 先取消任何可能的定时关闭
        if hasattr(self.processor, 'cancel_timed_close'):
            self.processor.cancel_timed_close()

        # 立即显示对话框，并设置强制可见（如果支持）
        if hasattr(self.processor, 'dialog') and hasattr(self.processor.dialog, 'set_force_visible'):
            self.processor.dialog.set_force_visible(True)

        # 错误情况：使用配置的动画设置
        error_config = get_animation_config("错误情况")
        folder = error_config.get('folder', 'bowWhileTalk')
        scale_factor = error_config.get('scale_factor', 1.0)
        play_speed = error_config.get('play_speed', 3.0)
        self.processor.play(folder, scale_factor=scale_factor, loop=True, play_speed=play_speed)
        self.processor.show_dialog(error_msg)

        # 启动语音合成，使用默认语调
        self.start_speech(error_msg, "Speak in a cheerful and positive tone.")

    def start_speech(self, text,dialog_shower=None, tone="Speak in a cheerful and positive tone."):
        """启动语音合成"""
        # 如果有正在运行的语音合成线程，先清理
        if self.current_tts_worker and self.current_tts_worker.isRunning():
            self.current_tts_worker.terminate()
            self.current_tts_worker.wait()

        # 设置语音播放状态
        self.is_speaking = True

        # 创建新的语音合成线程，传递tone参数
        self.current_tts_worker = TTSWorkerThread(text, tone, dialog_shower)
        self.current_tts_worker.speech_started.connect(self.on_speech_started)
        self.current_tts_worker.speech_finished.connect(self.on_speech_finished)
        self.current_tts_worker.finished.connect(self.on_tts_worker_finished)

        # 启动语音合成
        self.current_tts_worker.start()

    def on_speech_started(self):
        """语音开始播放时的回调"""
        # 确保对话框保持显示状态
        self.is_speaking = True
        print("语音开始播放...")

    def on_speech_finished(self):
        """语音播放完成时的回调"""
        # 取消强制可见状态（如果支持）
        if hasattr(self.processor, 'dialog') and hasattr(self.processor.dialog, 'set_force_visible'):
            self.processor.dialog.set_force_visible(False)

        # 延迟关闭对话框，确保语音完全播放完毕
        QTimer.singleShot(500, self.processor.hide_dialog)
        self.is_speaking = False
        print("语音播放完成")

    def on_tts_worker_finished(self):
        """语音合成线程完成时的清理"""
        if self.current_tts_worker:
            self.current_tts_worker.deleteLater()
            self.current_tts_worker = None
        self.is_speaking = False

    def on_worker_finished(self):
        """工作线程完成时的清理"""
        if self.current_worker:
            self.current_worker.deleteLater()
            self.current_worker = None

    def handle_history_command(self):
        summary = chat_history.get_history_summary()
        message = f"主人，{summary}"
        # 普通反馈：使用配置的动画设置
        normal_config = get_animation_config("普通反馈")
        if normal_config and 'folders' in normal_config:
            folder = random.choice(normal_config['folders'])
        else:
            folder = get_random_normal_audio()
        
        scale_factor = normal_config.get('scale_factor', 1.0)
        play_speed = normal_config.get('play_speed', 3.0)
        self.processor.play(folder, scale_factor=scale_factor, loop=True, play_speed=play_speed)
        # 显示定时对话框
        self.processor.show_timed_dialog(message)

    def handle_clear_history_command(self):
        chat_history.clear_history()
        message = "主人，历史记录已清空了哟～"
        # 普通反馈：使用配置的动画设置
        normal_config = get_animation_config("普通反馈")
        if normal_config and 'folders' in normal_config:
            folder = random.choice(normal_config['folders'])
        else:
            folder = get_random_normal_audio()
        
        scale_factor = normal_config.get('scale_factor', 1.0)
        play_speed = normal_config.get('play_speed', 3.0)
        self.processor.play(folder, scale_factor=scale_factor, loop=True, play_speed=play_speed)
        # 显示定时对话框
        self.processor.show_timed_dialog(message)

    def handle_quit_command(self):
        """处理退出命令"""
        message = "主人，再见～"
        # 普通反馈：使用配置的动画设置
        normal_config = get_animation_config("普通反馈")
        if normal_config and 'folders' in normal_config:
            folder = random.choice(normal_config['folders'])
        else:
            folder = get_random_normal_audio()
        
        scale_factor = normal_config.get('scale_factor', 1.0)
        play_speed = normal_config.get('play_speed', 3.0)
        self.processor.play(folder, scale_factor=scale_factor, loop=True, play_speed=play_speed)
        # 显示定时对话框
        self.processor.show_timed_dialog(message)
        QTimer.singleShot(2000, self.cleanup_and_exit)  # 缩短显示时间，直接调用清理退出

    def quit(self):
        """用户主动退出命令"""
        message = "主人，再见～"
        # 普通反馈：使用配置的动画设置
        normal_config = get_animation_config("普通反馈")
        if normal_config and 'folders' in normal_config:
            folder = random.choice(normal_config['folders'])
        else:
            folder = get_random_normal_audio()
        
        scale_factor = normal_config.get('scale_factor', 1.0)
        play_speed = normal_config.get('play_speed', 3.0)
        self.processor.play(folder, scale_factor=scale_factor, loop=True, play_speed=play_speed)
        # 显示定时对话框
        self.processor.show_timed_dialog(message)
        QTimer.singleShot(2000, self.cleanup_and_exit)  # 缩短显示时间

    def cleanup_and_exit(self):
        """清理资源并退出程序"""
        print("正在清理资源并退出程序...")
        
        # 强制关闭输入对话框
        if hasattr(self.input_manager, 'force_close_dialog'):
            self.input_manager.force_close_dialog()
        elif hasattr(self.input_manager, 'dialog'):
            self.input_manager.dialog.close()
        
        # 清理AI工作线程
        if self.current_worker and self.current_worker.isRunning():
            self.current_worker.terminate()
            self.current_worker.wait(3000)  # 等待最多3秒
            if self.current_worker.isRunning():
                self.current_worker.forceTerminate()  # 强制终止

        # 清理语音合成线程
        if self.current_tts_worker and self.current_tts_worker.isRunning():
            self.current_tts_worker.terminate()
            self.current_tts_worker.wait(3000)  # 等待最多3秒
            if self.current_tts_worker.isRunning():
                self.current_tts_worker.forceTerminate()  # 强制终止

        # 停止热键监听
        self.hotkey_manager.stop_listening()
        
        # 关闭图像处理器
        if hasattr(self.processor, 'close'):
            self.processor.close()
        
        # 强制退出应用程序
        print("程序退出完成")
        self.app.quit()
        sys.exit(0)
    
    def _signal_handler(self, signum, frame):
        """处理系统信号"""
        print(f"收到系统信号 {signum}，正在退出程序...")
        self.cleanup_and_exit()


if __name__ == "__main__":
    try:
        start_maid_system()
    except Exception as e:
        print(f"运行错误: {e}")
        # 错误情况的处理，但这里没有processor实例，所以只能打印
        traceback.print_exc()
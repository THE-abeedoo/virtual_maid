import os
import json
import threading
import sys
import math
import re
import concurrent.futures
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QWidget
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject, QThread, QRect, QUrl
from PyQt5.QtGui import QPixmap, QImage, QPainter, QFont, QFontMetrics, QColor, QDragEnterEvent, QDropEvent, QIcon
from PIL import Image
from call_ai import describe_image


def calculate_height(s):
    base = int(1.9 * s ** 0.6)
    return base


class _DialogSignalHelper(QObject):
    """内部信号助手类，用于线程安全通信"""
    update_text_signal = pyqtSignal(str)
    show_signal = pyqtSignal()
    hide_signal = pyqtSignal()
    close_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        # 确保信号助手在主线程中
        if QApplication.instance():
            self.moveToThread(QApplication.instance().thread())


class DialogWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = self._load_config()
        self.backgrounds = self._load_backgrounds()
        self.current_bg = None
        self.text = ""
        self.text_rect = QRect()
        # 统一设置为左上对齐，并启用自动换行
        self.alignment = Qt.AlignLeft | Qt.AlignTop
        self.font = QFont("Unifont", 12)
        self.font.setBold(False)

        # 添加线程安全的信号槽机制
        self._signal_helper = _DialogSignalHelper()
        self._signal_helper.update_text_signal.connect(self._safe_update_text)
        self._signal_helper.show_signal.connect(self._safe_show)
        self._signal_helper.hide_signal.connect(self._safe_hide)
        self._signal_helper.close_signal.connect(self._safe_close)

    def _load_config(self):
        try:
            with open("config.json", "r", encoding="utf-8") as f:
                return json.load(f)["dialog_config"]
        except Exception as e:
            print(f"警告: 读取 config.json 失败: {e}，使用默认设置。")
            return {"scale": 1.0, "padding_pixels": {"left": 40, "top": 20, "right": 20, "bottom": 68}}

    def _load_backgrounds(self):
        bg_dir = "ui_images"
        bg_files = {
            'small': os.path.join(bg_dir, 'dialog box small.png'),
            'medium': os.path.join(bg_dir, 'dialog box medium.png'),
            'big': os.path.join(bg_dir, 'dialog box big.png'),
            'default': os.path.join(bg_dir, 'dialog box.png'),
        }
        backgrounds = {}
        for name, path in bg_files.items():
            if os.path.exists(path):
                backgrounds[name] = QPixmap(path)
        sorted_keys = ['small', 'default', 'medium', 'big']
        return {k: backgrounds[k] for k in sorted_keys if k in backgrounds}

    def _visual_length(self, text):
        """计算文本的视觉长度（中文字符计为2，英文字符计为1）"""
        return sum(2 if ord(c) > 127 else 1 for c in text)

    def _estimate_required_lines(self, text, available_width, font_metrics):
        """
        估算文本在给定宽度下需要的行数
        使用Qt的文本渲染来准确计算
        """
        if not text or available_width <= 0:
            return 1

        # 使用Qt的文本布局来计算实际需要的行数
        from PyQt5.QtGui import QTextLayout

        layout = QTextLayout(text, self.font)
        layout.beginLayout()

        line_count = 0
        y = 0

        while True:
            line = layout.createLine()
            if not line.isValid():
                break

            line.setLineWidth(available_width)
            line_count += 1
            y += font_metrics.height()

        layout.endLayout()
        return max(1, line_count)

    def _calculate_optimal_scale(self, text):
        """
        计算文本显示所需的最佳缩放比例
        """
        base_scale = self.config.get("scale", 1.0)
        padding = self.config.get("padding_pixels", {})

        # 从基础缩放开始尝试
        scale = base_scale
        max_scale = base_scale + 5  # 设置最大缩放限制

        while scale <= max_scale:
            # 计算当前缩放下的容量限制
            width_limit = int(9.0 * scale ** 1.0)  # 字符宽度限制
            height_limit = calculate_height(scale)  # 行数限制
            total_capacity = width_limit * height_limit

            # 检查文本长度是否在总容量范围内
            text_visual_length = self._visual_length(text)
            if text_visual_length <= total_capacity:
                # 进一步检查是否有合适的背景图片
                pad_l = int(padding.get("left", 20) * scale)
                pad_r = int(padding.get("right", 20) * scale)

                # 找到第一个能容纳文本的背景
                for bg_name, bg_pixmap in self.backgrounds.items():
                    available_width = int(bg_pixmap.width() * scale) - pad_l - pad_r

                    if available_width > 0:
                        font_metrics = QFontMetrics(self.font)
                        estimated_lines = self._estimate_required_lines(text, available_width, font_metrics)

                        # 检查预估行数是否在限制内
                        if estimated_lines <= height_limit:
                            return scale

            scale += 1

        return scale  # 返回最终尝试的缩放比例

    def _is_main_thread(self):
        """检查当前是否在主线程中"""
        return QThread.currentThread() == QApplication.instance().thread()

    def _safe_update_text(self, text):
        """内部线程安全的文本更新方法"""
        self.text = text

        # 计算最佳缩放比例
        optimal_scale = self._calculate_optimal_scale(text)

        padding = self.config.get("padding_pixels", {})
        pad_l = int(padding.get("left", 20) * optimal_scale)
        pad_t = int(padding.get("top", 20) * optimal_scale)
        pad_r = int(padding.get("right", 20) * optimal_scale)
        pad_b = int(padding.get("bottom", 68) * optimal_scale)

        # 选择合适的背景图片
        self.current_bg = None
        font_metrics = QFontMetrics(self.font)
        height_limit = calculate_height(optimal_scale)

        for bg_name, bg_pixmap in self.backgrounds.items():
            bg_width = int(bg_pixmap.width() * optimal_scale)
            bg_height = int(bg_pixmap.height() * optimal_scale)
            available_width = bg_width - pad_l - pad_r
            available_height = bg_height - pad_t - pad_b

            if available_width > 0 and available_height > 0:
                # 检查文本是否能在此背景中正确显示
                estimated_lines = self._estimate_required_lines(text, available_width, font_metrics)
                required_height = estimated_lines * font_metrics.height()

                if estimated_lines <= height_limit and required_height <= available_height:
                    self.current_bg = bg_pixmap
                    break

        # 如果没有找到合适的背景，使用最大的背景
        if not self.current_bg and self.backgrounds:
            self.current_bg = list(self.backgrounds.values())[-1]

        if self.current_bg:
            # 设置窗口大小
            final_w = int(self.current_bg.width() * optimal_scale)
            final_h = int(self.current_bg.height() * optimal_scale)
            self.setFixedSize(final_w, final_h)

            # 设置文本绘制区域
            text_w = final_w - pad_l - pad_r
            text_h = final_h - pad_t - pad_b
            self.text_rect = QRect(pad_l, pad_t, text_w, text_h)

        self.update()

    def _safe_show(self):
        """内部线程安全的显示方法"""
        super().show()

    def _safe_hide(self):
        """内部线程安全的隐藏方法"""
        super().hide()

    def _safe_close(self):
        """内部线程安全的关闭方法"""
        super().close()

    # 重写公共方法，添加线程安全检查
    def update_text(self, text):
        """线程安全的文本更新方法"""
        if self._is_main_thread():
            self._safe_update_text(text)
        else:
            self._signal_helper.update_text_signal.emit(text)

    def show(self):
        """线程安全的显示方法"""
        if self._is_main_thread():
            self._safe_show()
        else:
            self._signal_helper.show_signal.emit()

    def hide(self):
        """线程安全的隐藏方法"""
        if self._is_main_thread():
            self._safe_hide()
        else:
            self._signal_helper.hide_signal.emit()

    def close(self):
        """线程安全的关闭方法"""
        if self._is_main_thread():
            self._safe_close()
        else:
            self._signal_helper.close_signal.emit()

    def paintEvent(self, event):
        super().paintEvent(event)
        if not self.current_bg:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 绘制背景
        painter.drawPixmap(self.rect(), self.current_bg)

        # 绘制文本 - 使用Qt的自动换行功能
        painter.setFont(self.font)
        painter.setPen(QColor(0, 0, 0))

        # 使用Qt的自动换行功能绘制文本
        # Qt.TextWordWrap 启用自动换行
        text_flags = self.alignment | Qt.TextWordWrap
        painter.drawText(self.text_rect, text_flags, self.text)


class ImageLoader(QObject):
    images_loaded = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self.standard_size = 0
        self.scale_factor = 1.0

    def set_parameters(self, standard_size, scale_factor):
        self.standard_size = standard_size
        self.scale_factor = scale_factor

    def resize_image(self, image):
        width, height = image.size
        if height == 0: return image
        target_height = int(self.standard_size * self.scale_factor)
        new_height = target_height
        new_width = int(width * (target_height / height))
        return image.resize((new_width, new_height), Image.LANCZOS)

    def load_images(self, inner_folder):
        images = []
        folder_path = os.path.join("pr", inner_folder)
        if not os.path.exists(folder_path):
            self.images_loaded.emit([])
            return

        image_files = sorted([f for f in os.listdir(folder_path) if f.lower().endswith('.png')])
        if not image_files:
            self.images_loaded.emit([])
            return

        for img_file in image_files:
            try:
                img_path = os.path.join(folder_path, img_file)
                img = Image.open(img_path).convert("RGBA")
                processed_img = self.resize_image(img)
                qimg = QImage(processed_img.tobytes(), processed_img.width, processed_img.height,
                              QImage.Format_RGBA8888)
                pixmap = QPixmap.fromImage(qimg)
                images.append({'pixmap': pixmap})
            except Exception as e:
                print(f"載入圖像 {img_file} 時出錯: {e}")

        self.images_loaded.emit(images)


class AIImageAnalyzer(QObject):
    """AI图像分析器，使用线程池避免卡死"""
    analysis_complete = pyqtSignal(str)
    start_analysis = pyqtSignal(str)

    def __init__(self, max_workers=2):
        super().__init__()
        self.start_analysis.connect(self.analyze_image)
        # 使用线程池来处理耗时的AI分析任务
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
        self.pending_futures = set()

    def analyze_image(self, image_path):
        """使用线程池异步分析图片"""
        try:
            # 提交任务到线程池
            future = self.executor.submit(self._analyze_image_blocking, image_path)
            self.pending_futures.add(future)

            # 添加完成回调
            future.add_done_callback(self._on_analysis_done)

        except Exception as e:
            error_msg = f"提交AI分析任务时出错: {str(e)}"
            print(error_msg)
            self.analysis_complete.emit(error_msg)

    def _analyze_image_blocking(self, image_path):
        """实际的阻塞分析函数，在线程池中运行"""
        try:
            # 这里是可能阻塞的AI分析调用
            return describe_image(image_path)
        except Exception as e:
            raise Exception(f"AI分析图片时出错: {str(e)}")

    def _on_analysis_done(self, future):
        """分析完成的回调函数"""
        # 从待处理集合中移除
        self.pending_futures.discard(future)

        try:
            result = future.result()
            self.analysis_complete.emit(result)
        except Exception as e:
            error_msg = f"AI分析失败: {str(e)}"
            print(error_msg)
            self.analysis_complete.emit(error_msg)

    def shutdown(self):
        """关闭线程池"""
        # 取消所有待处理的任务
        for future in list(self.pending_futures):
            future.cancel()

        # 关闭线程池
        self.executor.shutdown(wait=True)
        self.pending_futures.clear()


class DragDropImageLabel(QLabel):
    """支持拖拽的图像标签"""
    image_dropped = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        # 默认完全透明，无任何视觉提示
        self.setStyleSheet("QLabel { background-color: transparent; border: none; }")

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls and self._is_image_file(urls[0].toLocalFile()):
                event.acceptProposedAction()
                # 只在拖拽进入时显示边框
                self.setStyleSheet("""
                    QLabel {
                        border: 2px solid #0078d4;
                        border-radius: 5px;
                        background-color: rgba(0, 120, 212, 0.2);
                    }
                """)
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        # 拖拽离开时恢复透明
        self.setStyleSheet("QLabel { background-color: transparent; border: none; }")

    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                file_path = urls[0].toLocalFile()
                if self._is_image_file(file_path):
                    self.image_dropped.emit(file_path)
                    event.acceptProposedAction()

                    # 拖拽完成后恢复透明
                    self.setStyleSheet("QLabel { background-color: transparent; border: none; }")
        else:
            event.ignore()

    def _is_image_file(self, file_path):
        """检查文件是否为图像文件"""
        image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp'}
        return any(file_path.lower().endswith(ext) for ext in image_extensions)


class DraggableWindow(QMainWindow):
    """可拖曳的視窗, 現在包含動畫和對話框, 並能自動調整佈局"""

    def __init__(self):
        super().__init__()
        self.dragging = False
        self.offset = None

        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # 设置窗口图标
        icon_path = "./ui_images/icon.png"
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        container = QWidget(self)
        self.setCentralWidget(container)

        # 使用支持拖拽的图像标签
        self.image_label = DragDropImageLabel(container)
        self.image_label.setAlignment(Qt.AlignCenter)

        self.dialog_widget = DialogWidget(container)
        self.dialog_widget.hide()

    def update_layout(self):
        """自動定位動畫和對話框，並調整主視窗大小"""
        anim_size = self.image_label.size()

        self.image_label.move(0, 0)

        total_width = anim_size.width()
        total_height = anim_size.height()

        if not self.dialog_widget.isHidden():
            dialog_size = self.dialog_widget.size()

            dialog_x = anim_size.width()
            dialog_y = (anim_size.height() - dialog_size.height()) // 2
            self.dialog_widget.move(dialog_x, max(0, dialog_y))

            total_width += dialog_size.width()
            total_height = max(total_height, dialog_size.height())

        self.setFixedSize(total_width, total_height)
        self.centralWidget().setFixedSize(total_width, total_height)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.offset = event.pos()

    def mouseMoveEvent(self, event):
        if self.dragging and self.offset is not None:
            self.move(event.globalPos() - self.offset)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False
            self.offset = None


class PRImageProcessor(QObject):
    _dialog_update_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.app = QApplication.instance() or QApplication(sys.argv)
        self.root = DraggableWindow()
        self.root.setWindowTitle("整合UI系統")

        screen = self.app.primaryScreen().size()
        self.screen_width = screen.width()
        self.screen_height = screen.height()
        self.standard_size = int(self.screen_height / 15)

        self.images = []
        self.current_image_index = 0
        self.is_playing = False
        self.play_speed = 1.0
        self.loop = False
        self.scale_factor = 1.0

        self.timer = QTimer()
        self.timer.timeout.connect(self.next_image)

        # 添加定时对话框关闭的定时器
        self.dialog_timer = QTimer()
        self.dialog_timer.setSingleShot(True)  # 确保只触发一次
        self.dialog_timer.timeout.connect(self.hide_dialog)

        self.loader_thread = QThread()
        self.image_loader = ImageLoader()
        self.image_loader.moveToThread(self.loader_thread)
        self.image_loader.images_loaded.connect(self.on_images_loaded)
        self.loader_thread.start()

        # 设置AI分析器 - 不再使用单独的线程，而是使用线程池
        self.ai_analyzer = AIImageAnalyzer(max_workers=2)
        self.ai_analyzer.analysis_complete.connect(self.on_image_analysis_complete)

        # 连接拖拽信号
        self.root.image_label.image_dropped.connect(self.on_image_dropped)

        self.switch_lock = threading.Lock()
        self.current_folder = None
        self.scale_factors = self._load_scale_factors()
        self.window_shown = False

        self._dialog_update_signal.connect(self._execute_dialog_update)

    def _load_scale_factors(self):
        try:
            with open("pixel_scale_factors.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _calculate_display_time(self, text):
        """
        计算文本显示时间，每个字符0.3秒
        """
        char_count = len(text)
        return int(char_count * 300)  # 300毫秒 = 0.3秒，返回毫秒

    def on_images_loaded(self, images):
        with self.switch_lock:
            self.images = images
            if self.images:
                self.current_image_index = 0
                self.display_current_image()

                if not self.window_shown:
                    self.root.show()
                    self.window_shown = True

                if self.is_playing:
                    delay = int(1000 / self.play_speed)
                    self.timer.start(delay)
            else:
                print("沒有載入到任何圖像")

    def display_current_image(self):
        if not self.images: return

        pixmap = self.images[self.current_image_index]['pixmap']
        self.root.image_label.setPixmap(pixmap)
        self.root.image_label.setFixedSize(pixmap.size())

        self.root.update_layout()

        if not self.window_shown:
            x_pos = (self.screen_width - self.root.width()) // 2
            y_pos = (self.screen_height - self.root.height()) // 2
            self.root.move(x_pos, y_pos)

    def next_image(self):
        if not self.images: return

        with self.switch_lock:
            self.current_image_index = (self.current_image_index + 1)
            if self.current_image_index >= len(self.images):
                if self.loop:
                    self.current_image_index = 0
                else:
                    self.is_playing = False
                    self.timer.stop()
                    self.current_image_index = len(self.images) - 1

            self.display_current_image()

    def hot_switch(self, inner_folder, scale_factor=1.0, loop=False, play_speed=1.0):
        with self.switch_lock:
            folder_scale = self.scale_factors.get(inner_folder, 1.0)
            self.scale_factor = scale_factor * folder_scale
            self.loop = loop
            self.play_speed = play_speed

            self.timer.stop()
            self.current_folder = inner_folder
            self.image_loader.set_parameters(self.standard_size, self.scale_factor)
            self.image_loader.load_images(inner_folder)

    def play(self, inner_folder, scale_factor=1.0, loop=False, play_speed=1.0):
        self.current_folder = inner_folder
        folder_scale = self.scale_factors.get(inner_folder, 1.0)
        self.scale_factor = scale_factor * folder_scale
        self.loop = loop
        self.play_speed = play_speed
        self.is_playing = True

        self.image_loader.set_parameters(self.standard_size, self.scale_factor)
        self.image_loader.load_images(inner_folder)

        self.app.exec_()

    def on_image_dropped(self, image_path):
        """处理拖拽的图片 - 已更新以包含历史记录"""
        print(f"图片已拖拽: {image_path}")

        # 显示分析提示
        analyzing_message = "正在分析图片，请稍候..."
        self.show_timed_dialog(analyzing_message)

        # 使用信号触发分析，现在使用线程池避免卡死
        # 历史记录会在 describe_image 函数中自动保存
        self.ai_analyzer.start_analysis.emit(image_path)

    def on_image_analysis_complete(self, description):
        """处理AI分析完成的结果 - 已更新以包含历史记录"""
        print(f"AI分析结果: {description}")

        # 图片分析结果已经在 describe_image 函数中保存到历史记录了
        # 这里只需要显示对话
        self.show_dialog(description)

    def close(self):
        """关闭图像处理器"""
        print("正在关闭图像处理器...")
        
        try:
            # 停止所有定时器
            self.timer.stop()
            self.dialog_timer.stop()
            
            # 停止图像加载线程
            if hasattr(self, 'loader_thread') and self.loader_thread.isRunning():
                self.loader_thread.quit()
                self.loader_thread.wait(3000)  # 等待最多3秒
                if self.loader_thread.isRunning():
                    self.loader_thread.terminate()
                    self.loader_thread.wait(1000)
            
            # 关闭AI分析器的线程池
            if hasattr(self, 'ai_analyzer'):
                self.ai_analyzer.shutdown()
            
            # 关闭主窗口
            if hasattr(self, 'root'):
                self.root.close()
            
            # 退出应用程序
            if hasattr(self, 'app'):
                self.app.quit()
                
            print("图像处理器关闭完成")
            
        except Exception as e:
            print(f"关闭图像处理器时出错: {e}")
            # 强制退出
            try:
                if hasattr(self, 'app'):
                    self.app.quit()
            except:
                pass

    def _execute_dialog_update(self, text):
        if text:
            self.root.dialog_widget.update_text(text)
            self.root.dialog_widget.show()
        else:
            self.root.dialog_widget.hide()

        self.root.update_layout()

    def show_dialog(self, text):
        """显示对话框（不自动关闭）"""
        self._dialog_update_signal.emit(text)

    def show_timed_dialog(self, *texts: str, duration = None):
        """依次显示多个定时对话框。
        每个字符串按 duration 显示毫秒数；如果未提供，则按字符数 × 0.3 秒自动计算。

        参数:
            *texts: 要依次显示的文本
            duration: 每段文本显示时长（毫秒），如果为 None 则自动计算
        """
        self.dialog_timer.stop()

        # 将 (text, duration) 打包为元组，统一处理
        self._dialog_queue = [(text, duration) for text in texts]
        self._show_next_dialog()


    def _show_next_dialog(self):
        """显示下一个对话内容"""
        if not self._dialog_queue:
            return

        text, duration = self._dialog_queue.pop(0)
        self._dialog_update_signal.emit(text)

        # 决定显示时长
        display_time = duration if duration is not None else self._calculate_display_time(text)

        # 确保不会重复连接信号（避免多次触发）
        try:
            self.dialog_timer.timeout.disconnect()
        except TypeError:
            pass

        self.dialog_timer.timeout.connect(self._show_next_dialog)
        self.dialog_timer.start(display_time)


    def cancel_timed_close(self):
        """停止用于定时关闭对话框的计时器"""
        self.dialog_timer.stop()

    def hide_dialog(self):
        """隐藏对话框"""
        self._dialog_update_signal.emit("")
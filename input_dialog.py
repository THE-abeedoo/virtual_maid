import os
import json
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QTextEdit, QVBoxLayout, QPushButton
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject, QThread, QRect, QPoint
from PyQt5.QtGui import QPixmap, QImage, QPainter, QFont, QFontMetrics, QColor, QPen, QBrush, QKeySequence
from PyQt5.QtWidgets import QGraphicsDropShadowEffect


class _InputDialogSignalHelper(QObject):
    """内部信号助手类，用于线程安全通信"""
    show_signal = pyqtSignal()
    hide_signal = pyqtSignal()
    close_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        # 确保信号助手在主线程中
        if QApplication.instance():
            self.moveToThread(QApplication.instance().thread())


class InputDialogWidget(QWidget):
    # 定义信号
    input_submitted = pyqtSignal(str)
    dialog_closed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = self._load_config()
        self.background = self._load_background()

        # 拖动相关变量
        self.dragging = False
        self.drag_start_pos = QPoint()
        self.drag_start_global_pos = QPoint()
        self.drag_threshold = 5  # 拖动阈值，像素

        # 设置窗口属性
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        


        # 添加线程安全的信号槽机制
        self._signal_helper = _InputDialogSignalHelper()
        self._signal_helper.show_signal.connect(self._safe_show)
        self._signal_helper.hide_signal.connect(self._safe_hide)
        self._signal_helper.close_signal.connect(self._safe_close)

        # 设置输入框
        self._setup_input_area()

        # 设置失焦关闭计时器
        self.unfocus_close_timer = QTimer(self)
        self.unfocus_close_timer.setSingleShot(True)
        self.unfocus_close_timer.setInterval(1000)  # 1秒后关闭
        self.unfocus_close_timer.timeout.connect(self._handle_unfocus_close)

        # 设置窗口大小和位置
        self._setup_window_size()

    def _load_config(self):
        """加载配置文件"""
        try:
            with open("input_dialog_config.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"警告: 读取 input_dialog_config.json 失败: {e}，使用默认设置。")
            # 创建默认配置
            default_config = {
                "scale_x": 1.0,
                "scale_y": 1.0,
                "font_size": 14,
                "font_family": "Microsoft YaHei",
                "padding_pixels": {
                    "left": 40,
                    "top": 30,
                    "right": 40,
                    "bottom": 80
                }
            }
            # 保存默认配置
            try:
                with open("input_dialog_config.json", "w", encoding="utf-8") as f:
                    json.dump(default_config, f, ensure_ascii=False, indent=2)
            except Exception as save_e:
                print(f"无法保存默认配置: {save_e}")
            return default_config

    def _load_background(self):
        """加载背景图片"""
        bg_path = os.path.join("ui_images", "dialog box big.png")
        if os.path.exists(bg_path):
            return QPixmap(bg_path)
        else:
            print(f"警告: 未找到背景图片 {bg_path}")
            return None

    def _setup_input_area(self):
        """设置输入区域"""
        self.text_edit = QTextEdit(self)

        # 设置字体
        scale_x = self.config.get("scale_x", 1.0)
        font_size = int(self.config.get("font_size", 14) * min(scale_x, 1.2))
        font = QFont(
            self.config.get("font_family", "Microsoft YaHei"),
            font_size
        )
        self.text_edit.setFont(font)

        # 设置样式：透明背景，无边框，无滚动条
        self.text_edit.setStyleSheet("""
            QTextEdit {
                background-color: rgba(255, 255, 255, 0);
                border: none;
                color: #333333;
                selection-background-color: rgba(0, 120, 212, 0.3);
                padding: 5px;
            }
            QTextEdit:focus {
                background-color: rgba(255, 255, 255, 0);
            }
        """)

        # 禁用滚动条
        self.text_edit.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.text_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # 连接回车事件
        self.text_edit.installEventFilter(self)

        # 设置占位符文本
        self.text_edit.setPlaceholderText("请输入指令，按回车提交...")

        # 确保文本框可以获得焦点
        self.text_edit.setFocusPolicy(Qt.StrongFocus)

    def _setup_window_size(self):
        """设置窗口大小"""
        if self.background:
            # 使用分别的横纵缩放
            scale_x = self.config.get("scale_x", 1.0)
            scale_y = self.config.get("scale_y", 1.0)

            # 如果配置中还有旧的scale属性，用它来初始化scale_x和scale_y
            if "scale" in self.config and "scale_x" not in self.config:
                scale_x = scale_y = self.config["scale"]

            bg_width = int(self.background.width() * scale_x)
            bg_height = int(self.background.height() * scale_y)

            self.setFixedSize(bg_width, bg_height)

            # 设置输入框位置
            padding = self.config.get("padding_pixels", {})
            pad_l = int(padding.get("left", 40) * scale_x)
            pad_t = int(padding.get("top", 30) * scale_y)
            pad_r = int(padding.get("right", 40) * scale_x)
            pad_b = int(padding.get("bottom", 80) * scale_y)

            input_x = pad_l
            input_y = pad_t
            input_w = bg_width - pad_l - pad_r

            # 计算文字高度
            font_size = int(self.config.get("font_size", 14) * min(scale_x, 1.2))
            font = QFont(
                self.config.get("font_family", "Microsoft YaHei"),
                font_size
            )
            font_metrics = QFontMetrics(font)
            line_height = font_metrics.height()

            # 1.5行的高度 + padding
            input_h = int(line_height * 1.5) + 10

            # 确保输入框大小合理
            input_w = max(100, input_w)
            input_h = max(20, input_h)

            self.text_edit.setGeometry(input_x, input_y, input_w, input_h)

    def _is_main_thread(self):
        """检查当前是否在主线程中"""
        return QThread.currentThread() == QApplication.instance().thread()

    def _safe_show(self):
        """内部线程安全的显示方法"""
        # 居中显示
        screen = QApplication.primaryScreen().size()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

        super().show()
        self.raise_()
        self.activateWindow()

        # 强制设置焦点到文本框
        QTimer.singleShot(100, self._set_focus_to_text_edit)

        # 清空文本框
        self.text_edit.clear()

    def _set_focus_to_text_edit(self):
        """设置焦点到文本编辑框"""
        try:
            self.text_edit.setFocus()
            self.text_edit.activateWindow()
        except Exception as e:
            print(f"设置焦点失败: {e}")

    def _safe_hide(self):
        """内部线程安全的隐藏方法"""
        super().hide()

    def _safe_close(self):
        """内部线程安全的关闭方法"""
        super().close()
    
    def force_close(self):
        """强制关闭对话框，用于程序退出时"""
        try:
            self.hide()
            self.dialog_closed.emit()
            self.close()
        except Exception as e:
            print(f"强制关闭对话框错误: {e}")
            # 如果正常关闭失败，尝试强制删除
            try:
                self.deleteLater()
            except:
                pass

    def _handle_unfocus_close(self):
        """处理因失焦导致的对话框关闭"""
        if self.isVisible():
            self.hide_dialog()
            self.dialog_closed.emit()

    def show_dialog(self):
        """线程安全的显示方法"""
        if self._is_main_thread():
            self._safe_show()
        else:
            self._signal_helper.show_signal.emit()

    def hide_dialog(self):
        """线程安全的隐藏方法"""
        if self._is_main_thread():
            self._safe_hide()
        else:
            self._signal_helper.hide_signal.emit()

    def close_dialog(self):
        """线程安全的关闭方法"""
        if self._is_main_thread():
            self._safe_close()
        else:
            self._signal_helper.close_signal.emit()

    def keyPressEvent(self, event):
        """键盘按下事件"""
        if event.key() == Qt.Key_Escape:
            self.hide_dialog()
            self.dialog_closed.emit()
        super().keyPressEvent(event)

    def event(self, event):
        """重写事件处理，以检测窗口活动状态变化"""
        if event.type() == event.WindowDeactivate:
            # 窗口失去焦点，启动计时器
            self.unfocus_close_timer.start()
        elif event.type() == event.WindowActivate:
            # 窗口获得焦点，停止计时器
            self.unfocus_close_timer.stop()
        return super().event(event)

    def eventFilter(self, obj, event):
        """事件过滤器，处理文本框的回车事件"""
        if obj == self.text_edit and event.type() == event.KeyPress:
            if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
                if not event.modifiers() & Qt.ShiftModifier:  # 不是Shift+Enter
                    text = self.text_edit.toPlainText().strip()
                    if text:
                        self.input_submitted.emit(text)
                        self.hide_dialog()
                    return True
            elif event.key() == Qt.Key_Escape:
                self.hide_dialog()
                self.dialog_closed.emit()
                return True
        return super().eventFilter(obj, event)

    def mousePressEvent(self, event):
        """鼠标点击事件"""
        try:
            if event.button() == Qt.LeftButton:
                # 记录拖动开始位置
                self.drag_start_pos = event.pos()
                self.drag_start_global_pos = event.globalPos()
                self.dragging = False

                # 如果点击在文本框外但窗口内，给文本框焦点
                if not self.text_edit.geometry().contains(event.pos()):
                    self.text_edit.setFocus()

        except Exception as e:
            print(f"鼠标点击事件错误: {e}")
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        try:
            if event.buttons() & Qt.LeftButton:
                # 计算移动距离
                move_distance = (event.globalPos() - self.drag_start_global_pos).manhattanLength()

                # 如果移动距离超过阈值，开始拖动
                if move_distance > self.drag_threshold:
                    self.dragging = True

                    # 计算窗口新位置
                    new_pos = event.globalPos() - self.drag_start_pos
                    self.move(new_pos)

                    # 如果正在拖动，移除文本框焦点以避免干扰
                    if self.text_edit.hasFocus():
                        self.setFocus()

        except Exception as e:
            print(f"鼠标移动事件错误: {e}")
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        try:
            if event.button() == Qt.LeftButton:
                # 如果没有发生拖动，则恢复文本框焦点
                if not self.dragging:
                    # 延迟一点再设置焦点，确保界面稳定
                    QTimer.singleShot(50, lambda: self.text_edit.setFocus())

                # 重置拖动状态
                self.dragging = False
                self.drag_start_pos = QPoint()
                self.drag_start_global_pos = QPoint()

        except Exception as e:
            print(f"鼠标释放事件错误: {e}")
        super().mouseReleaseEvent(event)

    def paintEvent(self, event):
        """绘制事件"""
        try:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)

            # 绘制背景
            if self.background:
                # 使用分别的横纵缩放来绘制背景
                scale_x = self.config.get("scale_x", 1.0)
                scale_y = self.config.get("scale_y", 1.0)

                # 如果配置中还有旧的scale属性，用它来初始化scale_x和scale_y
                if "scale" in self.config and "scale_x" not in self.config:
                    scale_x = scale_y = self.config["scale"]

                bg_width = int(self.background.width() * scale_x)
                bg_height = int(self.background.height() * scale_y)

                # 绘制缩放后的背景
                painter.drawPixmap(QRect(0, 0, bg_width, bg_height), self.background)

        except Exception as e:
            print(f"绘制事件错误: {e}")

    def get_input_text(self):
        """获取输入的文本"""
        return self.text_edit.toPlainText()

    def clear_input(self):
        """清空输入"""
        self.text_edit.clear()

    def showEvent(self, event):
        """窗口显示事件"""
        super().showEvent(event)
        # 延迟设置焦点，确保窗口完全显示后再设置
        QTimer.singleShot(100, self._set_focus_to_text_edit)


class InputDialogManager(QObject):
    """输入对话框管理器"""
    input_received = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        # 确保使用现有的QApplication实例
        self.app = QApplication.instance()
        if not self.app:
            self.app = QApplication(sys.argv)

        self.dialog = InputDialogWidget()

        # 连接信号
        self.dialog.input_submitted.connect(self.on_input_submitted)
        self.dialog.dialog_closed.connect(self.on_dialog_closed)

    def show_input_dialog(self):
        """显示输入对话框"""
        self.dialog.show_dialog()

    def hide_input_dialog(self):
        """隐藏输入对话框"""
        self.dialog.hide_dialog()
    
    def force_close_dialog(self):
        """强制关闭输入对话框"""
        if hasattr(self.dialog, 'force_close'):
            self.dialog.force_close()
        else:
            self.dialog.close()

    def on_input_submitted(self, text):
        """处理输入提交"""
        self.input_received.emit(text)

    def on_dialog_closed(self):
        """处理对话框关闭"""
        print("输入对话框已关闭")


# 使用示例
if __name__ == "__main__":
    app = QApplication(sys.argv)

    # 创建输入对话框管理器
    manager = InputDialogManager()


    def on_input_received(text):
        print(f"收到输入: {text}")
        # 可以在这里再次显示对话框进行测试
        QTimer.singleShot(1000, manager.show_input_dialog)


    manager.input_received.connect(on_input_received)
    manager.show_input_dialog()

    sys.exit(app.exec_())
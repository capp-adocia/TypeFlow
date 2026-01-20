from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel, QApplication
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter, QColor, QBrush, QCursor
from pynput import keyboard
import time
from threading import Thread
from collections import deque

class KeyboardMonitor:
    """键盘监控类"""
    def __init__(self):
        self.key_times = deque(maxlen=100)  # 记录按键时间
        self.frequency = 0  # 当前频率
        self.listener = None
        self.running = False
        
    def start(self):
        """启动键盘监听"""
        self.running = True
        def on_press(key):
            if self.running:
                self.key_times.append(time.time())
        
        # 在独立线程中运行监听器
        self.listener_thread = Thread(
            target=self._run_listener, 
            args=(on_press,), 
            daemon=True
        )
        self.listener_thread.start()
        
        # 启动定时器计算频率
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frequency)
        self.timer.start(100)  # 每100ms更新一次频率
    
    def _run_listener(self, on_press):
        """运行键盘监听器"""
        with keyboard.Listener(on_press=on_press) as listener:
            self.listener = listener
            listener.join()
    
    def update_frequency(self):
        """更新按键频率"""
        if not self.running:
            return
            
        current_time = time.time()
        cutoff = current_time - 1.0  # 最近1秒
        
        # 计算频率
        count = 0
        for t in reversed(self.key_times):
            if t > cutoff:
                count += 1
            else:
                break
        
        self.frequency = count
    
    def stop(self):
        """停止监听"""
        self.running = False
        if self.listener:
            self.listener.stop()


class DotWidget(QWidget):
    """单个圆点霓虹灯组件"""
    def __init__(self, parent=None, radius=6):
        super().__init__(parent=parent)
        self.radius = radius
        self.current_color = QColor("#333333")  # 默认灰色
        self.target_color = self.current_color
        self.setFixedSize(radius * 2 + 4, radius * 2 + 4)
    
    def set_color(self, color, animate=True):
        """设置圆点颜色"""
        self.target_color = QColor(color)
        
        if not animate or self.current_color == self.target_color:
            self.current_color = self.target_color
            self.update()
        else:
            # 平滑过渡
            self.current_color = self.target_color
            self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        center_x = self.width() // 2
        center_y = self.height() // 2
        
        # 绘制发光效果
        glow_color = QColor(self.current_color)
        glow_color.setAlpha(100)
        painter.setBrush(QBrush(glow_color))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(int(center_x - self.radius*1.5), 
                   int(center_y - self.radius*1.5), 
                   int(self.radius*3), int(self.radius*3))
        
        # 绘制主圆点
        painter.setBrush(QBrush(self.current_color))
        painter.drawEllipse(center_x - self.radius, 
                           center_y - self.radius, 
                           self.radius*2, self.radius*2)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        screen = QApplication.primaryScreen().availableGeometry()
        self.screen_width = screen.width()
        self.screen_height = screen.height()
        
        # 窗口设置
        self.narrow_width = 15
        self.wide_width = 60
        self.w_height = 40
        self.current_width = self.narrow_width
        
        # 颜色配置
        self.color_states = [
            "#333333",    # 灰色（无输入)
            "#004400",    # 深绿
            "#008800",    # 中绿
            "#00CC00",    # 亮绿
            "#44FF00",    # 绿黄
            "#88FF00",    # 黄绿
            "#CCFF00",    # 亮黄绿
            "#FFFF00",    # 黄色
            "#FFCC00",    # 橙黄
            "#FF9900",    # 橙色
            "#FF6600",    # 橙红
            "#FF3300",    # 红橙
            "#FF0000",    # 红色
            "#FF0066",    # 品红（最高频率）
        ]
        self.gray_color = self.color_states[0]  # 灰色（无输入状态）
        
        # 键盘监控
        self.key_monitor = KeyboardMonitor()
        
        # 动画状态
        self.current_level = 0  # 0表示灰色
        self.target_level = 0
        
        self.setup_window_flags()
        self.init_ui()
        self.init_timer()
        self.start_keyboard_monitor()
        
    def setup_window_flags(self):
        """设置窗口属性"""
        self.setWindowFlags(
            Qt.FramelessWindowHint |  # 无边框
            Qt.WindowStaysOnTopHint | # 置顶
            Qt.Tool                   # 防止出现在ctrl+tab中
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        
    def init_ui(self):
        """初始化用户界面"""
        x = self.screen_width - self.current_width
        y = self.screen_height - 5 * self.w_height
        self.setGeometry(x, y, self.current_width, self.w_height)
        
        # 创建中央部件
        central_widget = QWidget()
        central_widget.setStyleSheet("""
            QWidget {
                background-color: rgba(0, 0, 0, 0);
                border: none;
            }
        """)
        self.setCentralWidget(central_widget)
        
        # 创建三个霓虹灯圆点
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # 初始显示灰色
        self.dots = [
            DotWidget(central_widget, 5),  # 上
            DotWidget(central_widget, 5),  # 中
            DotWidget(central_widget, 5)   # 下
        ]
        
        for dot in self.dots:
            dot.set_color(self.gray_color)
            layout.addWidget(dot, 0, Qt.AlignCenter)
        
        layout.addStretch()

        # 创建自定义提示标签
        self.custom_tooltip = QLabel("点击并按下ESC退出", self)
        self.custom_tooltip.setAlignment(Qt.AlignCenter)
        self.custom_tooltip.setStyleSheet("""
            QLabel {
                color: white;
                background-color: rgba(50, 50, 50, 200);
                border-radius: 5px;
                padding: 5px 10px;
                font-size: 12px;
            }
        """)
        self.custom_tooltip.hide()
        self.custom_tooltip.setWindowFlags(
            Qt.ToolTip | 
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint
        )
        self.custom_tooltip.setAttribute(Qt.WA_ShowWithoutActivating)
        
        
    def start_keyboard_monitor(self):
        """启动键盘监控"""
        self.key_monitor.start()
        
    def init_timer(self):
        """初始化定时器"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(50)  # 20fps动画
        
    def update_animation(self):
        """更新动画"""
        frequency = self.key_monitor.frequency
        
        # 计算目标等级
        if frequency == 0:
            # 无输入：目标等级为0，当前等级下降
            target_level = 0
            if self.current_level > 0:
                self.current_level = max(0, self.current_level - 0.05)
        else:
            # 有输入：计算目标等级
            target_level = min(frequency // 3, 6)
            
            # 更新当前等级
            if target_level > self.current_level:
                # 频率增加：立即跳到目标等级
                self.current_level = target_level
            elif target_level < self.current_level:
                # 频率减少：缓慢下降到目标等级
                self.current_level = max(target_level, self.current_level - 0.05)
        
        # 获取整数等级
        level = int(self.current_level)
        
        # 优雅的颜色映射配置
        color_mapping = {
            0: [0, 0, 0],           # 灰色，全部使用索引0
            1: [3, 2, 1],           # 绿-黄绿-深绿
            2: [6, 5, 4],           # 亮黄绿-黄绿-绿黄
            3: [9, 8, 7],           # 橙-橙黄-黄
            4: [12, 11, 10],        # 品红-红-红橙
            5: [13, 13, 13],        # 最高频率：全部品红
        }
        
        # 获取对应等级的颜色索引
        color_indices = color_mapping.get(level, color_mapping[4])
        
        # 应用颜色
        for i, dot in enumerate(self.dots):
            color_index = color_indices[i] if i < len(color_indices) else color_indices[-1]
            # 确保索引不越界
            safe_index = min(color_index, len(self.color_states) - 1)
            dot.set_color(self.color_states[safe_index])
        
    def keyPressEvent(self, event):
        """处理键盘按下事件"""
        if event.key() == Qt.Key_Escape:
            self.close()
        
    def closeEvent(self, event):
        """关闭事件"""
        print("退出中...")
        
        if hasattr(self, 'timer'):
            self.timer.stop()
        if hasattr(self, 'key_monitor'):
            self.key_monitor.stop()
        if hasattr(self, 'dots'):
            for dot in self.dots:
                dot.setParent(None)  # 断开父子关系
                dot.deleteLater()    # 延迟删除
            self.dots.clear()
        self.hide()
        event.accept()
        QTimer.singleShot(100, QApplication.quit)
        
    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
            
    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        if event.buttons() == Qt.LeftButton:
            if hasattr(self, 'drag_position'):
                self.move(event.globalPos() - self.drag_position)
                event.accept()
                
    def enterEvent(self, event):
        """鼠标进入"""
        self.current_width = self.wide_width
        x = self.screen_width - self.current_width
        self.setGeometry(x, self.y(), self.current_width, self.w_height)
        
        # 获取鼠标的全局坐标
        mouse_pos = QCursor.pos()
        # 计算提示窗口位置（鼠标右下角偏移）
        tooltip_x = mouse_pos.x() + 15  # 向右偏移15px
        tooltip_y = mouse_pos.y() + 15  # 向下偏移15px
        screen_rect = QApplication.primaryScreen().availableGeometry()
        if tooltip_x + self.custom_tooltip.width() > screen_rect.right():
            tooltip_x = mouse_pos.x() - self.custom_tooltip.width() - 15
        # 如果提示框超出屏幕底部，显示在鼠标上方
        if tooltip_y + self.custom_tooltip.height() > screen_rect.bottom():
            tooltip_y = mouse_pos.y() - self.custom_tooltip.height() - 15
        
        self.custom_tooltip.move(tooltip_x, tooltip_y)
        self.custom_tooltip.show()
        
        QTimer.singleShot(3000, self.custom_tooltip.hide)
        
    def leaveEvent(self, event):
        """鼠标离开 - 变窄"""
        self.current_width = self.narrow_width
        x = self.screen_width - self.current_width
        self.setGeometry(x, self.y(), self.current_width, self.w_height)
        self.custom_tooltip.hide()
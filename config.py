class Config:
    """配置类，存储程序设置"""
    
    def __init__(self):
        self.window_opacity = 0.3
        self.window_background = "rgba(0, 0, 0, 200)"
        self.window_radius = 10
        self.text_color = "white"
        self.hint_color = "rgba(255, 255, 255, 150)"
        self.update_interval = 1000  # 更新间隔(ms)
        
        # 窗口位置和大小
        self.window_x = 100
        self.window_y = 100
        self.window_width = 400
        self.window_height = 300
        
        # 布局边距
        self.margin_left = 20
        self.margin_top = 20
        self.margin_right = 20
        self.margin_bottom = 20
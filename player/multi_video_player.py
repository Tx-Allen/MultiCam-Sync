# player/multi_video_player.py

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QPushButton, QGridLayout, QVBoxLayout,
    QHBoxLayout, QScrollArea, QFileDialog, QSpinBox,
    QLabel, QTextEdit, QSplitter, QLineEdit
)
from PyQt5.QtCore import Qt
from player.video_item import VideoItem
from datetime import datetime

class MultiVideoPlayerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Multi-Video Player - Screenshots saved in screenshots/<VideoNameWithoutExt>/")
        self.resize(1600, 900)

        # Top control panel
        self.btn_add_video = QPushButton("Add Video")
        self.btn_add_video.clicked.connect(self.on_add_video_dialog)
        self.btn_play_all = QPushButton("Play All")
        self.btn_play_all.clicked.connect(self.play_all)
        self.btn_pause_all = QPushButton("Pause All")
        self.btn_pause_all.clicked.connect(self.pause_all)
        
        # Global navigation: one spinbox for offset used for both rewind and fast-forward.
        self.spin_offset_global = QSpinBox()
        self.spin_offset_global.setRange(1, 99999)
        self.spin_offset_global.setValue(10)
        self.btn_global_rewind = QPushButton("Rewind All")
        self.btn_global_rewind.clicked.connect(self.rewind_all)
        self.btn_global_fast_forward = QPushButton("Fast-forward All")
        self.btn_global_fast_forward.clicked.connect(self.fast_forward_all)
        
        # Global Screenshot controls
        self.btn_snap1 = QPushButton("Screenshot (1x)")
        self.btn_snap3 = QPushButton("Screenshot (3x)")
        self.btn_snap10 = QPushButton("Screenshot (10x)")
        self.btn_snap1.clicked.connect(lambda: self.snapshot_all(1))
        self.btn_snap3.clicked.connect(lambda: self.snapshot_all(3))
        self.btn_snap10.clicked.connect(lambda: self.snapshot_all(10))
        self.label_intv = QLabel("Interval Frames:")
        self.spin_intv = QSpinBox()
        self.spin_intv.setRange(1, 99999)
        self.spin_intv.setValue(1)
        
        # Global Jump-to-Time row
        self.input_global_jump = QLineEdit("2024-12-05 09:30:00")
        self.btn_jump_all = QPushButton("Jump All to Time")
        self.btn_jump_all.clicked.connect(self.jump_all_to_time)
        
        # Assemble top controls in two rows.
        top_row = QHBoxLayout()
        top_row.addWidget(self.btn_add_video)
        top_row.addWidget(self.btn_play_all)
        top_row.addWidget(self.btn_pause_all)
        top_row.addWidget(QLabel("Global Offset:"))
        top_row.addWidget(self.spin_offset_global)
        top_row.addWidget(self.btn_global_rewind)
        top_row.addWidget(self.btn_global_fast_forward)
        top_row.addWidget(self.btn_snap1)
        top_row.addWidget(self.btn_snap3)
        top_row.addWidget(self.btn_snap10)
        top_row.addWidget(self.label_intv)
        top_row.addWidget(self.spin_intv)
        
        jump_row = QHBoxLayout()
        jump_row.addWidget(QLabel("Global Jump Time:"))
        jump_row.addWidget(self.input_global_jump)
        jump_row.addWidget(self.btn_jump_all)
        
        top_control_layout = QVBoxLayout()
        top_control_layout.addLayout(top_row)
        top_control_layout.addLayout(jump_row)
        top_widget = QWidget()
        top_widget.setLayout(top_control_layout)
        
        # Video grid (2 columns)
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(10)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.grid_widget)
        
        # Log output panel
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        
        # Splitter to separate video area and log output
        self.splitter = QSplitter(Qt.Vertical)
        top_area_widget = QWidget()
        top_area_layout = QVBoxLayout(top_area_widget)
        top_area_layout.addWidget(top_widget)
        top_area_layout.addWidget(self.scroll_area)
        self.splitter.addWidget(top_area_widget)
        self.splitter.addWidget(self.log_text)
        
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.splitter)
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)
        
        self.video_items = []
    
    def log_html(self, html):
        self.log_text.append(html)
    
    def on_add_video_dialog(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Select Videos", "",
                                                "Video Files (*.mp4 *.avi *.mkv *.mov *.flv);;All Files (*)")
        for p in paths:
            self.add_video_item(p)
    
    def add_video_item(self, video_path):
        item = VideoItem(log_func=self.log_html)
        item.delete_callback = self.delete_video_item
        item.load_video_manually(video_path)
        idx = len(self.video_items)
        row = idx // 2
        col = idx % 2
        self.grid_layout.addWidget(item, row, col)
        self.video_items.append(item)
        self.log_html(f"<font color='black'>Added video at row={row}, col={col}, path={video_path}</font>")
    
    def delete_video_item(self, item):
        if item in self.video_items:
            self.video_items.remove(item)
            self.grid_layout.removeWidget(item)
            item.delete_self()
            self.log_html(f"<font color='black'>Deleted video: {item.video_path}</font>")
            self.refresh_grid_layout()
    
    def refresh_grid_layout(self):
        while self.grid_layout.count():
            child = self.grid_layout.takeAt(0)
            if child.widget():
                child.widget().setParent(None)
        for i, vi in enumerate(self.video_items):
            row = i // 2
            col = i % 2
            self.grid_layout.addWidget(vi, row, col)
    
    def play_all(self):
        self.log_html("<font color='black'>[Play All]</font>")
        for it in self.video_items:
            it.play_video()
    
    def pause_all(self):
        self.log_html("<font color='black'>[Pause All]</font>")
        for it in self.video_items:
            it.pause_video()
    
    def fast_forward_all(self):
        steps = self.spin_offset_global.value()  # Using the global offset spinbox
        self.log_html(f"<font color='black'>[Fast-forward All] +{steps} frames</font>")
        for it in self.video_items:
            it.show_frame(it.current_frame + steps)
    
    def rewind_all(self):
        steps = self.spin_offset_global.value()
        self.log_html(f"<font color='black'>[Rewind All] -{steps} frames</font>")
        for it in self.video_items:
            it.show_frame(it.current_frame - steps)
    
    def snapshot_all(self, times=1):
        interval = self.spin_intv.value()
        self.log_html(f"<font color='black'>[Multi-screenshot] times={times}, interval={interval} frames</font>")
        for _ in range(times):
            for it in self.video_items:
                it.screenshot()
                it.show_frame(it.current_frame + interval)
        self.log_html(f"<font color='#006400'>[Multi-screenshot finished] {times} times, interval={interval} frames</font>")
    
    def jump_all_to_time(self):
        t_str = self.input_global_jump.text().strip()
        try:
            target_dt = datetime.strptime(t_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            self.log_html("<font color='red'>Global Jump: Time format incorrect!</font>")
            return
        for it in self.video_items:
            if it.start_time and it.end_time:
                total_secs = (it.end_time - it.start_time).total_seconds()
                if total_secs <= 0:
                    it.log_red("Invalid time range!")
                    continue
                delta_secs = (target_dt - it.start_time).total_seconds()
                ratio = delta_secs / total_secs
                ratio = max(0, min(1, ratio))
                fidx = int(ratio * it.total_frames)
                it.show_frame(fidx)
                it.log_black(f"Global Jump: {t_str} -> frame={fidx}")
        self.log_html(f"<font color='black'>Global jump executed for time: {t_str}</font>")

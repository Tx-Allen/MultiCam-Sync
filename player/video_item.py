# player/video_item.py

import os
import cv2
import pytesseract
import re
from datetime import datetime, timedelta
from PyQt5.QtCore import Qt, QTimer, QEvent
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import (
    QWidget, QLabel, QPushButton, QLineEdit, QSpinBox, QVBoxLayout,
    QHBoxLayout, QSlider, QFileDialog, QDialog
)

def normalize_ocr_text(text):
    # Replace various dash characters with ASCII '-' and normalize whitespace.
    text = text.replace('—','-').replace('–','-').replace('－','-')
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_time_from_roi(frame, roi=(0, 0, 250, 40), log_func=None):
    """
    Attempts to extract a time string "YYYY-MM-DD HH:MM:SS" from the given ROI.
    Logs the raw and normalized OCR text if log_func is provided.
    """
    x, y, w, h = roi
    roi_frame = frame[y:y+h, x:x+w]
    gray = cv2.cvtColor(roi_frame, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY)
    
    text = pytesseract.image_to_string(thresh)
    if log_func:
        log_func(f"<font color='black'>[OCR Raw]: {repr(text)}</font>")
    
    text = normalize_ocr_text(text)
    if log_func:
        log_func(f"<font color='black'>[OCR Normalized]: {repr(text)}</font>")
    
    pattern = r"(\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2})"
    match = re.search(pattern, text)
    if match:
        time_str = match.group(1)
        try:
            return datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            pass
    return None

class VideoItem(QWidget):
    """
    Represents a single video item.
    
    Screenshots are saved under:
       screenshots/<video_filename_without_extension>/
    with filename: "<remark>_<frame>.png" (or "screenshot_<frame>.png" if no remark is provided).
    
    OCR is performed on the first frame; if successful, start_time is set to the OCR result and 
    end_time is set to start_time + 5 minutes.
    
    All notifications are output to the log (colored HTML) rather than via pop-up dialogs.
    
    Also includes a "Hide Info/Show Info" toggle button and a "Delete Video" button.
    
    Local navigation uses a single spinbox (spin_offset) for setting the frame offset, with two buttons:
    "Rewind" (subtract frames) and "Fast Forward" (add frames).
    """
    def __init__(self, log_func=None, parent=None):
        super().__init__(parent)
        self.log_func = log_func if log_func else (lambda msg: None)

        self.cap = None
        self.video_path = None
        self.screens_dir = None  # Will be set to "screenshots/<video_filename_without_extension>"
        self.fps = 0
        self.total_frames = 0
        self.current_frame = 0
        self.orig_frame = None
        self.play_timer = None

        self.start_time = None
        self.end_time = None
        self._remark_name = ""

        # Top row: Video info, Toggle Info, Copy Path, Delete Video, and Remark input.
        self.label_info = QLabel("Video: Not loaded")
        self.label_info.setWordWrap(True)
        self.btn_toggle_info = QPushButton("Hide Info")
        self.btn_toggle_info.clicked.connect(self.toggle_info)
        self.btn_copy_path = QPushButton("Copy Path")
        self.btn_copy_path.clicked.connect(self.copy_path)
        self.btn_delete = QPushButton("Delete Video")
        self.btn_delete.clicked.connect(self.delete_self)
        self.input_remark_name = QLineEdit("")
        self.input_remark_name.setPlaceholderText("Remark name (for screenshot filename)")
        self.btn_apply_remark = QPushButton("Apply Remark")
        self.btn_apply_remark.clicked.connect(self.apply_remark_name)
        top_row = QHBoxLayout()
        top_row.addWidget(self.label_info)
        top_row.addWidget(self.btn_toggle_info)
        top_row.addWidget(self.btn_copy_path)
        top_row.addWidget(self.btn_delete)
        top_row.addWidget(self.input_remark_name)
        top_row.addWidget(self.btn_apply_remark)

        # Video preview area
        self.video_label = QLabel("Preview")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.installEventFilter(self)

        # Load button
        self.btn_load = QPushButton("Load Video")
        self.btn_load.clicked.connect(self.load_video)

        # Play/Pause/Screenshot and navigation controls
        self.btn_play = QPushButton("Play")
        self.btn_play.clicked.connect(self.play_video)
        self.btn_pause = QPushButton("Pause")
        self.btn_pause.clicked.connect(self.pause_video)
        self.btn_screenshot = QPushButton("Screenshot")
        self.btn_screenshot.clicked.connect(self.screenshot)
        self.slider = QSlider(Qt.Horizontal)
        self.slider.valueChanged.connect(self.on_slider_changed)
        self.spin_frame = QSpinBox()
        self.spin_frame.valueChanged.connect(self.on_spin_changed)
        self.label_frame_info = QLabel("0/0")
        controls_row = QHBoxLayout()
        controls_row.addWidget(self.btn_play)
        controls_row.addWidget(self.btn_pause)
        controls_row.addWidget(self.btn_screenshot)
        controls_row.addWidget(self.slider)
        controls_row.addWidget(self.spin_frame)
        controls_row.addWidget(self.label_frame_info)

        # Manual start/end time row
        self.input_start_time = QLineEdit("2024-12-05 09:00:00")
        self.input_end_time = QLineEdit("2024-12-05 09:05:00")
        self.btn_apply_start_end = QPushButton("Apply Start/End")
        self.btn_apply_start_end.clicked.connect(self.apply_start_end_times)
        manual_row = QHBoxLayout()
        self.btn_ocr_detect = QPushButton("OCR Detect")
        self.btn_ocr_detect.clicked.connect(self.ocr_detect_first_frame)
        manual_row.addWidget(self.btn_ocr_detect)
        manual_row.addWidget(self.input_start_time)
        manual_row.addWidget(self.input_end_time)
        manual_row.addWidget(self.btn_apply_start_end)

        # Jump-to-time row
        self.input_jump_time = QLineEdit("2024-12-05 09:30:00")
        self.btn_jump_time = QPushButton("Jump to Time")
        self.btn_jump_time.clicked.connect(self.jump_to_time)
        jump_row = QHBoxLayout()
        jump_row.addWidget(self.input_jump_time)
        jump_row.addWidget(self.btn_jump_time)

        # Local navigation row: Use one spinbox (spin_offset) for both rewind and fast forward.
        self.spin_offset = QSpinBox()
        self.spin_offset.setRange(1, 99999)
        self.spin_offset.setValue(10)
        self.btn_rewind = QPushButton("Rewind")
        self.btn_rewind.clicked.connect(self.rewind_local)
        self.btn_fast_forward = QPushButton("Fast Forward")
        self.btn_fast_forward.clicked.connect(self.fast_forward_local)
        nav_row = QHBoxLayout()
        nav_row.addWidget(self.spin_offset)
        nav_row.addWidget(self.btn_rewind)
        nav_row.addWidget(self.btn_fast_forward)

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.addLayout(top_row)
        main_layout.addWidget(self.video_label)
        main_layout.addWidget(self.btn_load)
        main_layout.addLayout(controls_row)
        main_layout.addLayout(manual_row)
        main_layout.addLayout(jump_row)
        main_layout.addLayout(nav_row)

        self.setLayout(main_layout)
        self.remark_name = ""

    # ---------- remark_name property ----------
    @property
    def remark_name(self):
        return self._remark_name

    @remark_name.setter
    def remark_name(self, value):
        self._remark_name = value
        self.input_remark_name.setText(value)

    def apply_remark_name(self):
        name = self.input_remark_name.text().strip()
        self._remark_name = name
        self.log_black(f"Remark name set to: {name}")

    # ---------- Logging functions ----------
    def log_red(self, msg):
        self.log_func(f"<font color='red'>{msg}</font>")

    def log_green(self, msg):
        self.log_func(f"<font color='#006400'>{msg}</font>")

    def log_black(self, msg):
        self.log_func(f"<font color='black'>{msg}</font>")

    # ---------- Toggle Info ----------
    def toggle_info(self):
        if self.label_info.isVisible():
            self.label_info.hide()
            self.btn_toggle_info.setText("Show Info")
            self.log_black("Info hidden.")
        else:
            self.label_info.show()
            self.btn_toggle_info.setText("Hide Info")
            self.log_black("Info shown.")

    # ---------- Delete Video ----------
    def delete_self(self):
        self.log_black(f"Deleting video: {self.video_path}")
        if self.cap:
            self.cap.release()
        self.setParent(None)
        self.deleteLater()
        if hasattr(self, 'delete_callback') and callable(self.delete_callback):
            self.delete_callback(self)

    # ---------- Event Filter for double-click to enlarge preview ----------
    def eventFilter(self, source, event):
        if source == self.video_label and event.type() == QEvent.MouseButtonDblClick:
            if self.orig_frame is not None:
                self.enlarge_preview()
                return True
        return super().eventFilter(source, event)

    def enlarge_preview(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Enlarged Preview")
        from PyQt5.QtWidgets import QVBoxLayout
        lbl = QLabel(dlg)
        if self.orig_frame is None:
            lbl.setText("No frame available.")
        else:
            frame = self.orig_frame
            h, w, ch = frame.shape
            scale_factor = 1.5
            new_w = int(w * scale_factor)
            new_h = int(h * scale_factor)
            if new_w > 1920:
                new_w = 1920
            if new_h > 1080:
                new_h = 1080
            frame_resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)
            frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
            qimg = QImage(frame_rgb.data, new_w, new_h, 3 * new_w, QImage.Format_RGB888)
            pix = QPixmap.fromImage(qimg)
            lbl.setPixmap(pix)
        ly = QVBoxLayout()
        ly.addWidget(lbl)
        dlg.setLayout(ly)
        dlg.exec_()

    # ---------- Copy Path ----------
    def copy_path(self):
        if not self.video_path:
            self.log_red("No video loaded!")
            return
        from PyQt5.QtWidgets import QApplication
        cb = QApplication.clipboard()
        cb.setText(self.video_path)
        self.log_black(f"Copied video path: {self.video_path}")

    # ---------- Load Video ----------
    def load_video(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Video", "",
                                              "Video Files (*.mp4 *.avi *.mkv *.mov *.flv);;All Files (*)")
        if path:
            self.load_video_manually(path)

    def load_video_manually(self, path):
        if self.cap:
            self.cap.release()
        self.cap = cv2.VideoCapture(path)
        if not self.cap.isOpened():
            self.log_red(f"Failed to open video: {path}")
            self.cap = None
            return
        self.video_path = path
        basename = os.path.basename(path)
        file_no_ext = os.path.splitext(basename)[0]
        self.screens_dir = os.path.join("screenshots", file_no_ext)
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.current_frame = 0
        self.orig_frame = None
        info_str = f"File: {basename}<br>Path: {path}<br>Total Frames: {self.total_frames}<br>FPS: {self.fps}"
        self.label_info.setText(info_str)
        self.slider.setRange(0, max(0, self.total_frames - 1))
        self.spin_frame.setRange(0, max(0, self.total_frames - 1))
        self.label_frame_info.setText(f"0/{self.total_frames}")
        self.show_frame(0)
        self.log_black(f"Video loaded: {path}, frames={self.total_frames}, fps={self.fps}")
        # Automatically perform OCR on the first frame.
        self.ocr_detect_first_frame()

    def show_frame(self, frame_idx):
        if not self.cap:
            return
        if frame_idx < 0:
            frame_idx = 0
        if frame_idx >= self.total_frames:
            frame_idx = self.total_frames - 1
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = self.cap.read()
        if not ret or frame is None:
            return
        self.current_frame = frame_idx
        self.orig_frame = frame
        pix = self.frame_to_pixmap(frame, self.video_label.width(), self.video_label.height())
        self.video_label.setPixmap(pix)
        self.slider.blockSignals(True)
        self.slider.setValue(frame_idx)
        self.slider.blockSignals(False)
        self.spin_frame.blockSignals(True)
        self.spin_frame.setValue(frame_idx)
        self.spin_frame.blockSignals(False)
        self.label_frame_info.setText(f"{frame_idx}/{self.total_frames}")

    def frame_to_pixmap(self, cv_frame, label_w, label_h):
        if label_w <= 0 or label_h <= 0:
            label_w, label_h = 640, 480
        h, w, ch = cv_frame.shape
        aspect_frame = w / h
        aspect_label = label_w / label_h
        if aspect_frame > aspect_label:
            new_w = label_w
            new_h = int(label_w / aspect_frame)
        else:
            new_h = label_h
            new_w = int(label_h * aspect_frame)
        frame_resized = cv2.resize(cv_frame, (new_w, new_h), interpolation=cv2.INTER_AREA)
        frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
        return QPixmap.fromImage(QImage(frame_rgb.data, new_w, new_h, 3 * new_w, QImage.Format_RGB888))

    # ---------- Play/Pause ----------
    def play_video(self):
        if not self.cap:
            self.log_red("Load a video first!")
            return
        if self.play_timer:
            self.play_timer.stop()
        from PyQt5.QtCore import QTimer
        self.play_timer = QTimer(self)
        interval = 40
        if self.fps > 0:
            interval = int(1000 // self.fps)
        self.play_timer.timeout.connect(self.play_next_frame)
        self.play_timer.start(interval)
        self.log_black(f"Playing: {self.video_path}, interval={interval}ms")

    def play_next_frame(self):
        if self.current_frame < self.total_frames - 1:
            self.show_frame(self.current_frame + 1)
        else:
            self.play_timer.stop()

    def pause_video(self):
        if self.play_timer:
            self.play_timer.stop()
        self.log_black(f"Paused: {self.video_path}")

    def on_slider_changed(self):
        if not self.cap:
            return
        self.show_frame(self.slider.value())

    def on_spin_changed(self):
        if not self.cap:
            return
        self.show_frame(self.spin_frame.value())

    # ---------- Screenshot ----------
    def screenshot(self):
        if self.orig_frame is None:
            self.log_red("No frame available for screenshot!")
            return
        import os
        if not self.screens_dir:
            self.log_red("Video not loaded; cannot determine screenshot folder!")
            return
        os.makedirs(self.screens_dir, exist_ok=True)
        if self.remark_name:
            fname = f"{self.remark_name}_{self.current_frame}.png"
        else:
            fname = f"screenshot_{self.current_frame}.png"
        fullpath = os.path.join(self.screens_dir, fname)
        cv2.imwrite(fullpath, self.orig_frame)
        self.log_green(f"Screenshot saved: {fullpath}")

    # ---------- Apply Start/End Times ----------
    def apply_start_end_times(self):
        s_str = self.input_start_time.text().strip()
        e_str = self.input_end_time.text().strip()
        try:
            sdt = datetime.strptime(s_str, "%Y-%m-%d %H:%M:%S")
            edt = datetime.strptime(e_str, "%Y-%m-%d %H:%M:%S")
            if edt <= sdt:
                self.log_red("End time must be later than start time!")
                return
            self.start_time = sdt
            self.end_time = edt
            self.log_black(f"Manual time set: {sdt} ~ {edt}")
        except ValueError:
            self.log_red("Time format error (YYYY-MM-DD HH:MM:SS)")

    # ---------- OCR Detect (first frame only) ----------
    def ocr_detect_first_frame(self):
        if not self.cap:
            self.log_red("Load a video first!")
            return
        if self.total_frames < 1:
            self.log_red("Video has too few frames for OCR!")
            return
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        ret, frame = self.cap.read()
        if not ret or frame is None:
            self.log_red("Failed to read first frame!")
            return
        dt = extract_time_from_roi(frame, roi=(0, 0, 250, 40), log_func=self.log_black)
        if dt:
            self.start_time = dt
            self.end_time = dt + timedelta(minutes=5)
            self.input_start_time.setText(dt.strftime("%Y-%m-%d %H:%M:%S"))
            self.input_end_time.setText(self.end_time.strftime("%Y-%m-%d %H:%M:%S"))
            self.log_green(f"OCR success: start = {dt}, end = {self.end_time} (start + 5 min)")
        else:
            self.log_red("OCR detection failed: No valid time found in first frame!")

    # ---------- Jump to Time ----------
    def jump_to_time(self):
        if not self.cap:
            self.log_red("Load a video first!")
            return
        if not (self.start_time and self.end_time):
            self.log_red("Set the time range manually or use OCR!")
            return
        t_str = self.input_jump_time.text().strip()
        try:
            target_dt = datetime.strptime(t_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            self.log_red("Time format incorrect!")
            return
        total_secs = (self.end_time - self.start_time).total_seconds()
        if total_secs <= 0:
            self.log_red("Invalid time range!")
            return
        delta_secs = (target_dt - self.start_time).total_seconds()
        ratio = delta_secs / total_secs
        ratio = max(0, min(1, ratio))
        fidx = int(ratio * self.total_frames)
        self.show_frame(fidx)
        self.log_black(f"Jump to time: {t_str} -> frame={fidx}")

    # ---------- Fast Forward (local) ----------
    def fast_forward_local(self):
        steps = self.spin_offset.value()
        nf = self.current_frame + steps
        self.show_frame(nf)
        self.log_black(f"Local fast forward: +{steps} -> frame={nf}")

    # ---------- Rewind (local) ----------
    def rewind_local(self):
        steps = self.spin_offset.value()
        nf = self.current_frame - steps
        self.show_frame(nf)
        self.log_black(f"Local rewind: -{steps} -> frame={nf}")


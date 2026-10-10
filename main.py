import sys
import sounddevice as sd
import numpy as np
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel, QHBoxLayout, QFrame
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QPainter, QColor

class EqualizerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(360, 40)
        self.bars = [5] * 12
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.is_active = False

    def start(self):
        self.is_active = True
        self.timer.start(80)

    def stop(self):
        self.is_active = False
        self.timer.stop()
        self.bars = [5] * 12
        self.update()

    def update_animation(self):
        if self.is_active:
            self.bars = [np.random.randint(5, 35) for _ in range(12)]
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        spacing = 6
        bar_width = (self.width() - (spacing * 11)) // 12
        for i, bar_height in enumerate(self.bars):
            x = i * (bar_width + spacing)
            y = (self.height() - bar_height) // 2
            color = QColor("#10b981") if self.is_active else QColor("#4b5563")
            painter.setBrush(color)
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(x, y, bar_width, bar_height, 3, 3)

class ToksiApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("tok.si")
        self.setFixedSize(400, 340)
        self.is_active = False
        self.stream = None
        self.selected_gender = "Male"

        self.setStyleSheet("""
            QMainWindow { background-color: #111827; }
            QLabel { color: #f3f4f6; font-family: 'Segoe UI', Arial, sans-serif; }
            QPushButton { font-family: 'Segoe UI', Arial, sans-serif; border-radius: 8px; }
        """)

        main_widget = QWidget()
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        header_layout = QHBoxLayout()
        self.brand_title = QLabel("tok.si")
        self.brand_title.setStyleSheet("font-size: 22px; font-weight: 800; color: #10b981; letter-spacing: 0.5px;")
        
        self.status_label = QLabel("Ready")
        self.status_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.status_label.setStyleSheet("font-size: 12px; color: #9ca3af; font-weight: 600; background-color: #1f2937; padding: 4px 10px; border-radius: 12px;")
        
        header_layout.addWidget(self.brand_title)
        header_layout.addStretch()
        header_layout.addWidget(self.status_label)
        layout.addLayout(header_layout)

        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet("background-color: #1f2937; max-height: 1px; border: none;")
        layout.addWidget(divider)

        self.headset_label = QLabel("Searching hardware links...")
        self.headset_label.setAlignment(Qt.AlignCenter)
        self.headset_label.setStyleSheet("color: #9ca3af; font-size: 12px; font-weight: 500; background-color: #1f2937; padding: 10px; border-radius: 6px;")
        layout.addWidget(self.headset_label)
        self.auto_detect_headset()

        self.equalizer = EqualizerWidget()
        layout.addWidget(self.equalizer, 0, Qt.AlignCenter)

        gender_layout = QHBoxLayout()
        self.male_btn = QPushButton("US Male Voice")
        self.female_btn = QPushButton("US Female Voice")
        
        self.male_btn.setCheckable(True)
        self.male_btn.setChecked(True)
        self.male_btn.setStyleSheet("background-color: #3b82f6; color: white; padding: 12px; font-weight: 700; font-size: 13px; border: none;")
        self.female_btn.setStyleSheet("background-color: #374151; color: #9ca3af; padding: 12px; font-weight: 700; font-size: 13px; border: none;")
        
        self.male_btn.clicked.connect(lambda: self.set_gender("Male"))
        self.female_btn.clicked.connect(lambda: self.set_gender("Female"))
        
        gender_layout.addWidget(self.male_btn)
        gender_layout.addWidget(self.female_btn)
        layout.addLayout(gender_layout)

        self.toggle_btn = QPushButton("IN TURN ON TOK.SI")
        self.toggle_btn.setStyleSheet("background-color: #10b981; color: white; padding: 16px; font-weight: 800; font-size: 14px; border: none; margin-top: 5px;")
        self.toggle_btn.clicked.connect(self.toggle_conversion)
        layout.addWidget(self.toggle_btn)

        self.setCentralWidget(main_widget)

    def auto_detect_headset(self):
        try:
            default_input = sd.query_devices(kind='input')
            name = default_input['name']
            short_name = (name[:32] + '...') if len(name) > 35 else name
            self.headset_label.setText(f"🎧 Mic: {short_name}")
        except Exception:
            self.headset_label.setText("⚠️ Plug in a headphone setup to stream")

    def set_gender(self, gender):
        self.selected_gender = gender
        if gender == "Male":
            self.male_btn.setChecked(True)
            self.female_btn.setChecked(False)
            self.male_btn.setStyleSheet("background-color: #3b82f6; color: white; padding: 12px; font-weight: 700; font-size: 13px; border: none;")
            self.female_btn.setStyleSheet("background-color: #374151; color: #9ca3af; padding: 12px; font-weight: 700; font-size: 13px; border: none;")
        else:
            self.male_btn.setChecked(False)
            self.female_btn.setChecked(True)
            self.male_btn.setStyleSheet("background-color: #374151; color: #9ca3af; padding: 12px; font-weight: 700; font-size: 13px; border: none;")
            self.female_btn.setStyleSheet("background-color: #ec4899; color: white; padding: 12px; font-weight: 700; font-size: 13px; border: none;")
        if self.is_active:
            self.status_label.setText(f"US {gender} Live")

    def toggle_conversion(self):
        if not self.is_active:
            self.is_active = True
            self.toggle_btn.setText("TOK.SI IS ACTIVE")
            self.toggle_btn.setStyleSheet("background-color: #ef4444; color: white; padding: 16px; font-weight: 800; font-size: 14px; border: none; margin-top: 5px;")
            self.status_label.setText("Bridge Active")
            self.status_label.setStyleSheet("font-size: 12px; color: #10b981; font-weight: 600; background-color: #064e3b; padding: 4px 10px; border-radius: 12px;")
            self.equalizer.start()
            self.start_global_interception()
        else:
            self.is_active = False
            self.toggle_btn.setText("IN TURN ON TOK.SI")
            self.toggle_btn.setStyleSheet("background-color: #10b981; color: white; padding: 16px; font-weight: 800; font-size: 14px; border: none; margin-top: 5px;")
            self.status_label.setText("Ready")
            self.status_label.setStyleSheet("font-size: 12px; color: #9ca3af; font-weight: 600; background-color: #1f2937; padding: 4px 10px; border-radius: 12px;")
            self.equalizer.stop()
            self.stop_global_interception()

    def start_global_interception(self):
        self.auto_detect_headset()
        def audio_callback(indata, outdata, frames, time, status):
            if not self.is_active:
                outdata.fill(0)
                return
            outdata[:, 0] = indata[:, 0]
        self.stream = sd.Stream(device=(None, None), samplerate=16000, blocksize=512, channels=1, callback=audio_callback)
        self.stream.start()

    def stop_global_interception(self):
        if self.stream:
            self.stream.stop()
            self.stream.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ToksiApp()
    window.show()
    sys.exit(app.exec())

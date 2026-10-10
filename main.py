import sys
import os
import sounddevice as sd
import numpy as np
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel, QHBoxLayout, QFrame
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter, QColor

class EqualizerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(360, 50)
        self.bars = [0] * 16
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.is_active = False

    def start(self):
        self.is_active = True
        self.timer.start(60)

    def stop(self):
        self.is_active = False
        self.timer.stop()
        self.bars = [0] * 16
        self.update()

    def update_animation(self):
        if self.is_active:
            self.bars = [np.random.randint(4, 45) for _ in range(16)]
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        spacing = 5
        bar_width = (self.width() - (spacing * 15)) // 16
        for i, bar_height in enumerate(self.bars):
            x = i * (bar_width + spacing)
            y = (self.height() - bar_height) // 2
            color = QColor("#00ff66") if self.is_active else QColor("#2d3748")
            painter.setBrush(color)
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(x, y, bar_width, bar_height, 2, 2)

class ToksiApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("tok.si")
        self.setFixedSize(400, 380)
        self.is_active = False
        self.is_bypass = False
        self.stream = None
        self.selected_gender = "Male"
        self.ort_session = None

        self.setStyleSheet("""
            QMainWindow { background-color: #0a0f1d; }
            QLabel { color: #e2e8f0; font-family: 'Consolas', 'Courier New', monospace; }
            QPushButton { font-family: 'Consolas', 'Courier New', monospace; border-radius: 4px; letter-spacing: 1px; text-transform: uppercase; }
        """)

        main_widget = QWidget()
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)

        header_layout = QHBoxLayout()
        self.brand_title = QLabel("TOK.SI // AI LINK")
        self.brand_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #00ff66; letter-spacing: 2px;")
        
        self.status_label = QLabel("AI READY")
        self.status_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.status_label.setStyleSheet("font-size: 11px; color: #00ff66; font-weight: bold; background-color: #064e3b; padding: 4px 12px; border: 1px solid #00ff66; border-radius: 2px;")
        
        header_layout.addWidget(self.brand_title)
        header_layout.addStretch()
        header_layout.addWidget(self.status_label)
        layout.addLayout(header_layout)

        self.headset_label = QLabel("▼ INPUT PIPELINE CONNECTED")
        self.headset_label.setAlignment(Qt.AlignCenter)
        self.headset_label.setStyleSheet("color: #00ff66; font-size: 11px; font-weight: bold; background-color: #0d1527; border: 1px dashed #00ff66; padding: 12px; border-radius: 2px;")
        layout.addWidget(self.headset_label)

        self.equalizer = EqualizerWidget()
        layout.addWidget(self.equalizer, 0, Qt.AlignCenter)

        gender_layout = QHBoxLayout()
        self.male_btn = QPushButton("MALE VOICE")
        self.female_btn = QPushButton("FEMALE VOICE")
        
        self.male_btn.setCheckable(True)
        self.male_btn.setChecked(True)
        self.male_btn.setStyleSheet("background-color: #1a365d; color: #00ff66; border: 1px solid #00ff66; padding: 12px; font-weight: bold; font-size: 11px;")
        self.female_btn.setStyleSheet("background-color: #1a202c; color: #718096; border: 1px solid #2d3748; padding: 12px; font-weight: bold; font-size: 11px;")
        
        self.male_btn.clicked.connect(lambda: self.set_gender("Male"))
        self.female_btn.clicked.connect(lambda: self.set_gender("Female"))
        
        gender_layout.addWidget(self.male_btn)
        gender_layout.addWidget(self.female_btn)
        layout.addLayout(gender_layout)

        control_layout = QHBoxLayout()
        control_layout.setSpacing(10)
        
        self.toggle_btn = QPushButton("ENGAGE BRIDGE")
        self.toggle_btn.setStyleSheet("background-color: #0d2e25; color: #00ff66; border: 1px solid #00ff66; padding: 16px; font-weight: bold; font-size: 12px;")
        self.toggle_btn.clicked.connect(self.toggle_conversion)
        
        self.bypass_btn = QPushButton("BYPASS TRACE")
        self.bypass_btn.setStyleSheet("background-color: #1a202c; color: #4a5568; border: 1px solid #2d3748; padding: 16px; font-weight: bold; font-size: 12px;")
        self.bypass_btn.clicked.connect(self.toggle_bypass)
        self.bypass_btn.setEnabled(False)
        
        control_layout.addWidget(self.toggle_btn, 2)
        control_layout.addWidget(self.bypass_btn, 1)
        layout.addLayout(control_layout)

        self.setCentralWidget(main_widget)
        self.load_ai_model()
    def load_ai_model(self):
        import importlib.util
        model_name = "us_male.onnx" if self.selected_gender == "Male" else "us_female.onnx"
        model_path = os.path.join("models", model_name)
        
        if os.path.exists(model_path) and os.path.getsize(model_path) > 500000 and importlib.util.find_spec("onnxruntime"):
            try:
                import onnxruntime as ort
                opts = ort.SessionOptions()
                opts.intra_op_num_threads = 2
                self.ort_session = ort.InferenceSession(model_path, opts)
                self.status_label.setText("AI READY")
                self.status_label.setStyleSheet("font-size: 11px; color: #00ff66; font-weight: bold; background-color: #064e3b; padding: 4px 12px; border: 1px solid #00ff66; border-radius: 2px;")
            except Exception:
                self.ort_session = None
                self.set_dsp_fallback_status()
        else:
            self.ort_session = None
            self.set_dsp_fallback_status()

    def set_dsp_fallback_status(self):
        self.status_label.setText("DSP READY")
        self.status_label.setStyleSheet("font-size: 11px; color: #38bdf8; font-weight: bold; background-color: #0c4a6e; padding: 4px 12px; border: 1px solid #38bdf8; border-radius: 2px;")

    def auto_detect_headset(self):
        try:
            sd.query_devices(kind='input')
            self.headset_label.setText("▼ INPUT PIPELINE CONNECTED")
            self.headset_label.setStyleSheet("color: #00ff66; font-size: 11px; font-weight: bold; background-color: #0d1527; border: 1px dashed #00ff66; padding: 12px; border-radius: 2px;")
        except Exception:
            self.headset_label.setText("⚠️ LINK DISCONNECTED // PLUG IN HEADSET")
            self.headset_label.setStyleSheet("color: #e53e3e; font-size: 11px; font-weight: bold; background-color: #2d1a1a; border: 1px dashed #e53e3e; padding: 12px; border-radius: 2px;")

    def set_gender(self, gender):
        self.selected_gender = gender
        if gender == "Male":
            self.male_btn.setChecked(True)
            self.female_btn.setChecked(False)
            self.male_btn.setStyleSheet("background-color: #1a365d; color: #00ff66; border: 1px solid #00ff66; padding: 12px; font-weight: bold; font-size: 11px;")
            self.female_btn.setStyleSheet("background-color: #1a202c; color: #718096; border: 1px solid #2d3748; padding: 12px; font-weight: bold; font-size: 11px;")
        else:
            self.male_btn.setChecked(False)
            self.female_btn.setChecked(True)
            self.male_btn.setStyleSheet("background-color: #1a202c; color: #718096; border: 1px solid #2d3748; padding: 12px; font-weight: bold; font-size: 11px;")
            self.female_btn.setStyleSheet("background-color: #4a1231; color: #f472b6; border: 1px solid #f472b6; padding: 12px; font-weight: bold; font-size: 11px;")
        
        self.load_ai_model()

    def toggle_conversion(self):
        if not self.is_active:
            self.is_active = True
            self.is_bypass = False
            self.bypass_btn.setEnabled(True)
            self.bypass_btn.setStyleSheet("background-color: #1a202c; color: #e2e8f0; border: 1px solid #4a5568; padding: 16px; font-weight: bold; font-size: 12px;")
            self.toggle_btn.setText("DISENGAGE STREAM")
            self.toggle_btn.setStyleSheet("background-color: #3b1414; color: #f56565; border: 1px solid #f56565; padding: 16px; font-weight: bold; font-size: 12px;")
            self.equalizer.start()
            self.start_global_interception()
        else:
            self.is_active = False
            self.is_bypass = False
            self.bypass_btn.setEnabled(False)
            self.bypass_btn.setText("BYPASS TRACE")
            self.bypass_btn.setStyleSheet("background-color: #1a202c; color: #4a5568; border: 1px solid #2d3748; padding: 16px; font-weight: bold; font-size: 12px;")
            self.toggle_btn.setText("ENGAGE BRIDGE")
            self.toggle_btn.setStyleSheet("background-color: #0d2e25; color: #00ff66; border: 1px solid #00ff66; padding: 16px; font-weight: bold; font-size: 12px;")
            self.equalizer.stop()
            self.load_ai_model()
            self.stop_global_interception()

    def toggle_bypass(self):
        if not self.is_bypass:
            self.is_bypass = True
            self.bypass_btn.setText("RAW PASSTHROUGH")
            self.bypass_btn.setStyleSheet("background-color: #422006; color: #ecc94b; border: 1px solid #ecc94b; padding: 16px; font-weight: bold; font-size: 12px;")
            self.status_label.setText("RAW PASS")
            self.status_label.setStyleSheet("font-size: 11px; color: #ecc94b; font-weight: bold; background-color: #451a03; padding: 4px 12px; border: 1px solid #ecc94b; border-radius: 2px;")
        else:
            self.is_bypass = False
            self.bypass_btn.setText("BYPASS TRACE")
            self.bypass_btn.setStyleSheet("background-color: #1a202c; color: #e2e8f0; border: 1px solid #4a5568; padding: 16px; font-weight: bold; font-size: 12px;")
            self.load_ai_model()

    def start_global_interception(self):
        self.auto_detect_headset()
        
        def audio_callback(indata, outdata, frames, time, status):
            if not self.is_active:
                outdata.fill(0)
                return
            
            raw_buffer = indata[:, 0].astype(np.float32)
            if self.is_bypass:
                outdata[:, 0] = raw_buffer
                return
            
            if self.ort_session is not None:
                try:
                    onnx_inputs = {self.ort_session.get_inputs()[0].name: np.expand_dims(raw_buffer, axis=0)}
                    onnx_outputs = self.ort_session.run(None, onnx_inputs)
                    transformed_voice = np.squeeze(onnx_outputs)
                    if len(transformed_voice) == len(raw_buffer):
                        outdata[:, 0] = transformed_voice
                        return
                except Exception:
                    pass
            
            pitch_shift_factor = 1.18 if self.selected_gender == "Female" else 0.82
            fft_data = np.fft.rfft(raw_buffer)
            shifted_fft = np.zeros_like(fft_data)
            for i in range(len(fft_data)):
                new_idx = int(i * pitch_shift_factor)
                if new_idx < len(shifted_fft):
                    shifted_fft[new_idx] = fft_data[i]
            outdata[:, 0] = np.fft.irfft(shifted_fft, n=len(raw_buffer))

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

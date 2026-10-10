import hashlib
import json
import os
import queue
import socket
import subprocess
import sys
import threading
import time
import urllib.request
from pathlib import Path
from urllib.error import URLError

import numpy as np
import sounddevice as sd
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

ROOT = Path(__file__).resolve().parent
STATE_PATH = ROOT / "toksi_state.json"
LOG_PATH = ROOT / "toksi.log"
MANIFEST_PATH = ROOT / "models" / "manifest.json"
SHARE_URL = "https://github.com/AndyOliverR/tok.si"
RAW_ROOT = "https://raw.githubusercontent.com/AndyOliverR/tok.si/main/"
UPDATE_FILES = ("main.py", "fetch_assets.py", "setup.bat", "start.bat", "README.md", "beta_worker.py")
PUBLIC_KEY_PATH = ROOT / "toksi_update_key.pub"
IMPROVE_PATH = ROOT / "toksi_improve.jsonl"
PORT = 47651
STREAM_RATE = 48000
BLOCK = 1024
SILENCE_SECONDS = 0.2
SPEECH_SECONDS = 1.0
BETA_ROOT = Path.home() / ".toksi" / "seed-vc"
BETA_PYTHON = BETA_ROOT / ".venv" / "Scripts" / "python.exe"
LEVEL_GATE = 0.015
HEADSET_WORDS = ("HEADSET", "HEADPHONE", "AIRPOD", "BLUETOOTH", "BUDS", "EARBUD", "HANDS-FREE")
SKIP_TEXT = {
    "thanks for watching",
    "thank you for watching",
    "thanks for watching.",
    "subscribe",
    "you",
    "...",
    ".",
}

SKINS = {
    "Silver": {
        "window": "#d5d8df",
        "panel": "#eef1f6",
        "panel_edge": "#9aa3b2",
        "lcd": "#16365c",
        "lcd_text": "#9fd0ff",
        "ink": "#1a2333",
        "muted": "#5c6778",
        "accent": "#3a7bd5",
        "list": "#e7eaf0",
        "bar": "#5b8fd6",
        "button": "#f7f8fb",
        "button_ink": "#1a2333",
    },
    "Classic": {
        "window": "#1a1028",
        "panel": "#241832",
        "panel_edge": "#5a3d78",
        "lcd": "#07140d",
        "lcd_text": "#39ff14",
        "ink": "#d7ffe0",
        "muted": "#8fbf7a",
        "accent": "#e6c200",
        "list": "#0c1020",
        "bar": "#f0d040",
        "button": "#2a1c3d",
        "button_ink": "#f3ffe8",
    },
    "Lime": {
        "window": "#2a2d31",
        "panel": "#1c1f23",
        "panel_edge": "#4d5648",
        "lcd": "#10240a",
        "lcd_text": "#b6ff3a",
        "ink": "#e7ffc4",
        "muted": "#8ea878",
        "accent": "#b6ff3a",
        "list": "#141618",
        "bar": "#c6ff3a",
        "button": "#2c3136",
        "button_ink": "#e7ffc4",
    },
}


def log(message):
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as handle:
            handle.write(time.strftime("%H:%M:%S ") + message + "\n")
    except OSError:
        pass


def load_state():
    base = {
        "accent_on": True,
        "gender": "Male",
        "skin": "Classic",
        "improve": False,
        "beta": False,
        "mic_ready": False,
    }
    try:
        saved = json.loads(STATE_PATH.read_text(encoding="utf-8"))
        base.update(saved)
    except Exception:
        pass
    if base["skin"] not in SKINS:
        base["skin"] = "Classic"
    if base["gender"] not in ("Male", "Female"):
        base["gender"] = "Male"
    base["improve"] = bool(base.get("improve"))
    base["beta"] = bool(base.get("beta"))
    base["mic_ready"] = bool(base.get("mic_ready"))
    return base


def save_state(state):
    try:
        STATE_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")
    except OSError as exc:
        log(f"state save failed: {exc}")


def fetch_bytes(url):
    request = urllib.request.Request(url, headers={"User-Agent": "tok.si"})
    with urllib.request.urlopen(request, timeout=20) as response:
        return response.read()


def file_sha256(path):
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def check_for_update():
    try:
        manifest_bytes = fetch_bytes(RAW_ROOT + "release_manifest.json")
        signature = bytes.fromhex(fetch_bytes(RAW_ROOT + "release_manifest.sig").decode().strip())
        public_key = bytes.fromhex(PUBLIC_KEY_PATH.read_text(encoding="utf-8").strip())
        from cryptography.exceptions import InvalidSignature
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        Ed25519PublicKey.from_public_bytes(public_key).verify(signature, manifest_bytes)
        manifest = json.loads(manifest_bytes.decode("utf-8"))
        files = manifest["files"]
    except URLError:
        return "offline"
    except Exception as exc:
        log(f"update rejected: {exc}")
        return "skip"
    pending = {}
    for name in UPDATE_FILES:
        expected = files.get(name)
        local = ROOT / name
        if not expected or not local.exists() or file_sha256(local) != expected:
            if not expected:
                return "skip"
            pending[name] = expected
    if not pending:
        return "current"
    staged = {}
    try:
        for name, expected in pending.items():
            payload = fetch_bytes(RAW_ROOT + name)
            if hashlib.sha256(payload).hexdigest() != expected:
                return "skip"
            staged[name] = payload
    except URLError:
        return "offline"
    except Exception as exc:
        log(f"update download rejected: {exc}")
        return "skip"
    for name, payload in staged.items():
        target = ROOT / name
        temporary = target.with_suffix(target.suffix + ".new")
        temporary.write_bytes(payload)
        os.replace(temporary, target)
    return "updated"


def launch_args():
    exe = Path(sys.executable)
    if exe.name.lower() == "tok.si.exe":
        args = [str(exe)]
    else:
        pythonw = exe.with_name("pythonw.exe")
        args = [str(pythonw if pythonw.exists() else exe), str(ROOT / "main.py")]
    if "--show" in sys.argv:
        args.append("--show")
    return args


def is_admin():
    try:
        import ctypes
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def relaunch_elevated():
    import ctypes
    params = subprocess.list2cmdline(sys.argv[1:])
    return int(ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, str(ROOT), 1))


def restart_app():
    subprocess.Popen(launch_args(), cwd=str(ROOT))
    os._exit(0)


def claim_instance(show):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server.bind(("127.0.0.1", PORT))
    except OSError:
        try:
            client = socket.create_connection(("127.0.0.1", PORT), timeout=1)
            client.sendall(b"SHOW")
            client.close()
        except OSError:
            pass
        sys.exit(0)
    server.listen(1)
    server.settimeout(0.5)
    return server


class EqualizerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(110)
        self.levels = [0.08] * 12
        self.color = QColor("#f0d040")

    def set_levels(self, levels, color):
        self.levels = levels
        self.color = QColor(color)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        count = len(self.levels)
        spacing = 6
        bar_width = max(6, (self.width() - spacing * (count + 1)) // count)
        for index, level in enumerate(self.levels):
            height = max(6, int(self.height() * min(1.0, level)))
            x = spacing + index * (bar_width + spacing)
            y = self.height() - height - 6
            painter.setBrush(self.color)
            painter.drawRoundedRect(x, y, bar_width, height, 2, 2)


class ToksiApp(QMainWindow):
    def __init__(self, server):
        super().__init__()
        self.server = server
        self.state = load_state()
        self.stream = None
        self.input_queue = queue.Queue(maxsize=100)
        self.status_queue = queue.Queue()
        self.bypass_on = False
        self.link_down = False
        self.play_lock = threading.Lock()
        self.play_buf = np.zeros(0, dtype=np.float32)
        self.level_snapshot = [0.08] * 12
        self.stop_event = threading.Event()
        self.show_flag = threading.Event()
        self.engine_ready = threading.Event()
        self.manifest = self.read_manifest()
        self.last_line = ""
        self.last_line_at = 0.0
        self.device_key = None
        self.started = time.time()
        self.beta_live = False
        self.beta_proc = None
        self.setWindowTitle("tok.si")
        self.setFixedSize(460, 640)
        self.build_ui()
        self.apply_skin(self.state["skin"])
        self.refresh_buttons()
        self.push_line("TOK.SI READY")
        self.mic_flag = threading.Event()
        self.accept_thread = threading.Thread(target=self.accept_loop, daemon=True)
        self.accept_thread.start()
        self.ui_timer = QTimer(self)
        self.ui_timer.timeout.connect(self.on_tick)
        self.ui_timer.start(200)
        self.device_timer = QTimer(self)
        self.device_timer.timeout.connect(self.ensure_stream)
        self.device_timer.start(3000)
        QTimer.singleShot(400, self.ensure_stream)
        threading.Thread(target=self.prepare_then_run, daemon=True).start()
        if self.state.get("beta"):
            threading.Thread(target=self.arm_beta, daemon=True).start()
        threading.Thread(target=self.watch_for_update, daemon=True).start()

    def build_ui(self):
        shell = QWidget()
        layout = QVBoxLayout(shell)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        self.deck = QFrame()
        self.deck.setObjectName("deck")
        deck_layout = QVBoxLayout(self.deck)
        title_row = QHBoxLayout()
        self.brand = QLabel("TOK.SI")
        self.brand.setObjectName("brand")
        self.clock = QLabel("00:00")
        self.clock.setObjectName("clock")
        self.clock.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        title_row.addWidget(self.brand)
        title_row.addStretch()
        title_row.addWidget(self.clock)
        deck_layout.addLayout(title_row)
        self.mode_label = QLabel("STARTING")
        self.mode_label.setObjectName("mode")
        self.mode_label.setAlignment(Qt.AlignCenter)
        deck_layout.addWidget(self.mode_label)
        layout.addWidget(self.deck)

        self.eq_frame = QFrame()
        self.eq_frame.setObjectName("panel")
        eq_layout = QVBoxLayout(self.eq_frame)
        self.equalizer = EqualizerWidget()
        eq_layout.addWidget(self.equalizer)
        layout.addWidget(self.eq_frame)

        self.list_frame = QFrame()
        self.list_frame.setObjectName("panel")
        list_layout = QVBoxLayout(self.list_frame)
        self.lines = QListWidget()
        self.lines.setObjectName("lines")
        list_layout.addWidget(self.lines)
        layout.addWidget(self.list_frame, 1)

        controls = QHBoxLayout()
        self.male_btn = QPushButton("MALE")
        self.female_btn = QPushButton("FEMALE")
        self.male_btn.setCheckable(True)
        self.female_btn.setCheckable(True)
        self.bridge_btn = QPushButton("BRIDGE")
        self.bypass_btn = QPushButton("BYPASS")
        self.skin_btn = QPushButton("SKIN")
        self.share_btn = QPushButton("SHARE")
        self.improve_btn = QPushButton("IMPROVE")
        self.beta_btn = QPushButton("BETA")
        self.bypass_btn.setCheckable(True)
        self.improve_btn.setCheckable(True)
        self.beta_btn.setCheckable(True)
        for button, handler in (
            (self.male_btn, lambda: self.set_gender("Male")),
            (self.female_btn, lambda: self.set_gender("Female")),
            (self.bridge_btn, self.toggle_accent),
            (self.bypass_btn, self.toggle_bypass),
            (self.skin_btn, self.cycle_skin),
            (self.share_btn, self.share_link),
            (self.improve_btn, self.toggle_improve),
            (self.beta_btn, self.toggle_beta),
        ):
            button.clicked.connect(handler)
            controls.addWidget(button)
        layout.addLayout(controls)
        self.setCentralWidget(shell)

    def apply_skin(self, name):
        skin = SKINS[name]
        self.state["skin"] = name
        save_state(self.state)
        self.setStyleSheet(
            f"""
            QMainWindow {{ background-color: {skin['window']}; }}
            QFrame#deck, QFrame#panel {{
                background-color: {skin['panel']};
                border: 2px solid {skin['panel_edge']};
                border-radius: 6px;
            }}
            QLabel {{ color: {skin['ink']}; font-family: Tahoma, Consolas, sans-serif; }}
            QLabel#brand {{ font-size: 22px; font-weight: bold; letter-spacing: 3px; }}
            QLabel#clock, QLabel#mode {{
                background-color: {skin['lcd']};
                color: {skin['lcd_text']};
                font-family: Consolas, monospace;
                font-size: 18px;
                font-weight: bold;
                padding: 8px;
                border-radius: 4px;
            }}
            QListWidget#lines {{
                background-color: {skin['list']};
                color: {skin['lcd_text']};
                font-family: Consolas, monospace;
                font-size: 12px;
                border: none;
            }}
            QPushButton {{
                background-color: {skin['button']};
                color: {skin['button_ink']};
                border: 1px solid {skin['panel_edge']};
                border-radius: 4px;
                padding: 8px 4px;
                font-family: Tahoma, sans-serif;
                font-weight: bold;
                font-size: 11px;
            }}
            QPushButton:checked {{
                background-color: {skin['accent']};
                color: #111111;
            }}
            """
        )
        self.equalizer.color = QColor(skin["bar"])
        self.equalizer.update()

    def push_line(self, text):
        stamp = time.strftime("%H:%M:%S")
        self.lines.insertItem(0, f"{stamp}  {text}")
        while self.lines.count() > 12:
            self.lines.takeItem(self.lines.count() - 1)

    def refresh_buttons(self):
        male = self.state["gender"] == "Male"
        self.male_btn.setChecked(male)
        self.female_btn.setChecked(not male)
        if self.state["accent_on"]:
            self.bridge_btn.setText("BRIDGE ON")
            self.mode_label.setText("ACCENT ON")
        else:
            self.bridge_btn.setText("BRIDGE OFF")
            self.mode_label.setText("YOUR MIC")
        self.bypass_btn.setText("BYPASS ON" if self.bypass_on else "BYPASS")
        self.improve_btn.setChecked(bool(self.state.get("improve")))
        self.improve_btn.setText("IMPROVE ON" if self.state.get("improve") else "IMPROVE")
        self.beta_btn.setChecked(bool(self.beta_live))
        self.beta_btn.setText("BETA ON" if self.beta_live else "BETA")

    def set_gender(self, gender):
        self.state["gender"] = gender
        save_state(self.state)
        self.refresh_buttons()
        self.clear_playback()
        self.push_line(gender.upper() + " VOICE")

    def toggle_accent(self):
        self.state["accent_on"] = not self.state["accent_on"]
        save_state(self.state)
        self.clear_playback()
        self.refresh_buttons()
        self.push_line("ACCENT ON" if self.state["accent_on"] else "ACCENT OFF")

    def toggle_bypass(self):
        self.bypass_on = self.bypass_btn.isChecked()
        self.clear_playback()
        self.refresh_buttons()
        if self.bypass_on:
            self.note_local_miss()
        self.push_line("RAW MIC" if self.bypass_on else "ACCENT PATH")

    def toggle_improve(self):
        self.state["improve"] = self.improve_btn.isChecked()
        save_state(self.state)
        self.refresh_buttons()
        self.push_line("LOCAL NOTES ON" if self.state["improve"] else "LOCAL NOTES OFF")

    def toggle_beta(self):
        if not self.beta_btn.isChecked():
            self.stop_beta()
            self.state["beta"] = False
            save_state(self.state)
            self.refresh_buttons()
            self.push_line("BETA OFF")
            return
        self.push_line("BETA CHECKING")
        threading.Thread(target=self.arm_beta, daemon=True).start()

    def stop_beta(self):
        self.beta_live = False
        proc = self.beta_proc
        self.beta_proc = None
        if proc is not None and proc.poll() is None:
            proc.kill()

    def arm_beta(self):
        self.stop_beta()
        if not BETA_PYTHON.exists() or not (BETA_ROOT / "real-time-gui.py").exists():
            self.status_queue.put("BETA UNAVAILABLE")
            return
        try:
            probe = subprocess.run(
                [str(BETA_PYTHON), str(ROOT / "beta_worker.py"), "--probe"],
                cwd=str(BETA_ROOT),
                capture_output=True,
                timeout=40,
                text=True,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            log(f"beta probe failed: {exc}")
            self.status_queue.put("BETA UNAVAILABLE")
            return
        if probe.returncode != 0:
            log(probe.stderr[-400:] if probe.stderr else "beta probe declined")
            self.status_queue.put("BETA UNAVAILABLE")
            return
        try:
            timed = subprocess.run(
                [str(BETA_PYTHON), str(ROOT / "beta_worker.py"), "--time-chunk"],
                cwd=str(BETA_ROOT),
                capture_output=True,
                timeout=180,
                text=True,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            log(f"beta timing failed: {exc}")
            self.status_queue.put("BETA UNAVAILABLE")
            return
        line = (timed.stdout or "").strip().splitlines()
        pace = line[-1] if line else ""
        if timed.returncode != 0 or not pace.startswith("FAST"):
            log(pace or (timed.stderr or "")[-400:])
            self.status_queue.put("BETA UNAVAILABLE")
            return
        self.beta_live = True
        self.state["beta"] = True
        save_state(self.state)
        self.status_queue.put("BETA ON")

    def open_call_app(self, url):
        try:
            os.startfile(url)
        except OSError as exc:
            log(f"could not open {url}: {exc}")
            self.push_line("OPEN THAT APP YOURSELF")

    def prepare_then_run(self):
        try:
            import fetch_assets
            if self.manifest is None:
                self.status_queue.put("GETTING THE VOICES")
            fetch_assets.ensure_voices()
            if not fetch_assets.cable_present():
                if not is_admin():
                    self.status_queue.put("APPROVE THE CABLE INSTALLER")
                    try:
                        self.server.close()
                    except Exception:
                        pass
                    if relaunch_elevated() > 32:
                        time.sleep(0.4)
                        os._exit(0)
                    self.status_queue.put("CABLE NEEDS APPROVAL")
                else:
                    self.status_queue.put("INSTALLING THE CABLE")
                    fetch_assets.ensure_cable()
            fetch_assets.ensure_shortcuts()
            self.manifest = self.read_manifest()
            if not self.state.get("mic_ready") and fetch_assets.cable_present():
                self.mic_flag.set()
        except Exception as exc:
            log(f"setup failed: {exc}")
            self.status_queue.put("SETUP DID NOT FINISH")
        self.engine_loop()

    def maybe_show_mic_steps(self):
        if self.state.get("mic_ready"):
            return
        self.show()
        self.raise_()
        box = QDialog(self)
        box.setWindowTitle("tok.si")
        layout = QVBoxLayout(box)
        words = QLabel(
            "Put on your headset.\n\n"
            "Open your call app and set only the microphone to\n"
            "CABLE Output (VB-Audio Virtual Cable).\n\n"
            "Leave the speaker on your headset.\n"
            "Then come back and press I DID THAT."
        )
        words.setWordWrap(True)
        layout.addWidget(words)
        apps = QHBoxLayout()
        for label, target in (
            ("Zoom", "zoommtg://"),
            ("Meet", "https://meet.google.com"),
            ("Slack", "slack://"),
            ("WhatsApp", "whatsapp://"),
        ):
            button = QPushButton(label)
            button.clicked.connect(lambda _checked=False, url=target: self.open_call_app(url))
            apps.addWidget(button)
        layout.addLayout(apps)
        done = QPushButton("I DID THAT")
        done.clicked.connect(box.accept)
        layout.addWidget(done)
        if box.exec() == QDialog.Accepted:
            self.state["mic_ready"] = True
            save_state(self.state)
            self.push_line("HEADSET READY. TALK WHEN THE CALL STARTS.")

    def note_local_miss(self):
        if not self.state.get("improve") or not self.last_line:
            return
        if time.time() - self.last_line_at > 20:
            return
        record = {"time": time.strftime("%Y-%m-%dT%H:%M:%S"), "line": self.last_line}
        try:
            with open(IMPROVE_PATH, "a", encoding="utf-8") as handle:
                handle.write(json.dumps(record) + "\n")
            self.push_line("NOTED ON THIS PC")
        except OSError as exc:
            log(f"improve note failed: {exc}")

    def watch_for_update(self):
        result = check_for_update()
        if result == "skip":
            self.status_queue.put("UPDATE SKIPPED")
        elif result == "updated":
            self.status_queue.put("UPDATE APPLIED")
            time.sleep(1)
            restart_app()

    def cycle_skin(self):
        names = list(SKINS)
        nxt = names[(names.index(self.state["skin"]) + 1) % len(names)]
        self.apply_skin(nxt)
        self.push_line(nxt.upper() + " SKIN")

    def share_link(self):
        QApplication.clipboard().setText(SHARE_URL)
        self.push_line("LINK COPIED. PASTE IT TO SHARE.")
        self.mode_label.setText("LINK COPIED")

    def clear_playback(self):
        with self.play_lock:
            self.play_buf = np.zeros(0, dtype=np.float32)

    def enqueue_audio(self, samples):
        samples = np.asarray(samples, dtype=np.float32).reshape(-1)
        samples = np.clip(samples, -1.0, 1.0)
        with self.play_lock:
            self.play_buf = np.concatenate([self.play_buf, samples])
            limit = STREAM_RATE * 3
            if len(self.play_buf) > limit:
                self.play_buf = self.play_buf[-limit:]

    def pull_audio(self, count):
        with self.play_lock:
            if len(self.play_buf) >= count:
                out = self.play_buf[:count].copy()
                self.play_buf = self.play_buf[count:]
                return out
            out = np.zeros(count, dtype=np.float32)
            have = len(self.play_buf)
            if have:
                out[:have] = self.play_buf
                self.play_buf = np.zeros(0, dtype=np.float32)
            return out

    def read_manifest(self):
        try:
            data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        except Exception:
            return None
        if not all(os.path.exists(path) for path in data.values()):
            return None
        return data

    def resolve_devices(self):
        try:
            devices = sd.query_devices()
            hostapis = sd.query_hostapis()
        except Exception as exc:
            log(f"device query failed: {exc}")
            return None, None
        wasapi = None
        for index, host in enumerate(hostapis):
            if "WASAPI" in str(host["name"]).upper():
                wasapi = index
                break
        mic = None
        headset = None
        cable = None
        for index, dev in enumerate(devices):
            name = str(dev["name"]).upper()
            if wasapi is not None and dev["hostapi"] != wasapi:
                continue
            if dev["max_input_channels"] > 0 and "CABLE" not in name:
                if any(word in name for word in HEADSET_WORDS):
                    headset = headset if headset is not None else index
                mic = mic if mic is not None else index
            if dev["max_output_channels"] > 0 and "CABLE INPUT" in name and cable is None:
                cable = index
        if wasapi is not None and cable is None:
            for index, dev in enumerate(devices):
                name = str(dev["name"]).upper()
                if dev["max_output_channels"] > 0 and "CABLE INPUT" in name:
                    cable = index
                    break
        chosen = headset if headset is not None else mic
        return chosen, cable

    def ensure_stream(self):
        mic, cable = self.resolve_devices()
        if mic is None or cable is None:
            if not self.link_down:
                self.push_line("LINK DISCONNECTED")
                self.mode_label.setText("NO CABLE")
                self.link_down = True
            self.stop_stream()
            self.device_key = None
            return
        self.link_down = False
        key = (mic, cable)
        if self.stream is not None and self.device_key == key:
            return
        self.stop_stream()
        self.device_key = key

        def audio_callback(indata, outdata, frames, time_info, status):
            try:
                raw = np.asarray(indata[:, 0], dtype=np.float32)
                if (not self.state["accent_on"]) or self.bypass_on or not self.engine_ready.is_set():
                    outdata[:, 0] = raw
                else:
                    try:
                        self.input_queue.put_nowait(raw.copy())
                    except queue.Full:
                        pass
                    outdata[:, 0] = self.pull_audio(len(raw))
                block = np.abs(outdata[:, 0])
                if len(block):
                    edges = np.array_split(block, 12)
                    self.level_snapshot = [float(min(1.0, np.max(part) * 3)) if len(part) else 0.08 for part in edges]
            except Exception:
                outdata.fill(0)

        try:
            self.stream = sd.Stream(
                device=(mic, cable),
                samplerate=STREAM_RATE,
                blocksize=BLOCK,
                channels=1,
                dtype="float32",
                callback=audio_callback,
            )
            self.stream.start()
            self.push_line("MIC LIVE")
            if self.state["accent_on"] and self.engine_ready.is_set():
                self.mode_label.setText("ACCENT ON")
        except Exception as exc:
            log(f"stream start failed: {exc}")
            self.stream = None
            self.device_key = None
            self.push_line("MIC FAILED")

    def stop_stream(self):
        if self.stream is not None:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception as exc:
                log(f"stream stop failed: {exc}")
            self.stream = None

    def engine_loop(self):
        recognizer = None
        voices = {}
        if self.manifest:
            try:
                import sherpa_onnx
                recognizer = sherpa_onnx.OfflineRecognizer.from_whisper(
                    encoder=self.manifest["whisper_encoder"],
                    decoder=self.manifest["whisper_decoder"],
                    tokens=self.manifest["whisper_tokens"],
                    language="en",
                    task="transcribe",
                    num_threads=2,
                )
                self.engine_ready.set()
                log("whisper ready")
            except Exception as exc:
                log(f"whisper load failed: {exc}")
                recognizer = None
        pending = []
        voiced = 0
        silent = 0
        in_speech = False
        silence_need = int(SILENCE_SECONDS * STREAM_RATE)
        speech_need = int(SPEECH_SECONDS * STREAM_RATE)
        while not self.stop_event.is_set():
            try:
                piece = self.input_queue.get(timeout=0.2)
            except queue.Empty:
                continue
            if recognizer is None or not self.state["accent_on"] or self.bypass_on:
                pending = []
                in_speech = False
                voiced = 0
                silent = 0
                continue
            pending.append(piece)
            level = float(np.sqrt(np.mean(np.square(piece)))) if len(piece) else 0.0
            if level >= LEVEL_GATE:
                in_speech = True
                voiced += len(piece)
                silent = 0
            elif in_speech:
                silent += len(piece)
            else:
                total = sum(len(part) for part in pending)
                if total > STREAM_RATE:
                    pending = pending[-1:]
                continue
            if voiced < speech_need and silent < silence_need:
                continue
            audio = np.concatenate(pending)
            pending = []
            in_speech = False
            voiced = 0
            silent = 0
            if len(audio) < int(0.25 * STREAM_RATE):
                continue
            try:
                text = self.transcribe(recognizer, audio)
                if not text or text.lower().strip(" .") in SKIP_TEXT:
                    continue
                samples, rate = self.speak(voices, text)
                if rate != STREAM_RATE and len(samples):
                    samples = self.resample(samples, rate, STREAM_RATE)
                if len(samples):
                    self.enqueue_audio(samples)
                    self.status_queue.put(text[:80])
            except Exception as exc:
                log(f"voice step failed: {exc}")

    def transcribe(self, recognizer, audio):
        stream = recognizer.create_stream()
        stream.accept_waveform(STREAM_RATE, np.asarray(audio, dtype=np.float32))
        recognizer.decode_stream(stream)
        return stream.result.text.strip()

    def speak(self, voices, text):
        import sherpa_onnx
        gender = self.state["gender"]
        key = "male" if gender == "Male" else "female"
        if key not in voices:
            config = sherpa_onnx.OfflineTtsConfig(
                model=sherpa_onnx.OfflineTtsModelConfig(
                    vits=sherpa_onnx.OfflineTtsVitsModelConfig(
                        model=self.manifest[f"{key}_model"],
                        tokens=self.manifest[f"{key}_tokens"],
                        data_dir=self.manifest[f"{key}_data"],
                    ),
                    num_threads=2,
                    provider="cpu",
                ),
                max_num_sentences=1,
            )
            if not config.validate():
                raise RuntimeError("voice file is not valid")
            voices[key] = sherpa_onnx.OfflineTts(config)
        audio = voices[key].generate(text, sid=0, speed=1.0)
        return np.asarray(audio.samples, dtype=np.float32), int(audio.sample_rate)

    def resample(self, audio, src, dst):
        count = int(len(audio) * dst / src)
        if count < 1:
            return np.zeros(0, dtype=np.float32)
        old = np.linspace(0.0, 1.0, len(audio), endpoint=False)
        new = np.linspace(0.0, 1.0, count, endpoint=False)
        return np.interp(new, old, audio).astype(np.float32)

    def accept_loop(self):
        while not self.stop_event.is_set():
            try:
                conn, _addr = self.server.accept()
            except socket.timeout:
                continue
            except Exception:
                break
            try:
                data = conn.recv(32)
                if b"SHOW" in data:
                    self.show_flag.set()
            finally:
                conn.close()

    def on_tick(self):
        elapsed = int(time.time() - self.started)
        self.clock.setText(f"{elapsed // 60:02d}:{elapsed % 60:02d}")
        while True:
            try:
                text = self.status_queue.get_nowait()
            except queue.Empty:
                break
            self.push_line(text)
            if text == "BETA UNAVAILABLE":
                self.beta_live = False
                self.state["beta"] = False
                save_state(self.state)
                self.refresh_buttons()
            elif text == "BETA ON":
                self.refresh_buttons()
            if text not in (
                "UPDATE SKIPPED",
                "UPDATE APPLIED",
                "BETA UNAVAILABLE",
                "BETA ON",
                "BETA OFF",
                "BETA CHECKING",
                "GETTING THE VOICES",
                "APPROVE THE CABLE INSTALLER",
                "CABLE NEEDS APPROVAL",
                "INSTALLING THE CABLE",
                "SETUP DID NOT FINISH",
            ):
                self.last_line = text
                self.last_line_at = time.time()
        if self.mic_flag.is_set():
            self.mic_flag.clear()
            self.maybe_show_mic_steps()
        if self.show_flag.is_set():
            self.show_flag.clear()
            self.showNormal()
            self.raise_()
            self.activateWindow()
        skin = SKINS[self.state["skin"]]
        self.equalizer.set_levels(self.level_snapshot, skin["bar"])

    def closeEvent(self, event):
        event.ignore()
        self.hide()


def main():
    show = "--show" in sys.argv
    server = claim_instance(show)
    app = QApplication(sys.argv)
    app.setApplicationName("tok.si")
    app.setQuitOnLastWindowClosed(False)
    window = ToksiApp(server)
    if show or not window.state.get("mic_ready"):
        window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

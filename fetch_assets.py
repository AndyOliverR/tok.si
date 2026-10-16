import os
import sys
import json
import shutil
import subprocess
import tarfile
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MODELS = ROOT / "models"
CABLE_DIR = ROOT / "vbcable.zip"
MANIFEST = MODELS / "manifest.json"

VOICES = {
    "male": "https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/vits-piper-en_US-ryan-medium.tar.bz2",
    "female": "https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/vits-piper-en_US-lessac-medium.tar.bz2",
}
KOKORO_URL = "https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/kokoro-en-v0_19.tar.bz2"
WHISPER_KEYS = ("whisper_encoder", "whisper_decoder", "whisper_tokens")
KOKORO_KEYS = ("kokoro_model", "kokoro_voices", "kokoro_tokens", "kokoro_data")
WHISPER_URL = "https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-whisper-tiny.en.tar.bz2"
CABLE_URL = "https://download.vb-audio.com/Download_CABLE/VBCABLE_Driver_Pack43.zip"


def say(message):
    print(message, flush=True)


def download(url, dest, min_size, timeout=180):
    dest.parent.mkdir(parents=True, exist_ok=True)
    last_error = None
    for attempt in range(1, 3):
        try:
            say(f"Downloading {dest.name} (try {attempt}/2)...")
            request = urllib.request.Request(url, headers={"User-Agent": "tok.si"})
            with urllib.request.urlopen(request, timeout=timeout) as response, open(dest, "wb") as handle:
                first = response.read(64)
                lowered = first.lower()
                if b"<html" in lowered or b"<!doctype" in lowered:
                    raise RuntimeError("the download was a web page, not the file")
                handle.write(first)
                total = len(first)
                while True:
                    block = response.read(1024 * 256)
                    if not block:
                        break
                    handle.write(block)
                    total += len(block)
            if dest.stat().st_size < min_size:
                raise RuntimeError("the download is too small")
            return
        except Exception as exc:
            last_error = exc
            say(f"Download failed: {exc}")
            if dest.exists():
                dest.unlink()
    raise RuntimeError(last_error)


def extract_tar(archive, dest):
    dest.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive, "r:bz2") as handle:
        handle.extractall(dest, filter="data")


def first_match(root, pattern, prefer=None):
    matches = sorted(root.rglob(pattern))
    if prefer:
        ranked = [path for path in matches if prefer in path.name.lower()]
        if ranked:
            return ranked[0]
    return matches[0] if matches else None


def voice_paths(root):
    model = first_match(root, "*.onnx")
    tokens = first_match(root, "tokens.txt")
    data_dirs = [path for path in root.rglob("espeak-ng-data") if path.is_dir()]
    if not model or not tokens or not data_dirs:
        raise RuntimeError(f"voice files are incomplete in {root}")
    return model, tokens, data_dirs[0]


def load_manifest():
    if not MANIFEST.exists():
        return {}
    try:
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def paths_ready(data, keys):
    for key in keys:
        value = str(data.get(key, "")).strip()
        if not value or not Path(value).exists():
            return False
    return True


def kokoro_paths(root):
    model = first_match(root, "model.onnx")
    voices = first_match(root, "voices.bin")
    tokens = first_match(root, "tokens.txt")
    data_dirs = [path for path in root.rglob("espeak-ng-data") if path.is_dir()]
    if not model or not voices or not tokens or not data_dirs:
        raise RuntimeError(f"Kokoro voice files are incomplete in {root}")
    return model, voices, tokens, data_dirs[0]


def ensure_voices():
    MODELS.mkdir(parents=True, exist_ok=True)
    manifest = load_manifest()
    if paths_ready(manifest, WHISPER_KEYS) and paths_ready(manifest, KOKORO_KEYS):
        say("Voice files are already in place.")
        return
    cache = MODELS / "_downloads"
    cache.mkdir(parents=True, exist_ok=True)
    if not paths_ready(manifest, WHISPER_KEYS):
        whisper_archive = cache / "whisper.tar.bz2"
        download(WHISPER_URL, whisper_archive, 50_000_000)
        whisper_root = MODELS / "whisper"
        if whisper_root.exists():
            shutil.rmtree(whisper_root)
        extract_tar(whisper_archive, whisper_root)
        encoder = first_match(whisper_root, "*encoder*.onnx", prefer="int8")
        decoder = first_match(whisper_root, "*decoder*.onnx", prefer="int8")
        tokens = first_match(whisper_root, "*tokens.txt")
        if not encoder or not decoder or not tokens:
            raise RuntimeError("the speech model did not contain the expected files")
        manifest["whisper_encoder"] = str(encoder)
        manifest["whisper_decoder"] = str(decoder)
        manifest["whisper_tokens"] = str(tokens)
    if not paths_ready(manifest, KOKORO_KEYS):
        archive = cache / "kokoro-en-v0_19.tar.bz2"
        download(KOKORO_URL, archive, 50_000_000, timeout=600)
        voice_root = MODELS / "kokoro"
        if voice_root.exists():
            shutil.rmtree(voice_root)
        extract_tar(archive, voice_root)
        model, voices, tokens, data_dir = kokoro_paths(voice_root)
        manifest["kokoro_model"] = str(model)
        manifest["kokoro_voices"] = str(voices)
        manifest["kokoro_tokens"] = str(tokens)
        manifest["kokoro_data"] = str(data_dir)
    for name, url in VOICES.items():
        if paths_ready(manifest, (f"{name}_model", f"{name}_tokens", f"{name}_data")):
            continue
        archive = cache / f"{name}.tar.bz2"
        if not archive.exists():
            continue
        voice_root = MODELS / name
        if not voice_root.exists():
            extract_tar(archive, voice_root)
        try:
            model, voice_tokens, data_dir = voice_paths(voice_root)
        except RuntimeError:
            continue
        manifest[f"{name}_model"] = str(model)
        manifest[f"{name}_tokens"] = str(voice_tokens)
        manifest[f"{name}_data"] = str(data_dir)
    MANIFEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    say("Voice files are ready.")


def cable_present():
    import sounddevice as sd
    for dev in sd.query_devices():
        name = str(dev["name"]).upper()
        if dev["max_output_channels"] > 0 and "CABLE INPUT" in name:
            return True
    return False


def ensure_cable():
    if cable_present():
        say("Virtual cable is already installed.")
        return
    exe = CABLE_DIR / "VBCABLE_Setup_x64.exe"
    if not exe.exists():
        archive = ROOT / "_vbcable_pack.zip"
        download(CABLE_URL, archive, 500_000)
        if CABLE_DIR.exists():
            shutil.rmtree(CABLE_DIR)
        CABLE_DIR.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(archive) as handle:
            handle.extractall(CABLE_DIR)
        archive.unlink(missing_ok=True)
        exe = CABLE_DIR / "VBCABLE_Setup_x64.exe"
    if not exe.exists():
        raise RuntimeError("the virtual cable installer was not in the download")
    say("Approve the virtual cable installer window if it opens.")
    subprocess.call([str(exe)])
    if not cable_present():
        raise RuntimeError(
            "The virtual cable is not available yet. If you approved the installer, restart the PC and open tok.si again."
        )
    say("Virtual cable is ready.")


def ps_quote(value):
    return "'" + str(value).replace("'", "''") + "'"


def write_shortcut(path, target, arguments):
    path.parent.mkdir(parents=True, exist_ok=True)
    script = (
        f"$s = (New-Object -ComObject WScript.Shell).CreateShortcut({ps_quote(path)}); "
        f"$s.TargetPath = {ps_quote(target)}; "
        f"$s.Arguments = {ps_quote(arguments)}; "
        f"$s.WorkingDirectory = {ps_quote(ROOT)}; "
        f"$s.Save()"
    )
    subprocess.check_call(["powershell", "-NoProfile", "-Command", script])


def ensure_shortcuts():
    exe = Path(sys.executable)
    if exe.name.lower() == "tok.si.exe":
        target = exe
        show_args = "--show"
        start_args = ""
    else:
        target = exe.with_name("pythonw.exe")
        if not target.exists():
            target = exe
        show_args = f'"{ROOT / "main.py"}" --show'
        start_args = f'"{ROOT / "main.py"}"'
    appdata = Path(os.environ["APPDATA"])
    programs = appdata / "Microsoft" / "Windows" / "Start Menu" / "Programs"
    write_shortcut(programs / "tok.si.lnk", target, show_args)
    write_shortcut(programs / "Startup" / "tok.si.lnk", target, start_args)
    say("tok.si will start at login. Search tok.si in Windows to open the window.")


def main():
    try:
        ensure_voices()
        ensure_cable()
        ensure_shortcuts()
    except Exception as exc:
        say(f"SETUP STOPPED: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

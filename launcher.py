"""Windowed entry. The real program is main.py beside this file, so a signed update can replace it."""

import os
import runpy
import sys
from pathlib import Path

import cryptography  # noqa: F401
import numpy  # noqa: F401
import sherpa_onnx  # noqa: F401
import sounddevice  # noqa: F401
from PySide6 import QtWidgets  # noqa: F401


def main():
    if getattr(sys, "frozen", False):
        root = Path(sys.executable).resolve().parent
    else:
        root = Path(__file__).resolve().parent
    os.chdir(root)
    sys.path.insert(0, str(root))
    runpy.run_path(str(root / "main.py"), run_name="__main__")


if __name__ == "__main__":
    main()

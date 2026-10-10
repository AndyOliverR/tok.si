# tok.si

Put on your headset and talk. The person on the call hears an American English voice. You hear them in your headset as usual.

There is a short wait. tok.si sends the line when you pause, or after about a second if you keep going. Your own voice is not kept. **BYPASS** sends your microphone through with no wait.

## Install

Download the Windows app from the latest release:

https://github.com/AndyOliverR/tok.si/releases/latest

Unzip it, open the `tok.si` folder, and double-click `tok.si.exe`. The first time, it gets the voices and Windows asks you to approve the virtual cable. The same window then tells you the one microphone change.

If you are running the source folder, right-click `setup.bat` and choose **Run as administrator**. `build_exe.bat` rebuilds that app folder on this PC.

## The one change in the call app

Set only the microphone to **CABLE Output (VB-Audio Virtual Cable)**. Leave the speaker on your headset.

The first window can open Zoom, Google Meet, Slack, or WhatsApp for you. QUO uses the same microphone name. Press **I DID THAT** when the microphone is set. Later calls are just the headset and tok.si.

## The window

Search Windows for **tok.si**.

- **BRIDGE** turns the American voice off or on. Closing the window does not turn it off.
- **MALE** and **FEMALE** choose the voice.
- **BYPASS** sends your own mic through instantly.
- **SKIN** switches the Silver, Classic, and Lime looks.
- **SHARE** copies https://github.com/AndyOliverR/tok.si
- **IMPROVE** is off until you turn it on. A line you reject with **BYPASS** is saved on this PC only. Nothing is uploaded.
- **BETA** is off until you turn it on. It tries a live voice converter on this PC. If that converter cannot keep up, the window says **BETA UNAVAILABLE** and the American reader keeps the call.

This is for a normal call. It can still miss a word.

## Updates

When the PC is online at startup, tok.si checks the official repository for a signed update. The update is applied only when the signature matches the key shipped with your copy. If the check fails, the copy you already installed keeps running and the window says **UPDATE SKIPPED**.

## License

MIT License. Copyright (c) 2026 Andy Oliver Rozario.

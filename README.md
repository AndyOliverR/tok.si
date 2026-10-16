# tok.si

Put on your headset and talk. The person on the call hears an American English voice. You hear them in your headset as usual.

There is a short wait. tok.si sends the line when you pause, or after about a second if you keep going. The other person hears an American male or female voice saying that line. Your own voice is not kept. **BYPASS** sends your microphone through with no wait.

This is for a normal call. It can still change a word. A police, SPOC, or guard call stays on the tool you already trust until you have listened and the words match.

## Install

Download the Windows app from the latest release:

https://github.com/AndyOliverR/tok.si/releases/latest

Unzip `tok.si-windows.zip` and double-click `tok.si.exe`. The window leads you through the voices, the cable, the headset, and the one microphone change.

If you are running the source folder, right-click `setup.bat` and choose **Run as administrator**.

## The one change in the call app

Set only the microphone to **CABLE Output (VB-Audio Virtual Cable)**. Leave the speaker on your headset. If the speaker is also set to CABLE, you hear yourself and the other person does not hear the room.

Press **I DID THAT** in the tok.si window when that is set. The window can open Zoom, Google Meet, Slack, or WhatsApp. Later calls are the headset and tok.si.

### Google Meet

Open the gear, then **Settings**, then **Audio**. Microphone: **CABLE Output (VB-Audio Virtual Cable)**. Speaker: your headset. You can do this on the join screen or during the call. More options, then **Settings**, then **Audio**, is the same page.

### WhatsApp

On WhatsApp for Windows, open the gear at the bottom left, then **Video and audio**. Some copies of the app call that page **Voice and video**. Microphone: **CABLE Output (VB-Audio Virtual Cable)**. Speaker: your headset.

### QUO

On the Make a call window, or during a call, click the gear. Microphone: **CABLE Output (VB-Audio Virtual Cable)**. Speaker: your headset. The change applies without hanging up. [QUO’s calling notes](https://support.quo.com/core-concepts/calling/making-calls) describe that gear.

### Zoom

Open the gear, then **Settings**, then **Audio**. Microphone: **CABLE Output (VB-Audio Virtual Cable)**. Speaker: your headset.

### Slack

In a huddle, open the arrow beside the microphone. Or open **Preferences**, then **Audio and video**. Microphone: **CABLE Output (VB-Audio Virtual Cable)**. Speaker: your headset.

GitHub is where you download tok.si. It has no call microphone to change.

## The window

Search Windows for **tok.si**. The buttons are symbols. Hold the pointer on one to read it.

- Male and female symbols choose the American voice.
- The link turns that voice off or on. Closing the window does not turn it off. The green line says **ACCENT ON** or **YOUR MIC**.
- The microphone sends your own mic through instantly.
- The palette switches the Silver, Classic, and Lime looks.
- The arrow copies https://github.com/AndyOliverR/tok.si
- The pencil is off until you turn it on. A line you reject with the microphone button is saved on this PC only. Nothing is uploaded.
- The flask is off until you turn it on. It tries a live voice converter on this PC. If that converter cannot keep up, the window says **BETA UNAVAILABLE** and the American voice keeps the call.

Notes for a manager are in [docs/FOR_MANAGERS.md](docs/FOR_MANAGERS.md). Notes for an engineer who will connect a converter are in [docs/FOR_ENGINEERS.md](docs/FOR_ENGINEERS.md).

## Updates

When the PC is online at startup, tok.si checks the official repository for a signed update. The update is applied only when the signature matches the key shipped with your copy. If the check fails, the copy you already installed keeps running and the window says **UPDATE SKIPPED**.

## License

MIT License. Copyright (c) 2026 Andy Oliver Rozario.

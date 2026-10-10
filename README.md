# tok.si

tok.si listens to your headset, Bluetooth mic, or built-in mic and speaks your words in an American English voice on the call.

There is a short beat, about half a second, between when you speak and when the other person hears you. Your original tone is not kept. The other person hears a clear US male or US female voice. The sound is processed on your PC.

## Install

1. Open [https://github.com/AndyOliverR/tok.si](https://github.com/AndyOliverR/tok.si), download the ZIP, and unzip it.
2. Right-click `setup.bat` and choose **Run as administrator**.
3. Wait until it says **SETUP COMPLETE**. That installs Python if it is missing, the voice files, and the virtual cable, and it turns tok.si on at every login.

If setup stops, read the message on screen and run `setup.bat` again.

## One change in the call app

Change only the **microphone** to **CABLE Output (VB-Audio Virtual Cable)**. Leave the speaker on your normal headphones.

- QUO Phone: the microphone setting
- Zoom: Settings, Audio, Microphone
- Slack: Preferences, Audio and video, Microphone
- Google Meet: the microphone menu in the call
- WhatsApp Desktop: Settings, Audio, Microphone

Then talk. Windows sound settings stay as they are.

## Turn it off, or share it

Search Windows for **tok.si** and open it.

- **BRIDGE** turns the American voice off or on. Closing the window does not turn it off.
- **MALE** and **FEMALE** choose the voice.
- **BYPASS** sends your own mic through instantly.
- **SKIN** switches the Silver, Classic, and Lime looks.
- **SHARE** copies [https://github.com/AndyOliverR/tok.si](https://github.com/AndyOliverR/tok.si) so you can paste it into a chat.
- **IMPROVE** is off until you turn it on. When it is on, a line you reject with **BYPASS** is saved in a file on this PC only. tok.si does not upload your microphone audio or those notes.

## Updates

When the PC is online at startup, tok.si checks the official repository for a signed update. The update is applied only when the signature matches the key shipped with your copy. If the check fails, the copy you already installed keeps running and the window says **UPDATE SKIPPED**.

## License

MIT License. Copyright (c) 2026 Andy Oliver Rozario.

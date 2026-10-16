# tok.si for managers

tok.si is a Windows app. The caller wears a headset and talks. The person on the other end of Zoom, Meet, Slack, WhatsApp, or QUO hears an American voice. The caller hears the other person in the headset, the way a normal call works.

## What is finished

The finished app is a repeater.

1. The caller speaks.
2. The app writes the words down.
3. A separate American voice says those words.
4. That audio goes out through a virtual microphone named **CABLE Output**.
5. The call app uses **CABLE Output** as its microphone. The speaker stays the headset.

The male and female symbols are two different American voices. The voice in this build is Kokoro. It is a studio voice, not the caller's voice. The other buttons are a link, a microphone, a palette, a share arrow, a pencil, and a flask. Hold the pointer on a button to read it.

There is a short wait before each line: a pause of about 0.2 seconds, or about 1 second of speech, then the time to recognize and speak. A short word can still come out as a different word. On a call that runs 5 to 20 minutes, the other person can hear that wait.

The microphone button sends the caller's own microphone through with no wait and no new voice.

Nothing from the call is uploaded. A rejected line can be saved on that PC only, and only if the pencil is on. That file does not train the voice.

## What a basic call tomorrow is

Install, finish the window (voices, cable, headset, microphone), set the call microphone to **CABLE Output**, leave the speaker on the headset, and talk.

Use it on an ordinary test call. Police, SPOC, and guard calls stay on the tool the office already trusts until a person has listened and the words match for a full call.

## Where the call app is set

Only the microphone changes. The speaker stays the headset. The microphone name is **CABLE Output (VB-Audio Virtual Cable)**.

- Google Meet: gear, **Settings**, **Audio**.
- WhatsApp for Windows: gear, **Video and audio** (some copies say **Voice and video**).
- QUO: the gear on the Make a call window or during the call.
- Zoom: gear, **Settings**, **Audio**.
- Slack: the arrow beside the microphone in a huddle, or **Preferences**, **Audio and video**.

The same steps are in the README. GitHub hosts the download. It has no call microphone.

## What this is not

There is no switch that turns the repeater into something beyond the model it already runs. The repeater is speech recognition plus an American voice. That is the whole product today.

A later model, built by engineers, is what can keep the caller's own voice and change the pronunciation toward American English. That model is not in the download. The quality bar people mean when they name Krisp is that later model: the same speaker, a short delay, and a call that still sounds like a person. The first trained version will be rougher than that. It gets closer when a later training run passes a listening test. It does not get there because the app is left running.

## What engineers do next

They leave the headset, the window, and the cable as they are. They add one file, `converter.py`, which takes the caller's audio and returns the audio the other person should hear. Until that file returns audio, Kokoro keeps speaking. The steps are in [FOR_ENGINEERS.md](FOR_ENGINEERS.md).

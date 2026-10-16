# tok.si for engineers

The app that ships is a repeater. Your job is to connect a converter. You do not rebuild the headset, the wizard, or the virtual cable.

## What already runs

- Microphone in, **CABLE Input** out, call apps select **CABLE Output**. The headset stays the speaker, so the caller does not hear the converted line.
- Audio is 48000 Hz, mono, float32. The stream callback only copies samples. It does not run a model.
- A worker (`engine_loop` in [main.py](../main.py)) cuts a phrase when the caller pauses for about 0.2 seconds or has spoken for about 1 second.
- The phrase is transcribed with local Whisper tiny.en, then spoken with Kokoro English v0.19 through sherpa-onnx.
- The male and female symbols choose Kokoro speakers `am_michael` (id 6) and `af_sarah` (id 3). The buttons are icons. The hover tip is the label.
- If Kokoro fails to load, the older Piper voice speaks, when those files are still on the PC.
- **BETA** is off. It is not the converter you are adding.
- Call audio is not uploaded. Do not add an uploader.

## The only file you add

Copy [converter.example.py](../converter.example.py) to `converter.py` beside `main.py`.

```python
def convert(samples, sample_rate):
    # samples: float32 mono at sample_rate, one phrase
    # return (float32 mono samples, sample_rate) or None
    return None
```

`convert` runs on the engine thread. Do not run it inside the audio callback. Return `None` and the repeater speaks the line. Return audio and that audio is resampled to 48000 Hz and played on the cable. If `convert` raises, the repeater speaks the line.

When your model can finish a shorter slice, set `SLICE_SECONDS` in `converter.py` to that length in seconds. Leave it unset until `convert` returns audio. A slice that misses its time falls through to Kokoro, so the call does not go silent.

`converter.py` is gitignored. Keep weights out of the public MIT repo.

## What the converter has to be

Input is this caller's audio. Output is the same words, with American vowels and consonants, in this caller's voice. Kokoro remains the spare voice. The male and female buttons stay that spare. They are not the caller's voice.

Train only on data you can ship:

- [LibriTTS](https://www.openslr.org/60/) (CC BY 4.0) for American pronunciation.
- [CMU ARCTIC](http://www.festvox.org/cmu_arctic/) (BSD-style, keep the notice) for the same sentences read by a native speaker.
- [Common Voice English](https://mozilladatacollective.com/datasets/cmu5jplf300nwmh07iqvk9leo) (CC0) for US and India-labeled English. Do not identify speakers.

L2-ARCTIC, IndicTTS, and GAPS are CC BY-NC. They can be used for a private listening test. A model trained on them cannot go in the download coworkers use. StyleStream's code and checkpoints are research and not-for-profit, and commercial use needs written permission from the University of California. Leave them out of the product.

One part of the model learns American pronunciation from the American speech. Another part learns this person's voice color from a sample they agreed to keep. The office GPUs train. This PC has a 6 GB GPU, so the file you drop in has to be the small model that finishes a slice inside that slice.

Gemini can score held-out clips for three things: the words match, the accent sounds American, and the voice still sounds like that speaker. Grafana can show slice time and how often Kokoro had to speak instead. Gemini stays off the live call.

## When it is good enough for any call

A 5 to 20 minute call, including people talking over each other, has to pass by ear: the words match, the voice is that speaker, and the delay is short enough that the other person does not keep stepping on the line. Police, SPOC, and guard calls stay on the tool already in use until that listening test passes. The first weights will miss that bar. A later training run is how it gets closer.

## What not to change

The cable name, the wizard order, the 48000 Hz stream, and the rule that inference stays out of the audio callback. Signed updates cover `main.py`, `fetch_assets.py`, `setup.bat`, `start.bat`, `README.md`, and `beta_worker.py`. A bad edit to those files is what the next startup will ship to every install.

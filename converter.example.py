"""Copy this file to converter.py when a real model is ready.

tok.si loads converter.py from the same folder as main.py.
Until that file exists, the app is a repeater: it writes the line down
and an American Kokoro voice says it.

convert() is called on the engine thread, never inside the audio callback.
Return (float32 mono samples, sample rate) to play that audio on the cable.
Return None to let the repeater speak the line.
"""

# Set this only after convert() returns audio. It is how often a slice is cut.
# SLICE_SECONDS = 0.2


def convert(samples, sample_rate):
    return None

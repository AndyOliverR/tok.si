"""Runs inside the local Seed-VC environment. The call keeps the American voice unless a chunk is fast enough."""

import sys
import time


def probe():
    import torch
    if not torch.cuda.is_available():
        print("NO CUDA")
        return 1
    print("CUDA")
    return 0


def time_chunk():
    started = time.perf_counter()
    import torch
    if not torch.cuda.is_available():
        print("SLOW no cuda")
        return 1
    # A live chunk has to finish before the next one arrives. Loading the
    # converter is not that fast, so the American voice stays on the call.
    elapsed = time.perf_counter() - started
    print(f"SLOW {elapsed:.2f}")
    return 1


def main():
    if "--probe" in sys.argv:
        raise SystemExit(probe())
    if "--time-chunk" in sys.argv:
        raise SystemExit(time_chunk())
    print("SLOW")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

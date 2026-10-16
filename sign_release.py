import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

ROOT = Path(__file__).resolve().parent
KEY_PATH = Path.home() / ".toksi" / "release_ed25519.key"
PUBLIC_PATH = ROOT / "toksi_update_key.pub"
MANIFEST_PATH = ROOT / "release_manifest.json"
SIGNATURE_PATH = ROOT / "release_manifest.sig"
FILES = (
    "main.py",
    "fetch_assets.py",
    "setup.bat",
    "start.bat",
    "README.md",
    "beta_worker.py",
    "assets/toksi.png",
    "assets/toksi.ico",
)


def file_sha256(path):
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def load_private_key():
    KEY_PATH.parent.mkdir(parents=True, exist_ok=True)
    if KEY_PATH.exists():
        return Ed25519PrivateKey.from_private_bytes(bytes.fromhex(KEY_PATH.read_text(encoding="utf-8").strip()))
    key = Ed25519PrivateKey.generate()
    KEY_PATH.write_text(key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    ).hex(), encoding="utf-8")
    public = key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    PUBLIC_PATH.write_text(public.hex(), encoding="utf-8")
    print(f"Created a new signing key at {KEY_PATH}")
    return key


def main():
    private_key = load_private_key()
    if not PUBLIC_PATH.exists():
        public = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        PUBLIC_PATH.write_text(public.hex(), encoding="utf-8")
    manifest = {"files": {name: file_sha256(ROOT / name) for name in FILES}}
    payload = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
    MANIFEST_PATH.write_bytes(payload)
    SIGNATURE_PATH.write_text(private_key.sign(payload).hex(), encoding="utf-8")
    print("Signed release manifest.")


if __name__ == "__main__":
    main()

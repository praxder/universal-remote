"""XDG-aware JSON store for saved devices and their pairing credentials."""

from __future__ import annotations

import json
import os
from pathlib import Path

from .models import Device


def default_store_path() -> Path:
    """`$XDG_CONFIG_HOME/universal-remote/devices.json`, falling back to ~/.config."""
    xdg = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg) if xdg else Path.home() / ".config"
    return base / "universal-remote" / "devices.json"


class DeviceStore:
    """Reads and writes the device list; the file is owner-only (0600)."""

    def __init__(self, path: Path | None = None) -> None:
        self._path = path or default_store_path()

    def list(self) -> list[Device]:
        if not self._path.exists():
            return []
        raw = json.loads(self._path.read_text())
        return [Device.from_dict(entry) for entry in raw.get("devices", [])]

    def save_all(self, devices: list[Device]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(
            {"devices": [device.to_dict() for device in devices]}, indent=2
        )
        # Create restricted; O_CREAT honours the mode only on creation, so chmod
        # afterwards guarantees 0600 even if the file already existed.
        fd = os.open(self._path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as handle:
            handle.write(payload)
        os.chmod(self._path, 0o600)

    def add(self, device: Device) -> Device:
        devices = self.list()
        devices.append(device)
        self.save_all(devices)
        return device

    def update(self, device: Device) -> None:
        devices = [
            device if existing.id == device.id else existing for existing in self.list()
        ]
        self.save_all(devices)

    def delete(self, device_id: str) -> None:
        devices = [device for device in self.list() if device.id != device_id]
        self.save_all(devices)

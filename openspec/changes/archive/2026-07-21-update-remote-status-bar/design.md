## Context

The remote screen's status bar is Textual's built-in `Header`, which renders `app.title`. On mount, `RemoteScreen` sets `self.app.title = f"Remote — {self._device.name}"` (`src/universal_remote/tui/remote_screen.py:173`) and restores the previous title on unmount. `Device` (`devices/models.py`) exposes `name`, `platform`, and `ip`. The registry already maps a `platform` to an `Adapter` carrying a human-readable `display_name` (`adapter.py:28`), reused today by the discover and add/edit screens.

## Goals / Non-Goals

**Goals:**
- Show `Name: <name> • Type: <type> • IP: <ip>` in the status bar.
- Render `<type>` via the existing human-readable label, reusing `adapter.display_name`.

**Non-Goals:**
- No new platform→label mapping (reuse the registry's `display_name`).
- No changes to the `#text-status` label, the Footer, or any other screen.

## Decisions

- Build the title from the device's `name`, `ip`, and the resolved adapter's `display_name`:
  ```python
  display_type = self.app.registry.resolve(self._device.platform).display_name
  self.app.title = f"Name: {self._device.name} • Type: {display_type} • IP: {self._device.ip}"
  ```
- Resolve the label through `self.app.registry` (already available on the screen) so the status bar and the device-type picker stay consistent.
- Restore-on-unmount behavior is unchanged.

## Risks / Trade-offs

- `registry.resolve(platform)` raises `UnsupportedPlatformError` for an unregistered platform. A saved device always carries a registered platform (enforced by the add flow's platform picker), so no fallback is added — per YAGNI, the assumption is documented here rather than guarded in code.
- The status string is longer than before; Textual's `Header` centers and truncates overflow, which is acceptable for a status bar.

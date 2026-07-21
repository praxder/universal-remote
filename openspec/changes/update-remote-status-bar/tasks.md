## 1. Implementation

- [ ] 1.1 In `src/universal_remote/tui/remote_screen.py`, replace the `app.title` assignment on mount (`f"Remote — {self._device.name}"`) with `f"Name: {self._device.name} • Type: {display_type} • IP: {self._device.ip}"`, where `display_type = self.app.registry.resolve(self._device.platform).display_name`.

## 2. Tests

- [ ] 2.1 Add a test asserting that, on the remote screen, `app.title == "Name: <name> • Type: <display_name> • IP: <ip>"` for a device whose platform resolves to a known human-readable label.
- [ ] 2.2 Run the formatter, linter, and full test suite; confirm all pass.

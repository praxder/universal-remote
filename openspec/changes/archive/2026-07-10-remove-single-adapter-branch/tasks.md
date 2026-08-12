## 1. Code cleanup

- [x] 1.1 Remove the `len(platforms) <= 1` early-return guard from `_platform_selector` in `src/universal_remote/tui/devices_screen.py`; keep the `_existing is not None` edit-mode guard
- [x] 1.2 Collapse `_selected_platform` in the same file to `return self.query_one("#platform", Select).value`, removing the `len(platforms) <= 1` fallback

## 2. Test cleanup

- [x] 2.1 Delete `test_given_one_adapter_when_adding_then_no_platform_selector_is_shown` in `tests/test_tui_devices.py`; leave the `_registry` helper and the multi-adapter test intact

## 3. Spec cleanup

- [x] 3.1 In `openspec/specs/device-management/spec.md`, simplify the "Add device with IP auto-fill" requirement sentence to drop the single-adapter and multi-adapter conditionals
- [x] 3.2 Reword the "Platform selected when multiple adapters registered" scenario to "Platform selected when adding a device" and drop the multi-adapter condition
- [x] 3.3 Delete the "Platform assigned when a single adapter registered" scenario

## 4. Verify

- [x] 4.1 Run the test suite (`uv run pytest`) and confirm all tests pass
- [x] 4.2 Run `openspec validate remove-single-adapter-branch` and confirm the change is valid

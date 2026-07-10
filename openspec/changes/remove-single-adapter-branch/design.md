## Context

`build_app` in `src/universal_remote/cli.py` registers the Samsung and LG adapters unconditionally at startup, so `AdapterRegistry.platforms()` always returns two or more entries in the running app. Two spots in `AddDeviceScreen` (`_platform_selector`, `_selected_platform`) still branch on `len(platforms) <= 1`, and the `device-management` spec still describes single-adapter behavior. That branch is only reachable by test-only registries built with one platform.

## Goals / Non-Goals

**Goals:**
- Remove the unreachable single-adapter branches from the Add-Device flow.
- Bring the `device-management` spec in line: platform selection is always offered.
- Keep the multi-adapter behavior and its test intact.

**Non-Goals:**
- Changing how adapters are registered or discovered.
- Editing archived change specs (frozen historical record).
- Changing edit-mode behavior (the platform selector is already hidden when editing, gated by `_existing`, which is unrelated to adapter count).

## Decisions

- **Drop the `<= 1` guard in `_platform_selector`, keep the `_existing` guard.** The `_existing is not None` early return (hide selector when editing) is a real, separate condition and stays.
- **Collapse `_selected_platform` to `return self.query_one("#platform", Select).value`.** The selector is always present on the add screen, so the fallback that returned `platforms[0]` is dead. Keep it as a named method for intent clarity rather than inlining.
- **Delete the single-adapter test** `test_given_one_adapter_when_adding_then_no_platform_selector_is_shown`. It constructs a one-adapter registry that production never produces. The multi-adapter test and the `_registry` helper remain.
- **Spec: MODIFY the requirement in place** rather than remove/re-add, and drop the single-adapter scenario by omitting it from the modified requirement block.

## Risks / Trade-offs

- [Removing the single-adapter test lowers coverage of a defensive path] → Acceptable: the path is unreachable given `build_app`, and re-introducing a single-adapter mode would be a new change that reintroduces the branch and its test deliberately.

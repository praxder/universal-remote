## 1. Test (red)

- [x] 1.1 Add a test that instantiates `UniversalRemoteApp` and collects the command-palette command titles, asserting they equal `{"Theme", "Quit", "Keys"}`
- [x] 1.2 Add assertions that "Maximize" and "Screenshot" are absent from the collected titles
- [x] 1.3 Run the test and confirm it fails against the current inherited palette

## 2. Implement (green)

- [x] 2.1 Override `get_system_commands` on `UniversalRemoteApp` in `src/universal_remote/tui/app.py` to yield from `super()` while skipping commands whose title is "Maximize" or "Screenshot"
- [x] 2.2 Run the test from section 1 and confirm it passes

## 3. Preflight

- [x] 3.1 Format and lint (ruff) the changed files
- [x] 3.2 Run the full test suite and confirm all tests pass
- [x] 3.3 Validate the change: `openspec validate codify-command-palette`

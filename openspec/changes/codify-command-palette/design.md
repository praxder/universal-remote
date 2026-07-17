## Context

`UniversalRemoteApp` (`src/universal_remote/tui/app.py`) subclasses Textual's `App` and does not touch the command palette, so it inherits `App.get_system_commands` verbatim. On Textual 8.2.8 that generator yields: Theme, Quit, Keys, Minimize/Maximize (conditional), and Screenshot. No project code defines a palette, a provider, or a maximize keybinding — the palette is the only entry point to maximize.

## Goals / Non-Goals

**Goals:**
- Remove Maximize and Screenshot from the command palette.
- Pin the palette's contents so upstream Textual changes cannot silently reintroduce commands.

**Non-Goals:**
- Adding any new custom palette commands.
- Disabling the command palette entirely.
- Changing keybindings or any other app behavior.

## Decisions

**Override `get_system_commands` and filter by command title.**
```python
def get_system_commands(self, screen):
    for command in super().get_system_commands(screen):
        if command.title in ("Maximize", "Screenshot"):
            continue
        yield command
```
Rationale: delegates to `super()` so retained commands (Theme, Quit, Keys, and the conditional Minimize) keep their upstream wiring and stay current across Textual upgrades. The override only names what it removes.

_Alternative — re-yield only the wanted commands._ Rejected: duplicates upstream logic (the Keys show/hide branch, the Minimize/Maximize conditional) into app code, creating a second thing to maintain and a drift risk of its own.

**Leave the Minimize branch alone.** Minimize is yielded by Textual only when `screen.maximized is not None`. With Maximize gone from the palette and no maximize keybinding, nothing sets that state, so Minimize never appears. Filtering it explicitly would be dead-code defense against a state that cannot occur.

**Guard the contract with a title-set test.** Call `get_system_commands` (or read the palette's provider output) and assert the resulting titles equal `{"Theme", "Quit", "Keys"}`. This fails loudly if a Textual upgrade adds, renames, or reorders commands.

## Risks / Trade-offs

- **Textual renames a command title** (e.g. "Screenshot" → "Save screenshot") → the filter silently stops matching and the command reappears. Mitigation: the title-set test fails on any change to the expected set, surfacing the rename at upgrade time.
- **Filtering by human-readable title is stringly-typed** → acceptable: `SystemCommand.title` is the stable public field and the same value the palette displays; there is no id to match on.

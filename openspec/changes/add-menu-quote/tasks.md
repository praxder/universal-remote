## 1. Quotes data + module (TDD)

- [ ] 1.1 Add `tests/test_tui_quotes.py`: `load_quotes()` parses `text|character|source` lines into `Quote`, skips blank and malformed lines; `random_quote()` returns a `Quote` from the loaded list, or `None` when the list is empty (red)
- [ ] 1.2 Create `src/universal_remote/tui/quotes.py`: frozen `Quote(text, character, source)` dataclass, `load_quotes()` reading the packaged file via `importlib.resources` and skipping blank/malformed lines, `random_quote()` returning `random.choice(...)` or `None` (green)
- [ ] 1.3 Create `src/universal_remote/tui/data/quotes.txt` with ~100 curated famous movie/TV quotes, one per line as `text|character|source`
- [ ] 1.4 Verify `quotes.txt` ships as package data — inspect `pyproject.toml` build config and add package-data inclusion for `tui/data` if missing

## 2. Dependency injection in the app

- [ ] 2.1 Add `quote_provider: Callable[[], Quote | None] | None = None` param to `UniversalRemoteApp.__init__`, defaulting to `random_quote`, stored as `self.quote_provider`
- [ ] 2.2 Add the `#quote` CSS rule to the `CSS` block in `app.py` (width 42, centered, muted color, top margin)

## 3. Menu rendering (TDD)

- [ ] 3.1 Add `tests/test_tui_menu.py` cases: given a provider returning a fixed `Quote`, the menu shows the quote text and `— character, source`; given a provider returning `None`, no `#quote` widget is present (red)
- [ ] 3.2 In `MenuScreen.compose`, after the Use Remote button, call `self.app.quote_provider()`; when truthy, yield a centered `Static` (id `quote`) with the quote text and attribution line, escaping Textual markup; when `None`, yield nothing (green)

## 4. Preflight

- [ ] 4.1 Run formatter/linter and fix any issues
- [ ] 4.2 Run the full test suite and confirm all tests pass
- [ ] 4.3 Launch the TUI and confirm a quote renders beneath the buttons with correct attribution

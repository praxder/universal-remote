## Context

The landing menu (`tui/menu.py` `MenuScreen`) currently renders an ASCII banner and two buttons (Manage Devices, Use Remote), styled by the `CSS` block in `tui/app.py`. The app already isolates side effects behind constructor-injected dependencies — `store`, `registry`, and `probe` are passed into `UniversalRemoteApp.__init__` and read off `self.app` by screens; tests inject fakes for determinism. This change adds a decorative rotating quote to the menu and must fit that existing pattern rather than introduce new global state or randomness that tests can't control.

## Goals / Non-Goals

**Goals:**
- Show one famous movie/TV quote with `— character, source` attribution beneath the two mode buttons.
- Keep quote selection deterministic under test via the existing DI pattern.
- Never crash the app on a missing, empty, or malformed quotes file — degrade to no quote row.
- No new runtime dependencies.

**Non-Goals:**
- Rotating the quote mid-session (one per launch is sufficient).
- Any UI for editing, filtering, or navigating quotes.
- Localization / internationalization of quotes.
- Rich formatting beyond a text line + attribution line.

## Decisions

**Decision: Store quotes in a packaged text file, one per line as `text|character|source`.**
Rationale: The user asked for a plain text file; pipe-delimited is the boring, obvious parse. Three fields support the chosen `— character, source` attribution. Located at `src/universal_remote/tui/data/quotes.txt` and read via `importlib.resources.files(...)`, so it works from the source tree and when installed.
Alternatives: JSON/TOML (heavier, unrequested); one string preformatted per line (loses structure needed to style attribution separately).

**Decision: New module `tui/quotes.py` with a frozen `Quote` dataclass, `load_quotes()`, and `random_quote()`.**
`Quote(text, character, source)` is frozen/immutable. `load_quotes()` reads the packaged file, splits each non-blank line on `|` into exactly three parts, and skips blank or malformed lines. `random_quote()` returns `random.choice(load_quotes())`, or `None` when the list is empty. `random_quote` is the default provider.
Rationale: Small, single-responsibility functions; parsing is isolated and unit-testable without the TUI.
Alternatives: Inlining parsing into the menu (couples IO to the view, hard to test).

**Decision: Inject `quote_provider: Callable[[], Quote | None] | None = None` into `UniversalRemoteApp`, defaulting to `random_quote`.**
Stored as `self.quote_provider`; `MenuScreen.compose` calls `self.app.quote_provider()`. Tests pass a fixed lambda (or one returning `None`) for determinism.
Rationale: Mirrors the existing `probe` injection exactly — no new pattern to learn, randomness stays out of tests.
Alternatives: Module-level random call in the menu (non-deterministic tests); seeding `random` globally (leaky, affects unrelated code).

**Decision: Render the quote as a centered `Static` with Textual markup escaped.**
`compose()` computes `q = self.app.quote_provider()`; if `q` is falsy, yield nothing. Otherwise yield a `Center` wrapping a `Static` with id `quote` showing the quote text and, on a second line, `— {character}, {source}`. Any `[`/`]` in quote text is escaped (or `markup=False`) so a stray bracket can't break rendering. A `#quote` CSS rule (width 42 to match the banner, centered text, muted color, top margin) is added to `app.py`.
Rationale: Consistent with how `#title` and buttons are composed and styled; escaping prevents accidental markup interpretation of user-facing text.

## Risks / Trade-offs

- **Packaging omits `quotes.txt`** → app installs but shows no quote. Mitigation: verify the build config (`pyproject.toml`) includes the `tui/data` package data; the graceful-empty path means worst case is a missing row, not a crash.
- **Unescaped brackets in a quote break Textual markup** → Mitigation: escape markup (or `markup=False`) on the quote `Static`.
- **Malformed lines silently dropped** → a typo'd quote just won't appear. Acceptable for a decorative feature; parsing is covered by a unit test asserting blank/malformed lines are skipped.

## Migration Plan

Additive only. No data migration, no config changes, no breaking changes. Ships with the change; nothing to roll back beyond reverting the commit.

## Open Questions

None — product decisions (attribution shape, random-per-launch, graceful-empty, self-authored quotes) were resolved during exploration.

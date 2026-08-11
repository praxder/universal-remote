## 1. Org prerequisites — blocking, and not ours to grant

- [ ] 1.1 Ask an org owner to make `RightNowMinistries/universal-remote` **public**. If refused, stop: the Homebrew requirements in `specs/homebrew-distribution/spec.md` assume anonymous read and must be rewritten (see design.md — Decision 1) before any other task starts
- [ ] 1.2 Ask an org owner to add a **bypass actor for the Repository admin role** to the org ruleset "Require Peer Review" (id `5324688`) for this repo, naming the trade-off: peer review becomes advisory for repo admins here. If refused, stop and re-open the proposal for the `hatch-vcs` tag-only fallback (design.md — Decision 2)
- [ ] 1.3 Verify the bypass took effect: `gh api repos/RightNowMinistries/universal-remote/rules/branches/main` no longer reports an enforcing `pull_request` rule for you, and `gh repo view` reports `PUBLIC`

## 2. Prepare the branch in the current repo

- [ ] 2.1 Branch from `development`
- [ ] 2.2 Copy `Formula/universal-remote.rb` in from `praxder/homebrew-tap` (current published version), rewriting `homepage` and `url` to the new org and refreshing the PLACEHOLDER comment to say the first release from this repo fills it in
- [ ] 2.3 Change `REPO_URL` in `src/universal_remote/tui/settings_screen.py` to `https://github.com/RightNowMinistries/universal-remote`, committed as `fix(tui): point the repo link at its new home` so the first merge to `main` cuts a release (design.md — Decision 6). `LICENSES_URL` derives from it; `tests/test_tui_settings.py` imports the constant, so confirm the suite passes with no test edit
- [ ] 2.4 Update `README.md`: the Homebrew section to the two-step tap + install, and the Releases link at line 33
- [ ] 2.5 Add a line to `CONTRIBUTING.md`: the formula bump lands on `main`, so `development`'s copy of `Formula/universal-remote.rb` is intentionally stale between merges
- [ ] 2.6 Decide the `LICENSE` copyright holder (design.md — Open Questions) and edit or leave it deliberately
- [ ] 2.7 Preflight: `uv run ruff format`, `uv run ruff check`, `uv run pytest`

## 3. Rework the release pipeline

- [ ] 3.1 Rewrite the `tap` job in `.github/workflows/release.yml`: check out this repo at `main` with the release credential instead of `praxder/homebrew-tap` with `HOMEBREW_TAP_TOKEN`, keep the same three `sed` rewrites, and `git pull --rebase` before pushing
- [ ] 3.2 Append `[skip ci]` to the formula-bump commit message — a PAT-authored push re-triggers workflows where `GITHUB_TOKEN` did not
- [ ] 3.3 Point both the `version` and `tap` jobs at `secrets.RELEASE_TOKEN` (the bypass is keyed to the repo-admin role, which `github-actions[bot]` does not hold)
- [ ] 3.4 Update the workflow's header comment to describe the in-repo formula bump

## 4. Import into the new repo

- [ ] 4.1 Add the org repo as a second remote and fetch it
- [ ] 4.2 `git merge --allow-unrelated-histories org/development` into the working branch, resolving the README in favour of ours, so the eventual push is a fast-forward past the `non_fast_forward` rule
- [ ] 4.3 Push `main` to the org repo (a branch creation, not an update). If rejected, seed it through the same pull request as task 4.5
- [ ] 4.4 Push the working branch as `import`
- [ ] 4.5 Open `import` → `development` and merge it (with the bypass, or one colleague's approval)
- [ ] 4.6 Push all tags `v1.0.0`–`v2.0.0` — tags are unruled, so this goes through untouched. Confirm python-semantic-release will continue from `v2.0.0`
- [ ] 4.7 Do **not** push the 15 stale feature branches

## 5. Configure the new repo

- [ ] 5.1 Set the default branch to `main` — Homebrew reads a tap from its default branch, so leaving it on `development` serves every user a stale formula (design.md — Decision 4)
- [ ] 5.2 Create a fine-grained PAT with contents-write on this repo and store it as the `RELEASE_TOKEN` Actions secret
- [ ] 5.3 Confirm "Allow merge commits" is enabled — python-semantic-release needs every conventional commit, so `development` → `main` must never be squashed
- [ ] 5.4 Confirm repo Actions settings still report `allowed_actions: "all"`, so `python-semantic-release` and `astral-sh/setup-uv` run
- [ ] 5.5 Repoint the local clone's `origin` at the new URL

## 6. Cut the first release and verify

- [ ] 6.1 Merge `development` → `main` with a merge commit; confirm the `version` job pushes the bump and the tag with no approval prompt
- [ ] 6.2 Confirm the GitHub Release for `v2.0.1` exists on the new repo with the binary asset attached and grouped notes
- [ ] 6.3 Confirm the `tap` job committed the new `version`, `url`, and `sha256` into `Formula/universal-remote.rb` on `main`, and that the commit carried `[skip ci]` and started no second run
- [ ] 6.4 On an arm64 Mac that did not build the binary: `brew untap praxder/tap`, then tap the new repo by URL and install. Confirm `universal-remote --version` and `ur --version` both report `2.0.1`
- [ ] 6.5 Confirm the Settings screen's GitHub row opens the new repo

## 7. Retire the old locations

- [ ] 7.1 Add `deprecate! because: "moved to RightNowMinistries/universal-remote"` to the formula in `praxder/homebrew-tap` and note the move in its README, with the re-tap commands
- [ ] 7.2 Leave `praxder/universal-remote` alive — the old formula's release assets are still served from it, and there is no redirect from the new repo. Archiving rather than deleting keeps old links resolving
- [ ] 7.3 Update the `homebrew-distribution` and `release-automation` `## Purpose` lines in `openspec/specs/` — both still name `praxder/homebrew-tap`, and a delta cannot change a Purpose

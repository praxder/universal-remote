## 1. Org prerequisites — blocking, and not ours to grant

- [x] 1.1 Ask an org owner to make `RightNowMinistries/universal-remote` **public**. If refused, stop: the Homebrew requirements in `specs/homebrew-distribution/spec.md` assume anonymous read and must be rewritten (see design.md — Decision 1) before any other task starts
- [x] 1.2 Install the **CI bot GitHub App** (app-id `4117226`) on this repo — done; "RightNow CI" is listed under the repo's Settings → GitHub Apps
- [x] 1.3 Add the App to the "Require Peer Review" ruleset's bypass list with `bypass_mode: always` — **already true, no request needed.** `tf-engineering-tools/github/repos/rulesets.tf` grants `actor_type = "Integration"` / `4117226` / `always` on `require_review`, whose `repository_name.include` is `["~ALL"]` with an exclude list that does not name this repo (design.md — Decision 2)
- [ ] 1.4 Ask DevOps to make the `CI_BOT_PRIVATE_KEY` org secret visible to this repo. **Not a Terraform change** — the secret appears in no `.tf` in the org (`github/secrets/secrets.tf` does not declare it), so it is managed by hand in the org's Actions settings. Confirm with `gh api repos/RightNowMinistries/universal-remote/actions/organization-secrets`, which today returns an empty list; kids-tv's equivalent lists it
- [ ] 1.5 Verify: `gh repo view` reports `PUBLIC`, the App appears in the repo's installed GitHub Apps, and DevOps confirms the `bypass_actors` entry is `Integration` / app-id `4117226` / `always` (the list is not readable without `admin:org`, so this is their confirmation, not a command you run). Record their self-merge answer in design.md — Decision 2 (already answered empirically by PR #1: self-merge works with zero reviews)

## 2. Prepare the branch in the current repo

- [x] 2.1 Branch from `development`
- [x] 2.2 Copy `Formula/universal-remote.rb` in from `praxder/homebrew-tap` (current published version), rewriting `homepage` and `url` to the new org and refreshing the PLACEHOLDER comment to say the first release from this repo fills it in
- [x] 2.3 Change `REPO_URL` in `src/universal_remote/tui/settings_screen.py` to `https://github.com/RightNowMinistries/universal-remote`, committed as `fix(tui): point the repo link at its new home` so the first merge to `main` cuts a release (design.md — Decision 6). `LICENSES_URL` derives from it; `tests/test_tui_settings.py` imports the constant, so confirm the suite passes with no test edit
- [x] 2.4 Update `README.md`: the Homebrew section to the two-step tap + install, and the Releases link at line 33
- [x] 2.5 Add a line to `CONTRIBUTING.md`: the formula bump lands on `main`, so `development`'s copy of `Formula/universal-remote.rb` is intentionally stale between merges
- [x] 2.6 Rewrite `LICENSE`'s copyright line to `Copyright (c) 2026 RightNow Ministries` (decided — design.md, Open Questions)
- [x] 2.7 Preflight: `uv run ruff format`, `uv run ruff check`, `uv run pytest`

## 3. Rework the release pipeline

- [x] 3.1 Rewrite the `tap` job in `.github/workflows/release.yml`: check out this repo at `main` with the App token instead of `praxder/homebrew-tap` with `HOMEBREW_TAP_TOKEN`, keep the same three `sed` rewrites, and `git pull --rebase` before pushing
- [x] 3.2 Append `[skip ci]` to the formula-bump commit message — an App-authored push re-triggers workflows where `GITHUB_TOKEN` did not. Leave `[tool.semantic_release] commit_message` in `pyproject.toml` alone; its `[skip ci]` stops being belt-and-suspenders and becomes the only guard against a version-bump release loop (design.md — Risks)
- [x] 3.3 Mint an App installation token in both the `version` and `tap` jobs with `actions/create-github-app-token@v2` (`app-id: 4117226`, `private-key: ${{ secrets.CI_BOT_PRIVATE_KEY }}`, `permission-contents: write`), and push as the App — `github-actions[bot]` is not an eligible bypass actor. **`version`:** pass the token as the PSR action's `github_token`; PSR pushes to `hvcs_client.remote_url(use_token=True)`, so that one input is the whole change. **`tap`:** raw git, so follow the kids-tv shape — `actions/checkout` with the App token, or `persist-credentials: false` plus `git remote set-url origin https://x-access-token:$TOKEN@…`
- [x] 3.4 Leave the `build` job on `secrets.GITHUB_TOKEN` — creating the Release and uploading the asset needs no branch-protection bypass, and the credential should not be reused for it
- [x] 3.5 Update the workflow's header comment to describe the in-repo formula bump and the App authentication

## 4. Import into the new repo

- [x] 4.1 Add the org repo as a second remote and fetch it
- [x] 4.2 `git merge --allow-unrelated-histories org/development` into the working branch, resolving the README in favour of ours, so the eventual push is a fast-forward past the `non_fast_forward` rule
- [x] 4.3 Push `main` to the org repo (a branch creation, not an update). If rejected, seed it through the same pull request as task 4.5
- [x] 4.4 Push the working branch as `import`
- [x] 4.5 Open `import` → `development` and merge it (with the bypass, or one colleague's approval)
- [x] 4.6 Push all tags `v1.0.0`–`v2.0.0` — tags are unruled, so this goes through untouched. Confirm python-semantic-release will continue from `v2.0.0`
- [x] 4.7 Do **not** push the 15 stale feature branches

## 5. Configure the new repo

- [ ] 5.1 **Ask an org admin** to set the default branch to `main` in the GitHub UI — Homebrew reads a tap from its default branch, so leaving it on `development` serves every user a stale formula (design.md — Decision 4). Not self-serve: `PATCH /repos/…` returns `422 You don't have permission to change the default branch` even with `permissions.admin: true` and a `repo`-scoped token. Not a Terraform change either: the shared repository module sets `lifecycle { ignore_changes = [auto_init, default_branch] }`, so `default_branch = "main"` would apply as a no-op, and lifting that would hand Terraform the default branch of every repo in the org
- [ ] 5.2 No PAT to create — confirm instead that the CI bot App is installed on the repo and that `CI_BOT_PRIVATE_KEY` resolves in a workflow run (task 1.4 checks visibility; this checks it actually mints a token)
- [x] 5.3 Confirm "Allow merge commits" is enabled — python-semantic-release needs every conventional commit, so `development` → `main` must never be squashed
- [x] 5.4 Confirm repo Actions settings still report `allowed_actions: "all"`, so `python-semantic-release` and `astral-sh/setup-uv` run
- [x] 5.5 Repoint the local clone's `origin` at the new URL

## 6. Cut the first release and verify

- [ ] 6.1 Merge `development` → `main` with a merge commit; confirm the `version` job's App-authenticated push lands the bump commit and the tag on protected `main` without being rejected by the ruleset. (Whether the merge itself needed a colleague's approval is a separate question — see task 1.4)
- [ ] 6.2 Confirm the GitHub Release for `v2.0.1` exists on the new repo with the binary asset attached and grouped notes
- [ ] 6.3 Confirm the `tap` job committed the new `version`, `url`, and `sha256` into `Formula/universal-remote.rb` on `main`, and that the commit carried `[skip ci]` and started no second run
- [ ] 6.4 On an arm64 Mac that did not build the binary: `brew untap praxder/tap`, then tap the new repo by URL and install. Confirm `universal-remote --version` and `ur --version` both report `2.0.1`
- [ ] 6.5 Confirm the Settings screen's GitHub row opens the new repo

## 7. Retire the old locations

- [ ] 7.1 Add `deprecate! because: "moved to RightNowMinistries/universal-remote"` to the formula in `praxder/homebrew-tap` and note the move in its README, with the re-tap commands
- [ ] 7.2 Leave `praxder/universal-remote` alive — the old formula's release assets are still served from it, and there is no redirect from the new repo. Archiving rather than deleting keeps old links resolving
- [ ] 7.3 Update the `homebrew-distribution` and `release-automation` `## Purpose` lines in `openspec/specs/` — both still name `praxder/homebrew-tap`, and a delta cannot change a Purpose

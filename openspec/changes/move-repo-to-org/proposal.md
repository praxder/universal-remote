## Why

The project lives on a personal account (`praxder/universal-remote`) with its
Homebrew formula in a second personal repo (`praxder/homebrew-tap`). It should
belong to the company org, `RightNowMinistries/universal-remote`, so ownership
does not rest on one person's account. Folding the formula into the same repo at
the same time removes the cross-repo release hop, the fine-grained PAT that hop
needs, and the second repo to keep in sync — the app and the thing that installs
it become one release.

## What Changes

- **Move the code to `RightNowMinistries/universal-remote`** by pushing the git
  history and all release tags. A GitHub repository *transfer* is not available:
  the org denies repo creation to members, and an enterprise ruleset blocks
  `repository_transfer`. Consequence: **no URL redirect** from the old location,
  and stars, issues, and existing GitHub Releases do not carry over.
- **Fold the Homebrew tap into this repo** as `Formula/universal-remote.rb`.
  `praxder/homebrew-tap` is deprecated, not deleted.
- **BREAKING (users):** the install command changes. The repo is not named
  `homebrew-*`, so the one-line `brew install <org>/<tap>/<formula>` shorthand
  cannot auto-tap it. Users tap explicitly first:

  ```sh
  brew tap rightnowministries/universal-remote https://github.com/RightNowMinistries/universal-remote
  brew install rightnowministries/universal-remote/universal-remote
  ```

- **Rework the release pipeline's `tap` job** to rewrite the formula in this
  repo and push it to the default branch, authenticated by a credential that can
  write to a branch the org protects with a required-review ruleset. The
  `HOMEBREW_TAP_TOKEN` secret and the cross-repo checkout are removed.
- **Point every repo URL at the new home** — the Settings screen's GitHub row,
  the README install and Releases links, and the specs that name the old tap.
- **Org prerequisites (not code, and not ours to grant):** an org owner must make
  the repo public and add a bypass actor to the org's "Require Peer Review"
  ruleset for it. Without the bypass no release can complete unattended, and
  merging `development` → `main` needs another person's approval every time.

## Capabilities

### New Capabilities
<!-- None: the move introduces no new behavior. -->

### Modified Capabilities

- `homebrew-distribution`: the tap is now this repository rather than a separate
  `praxder/homebrew-tap`, which changes the formula's location and the commands
  a user runs to install.
- `release-automation`: the formula bump is an in-repo commit on the default
  branch instead of a cross-repo push, and the pipeline must publish without a
  human approving a pull request.
- `tui-settings`: the GitHub repository row opens the new URL.

## Impact

- **Code:** `src/universal_remote/tui/settings_screen.py` (`REPO_URL`;
  `LICENSES_URL` derives from it). `tests/test_tui_settings.py` imports the
  constant rather than hard-coding the string, so no test changes.
- **New files:** `Formula/universal-remote.rb` (moved from the tap repo).
- **Workflow:** `.github/workflows/release.yml` — the `tap` job; both the
  `version` and `tap` jobs' push credential.
- **Docs:** `README.md` install + Releases links, `CONTRIBUTING.md` (the formula
  bump lands on `main`, so `development`'s copy is intentionally stale).
- **Secrets:** `HOMEBREW_TAP_TOKEN` deleted; a `RELEASE_TOKEN` added with rights
  to push to the protected default branch.
- **Legal:** `LICENSE` still reads `Copyright (c) 2026 Adam Smith`. Moving to a
  company repo is the moment to decide whether the holder becomes Right Now
  Ministries.
- **Out of scope:** deleting or archiving `praxder/universal-remote`. Nothing
  stops us — it is a personal repo, so the enterprise `repository_delete` rule
  does not reach it — but its release assets are what the old formula still
  serves, and there is no redirect from the new repo. Also out of scope: the 15
  stale feature branches
  (not carried over), and adding a test CI workflow (the repo has none today;
  that is a separate change).
- **Risk:** the new repo has no releases at cutover, so its formula points at an
  asset that does not exist there yet. Until the first release is cut from the
  new repo, `brew install` from the new tap fails.

## Context

See `proposal.md` — Why. What shapes this design is not the code but the
destination org's governance. Verified against the live API on the target repo
(`gh api repos/RightNowMinistries/universal-remote/rules/branches/main`):

| Ruleset | Source | Rules | Applies to | `bypass_actors` |
| --- | --- | --- | --- | --- |
| Require Peer Review | org | `pull_request`: 1 approval, code-owner review, last-push approval | `~DEFAULT_BRANCH`, `main`, `development`, `hotfix` | `null` |
| Branch Hygiene | org | `deletion`, `non_fast_forward` | same four refs | `null` |
| No Delete Repository Policy | enterprise | `repository_delete`, `repository_transfer` | whole repo | `null` |

Plus: `members_can_create_public_repositories: false`,
`members_can_create_private_repositories: false`, and our role in the org is
`member`. We hold `admin` on the target repo itself.

Three consequences drive everything below:

1. **No transfer.** Transferring a repo into an org requires repo-creation rights
   there, which members do not have.
2. **No unattended push to `main` or `development`.** Every automated push the
   release pipeline makes today — the version bump and the formula bump — lands
   on a branch that requires a reviewed pull request, and no actor is exempt.
3. **Tags are unruled.** All three rulesets target `branch` or `repository`;
   none targets `tag`. Tag pushes go through untouched.

The target repo is not empty: it holds one commit ("Initial commit", a README) on
a `development` branch that `non_fast_forward` and `deletion` both protect.

Homebrew facts verified locally against Homebrew 6.0.15:

- `brew tap <user>/<repo> <URL>` — the two-argument form — is current and
  documented in `brew tap --help`. It taps any repo regardless of its name.
- A tap is read from its **default branch**. Nothing lets a user tap a
  non-default branch.
- `grep -r GitHubPrivateRepositoryReleaseDownloadStrategy $(brew --repository)/Library/Homebrew`
  returns nothing — Homebrew ships no built-in strategy for private release
  assets. A private tap would need a download-strategy class written into the
  formula plus `HOMEBREW_GITHUB_API_TOKEN` set by every user.

## Goals / Non-Goals

**Goals:**

- Preserve full git history and every release tag at the new location.
- One repository holds the app and the formula that installs it.
- Releases stay unattended: merge to `main`, and the version, the GitHub Release,
  the binary, and the formula all follow with no human step.

**Non-Goals:**

- Preserving stars, issues, closed pull requests, or the old release objects.
- Keeping the old install command working. It changes, and that is accepted.
- Re-homing the 15 stale feature branches.
- Solving distribution for a private repo. This design assumes the repo is made
  public; see Decision 1.

## Decisions

### 1. The repo is made public, by an org owner

**Why:** the whole distribution story — an unauthenticated `brew tap`, an
unauthenticated release-asset download, the Settings screen's link to
`THIRD_PARTY_LICENSES.md` on GitHub — assumes anonymous read access. Public also
makes macOS Actions runners free rather than billed at the 10× multiplier.

**Alternative considered — stay private.** Rejected as a default because the cost
is not a URL swap: the formula needs a hand-written `GitHubPrivateRepositoryRelease`
download-strategy class, every user must export `HOMEBREW_GITHUB_API_TOKEN`, and
the tap clone itself needs git credentials. If the org refuses public, this
change's Homebrew requirements need rewriting before implementation starts —
treat it as a blocking prerequisite, not a fallback.

### 2. An org owner adds a bypass actor to "Require Peer Review": the Repository admin role

**Why:** the release pipeline pushes two commits to `main` per release, and no
GitHub actor is currently exempt. Scoping the bypass to the **Repository admin**
role also fixes a second problem that exists with or without this change: GitHub
forbids approving your own pull request, so a solo maintainer cannot merge
`development` → `main` at all under this ruleset.

**Alternatives considered:**

- *Deploy key as the bypass actor.* Tighter scope, but it exempts only the bot,
  leaving every `development` → `main` merge waiting on a colleague.
- *Bot opens a formula-bump PR each release.* No owner involvement, but a manual
  approval per release, and required code-owner review plus last-push approval
  means the bot cannot self-merge.
- *Restructure so nothing touches a protected branch* — derive the version from
  the tag with `hatch-vcs` and push tags only. This genuinely works for the
  version bump, and is the fallback if the bypass is refused. It does **not**
  solve the formula bump: Homebrew reads the tap's default branch, and the
  default branch is always matched by the ruleset's `~DEFAULT_BRANCH` condition,
  so there is no unprotected branch a formula can usefully live on.
- *Ship a cask with `version :latest` and `sha256 :no_check`* pointing at
  `/releases/latest/download/…`, so the file never changes and nothing is ever
  pushed. Rejected: it discards checksum verification, and `brew upgrade` skips
  `:latest` casks unless run with `--greedy`.

**Trade-off to state plainly to the owner:** repo-admin bypass means peer review
becomes advisory for repo admins on this repo.

With the bypass in place, the `version` job keeps working exactly as it does
today — no `hatch-vcs`, no tag-only restructure. The pipeline change is confined
to the `tap` job.

### 3. The formula lives at `Formula/universal-remote.rb` in this repo, tapped with the two-argument form

**Why:** Homebrew scans `Formula/`, `HomebrewFormula/`, or the repo root of a
tap. `Formula/` matches where the file already lives in `praxder/homebrew-tap`,
so the move is a copy with three URLs edited.

Because the repo is not named `homebrew-universal-remote`, the shorthand
`brew install rightnowministries/universal-remote/universal-remote` cannot
auto-tap on a clean machine — it resolves to a `homebrew-universal-remote` repo
that does not exist. Users run the two-argument `brew tap` once, after which the
fully-qualified install works.

**Alternative considered — rename the repo `homebrew-universal-remote`** so the
one-liner works. Rejected: it makes the app repo's name about its packaging.

### 4. The new repo's default branch is `main`

Not a settings-checklist item — a correctness requirement. Homebrew reads a tap
from its default branch. The formula bump is committed to `main`. The target repo
currently defaults to `development`; leaving it there would serve every `brew`
user a formula frozen at whatever version `development` happens to hold.

The corollary is that `development`'s copy of the formula is permanently stale
between merges, exactly as `pyproject.toml`'s version already is. That is
intended and gets one line in `CONTRIBUTING.md`.

### 5. Import by push, seeding `development` through a pull request

`git push --mirror` cannot work: `non_fast_forward` blocks overwriting the
placeholder's `development`, and `deletion` blocks removing it. The sequence that
does work:

```
git fetch org
git merge --allow-unrelated-histories org/development   # keep our README
   → now our history contains theirs, so the push is a fast-forward
push  main            (new branch — creation is not a ruled action)
push  import          (unprotected name)
PR    import → development, merge
push  --tags          (tags are unruled)
set   default branch → main
```

`main` does not exist at the target, so pushing it creates a branch rather than
updating one; no ruleset here declares a `creation` rule. If that push is
rejected anyway, `main` is seeded through the same `import`-branch pull request
as `development`.

### 6. The first release from the new repo is a real `fix:`, not a forced bump

At cutover the new repo has tags but no GitHub Releases, so the formula it ships
points at an asset that lives only on the old repo. Rather than force a version
with `workflow_dispatch`, the URL change earns its own release honestly: moving
`REPO_URL` is a user-facing fix to the Settings screen's GitHub row, so it is
committed as `fix(tui): point the repo link at its new home` and the first merge
to `main` cuts `v2.0.1`, publishes the asset, and rewrites the formula.

Until that release lands, the formula in the repo carries the same PLACEHOLDER
comment the original tap formula carried on day one.

**Alternative considered — recreate the `v2.0.0` release** by re-uploading the
existing asset, keeping its `sha256` valid so the tap works instantly. Rejected
in favour of a clean first release; the gap lasts one merge.

## Risks / Trade-offs

- **An org owner declines the public flip** → the Homebrew requirements in this
  change are wrong as written. Resolve before implementation; do not start and
  discover it at task 6.
- **An org owner declines the ruleset bypass** → fall back to Decision 2's
  `hatch-vcs` tag-only restructure for the version bump, and accept a
  human-approved formula-bump PR per release. This is a materially different
  release design, so re-open the proposal rather than improvising in `tasks.md`.
- **A PAT is used where `GITHUB_TOKEN` used to be** → a PAT-authored push *does*
  re-trigger workflows, unlike `GITHUB_TOKEN`. Both automated commits must carry
  `[skip ci]`; the version-bump commit already does via
  `[tool.semantic_release] commit_message`, and the formula commit gains it.
- **The `tap` job races the `version` job's push** → `tap` checks out `main`
  after `version` has already pushed, and `concurrency: group: release` prevents
  overlapping runs, but the job pulls before pushing so a rebase resolves rather
  than a rejected push.
- **No redirect from the old URL** → anything linking to
  `github.com/praxder/universal-remote` breaks the day that repo is deleted. Keep
  it alive (archived, not deleted) until the old formula is deprecated and the
  new tap is verified working.
- **`brew audit`/`brew style` on a tap that is also an app repo** → the extra
  source tree is ignored by Homebrew's formula scan, but the tap clone now
  carries the full history and the `docs/screenshots` PNGs. A few MB per user;
  accepted.

## Migration Plan

Rollback at any point before task 6 is: change nothing on the old repo, which
keeps releasing and keeps `praxder/homebrew-tap` current. The new repo is
additive until the old formula is deprecated. After the first release is cut from
the new repo, rolling back means re-pointing the old tap's formula at the last
`praxder`-hosted asset — recoverable, but it is the point of no easy return.

Existing `brew` users migrate by hand:

```sh
brew uninstall universal-remote && brew untap praxder/tap
brew tap rightnowministries/universal-remote https://github.com/RightNowMinistries/universal-remote
brew install rightnowministries/universal-remote/universal-remote
```

Homebrew's `tap_migrations.json` would automate this, but it resolves its target
through the `homebrew-<name>` shorthand and so cannot point at a tap whose repo
is named `universal-remote`. With the installed user base at roughly one, a
`deprecate!` line and a README note on the old tap are proportionate.

## Open Questions

- ~~Does `LICENSE`'s copyright holder become Right Now Ministries?~~ **Resolved:**
  yes. Task 2.6 rewrites the line to `Copyright (c) 2026 RightNow Ministries`.

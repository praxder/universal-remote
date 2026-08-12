## Context

See `proposal.md` — Why. What shapes this design is not the code but the
destination org's governance. Verified against the live API on the target repo
(`gh api repos/RightNowMinistries/universal-remote/rules/branches/main`):

| Ruleset | Source | Rules | Applies to |
| --- | --- | --- | --- |
| Require Peer Review (`5324688`) | org | `pull_request`: 1 approval, code-owner review, last-push approval | `~DEFAULT_BRANCH`, `main`, `development`, `hotfix` |
| Branch Hygiene (`17752160`) | org | `deletion`, `non_fast_forward` | same four refs |
| No Delete Repository Policy (`5327550`) | enterprise | `repository_delete`, `repository_transfer` | whole repo |

`bypass_actors` is **not readable from here** — `gh api orgs/…/rulesets/5324688`
returns 404 without the `admin:org` scope. The repo-scoped view reports
`current_user_can_bypass: "pull_requests_only"` on Require Peer Review, so some
bypass entry already reaches the maintainer for pull-request merges; which actor
grants it is unknown, and direct pushes are not covered either way. The rulesets
live in a Terraform workspace the platform team owns.

Plus: `members_can_create_public_repositories: false`,
`members_can_create_private_repositories: false`, and our role in the org is
`member`. We hold `admin` on the target repo itself.

Three consequences drive everything below:

1. **No transfer.** Transferring a repo into an org requires repo-creation rights
   there, which members do not have.
2. **No unattended push to `main` or `development` as `github-actions[bot]`.**
   Every automated push the release pipeline makes today — the version bump and
   the formula bump — lands on a branch that requires a reviewed pull request,
   and the default `GITHUB_TOKEN` is not an eligible bypass actor. See
   Decision 2 for the org's answer to this.
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

### 2. The pipeline authenticates as the org's CI bot GitHub App, which the ruleset grants `bypass_mode: always`

**Why:** the release pipeline pushes two commits to `main` per release, and
`github-actions[bot]` is not an eligible ruleset bypass actor at all — the
default `GITHUB_TOKEN` cannot be granted one.

**Set by the platform team, not chosen here.** The original ask was a bypass
actor for the **Repository admin** role. DevOps replied that the org already
solves this with a dedicated **CI bot GitHub App** (app-id `4117226`, private key
in the `CI_BOT_PRIVATE_KEY` org secret), Terraform-managed onto the bypass list
of every `main`-targeting ruleset with `bypass_mode: always`. The workflow mints
an installation token and pushes as the App.

This is strictly better than what was asked for:

- **The repo-admin trade-off disappears.** Peer review does not become advisory
  for anyone. One App is exempt, not a role.
- **It is precedent, not invention.** `RightNowMinistries/kids-tv` runs exactly
  this shape; see its `.github/workflows/deploy.yml` and
  `docs/ci/release-pipeline.md`.
- **Scope follows the App installation**, so a ruleset-wide bypass entry still
  only reaches repos the App is installed on.

**The human merge — resolved, and it is fine.** The App bypass covers the
pipeline's pushes, not a person's pull request, so the question was whether a
solo maintainer can merge `development` → `main` at all: GitHub forbids
approving your own pull request, and the ruleset wants one approval plus
code-owner review plus last-push approval.

The import pull request answered it empirically. PR #1 (`import` →
`development`) reported `mergeStateStatus: BLOCKED` and
`reviewDecision: REVIEW_REQUIRED`, and the maintainer merged it anyway with
**zero reviews on record**. So the pre-existing
`current_user_can_bypass: "pull_requests_only"` entry does cover self-merge, and
releases need no colleague. Which actor grants it is still not visible without
`admin:org`, and it is not ours to rely on permanently — if it is ever removed,
each `development` → `main` merge needs one approval. That is an operational
cost, not a redesign.

**Alternatives considered:**

- *Bypass actor for the Repository admin role.* The original ask. Superseded:
  broader blast radius and it makes peer review advisory for repo admins.
- *Deploy key as the bypass actor.* The App is the org's supported form of this.
- *Bot opens a formula-bump PR each release.* No owner involvement, but a manual
  approval per release, and required code-owner review plus last-push approval
  means the bot cannot self-merge.
- *Restructure so nothing touches a protected branch* — derive the version from
  the tag with `hatch-vcs` and push tags only. This genuinely works for the
  version bump, and is the fallback if the App route is refused. It does **not**
  solve the formula bump: Homebrew reads the tap's default branch, and the
  default branch is always matched by the ruleset's `~DEFAULT_BRANCH` condition,
  so there is no unprotected branch a formula can usefully live on.
- *Ship a cask with `version :latest` and `sha256 :no_check`* pointing at
  `/releases/latest/download/…`, so the file never changes and nothing is ever
  pushed. Rejected: it discards checksum verification, and `brew upgrade` skips
  `:latest` casks unless run with `--greedy`.

With the App in place, the `version` job keeps its current shape — no
`hatch-vcs`, no tag-only restructure. `python-semantic-release` pushes to
`hvcs_client.remote_url(use_token=True)` (`ignore_token_for_push` defaults to
false, and this project does not set it), so handing the action the App
installation token as `github_token` is enough to make the push authenticate as
the App. The `tap` job runs raw git, so it takes the kids-tv shape instead:
check out with the App token, then commit and push.

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

**And it is not ours to set.** `PATCH /repos/…` with `default_branch=main`
returns `422 You don't have permission to change the default branch`, despite
`permissions.admin: true` on the repo — an org or enterprise policy reserves it.
So this joins the org-prerequisite list rather than the configuration checklist,
and it blocks the Homebrew half of this change just as firmly as the public flip
did.

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
- **The CI bot App is not installed on this repo, or not added to the bypass
  list** → fall back to Decision 2's `hatch-vcs` tag-only restructure for the
  version bump, and accept a human-approved formula-bump PR per release. This is
  a materially different release design, so re-open the proposal rather than
  improvising in `tasks.md`.
- **An App installation token is used where `GITHUB_TOKEN` used to be** → an
  App-authored push *does* re-trigger workflows, unlike `GITHUB_TOKEN`. Both
  automated commits must carry `[skip ci]`. The version-bump commit already does
  via `[tool.semantic_release] commit_message` in `pyproject.toml`, and the
  formula commit gains it. **This changes what `[skip ci]` is load-bearing for:**
  today it is belt-and-suspenders, because `GITHUB_TOKEN` would not re-trigger
  anyway. After the swap it is the only thing standing between the version-bump
  commit and an infinite `on: push: main` loop. Do not remove or reword it.
  (kids-tv belts this a second way — a `setup`-job guard that skips runs whose
  head commit is the bot's release commit. Worth copying if the loop ever
  materialises.)
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

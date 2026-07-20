# Contributing

## Commits

This project uses [Conventional Commits](https://www.conventionalcommits.org/).
The release version and notes are derived from commit types, so the type prefix
matters:

- `feat:` → minor bump (new user-facing capability)
- `fix:` → patch bump
- `feat!:` / `fix!:` / a `BREAKING CHANGE:` footer → major bump
- `docs:`, `chore:`, `refactor:`, `test:`, etc. → no release on their own

## Merge into `main` with a merge commit — never squash

Releases are cut automatically on every push to `main` (see
`.github/workflows/release.yml`). [python-semantic-release] reads **every**
conventional commit since the last tag to decide the version bump and to build
the changelog.

**Squash-merging `development` → `main` collapses the whole cycle into one
commit**, so the release gets the wrong version bump and a one-line changelog.
Always merge `development` into `main` with a **merge commit** (the repo keeps
`Allow merge commits` enabled); do not squash and do not fast-forward-flatten.

[python-semantic-release]: https://python-semantic-release.readthedocs.io/

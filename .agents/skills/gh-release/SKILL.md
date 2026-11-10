---
name: gh-release
description: "Create new release, commit, tag and push"
---

Use this skill only for creating and pushing a Git tag. The repository GitHub Actions workflow creates the GitHub release automatically when the tag is pushed. Do not create a GitHub release directly.

1. Read the current release version from `pyproject.toml`.
2. Bump version to next one x.y.z, or x.y.zbW for beta releases, where W is the beta number. Or use specific version provided by user.
3. Update to new version in `src/legalsuffix/__init__.py`
4. Come up with new release notes from commits since the previous release tag, excluding `chore`, `refactor`, `test`, and `docs` commits, and including only functionality-related changes. Use those release notes as the commit message instead of `Bump app version to <version>` or other generic messages. User can provide specific release notes if desired.
5. Update the `CHANGELOG.md` file with new version and changes.
6. Commit all changes and add tag for the new version. Push only the tag to the `master` branch. Push commit and tag. Important: tag name should be prefixed with `v` (e.g. `v0.0.1b`).

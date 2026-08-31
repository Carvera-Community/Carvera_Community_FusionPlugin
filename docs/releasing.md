# Creating a release

Releases are built by the `Create Fusion Plugin Release` GitHub Actions
workflow. The workflow stamps and packages the add-in without changing the
source files on the selected branch.

## Dry run

1. Open **Actions** in GitHub.
2. Select **Create Fusion Plugin Release**.
3. Select **Run workflow** and choose the source branch.
4. Enter a SemVer version without a leading `v`, such as `0.9.2-beta.1`.
5. Leave **Build and validate artifacts without creating a tag or release**
   enabled.
6. Run the workflow.
7. Download the dry-run artifact from the completed workflow run and inspect
   the zip and checksum.

A dry run creates neither a Git tag nor a GitHub release. Its artifact is kept
for seven days.

## Publish

Repeat the dry run with its checkbox disabled. The workflow creates tag
`vX.Y.Z`, a GitHub release named `Makera Community Fusion Plugin vX.Y.Z`, the
installable zip, and its SHA-256 checksum.

Versions containing a prerelease suffix, such as `-beta.1` or `-rc.1`, are
always published as prereleases. A stable version selected from any ref other
than `main` also defaults to prerelease. Publishing it as stable requires the
explicit **allow a stable release when the selected ref is not main** option.

The workflow refuses to overwrite an existing tag.

## Version boundaries

The release builder stamps exactly these packaged values:

- `version` in `Makera Community.manifest`
- `PLUGIN_VERSION` in `config.py`

It also forces packaged builds to `DEBUG = False` and excludes local
`settings.settings` files, bytecode, tests, and development-only files.

It does not change `SETTINGS_VERSION`, translation `fileVersion` values, UI
catalog schema versions, or referenced post-processor versions.

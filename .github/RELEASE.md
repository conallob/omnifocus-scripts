# Release Process

This document describes how to create a new release of omnifocus-scripts.

## Prerequisites

Before creating a release, you need to set up a GitHub secret for the Homebrew tap repository:

1. Create a Personal Access Token (PAT) on GitHub:
   - Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
   - Click "Generate new token (classic)"
   - Give it a descriptive name like "omnifocus-scripts-homebrew-tap"
   - Select the following scopes:
     - `repo` (all)
   - Click "Generate token" and copy the token

2. Add the token to this repository's secrets:
   - Go to this repository's Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Name: `HOMEBREW_TAP_TOKEN`
   - Value: Paste the PAT you created
   - Click "Add secret"

## Creating a Release

To create a new release:

1. **Update version references** in documentation if needed (optional)

2. **Create and push a version tag:**
   ```bash
   # Example: Creating version 1.0.0
   git tag -a v1.0.0 -m "Release version 1.0.0"
   git push origin v1.0.0
   ```

3. **The automation will:**
   - Create a GitHub release with release notes
   - Calculate the SHA256 of the release tarball
   - Update the Homebrew formula in `conallob/homebrew-tap`
   - Commit and push the updated formula

4. **Verify the release:**
   - Check the [releases page](https://github.com/conallob/omnifocus-scripts/releases)
   - Verify the Homebrew formula was updated in [homebrew-tap](https://github.com/conallob/homebrew-tap)

## Testing the Homebrew Installation

After a release is created, test the installation:

```bash
# Update local tap
brew update

# Install the formula
brew install conallob/tap/omnifocus-scripts

# Verify installation
brew test omnifocus-scripts

# Check installed location
ls -la $(brew --prefix)/share/omnifocus-scripts
```

## Version Numbering

We follow [Semantic Versioning](https://semver.org/):

- **MAJOR** version (1.x.x) - Incompatible API changes
- **MINOR** version (x.1.x) - Add functionality in a backward-compatible manner
- **PATCH** version (x.x.1) - Backward-compatible bug fixes

## Troubleshooting

### Release workflow fails

If the GitHub Actions workflow fails:

1. Check the workflow logs in the Actions tab
2. Common issues:
   - `HOMEBREW_TAP_TOKEN` secret not set or expired
   - Network issues connecting to GitHub
   - Syntax errors in the formula

### Formula update fails

If the Homebrew formula update fails:

1. Verify the `HOMEBREW_TAP_TOKEN` has `repo` scope
2. Check that the homebrew-tap repository exists and is accessible
3. Manually update the formula if needed (see Manual Formula Update below)

### Manual Formula Update

If you need to manually update the Homebrew formula:

```bash
# Clone the tap repository
git clone https://github.com/conallob/homebrew-tap.git
cd homebrew-tap

# Download the release tarball and calculate SHA256
curl -sL https://github.com/conallob/omnifocus-scripts/archive/v1.0.0.tar.gz -o release.tar.gz
shasum -a 256 release.tar.gz

# Edit Formula/omnifocus-scripts.rb and update:
# - url with the new version tag
# - sha256 with the calculated hash
# - version with the new version number

# Commit and push
git add Formula/omnifocus-scripts.rb
git commit -m "omnifocus-scripts: update to 1.0.0"
git push origin main
```

## Post-Release

After a successful release:

1. Announce the release in relevant channels
2. Update documentation if there are breaking changes
3. Close any related issues/PRs

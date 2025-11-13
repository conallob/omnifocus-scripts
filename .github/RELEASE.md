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

1. **Update CHANGELOG.md:**
   - Move items from "Unreleased" to a new version section
   - Add the release date
   - Include breaking changes, new features, bug fixes, etc.
   - Commit the changes

2. **Update version references** in documentation if needed (optional)

3. **Create and push a version tag:**
   ```bash
   # Example: Creating version 1.0.0
   git tag -a v1.0.0 -m "Release version 1.0.0"
   git push origin v1.0.0
   ```

   Note: Tags must follow semantic versioning (v[MAJOR].[MINOR].[PATCH])
   - Use `v1.0.0` for production releases
   - Use `v1.0.0-beta.1` for pre-releases

4. **The automation will:**
   - Validate that required secrets are configured
   - Create a GitHub release with auto-generated notes
   - Wait for GitHub to generate the release tarball
   - Download and calculate SHA256 with retry logic (5 attempts with exponential backoff)
   - Generate Homebrew formula from template using `sed` substitution
   - Securely push to `conallob/homebrew-tap` using gh CLI (no token exposure)
   - Run formula tests to verify installation works
   - Run `brew audit --strict` to check for issues

5. **Verify the release:**
   - Check the [releases page](https://github.com/conallob/omnifocus-scripts/releases)
   - Verify the Homebrew formula was updated in [homebrew-tap](https://github.com/conallob/homebrew-tap)
   - Check that the test-formula job passed
   - Monitor for any issues reported by `brew audit`

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

# Set the version you want to release
VERSION="1.0.0"
TAG="v${VERSION}"

# Download the release tarball and calculate SHA256
curl -sL "https://github.com/conallob/omnifocus-scripts/archive/${TAG}.tar.gz" -o release.tar.gz
SHA256=$(shasum -a 256 release.tar.gz | awk '{print $1}')
echo "SHA256: $SHA256"

# Update the formula using the template
sed -e "s|__VERSION__|${VERSION}|g" \
    -e "s|__TAG__|${TAG}|g" \
    -e "s|__SHA256__|${SHA256}|g" \
    ../omnifocus-scripts/.github/homebrew-formula-template.rb \
    > Formula/omnifocus-scripts.rb

# Or manually edit Formula/omnifocus-scripts.rb and update:
# - url: change the tag to the new version (e.g., v1.0.0)
# - sha256: paste the calculated hash
# - version: change to the new version number (e.g., 1.0.0)
# - Ensure license is "BSD-3-Clause"

# Verify the formula
cat Formula/omnifocus-scripts.rb

# Test the formula locally (optional)
brew install --build-from-source Formula/omnifocus-scripts.rb
brew test omnifocus-scripts

# Commit and push
git add Formula/omnifocus-scripts.rb
git commit -m "omnifocus-scripts: update to ${VERSION}"
git push origin main
```

## Security Features

The release workflow includes several security best practices:

1. **Secure Token Handling:**
   - Uses GitHub CLI (`gh`) for authentication instead of embedding tokens in URLs
   - Token never appears in git logs or shell history
   - Temporary directory cleanup with trap handlers

2. **Secret Validation:**
   - Validates `HOMEBREW_TAP_TOKEN` is configured before proceeding
   - Fails fast with clear error messages if secrets are missing

3. **Download Verification:**
   - Verifies tarball exists and is not empty before calculating SHA256
   - Implements retry logic with exponential backoff (5 attempts)
   - Prevents race conditions by waiting for GitHub to generate archives

4. **Formula Verification:**
   - Validates generated formula contains expected version
   - Tests formula installation with `brew test`
   - Runs `brew audit --strict` to catch common issues

## Post-Release

After a successful release:

1. Announce the release in relevant channels
2. Update documentation if there are breaking changes
3. Close any related issues/PRs
4. Update CHANGELOG.md's [Unreleased] section for next development cycle

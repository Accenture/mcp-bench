# Wikipedia MCP Release Process

This document describes how to create new releases for the Wikipedia MCP project using GitHub Actions.

## Automated Release Using GitHub Actions

We have set up a GitHub Actions workflow that automates most of the release process. The workflow is defined in the `.github/workflows/release.yml` file and can be triggered manually from the GitHub interface.

### Steps to Create a Release with GitHub Actions

1. **Navigate to the Actions tab** in your GitHub repository at https://github.com/rudra-ravi/wikipedia-mcp/actions

2. **Select the "Release Wikipedia MCP" workflow** from the list of workflows on the left side.

3. **Click the "Run workflow" button** (dropdown at the right side).

4. **Enter the release details**:
   - **Version**: For version 1.0.2, enter `1.0.2`
   - **Is this a pre-release?**: Select if this is a pre-release or a full release

5. **Click "Run workflow"** to start the release process.

6. **Monitor the workflow execution**:
   - The workflow will:
     - Update the version in setup.py
     - Build the Python package
     - Create a Git tag and commit
     - Create a GitHub Release with the built packages attached
     - Publish to PyPI (if not a pre-release)

7. **Once completed**, verify that:
   - The new tag appears in your repository
   - The GitHub Release is created with the correct assets
   - The package is published to PyPI (if not a pre-release)

### Release Workflow Details

The GitHub Actions workflow performs these steps:

1. Checks out the repository code
2. Sets up Python environment
3. Installs required dependencies
4. Updates the version number in setup.py
5. Builds the Python package (source distribution and wheel)
6. Creates a Git tag and commits the version change
7. Creates a GitHub Release with the built packages
8. Publishes the package to PyPI (if not a pre-release)

## Manually Creating a Release (Alternative Method)

If you need to create a release manually without using GitHub Actions, follow these steps:

### 1. Update Version Number

Update the version number in `setup.py`:

```python
setup(
    name="wikipedia-mcp",
    version="1.0.2",  # Update this to the new version
    # ...
)
```

### 2. Create and Update CHANGELOG.md

```markdown
# Changelog

## [1.0.2] - YYYY-MM-DD

### Added
- New features

### Fixed
- Bug fixes

### Changed
- Other changes
```

### 3. Build the Package

```bash
# Install build tools if needed
pip install --upgrade build twine

# Build the package
python -m build
```

### 4. Create a Git Tag

```bash
git add .
git commit -m "Bump version to 1.0.2"
git tag -a v1.0.2 -m "Version 1.0.2"
git push origin v1.0.2
git push origin main
```

### 5. Create a GitHub Release

1. Go to https://github.com/rudra-ravi/wikipedia-mcp/releases/new
2. Select the tag you just created (v1.0.2)
3. Set the title to "Wikipedia MCP v1.0.2"
4. Add release notes (e.g., from your CHANGELOG.md)
5. Attach the distribution files (.tar.gz and .whl) from the dist/ directory
6. Click "Publish release"

### 6. Publish to PyPI

```bash
twine upload dist/*
```

## Release Guidelines

When creating releases, keep these guidelines in mind:

1. **Follow Semantic Versioning**:
   - **MAJOR**: Breaking changes (1.0.0)
   - **MINOR**: New features, backward compatible (0.x.0)
   - **PATCH**: Bug fixes, backward compatible (0.0.x)

2. **Release Notes**: Provide clear, concise release notes that highlight:
   - New features
   - Bug fixes
   - Breaking changes (if any)
   - Upgrade instructions (if needed)

3. **Testing**: Before creating a release:
   - Run all tests
   - Verify installation from the built packages
   - Test key functionality

4. **Security**: Prioritize fixes for security vulnerabilities

## Setting Up PyPI Credentials for GitHub Actions

To enable automatic publishing to PyPI, you need to add your PyPI credentials as GitHub secrets:

1. Go to your repository's Settings tab
2. Click on "Secrets and variables" → "Actions"
3. Add these secrets:
   - PYPI_USERNAME: Your PyPI username
   - PYPI_PASSWORD: Your PyPI password or token (recommended)

## Troubleshooting

If you encounter issues with the release process, check:

1. **GitHub Actions logs** for detailed error messages
2. **Git tags and commits** to verify they were created correctly
3. **PyPI credentials** if the package publishing fails
4. **Build artifacts** to ensure they were created correctly

## Contact

If you encounter persistent issues with the release process, please open an issue on the GitHub repository. 
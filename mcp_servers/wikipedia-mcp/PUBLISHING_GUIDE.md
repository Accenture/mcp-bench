# PyPI Publishing Guide for Wikipedia MCP

This guide will help you set up automated PyPI publishing for the Wikipedia MCP server using modern **Trusted Publishing** (OpenID Connect).

## 🔐 Modern Trusted Publishing Setup (Recommended)

Trusted Publishing is the modern, secure way to publish to PyPI. It eliminates the need for API tokens and uses OpenID Connect (OIDC) for authentication.

### Step 1: Set Up PyPI Trusted Publisher

1. **For PyPI (Production)**:
   - Go to [PyPI Trusted Publishers](https://pypi.org/manage/account/publishing/)
   - Click "Add a new pending publisher"
   - Fill in the form:
     - **PyPI project name**: `wikipedia-mcp`
     - **Owner**: `Rudra-ravi`
     - **Repository name**: `wikipedia-mcp`
     - **Workflow name**: `release.yml`
     - **Environment name**: `pypi`

2. **For TestPyPI (Testing)**:
   - Go to [TestPyPI Trusted Publishers](https://test.pypi.org/manage/account/publishing/)
   - Fill in the same form but with:
     - **Environment name**: `testpypi`

### Step 2: Create GitHub Environments

1. Go to your GitHub repository settings
2. Navigate to **Environments** (in the left sidebar under "Code and automation")
3. Create two environments:

#### PyPI Environment (Production)
- **Name**: `pypi`
- **Protection rules**: 
  - ✅ Required reviewers (add yourself)
  - ✅ Wait timer: 0 minutes
  - ✅ Deployment branches: Selected branches → `main`

#### TestPyPI Environment (Testing)
- **Name**: `testpypi`
- **Protection rules**: 
  - ✅ Deployment branches: All branches (for testing)

### Step 3: Test the Workflow

1. Go to your GitHub repository
2. Click **Actions** tab
3. Click **Release Wikipedia MCP** workflow
4. Click **Run workflow**
5. Enter version (e.g., `1.5.5`)
6. Choose if it's a pre-release
7. Click **Run workflow**

## 🔧 Troubleshooting Current Issues

### Issue 1: Git Push Error
**Error**: `error: src refspec main does not match any`

**Solution**: The updated workflow now properly handles the main branch push by using `git push origin HEAD:main`.

### Issue 2: Detached HEAD State
**Solution**: The workflow now commits changes before creating tags, avoiding detached HEAD issues.

### Issue 3: Missing Trusted Publishing Setup
**Solution**: Follow Step 1 above to set up trusted publishers on PyPI and TestPyPI.

### Issue 4: Missing GitHub Environments
**Solution**: Follow Step 2 above to create the required environments.

## 📦 Package Installation Commands

After successful publishing, users can install your package with:

```bash
# Using pip
pip install wikipedia-mcp

# Using uvx (recommended for MCP servers)
uvx wikipedia-mcp

# Using pipx
pipx install wikipedia-mcp
```

## 🔄 MCP Configuration

Users can then add to their MCP configuration:

```json
{
  "wikipedia": {
    "command": "uvx",
    "args": ["wikipedia-mcp"]
  }
}
```

## 🚀 Release Process

1. **Update CHANGELOG.md** with your changes
2. **Run the workflow**:
   - Go to Actions → Release Wikipedia MCP
   - Click "Run workflow"
   - Enter the new version number
   - Choose if it's a pre-release
   - Click "Run workflow"
3. **The workflow will**:
   - Build the package
   - Create a GitHub release with files
   - Publish to TestPyPI (always)
   - Publish to PyPI (only for non-pre-releases)

## 🔍 Verification Steps

After a successful release:

1. **Check GitHub Release**: Should appear in your repository's releases
2. **Check TestPyPI**: Visit [test.pypi.org/project/wikipedia-mcp](https://test.pypi.org/project/wikipedia-mcp/)
3. **Check PyPI**: Visit [pypi.org/project/wikipedia-mcp](https://pypi.org/project/wikipedia-mcp/)
4. **Test Installation**: `pip install wikipedia-mcp==<version>`

## ⚠️ Important Notes

1. **First Time Setup**: The trusted publisher will create the PyPI project automatically on first use
2. **Environment Protection**: The `pypi` environment requires manual approval for security
3. **Version Management**: Always increment the version number for new releases
4. **Pre-releases**: Use pre-release option for alpha/beta versions

## 🛠️ Advanced Configuration

### Custom Package Name
If you want to publish under a different name, update:
- PyPI trusted publisher configuration
- `pyproject.toml` name field
- Workflow environment URLs

### Additional Security
Consider adding:
- Branch protection rules
- Required status checks
- CODEOWNERS file

## 📚 References

- [PyPI Trusted Publishing Documentation](https://docs.pypi.org/trusted-publishers/)
- [GitHub Actions OpenID Connect](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/configuring-openid-connect-in-pypi)
- [Python Packaging User Guide](https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/)

---

This setup provides a secure, modern, and automated way to publish your Python package to PyPI without managing API tokens!

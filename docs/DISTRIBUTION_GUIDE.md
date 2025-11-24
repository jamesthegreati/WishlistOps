# 📦 WishlistOps Distribution Guide

This guide explains how to distribute WishlistOps to end users. The project is built as a Python package that can be installed via `pip`.

## ✅ Build Status
**Current Build:** `v1.0.0`
**Build Artifacts:**
- Wheel: `dist/wishlistops-1.0.0-py3-none-any.whl` (Recommended for users)
- Source: `dist/wishlistops-1.0.0.tar.gz`

## 🚀 Distribution Options

### Option 1: GitHub Releases (Recommended for Private/Beta)
Best for distributing to a specific group of users or for beta testing.

1.  **Create a Release:**
    - Go to the GitHub repository.
    - Click "Releases" > "Draft a new release".
    - Tag version: `v1.0.0`.
    - Title: "WishlistOps v1.0.0 - Production Release".
    - Description: Paste the contents of `CHANGELOG.md` or the commit message.

2.  **Upload Artifacts:**
    - Drag and drop the `.whl` file from the `dist/` folder into the release assets.

3.  **User Installation:**
    Users can install directly from the URL:
    ```bash
    pip install https://github.com/jamesthegreati/WishlistOps/releases/download/v1.0.0/wishlistops-1.0.0-py3-none-any.whl
    ```

### Option 2: PyPI (Public Distribution)
Best for making the tool available to everyone via `pip install wishlistops`.

1.  **Install Twine:**
    ```bash
    pip install twine
    ```

2.  **Upload to TestPyPI (Optional but Recommended):**
    ```bash
    twine upload --repository testpypi dist/*
    ```

3.  **Upload to Production PyPI:**
    ```bash
    twine upload dist/*
    ```

4.  **User Installation:**
    ```bash
    pip install wishlistops
    ```

### Option 3: Direct File Sharing
Best for internal team distribution.

1.  Send the `.whl` file to your team.
2.  They install it locally:
    ```bash
    pip install wishlistops-1.0.0-py3-none-any.whl
    ```

## 🛠️ Post-Installation Setup for Users

After installing, users should run the onboarding wizard:

```bash
# 1. Run the tool
wishlistops

# 2. The onboarding wizard will start automatically if no configuration is found.
#    It will guide them through:
#    - Steam API Setup
#    - Google AI Setup
#    - Discord Webhook Setup
```

## 🔄 Updating the Package

To release a new version:

1.  Update the version number in `setup.py` and `wishlistops/__init__.py`.
2.  Clean old builds:
    ```bash
    rm -rf dist/ build/ *.egg-info
    ```
3.  Rebuild:
    ```bash
    python -m build
    ```
4.  Distribute the new `.whl` file.

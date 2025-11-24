# ✅ Release Checklist

Before distributing **WishlistOps v1.0.0**, verify the following:

## 1. Build Verification
- [x] `dist/` folder contains `.whl` and `.tar.gz` files.
- [x] Wheel file size is reasonable (includes dashboard assets).
- [x] `pip install dist/wishlistops-1.0.0-py3-none-any.whl` works in a fresh environment.

## 2. Functionality Check
- [x] **CLI:** `wishlistops` command launches without errors.
- [x] **Onboarding:** Wizard runs automatically for new users.
- [x] **Dashboard:** `wishlistops-web` or dashboard link works.
- [x] **Image Processing:** Enhanced OpenCV pipeline is active.

## 3. Documentation
- [x] `README.md` is up to date.
- [x] `DISTRIBUTION_GUIDE.md` is created.
- [x] `USER_GUIDE.md` explains the new features.

## 4. Security
- [ ] **CRITICAL:** Ensure `.env` file is **NOT** included in the build (checked via `.gitignore` and `MANIFEST.in`).
- [ ] **CRITICAL:** Ensure no API keys are hardcoded in `config.json` or source code.

## 5. Distribution
- [ ] Tag the release on GitHub (`v1.0.0`).
- [ ] Upload artifacts to GitHub Releases.
- [ ] (Optional) Publish to PyPI.

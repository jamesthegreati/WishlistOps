# Commit Best Practices for WishlistOps

**Make your commits work harder for you!** WishlistOps automatically generates Steam announcements from your Git commits. Follow these guidelines to ensure the tool detects and announces the right changes.

---

## 🎯 Commit Detection Patterns

WishlistOps uses two methods to identify player-facing commits:

### 1. Conventional Commits (Recommended)

Use standard commit types that WishlistOps recognizes:

**✅ Player-Facing Types** (Will trigger announcements):
- `feat:` - New features
- `fix:` - Bug fixes
- `perf:` - Performance improvements
- `revert:` - Reverted changes

**❌ Internal Types** (Won't trigger announcements):
- `chore:` - Maintenance tasks
- `docs:` - Documentation updates
- `style:` - Code formatting
- `refactor:` - Code restructuring
- `test:` - Test updates
- `build:` - Build system changes
- `ci:` - CI/CD configuration

**Examples**:
```bash
# ✅ Will create announcement
git commit -m "feat: add boss fight mechanics"
git commit -m "fix: resolve player falling through floor bug"
git commit -m "perf: optimize rendering for 60fps gameplay"

# ❌ Won't create announcement
git commit -m "chore: update dependencies"
git commit -m "docs: fix typo in README"
git commit -m "refactor: extract enemy AI into separate class"
```

---

### 2. Keyword Detection

If you don't use conventional commits, WishlistOps scans for player-facing keywords:

#### **Gameplay & Features**
- `add feature`, `new mechanic`, `implement ability`
- `add gameplay`, `new combat`, `introduce skill`
- `add weapon`, `new enemy`, `boss fight`

#### **Fixes & Improvements**
- `fix bug`, `resolve crash`, `fix glitch`
- `fix player`, `fix boss`, `fix animation`
- `improve performance`, `optimize framerate`

#### **Content Updates**
- `new map`, `add level`, `new area`
- `update art`, `new sprite`, `add texture`
- `new sound`, `add music`, `update voice`

#### **Balancing**
- `balance damage`, `tweak difficulty`
- `adjust enemy`, `rebalance boss`

**Examples**:
```bash
# ✅ Will create announcement
git commit -m "Add exciting boss fight to level 3"
git commit -m "Fix critical crash when player enters water"
git commit -m "New weapon: Lightning Sword with special abilities"
git commit -m "Improve framerate in large battle scenes"

# ❌ Won't create announcement
git commit -m "Update build script"
git commit -m "WIP testing new feature"
git commit -m "Merge pull request #42"
```

---

## 📸 Screenshot Directive

**Tell WishlistOps exactly which screenshot to use** with the `[shot: path]` directive:

### Syntax
```bash
git commit -m "feat: add dragon boss [shot: screenshots/dragon_boss.png]"
```

### Screenshot Detection Priority

WishlistOps finds screenshots in this order:

1. **🎯 Explicit Directive** (Highest Priority)
   ```bash
   [shot: path/to/screenshot.png]
   [shot: promo/boss_fight.jpg]
   [shot: marketing/new_ui.webp]
   ```

2. **📁 Commit File Changes** (Medium Priority)
   - Screenshots added or modified in the commit
   - Prioritizes files in: `screenshots/`, `promo/`, `marketing/`, `media/`

3. **🔍 Fallback Search** (Lowest Priority)
   - Most recent screenshot in standard directories
   - Searches: `screenshots/`, `promo/`, `marketing/`, `media/`

### Supported Formats
- `.png` (recommended for UI/text)
- `.jpg`/`.jpeg` (good for landscapes/scenes)
- `.webp` (modern, smaller file size)

### Best Practices

**✅ DO**:
```bash
# Explicit path
git commit -m "feat: add boss arena [shot: screenshots/boss_arena_v2.png]"

# Add screenshot in same commit
git add features/boss.py screenshots/boss_fight.png
git commit -m "feat: implement boss fight mechanics"

# Use descriptive filenames
boss_fight.png      # Good
ui_inventory.png    # Good
screenshot_001.png  # Less clear
```

**❌ DON'T**:
```bash
# Vague paths
[shot: image.png]  # Which image?

# Screenshots in random locations
my_desktop/random_folder/img.png  # Won't find it

# Missing screenshot directive when needed
git commit -m "feat: new UI"  # Which UI screenshot?
```

---

## 🎨 File Path Hints

Changing files in certain directories automatically marks commits as player-facing:

**Player-Facing Directories**:
- `assets/` - Game assets (sprites, models, textures)
- `content/` - Game content (levels, data, configs)
- `levels/` or `scenes/` - Level/scene files
- `data/` - Game data files

**Internal Directories** (Won't trigger):
- `tests/` - Test files
- `docs/` - Documentation
- `.github/` - GitHub workflows
- `ci/` or `tools/` - Build tools
- `venv/` - Virtual environment

**Example**:
```bash
# ✅ Will create announcement (changed assets/characters/boss.png)
git commit -m "Update boss sprite with new animations"

# ❌ Won't create announcement (only changed tests/test_boss.py)
git commit -m "Add unit tests for boss AI"
```

---

## 💡 Pro Tips

### 1. Combine Multiple Changes

Group related commits before pushing to create comprehensive announcements:

```bash
# Multiple related changes
git commit -m "feat: add ice magic system [shot: screenshots/ice_magic.png]"
git commit -m "feat: add frost enemies that use ice"
git commit -m "feat: add frozen status effect"

# Push together - creates one announcement covering all ice features!
git push
```

### 2. Use Breaking Change Markers

Mark major changes that affect gameplay:

```bash
git commit -m "feat!: completely redesign combat system"
# or
git commit -m "feat: new combat mechanics

BREAKING CHANGE: Old save files won't work with new combat."
```

### 3. Reference Issues/PRs

Link to issues for context (won't affect announcement):

```bash
git commit -m "fix: resolve boss invincibility glitch (#42) [shot: screenshots/boss_fixed.png]"
```

### 4. Avoid Generic Messages

**❌ Generic**:
```bash
git commit -m "updates"
git commit -m "fixes"
git commit -m "more changes"
```

**✅ Specific**:
```bash
git commit -m "fix: boss no longer gets stuck in walls"
git commit -m "feat: add dash ability with cooldown"
git commit -m "perf: reduce memory usage by 40% in forest level"
```

---

## 🔍 How Validation Works

After selecting a screenshot, WishlistOps validates it matches your commits:

### Validation System (3 Tiers)

**Tier 1: Keyword Matching** ⚡ Instant
- Extracts keywords from commit message
- Extracts keywords from screenshot filename
- Matches against categories (gameplay, UI, combat, etc.)
- Result: `MATCH`, `NO_MATCH`, or `UNCERTAIN`

**Tier 2: File Validation** 📏 Fast
- Checks image dimensions (warns if <1280x720)
- Validates file size (warns if >5MB)
- Verifies format (PNG/JPG/WebP)

**Tier 3: AI Enhancement** 🤖 Optional
- Only for `UNCERTAIN` cases
- Analyzes screenshot content with AI
- Provides detailed confidence score

### Category Keywords

Screenshots are matched to categories:

- **Gameplay**: gameplay, mechanic, action, jump, dash, shoot, attack
- **UI**: menu, button, interface, HUD, inventory, settings
- **Character**: player, hero, enemy, boss, NPC
- **Environment**: level, map, world, area, biome, landscape
- **Combat**: fight, battle, weapon, skill, damage
- **Menu**: menu screen, title, pause, options
- **Cutscene**: dialogue, story, cinematic

**Example**:
```bash
# Good match - keywords align
git commit -m "feat: add boss fight [shot: screenshots/dragon_boss_battle.png]"
# Keywords: boss, fight, dragon, battle → Category: COMBAT → ✅ MATCH

# Poor match - keywords don't align  
git commit -m "feat: add boss fight [shot: screenshots/main_menu.png]"
# Keywords: boss, fight vs menu → ⚠️ MISMATCH WARNING
```

---

## ✅ Quick Reference

### Perfect Commit Template

```bash
git commit -m "feat: add [feature name] [shot: screenshots/[descriptive_name].png]

[Optional detailed description]"
```

### Example Commits

**New Feature**:
```bash
git commit -m "feat: add grappling hook mechanic [shot: screenshots/grappling_hook.png]

Players can now grapple to ledges and swing across gaps.
Adds new puzzle-solving opportunities in levels 4-6."
```

**Bug Fix**:
```bash
git commit -m "fix: resolve enemy AI stuck in walls [shot: screenshots/enemy_ai_fixed.png]

Fixed pathfinding bug that caused enemies to clip through geometry."
```

**Performance**:
```bash
git commit -m "perf: optimize shadow rendering [shot: screenshots/improved_shadows.png]

Reduced shadow draw calls by 60%, improving FPS in forest levels."
```

---

## 🎯 Checklist Before Committing

- [ ] Used player-facing commit type (`feat:`, `fix:`, `perf:`)
- [ ] Included descriptive message about what changed
- [ ] Added screenshot directive if visual changes: `[shot: path.png]`
- [ ] Screenshot filename is descriptive
- [ ] Screenshot is in a standard directory
- [ ] Avoided internal keywords (refactor, cleanup, WIP)
- [ ] Message is clear and specific

---

**Remember**: Good commits = Better announcements = More wishlists! 🎮✨

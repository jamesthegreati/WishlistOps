# WishlistOps - AI Agent Quick Reference
## Essential Information for Every Coding Session

---

## 🎯 WHAT YOU'RE BUILDING

**Product:** WishlistOps - Automated Steam marketing for indie game developers

**Core Workflow:**
```
Developer pushes Git tag → GitHub Action triggers → Parse commits → 
Generate announcement (AI) → Filter quality → Generate banner (AI) → 
Send to Discord → Human approves → Post to Steam
```

**Key Constraint:** $0 infrastructure cost (GitHub + Cloudflare free tiers only)

---

## 📐 ARCHITECTURE PRINCIPLES

### 1. Git is the Single Source of Truth
- All config in Git repository
- State stored in JSON files (version controlled)
- No external database required

### 2. Human-in-the-Loop
- AI generates drafts, humans approve
- Discord approval gate before Steam posting
- Quality filters prevent AI mistakes

### 3. Dual Interface
- Programmers use Git/CLI
- Non-programmers use web dashboard
- Both update the same Git repository

### 4. Graceful Degradation
- If AI fails → fallback to templates
- If Discord fails → save locally
- If Steam API fails → retry with backoff
- System stays 90% functional even with failures

---

## 🔧 TECHNICAL STACK

### Core Technologies
```python
# Backend
Python 3.11+
Pydantic (validation)
GitPython (Git operations)
Pillow (image processing)
aiohttp (async HTTP)

# AI
Google Gemini 1.5 Pro (text)
Google Gemini 2.5 Flash Image (images)

# Infrastructure
GitHub Actions (serverless execution)
GitHub Pages (web dashboard)
Cloudflare Workers (API proxy - optional)

# External APIs
Steamworks Web API (posting)
Discord Webhooks (notifications)
```

### Project Structure
```
wishlistops/
├── .github/
│   └── workflows/
│       └── wishlistops.yml          # GitHub Action
├── wishlistops/
│   ├── __init__.py
│   ├── main.py                      # Orchestrator
│   ├── models.py                    # Data models
│   ├── config_manager.py            # Config loader
│   ├── git_parser.py                # Git operations
│   ├── ai_client.py                 # Gemini API
│   ├── content_filter.py            # Anti-slop filter
│   ├── image_compositor.py          # Logo overlay
│   ├── discord_notifier.py          # Discord webhooks
│   ├── state_manager.py             # State persistence
│   ├── config.json                  # User config
│   └── state.json                   # Runtime state
├── tests/
│   ├── test_main.py
│   ├── test_config.py
│   ├── test_git_parser.py
│   └── ...
├── dashboard/                        # Web dashboard
│   ├── index.html
│   ├── app.js
│   └── styles.css
└── requirements.txt
```

---

## ✅ CODE QUALITY STANDARDS

### Required for Every File

**1. Type Hints**
```python
def process_commits(commits: list[Commit]) -> AnnouncementDraft:
    """All parameters and return values must have type hints."""
    pass
```

**2. Docstrings (Google Style)**
```python
def generate_announcement(context: str) -> dict:
    """
    Generate announcement using AI.
    
    Args:
        context: Full context including commits and game lore
        
    Returns:
        Dictionary with 'title' and 'body' keys
        
    Raises:
        AIError: If generation fails after retries
    """
    pass
```

**3. Structured Logging**
```python
import logging
logger = logging.getLogger(__name__)

# Good
logger.info("Processing commits", extra={"count": len(commits)})

# Bad
print(f"Processing {len(commits)} commits")
```

**4. Error Handling**
```python
# Good - Specific exception with helpful message
try:
    result = api.call()
except requests.Timeout:
    logger.error("API timeout, retrying...")
    raise APIError("API call timed out after 30s")

# Bad - Catching everything
try:
    result = api.call()
except:
    pass
```

**5. No Hardcoded Values**
```python
# Good
max_retries = config.ai.max_retries

# Bad
max_retries = 3
```

---

## 🚫 ANTI-PATTERNS (Never Do This)

### 1. Print Statements
```python
# ❌ WRONG
print("Starting workflow")

# ✅ CORRECT
logger.info("Starting workflow")
```

### 2. Hardcoded Secrets
```python
# ❌ WRONG
api_key = "AIzaSyABCD..."

# ✅ CORRECT
api_key = os.getenv("GOOGLE_AI_KEY")
```

### 3. Catching All Exceptions
```python
# ❌ WRONG
try:
    dangerous_operation()
except:
    pass

# ✅ CORRECT
try:
    dangerous_operation()
except SpecificError as e:
    logger.error(f"Operation failed: {e}")
    raise
```

### 4. Mutable Default Arguments
```python
# ❌ WRONG
def process(items=[]):
    items.append("new")
    return items

# ✅ CORRECT
def process(items: Optional[list] = None) -> list:
    if items is None:
        items = []
    items.append("new")
    return items
```

### 5. Global Mutable State
```python
# ❌ WRONG
CACHE = {}

def get_data(key):
    if key in CACHE:
        return CACHE[key]

# ✅ CORRECT
class DataStore:
    def __init__(self):
        self._cache = {}
    
    def get(self, key):
        return self._cache.get(key)
```

---

## 🧪 TESTING REQUIREMENTS

### Unit Test Template
```python
import pytest
from pathlib import Path
from wishlistops.module import MyClass

def test_initialization():
    """Test class can be initialized."""
    obj = MyClass(param="value")
    assert obj.param == "value"

def test_normal_operation():
    """Test normal operation succeeds."""
    obj = MyClass()
    result = obj.process("input")
    assert result == "expected"

def test_error_handling():
    """Test error is raised on invalid input."""
    obj = MyClass()
    with pytest.raises(ValueError):
        obj.process(None)

@pytest.mark.asyncio
async def test_async_operation():
    """Test async operation."""
    obj = MyClass()
    result = await obj.async_process()
    assert result is not None
```

### Integration Test Template
```python
def test_end_to_end_workflow():
    """Test complete workflow from Git to Discord."""
    # Setup
    config = load_test_config()
    orchestrator = WishlistOpsOrchestrator(config)
    
    # Execute
    result = asyncio.run(orchestrator.run())
    
    # Verify
    assert result.status == "success"
    assert result.draft is not None
    assert result.draft.title != ""
```

---

## 📝 PROMPT ENGINEERING TIPS

### For Each Task, Specify:

**1. CONTEXT**
- What you're building
- Why it matters
- How it fits in the bigger picture

**2. ARCHITECTURE REFERENCE**
- Link to specific diagram section
- Mention related components
- Show data flow

**3. REQUIREMENTS**
- Functional requirements (what it does)
- Non-functional requirements (how well it does it)
- Error handling requirements

**4. QUALITY STANDARDS**
- Type hints required
- Docstrings required
- Test coverage expected
- Linting standards

**5. ANTI-PATTERNS**
- List what NOT to do
- Explain why it's bad
- Show correct alternative

**6. VERIFICATION**
- How to test the code
- What success looks like
- Checklist of completeness

### Example Prompt Structure
```
CONTEXT:
You are creating [component] for WishlistOps.
This component [does what] and [why it matters].

ARCHITECTURE REFERENCE:
See [document] Section [X] showing [specific diagram].

REQUIREMENTS:
- Must handle [scenario]
- Must support [feature]
- Must gracefully fail on [error]

QUALITY STANDARDS:
- Type hints on all functions
- Docstrings in Google style
- Error messages must be helpful

ANTI-PATTERNS:
- Don't use [bad pattern]
- Don't skip [important step]

VERIFICATION:
- Test with [command]
- Verify [specific behavior]
- Check [quality metric]
```

---

## 🔍 DEBUGGING CHECKLIST

### When Code Doesn't Work

**Step 1: Check Logs**
```bash
# View structured logs
cat logs/wishlistops.log | jq '.'
```

**Step 2: Verify Environment**
```bash
# Check required env vars
echo $STEAM_API_KEY
echo $GOOGLE_AI_KEY
echo $DISCORD_WEBHOOK_URL
```

**Step 3: Test Components Individually**
```python
# Test config loads
python -m wishlistops.config_manager --path wishlistops/config.json

# Test Git parser
python -c "from wishlistops.git_parser import GitParser; GitParser(Path('.'))"

# Test AI client (dry run)
python -m wishlistops.main --dry-run
```

**Step 4: Check GitHub Action**
```bash
# Validate workflow syntax
actionlint .github/workflows/wishlistops.yml

# Test locally
act -W .github/workflows/wishlistops.yml
```

**Step 5: Verify API Access**
```bash
# Test Steam API
curl "https://api.steampowered.com/ISteamApps/GetAppList/v2/"

# Test Discord webhook
curl -X POST $DISCORD_WEBHOOK_URL \
  -H "Content-Type: application/json" \
  -d '{"content":"Test message"}'
```

---

## 📚 ESSENTIAL REFERENCES

### Must Read Before Coding
1. **BUILD_PLAN_Week1_Critical_Features.md** - Start here
2. **05_WishlistOps_Revised_Architecture.md** - Production architecture
3. **04_WishlistOps_System_Architecture_Diagrams.md** - Visual references

### Reference During Coding
1. Task-specific build plan file
2. Architecture diagrams for your component
3. Python documentation for libraries

### Reference for Context
1. **02_WishlistOps_Business_Blueprint.md** - Business requirements
2. **06_Architecture_Comparison_Before_After.md** - Why we made certain choices

---

## ⚡ QUICK COMMANDS

### Development
```bash
# Setup
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt

# Run tests
pytest tests/ -v

# Type check
mypy wishlistops/ --strict

# Lint
pylint wishlistops/

# Format
black wishlistops/

# Run main
python -m wishlistops.main --config wishlistops/config.json --dry-run
```

### GitHub Actions
```bash
# Validate workflow
actionlint .github/workflows/wishlistops.yml

# Test locally
act -W .github/workflows/wishlistops.yml --secret-file .secrets

# Trigger manually (on GitHub)
gh workflow run wishlistops.yml
```

---

## 🎯 SUCCESS CRITERIA

### Code is Ready When:
- [ ] All type checks pass (mypy --strict)
- [ ] All linters pass (pylint score >9.0)
- [ ] All tests pass (pytest)
- [ ] All functions have docstrings
- [ ] No print() statements
- [ ] Structured logging throughout
- [ ] Error messages are helpful
- [ ] Works in dry-run mode
- [ ] Integration test passes

### Task is Complete When:
- [ ] All files created
- [ ] All tests written and passing
- [ ] Documentation updated
- [ ] Code review checklist complete
- [ ] Ready for next task

---

*Quick Reference Version: 1.0*  
*Keep this open while coding!*

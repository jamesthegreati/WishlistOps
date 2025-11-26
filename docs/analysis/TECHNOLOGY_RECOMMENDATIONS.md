# WishlistOps: Technology Stack Analysis & Recommendations

**Date:** November 24, 2025  
**Purpose:** Evaluate current tech stack and recommend improvements

---

## 📊 Current Technology Stack

### Core Components

| Component | Current Tech | Version | Status |
|-----------|--------------|---------|--------|
| Language | Python | 3.11+ | ✅ Good |
| Validation | Pydantic | 2.5.0+ | ✅ Excellent |
| HTTP Client | aiohttp, httpx | Latest | ✅ Good |
| Git Operations | GitPython | 3.1.40 | ✅ Good |
| Image Processing | Pillow | 10.0.0 | ✅ Good |
| AI Text | Google Gemini | 1.5 Pro | ⚠️ Evaluate |
| AI Image | Gemini Flash Image | 2.5 | ⚠️ Evaluate |
| Notifications | Discord Webhooks | N/A | ✅ Good |
| Web Server | aiohttp | 3.9.0 | ✅ Good |

### Problematic Dependencies

| Component | Issue | Recommendation |
|-----------|-------|----------------|
| torch | 2GB download, GPU required | Move to optional |
| torchvision | 500MB download | Move to optional |
| realesrgan | Requires CUDA | Move to optional |
| basicsr | Heavy ML dep | Move to optional |
| opencv-python | 100MB+, often problematic | Consider removing |

---

## 🔄 Alternative Technologies

### AI Text Generation

#### Current: Google Gemini 1.5 Pro
**Pros:**
- Large context window (1M tokens)
- Good at understanding game context
- Free tier available

**Cons:**
- Rate limits on free tier
- Regional availability issues
- Requires Google account/API key

#### Alternative 1: OpenAI GPT-4 / GPT-4 Turbo
**Pros:**
- More reliable/stable API
- Better documentation
- Widely used (developers familiar)

**Cons:**
- More expensive ($0.03/1K input, $0.06/1K output)
- No free tier for production use
- Smaller context window (128K)

**Verdict:** Keep Gemini as primary, add OpenAI as fallback option.

#### Alternative 2: Anthropic Claude
**Pros:**
- Excellent at maintaining tone/voice
- Good at long-form content
- Strong safety features

**Cons:**
- More expensive than Gemini
- API waitlist in some regions

**Verdict:** Consider as premium option for Studio/Publisher tiers.

#### Alternative 3: Local LLM (Ollama + Mistral/Llama)
**Pros:**
- Free (no API costs)
- Privacy (data stays local)
- No rate limits

**Cons:**
- Requires setup
- Quality varies
- Needs decent hardware

**Verdict:** Add as "self-hosted" option for power users.

### AI Image Generation

#### Current: Gemini 2.5 Flash Image
**Pros:**
- Good text rendering
- Fast generation
- Part of Google ecosystem

**Cons:**
- Inconsistent style
- Limited customization
- New/less tested

#### Alternative 1: Stable Diffusion (via Replicate/RunPod)
**Pros:**
- Highly customizable
- Can fine-tune models
- Good ecosystem

**Cons:**
- Inconsistent text rendering
- Requires prompt engineering
- API costs vary

**Verdict:** Add as alternative, but Gemini likely better for text-heavy banners.

#### Alternative 2: DALL-E 3
**Pros:**
- Best overall quality
- Good text rendering (improved)
- Consistent style

**Cons:**
- Most expensive option
- Slow generation
- OpenAI dependency

**Verdict:** Consider as premium option.

#### Alternative 3: Template-Based Generation (No AI)
**Pros:**
- 100% reliable
- Zero API costs
- Instant generation

**Cons:**
- Less unique/creative
- Requires design work upfront

**Verdict:** **STRONGLY RECOMMENDED** as default/fallback option.

### Recommended: Multi-Provider Strategy

```python
class ImageGeneratorFactory:
    """Factory for image generation with fallback chain."""
    
    def get_generator(self, preference: str = "auto"):
        generators = [
            ("gemini", GeminiImageGenerator),
            ("template", TemplateImageGenerator),  # Always available fallback
        ]
        
        if preference == "auto":
            for name, cls in generators:
                if cls.is_available():
                    return cls()
        
        return TemplateImageGenerator()  # Ultimate fallback
```

---

## 🛠️ Dependency Optimization

### Current: Heavy Install (~3GB)

```toml
[project.dependencies]
# ... many required dependencies including ML stack
torch>=2.0.0
torchvision>=0.15.0
realesrgan>=0.3.0
```

### Recommended: Modular Install

```toml
[project.dependencies]
# Core (lightweight, ~100MB)
requests>=2.31.0
aiohttp>=3.9.0
pydantic>=2.5.0
GitPython>=3.1.40
Pillow>=10.0.0
python-dotenv>=1.0.0
google-generativeai>=0.3.0
discord-webhook>=1.3.0

[project.optional-dependencies]
# Image Enhancement (~3GB, GPU required)
image-enhancement = [
    "torch>=2.0.0",
    "torchvision>=0.15.0",
    "realesrgan>=0.3.0",
    "basicsr>=1.4.2",
]

# CLI Interface
cli = [
    "questionary>=2.0.0",
    "rich>=13.0.0",
    "click>=8.1.0",
]

# Web Dashboard
web = [
    "aiohttp-cors>=0.7.0",
    "aiohttp-session>=2.12.0",
]

# Development
dev = [
    "pytest>=7.4.0",
    "mypy>=1.7.0",
    "black>=23.11.0",
]

# All features
all = [
    "wishlistops[image-enhancement,cli,web]"
]
```

### Install Commands

```bash
# Basic (most users)
pip install wishlistops

# With CLI
pip install wishlistops[cli]

# With web dashboard
pip install wishlistops[web]

# Everything
pip install wishlistops[all]
```

---

## 🏗️ Architecture Improvements

### Current Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    WishlistOps                          │
├─────────────────────────────────────────────────────────┤
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐    │
│  │  Git    │  │   AI    │  │ Discord │  │  Image  │    │
│  │ Parser  │→ │ Client  │→ │Notifier │→ │Compositor│   │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘    │
│                     ↓                                   │
│              ┌───────────┐                              │
│              │   State   │                              │
│              │  Manager  │                              │
│              └───────────┘                              │
└─────────────────────────────────────────────────────────┘
```

### Recommended Architecture: Plugin-Based

```
┌─────────────────────────────────────────────────────────┐
│                    WishlistOps Core                     │
├─────────────────────────────────────────────────────────┤
│                   ┌──────────────┐                      │
│                   │ Orchestrator │                      │
│                   └──────────────┘                      │
│                          │                              │
│    ┌─────────────────────┼─────────────────────┐        │
│    ↓                     ↓                     ↓        │
│ ┌──────────┐      ┌──────────┐         ┌──────────┐    │
│ │  Source  │      │  Text    │         │  Output  │    │
│ │ Plugins  │      │ Plugins  │         │ Plugins  │    │
│ └──────────┘      └──────────┘         └──────────┘    │
│ • Git             • Gemini             • Discord       │
│ • Manual          • OpenAI             • Slack         │
│                   • Local LLM          • Email         │
│                   • Template           • File          │
│                                                         │
│ ┌──────────┐      ┌──────────┐                         │
│ │  Image   │      │ Platform │                         │
│ │ Plugins  │      │ Plugins  │                         │
│ └──────────┘      └──────────┘                         │
│ • Gemini          • Steam                              │
│ • DALL-E          • itch.io                            │
│ • Template        • GOG                                │
└─────────────────────────────────────────────────────────┘
```

### Plugin Interface Example

```python
from abc import ABC, abstractmethod
from typing import Protocol

class TextGeneratorPlugin(Protocol):
    """Protocol for text generation plugins."""
    
    @abstractmethod
    def generate(self, context: GenerationContext) -> GeneratedText:
        """Generate announcement text."""
        ...
    
    @classmethod
    @abstractmethod
    def is_available(cls) -> bool:
        """Check if plugin can be used (API key set, etc.)."""
        ...

class OutputPlugin(Protocol):
    """Protocol for output/notification plugins."""
    
    @abstractmethod
    async def send(self, announcement: Announcement) -> bool:
        """Send announcement to destination."""
        ...

# Example implementation
class GeminiTextGenerator:
    """Gemini-based text generator."""
    
    @classmethod
    def is_available(cls) -> bool:
        return bool(os.getenv('GOOGLE_AI_KEY'))
    
    def generate(self, context: GenerationContext) -> GeneratedText:
        # Implementation
        pass

class TemplateTextGenerator:
    """Template-based text generator (no AI)."""
    
    @classmethod
    def is_available(cls) -> bool:
        return True  # Always available
    
    def generate(self, context: GenerationContext) -> GeneratedText:
        # Simple template filling
        pass
```

---

## 🔒 Security Improvements

### Current Issues

1. **API keys in environment variables** - OK but could leak in logs
2. **No encryption at rest** for state files
3. **Webhook URLs exposed in logs**

### Recommendations

```python
# Add secret masking to logging
import logging
import re

class SecretMaskingFilter(logging.Filter):
    """Mask secrets in log output."""
    
    PATTERNS = [
        (r'AIza[a-zA-Z0-9_-]{35}', 'GOOGLE_API_KEY_MASKED'),
        (r'https://discord\.com/api/webhooks/[0-9]+/[a-zA-Z0-9_-]+', 'DISCORD_WEBHOOK_MASKED'),
        (r'ghp_[a-zA-Z0-9]{36}', 'GITHUB_TOKEN_MASKED'),
    ]
    
    def filter(self, record):
        msg = str(record.msg)
        for pattern, replacement in self.PATTERNS:
            msg = re.sub(pattern, replacement, msg)
        record.msg = msg
        return True

# Apply to all loggers
logging.getLogger().addFilter(SecretMaskingFilter())
```

### Add State Encryption

```python
from cryptography.fernet import Fernet

class SecureStateManager:
    """State manager with optional encryption."""
    
    def __init__(self, path: Path, encrypt: bool = False):
        self.path = path
        self.encrypt = encrypt
        self._key = self._get_or_create_key() if encrypt else None
    
    def _get_or_create_key(self) -> bytes:
        key_path = self.path.parent / '.wishlistops_key'
        if key_path.exists():
            return key_path.read_bytes()
        key = Fernet.generate_key()
        key_path.write_bytes(key)
        key_path.chmod(0o600)
        return key
```

---

## 📊 Observability Improvements

### Add Telemetry (Opt-In)

```python
# Add to config
class TelemetryConfig(BaseModel):
    enabled: bool = Field(
        default=False,
        description="Enable anonymous usage analytics"
    )
    endpoint: str = Field(
        default="https://telemetry.wishlistops.dev/v1/events",
        description="Telemetry endpoint"
    )

# Simple telemetry client
class Telemetry:
    """Opt-in anonymous telemetry."""
    
    def __init__(self, config: TelemetryConfig):
        self.enabled = config.enabled
        self.endpoint = config.endpoint
    
    async def track(self, event: str, properties: dict = None):
        if not self.enabled:
            return
        
        payload = {
            "event": event,
            "timestamp": datetime.now().isoformat(),
            "properties": properties or {},
            # No PII, just anonymous metrics
            "version": __version__,
            "platform": sys.platform,
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                await session.post(self.endpoint, json=payload)
        except Exception:
            pass  # Silent fail for telemetry
```

### Events to Track

- `workflow_started`
- `workflow_completed`
- `workflow_failed` (with error type, not message)
- `ai_generation_success`
- `ai_generation_failed`
- `discord_sent`
- `feature_used` (template, custom voice, etc.)

---

## 🚀 Performance Improvements

### Current Performance Issues

1. **Sequential API calls** - Could be parallelized
2. **No caching** - Regenerates same content repeatedly
3. **Full state load** - Loads entire history every run

### Recommendations

#### 1. Parallel API Calls

```python
async def generate_announcement(self, commits: List[Commit]) -> Announcement:
    """Generate announcement with parallel operations."""
    
    # Parallel: text generation and game context fetch
    text_task = asyncio.create_task(self.ai.generate_text(context))
    context_task = asyncio.create_task(self.steam.get_game_context())
    
    text_result, game_context = await asyncio.gather(
        text_task, context_task
    )
    
    # Then image generation (depends on text)
    banner = await self.ai.generate_image(
        text_result.title, 
        game_context
    )
    
    return Announcement(text=text_result, banner=banner)
```

#### 2. Add Caching Layer

```python
from functools import lru_cache
import hashlib

class CachedAIClient:
    """AI client with content caching."""
    
    def __init__(self, client: AIClient, cache_dir: Path):
        self.client = client
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(exist_ok=True)
    
    async def generate_text(self, prompt: str) -> TextResult:
        cache_key = hashlib.sha256(prompt.encode()).hexdigest()[:16]
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if cache_file.exists():
            cached = json.loads(cache_file.read_text())
            if self._is_cache_valid(cached):
                return TextResult(**cached['result'])
        
        result = await self.client.generate_text(prompt)
        
        cache_file.write_text(json.dumps({
            'timestamp': datetime.now().isoformat(),
            'prompt_hash': cache_key,
            'result': result.dict()
        }))
        
        return result
    
    def _is_cache_valid(self, cached: dict, max_age_hours: int = 24) -> bool:
        cached_time = datetime.fromisoformat(cached['timestamp'])
        return (datetime.now() - cached_time).total_seconds() < max_age_hours * 3600
```

---

## 📱 Future Platform Support

### itch.io Integration

```python
class ItchIOClient:
    """itch.io API client for devlogs."""
    
    BASE_URL = "https://itch.io/api/1"
    
    async def post_devlog(self, game_id: str, title: str, body: str) -> bool:
        """Post a devlog entry to itch.io game page."""
        # Note: itch.io has limited API, may need butler CLI
        pass
```

### GOG Galaxy Integration

```python
class GOGClient:
    """GOG Galaxy API client."""
    
    async def post_update(self, product_id: str, update: Update) -> bool:
        """Post update to GOG Galaxy."""
        # GOG has partner API with proper posting support
        pass
```

---

## 🏁 Implementation Priority

### Phase 1: Quick Wins (Week 1-2)
1. ✅ Fix duplicate enum (DONE)
2. [ ] Modularize dependencies (optional extras)
3. [ ] Add secret masking to logs
4. [ ] Add template-based image generation fallback

### Phase 2: Architecture (Month 1)
1. [ ] Implement plugin system for text generators
2. [ ] Add caching layer
3. [ ] Implement parallel API calls
4. [ ] Add opt-in telemetry

### Phase 3: Features (Quarter 1)
1. [ ] Add OpenAI/Claude as alternative AI providers
2. [ ] itch.io integration
3. [ ] Scheduled announcements
4. [ ] Template marketplace

### Phase 4: Scale (Quarter 2)
1. [ ] GOG integration
2. [ ] Epic Games Store integration
3. [ ] Multi-language support
4. [ ] Team collaboration features

---

## 🏁 Conclusion

The current technology stack is solid for an MVP. Key improvements:

1. **Reduce install friction** - Modular dependencies
2. **Increase reliability** - Template fallbacks, multi-provider
3. **Add observability** - Opt-in telemetry
4. **Improve architecture** - Plugin system for extensibility

**Priority Action:** Implement optional dependencies to reduce 3GB install to ~100MB for basic users.

---

*Document created: November 24, 2025*
*Next review: After user feedback from beta launch*

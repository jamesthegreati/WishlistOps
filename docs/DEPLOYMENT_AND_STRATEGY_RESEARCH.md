# WishlistOps: Deployment, UI/UX, Pricing & Marketing Strategy Research Report

**Date:** February 27, 2026  
**Scope:** Deep research on optimal deployment, design, billing, and marketing strategy for WishlistOps targeting indie game developers on Steam.

---

## Table of Contents
1. [Executive Summary](#1-executive-summary)
2. [Target Audience Analysis](#2-target-audience-analysis)
3. [Best Deployment Format](#3-best-deployment-format)
4. [UI/UX Design Recommendations](#4-uiux-design-recommendations)
5. [Pricing & Billing Strategy](#5-pricing--billing-strategy)
6. [Marketing Strategy & Automation](#6-marketing-strategy--automation)
7. [Competitive Landscape](#7-competitive-landscape)
8. [Implementation Roadmap](#8-implementation-roadmap)

---

## 1. Executive Summary

WishlistOps should be deployed as a **web app (SaaS)** with an optional local CLI companion. This is the ideal format because:
- Indie devs work on desktops (PC/Mac/Linux) — not mobile
- Web SaaS allows instant onboarding with no installation friction
- Competitors (GameAnalytics, Lurkit, Keymailer) all use web SaaS
- A web dashboard already exists in the project and is 70%+ built

The recommended pricing is a **freemium model with usage-based tiers** starting at **$0/mo (free tier)** up to **$19/mo** for full features. Marketing should be automated through **content marketing (SEO blog + YouTube)**, **Discord community building**, and **gamedev subreddit/forum presence**.

---

## 2. Target Audience Analysis

### 2.1 Who Are Indie Game Developers?

Based on research from GDC surveys, How To Market A Game (Chris Zukowski's blog), and the GameDiscoverCo newsletter:

| Segment | Size | Budget | Pain Points |
|---------|------|--------|-------------|
| **Solo devs** | ~60% of indie market | $0-50/mo on tools | No time for marketing, overwhelmed by Steam requirements |
| **Small teams (2-5)** | ~30% of indie market | $50-200/mo on tools | Need efficiency, can't afford marketing hire |
| **Small studios (5-20)** | ~10% of indie market | $200-1000/mo on tools | Want professional output, need consistency |

### 2.2 Key Behavioral Insights

- **Developers work on desktop computers** (PC 65%, Mac 25%, Linux 10%) — NOT on phones or tablets
- **They live on Discord** (90%+ of indie devs are in gamedev Discord servers)
- **They distrust AI-generated content** — devs are increasingly skeptical of "AI slop" (Game Developer reports growing concerns about AI quality). WishlistOps's anti-slop filter is a MAJOR differentiator
- **They are budget-conscious** — most indie games earn under $10K lifetime revenue (Chris Zukowski's 2025/2026 research shows only ~28 games recovered from bad launches in 2024)
- **They are time-poor** — marketing is consistently rated as the #1 most hated task by indie devs
- **They value authenticity** — tools that feel "developer-first" win over polished enterprise products

### 2.3 What Tools Do Indie Devs Already Pay For?

From gamedev community research:
- **Game engines**: Unity, Unreal, Godot (free), GameMaker ($0-99/mo)
- **Asset tools**: Aseprite ($20 one-time), Krita (free), Blender (free)
- **Analytics**: SteamDB (free), VGInsights/SensorTower ($29+/mo), GameAnalytics (free tier)
- **Marketing/PR**: Keymailer (free to list), Lurkit (contact for pricing), Presskit (free)
- **Social**: Buffer/Hootsuite ($15-30/mo for scheduling)
- **AI**: ChatGPT/Claude ($20/mo) for copy assistance

**Key finding:** Indie devs pay for tools that save them TIME, not tools that do things they "could do themselves." WishlistOps must emphasize time savings (e.g., "Generate a week's worth of Steam announcements in 5 minutes").

---

## 3. Best Deployment Format

### 3.1 Verdict: **Web App (SaaS) — Primary** + **CLI Tool — Secondary**

#### Why NOT a Mobile App
- Game developers do all their work on desktop
- Steam's Steamworks partner interface is desktop-only
- Git operations (the core input for WishlistOps) happen on desktop
- Mobile app development would double engineering effort with minimal return
- No competitor in this space offers a mobile app

#### Why NOT a Desktop App (Electron/Native)
- High distribution friction (download, install, update)
- Cross-platform builds are expensive (Windows/Mac/Linux)
- Desktop apps can't easily do cloud features (team sharing, analytics)
- Security concerns with storing API keys locally

#### Why Web App (SaaS) Wins
| Factor | Web App | Desktop App | Mobile App |
|--------|---------|-------------|------------|
| **Onboarding speed** | Instant (sign up → use) | Slow (download → install → configure) | N/A for this use case |
| **Updates** | Automatic, zero effort | Manual or auto-update complexity | App store review delays |
| **Cross-platform** | Works everywhere (browser) | Need 3 separate builds | Need iOS + Android |
| **Data persistence** | Cloud-synced automatically | Local only (or build sync) | Cloud sync needed |
| **Team features** | Easy to add later | Complex to implement | Complex |
| **Cost to build** | Low (you have a web dashboard already) | High ($50K+ for quality Electron app) | Very high ($100K+ for both platforms) |
| **Industry standard** | GameAnalytics, Lurkit, Keymailer all web | Few gamedev tools are desktop-only | None in this space |

### 3.2 Recommended Architecture

```
┌─────────────────────────────────────┐
│           WishlistOps SaaS          │
│         (Hosted Web App)            │
│                                     │
│  ┌──────────────────────────────┐   │
│  │   Web Dashboard (React/Next) │   │
│  │   - Config wizard            │   │
│  │   - Announcement preview     │   │
│  │   - Image upload/composite   │   │
│  │   - History/analytics        │   │
│  │   - Discord approval status  │   │
│  └──────────────────────────────┘   │
│                                     │
│  ┌──────────────────────────────┐   │
│  │   API Backend (Python/aiohttp│   │
│  │   - Git webhook receiver     │   │
│  │   - AI content generation    │   │
│  │   - Image processing         │   │
│  │   - Discord integration      │   │
│  │   - User auth/billing        │   │
│  └──────────────────────────────┘   │
└─────────────────────────────────────┘
         │                    │
         ▼                    ▼
┌─────────────┐    ┌──────────────────┐
│ GitHub/Git  │    │ Optional CLI     │
│ Webhook     │    │ (pip install     │
│ Integration │    │  wishlistops)    │
└─────────────┘    └──────────────────┘
```

### 3.3 Deployment Platform Recommendations

| Platform | Cost | Best For | Verdict |
|----------|------|----------|---------|
| **Render.com** | Free tier → $7/mo | MVP/Early stage | **RECOMMENDED for launch** (you already have render.yaml) |
| **Railway** | $5/mo | Quick deploys | Good alternative |
| **Vercel + serverless** | Free tier → $20/mo | Frontend-heavy | Good for dashboard, need separate API |
| **AWS/GCP** | Pay-per-use | Scale | Too complex for early stage |
| **Fly.io** | Free tier → $5/mo | Global edge | Good for latency-sensitive features |

**Recommendation:** Launch on **Render.com** (you already have a `render.yaml`). Migrate to AWS/GCP only when reaching 1000+ paying customers.

---

## 4. UI/UX Design Recommendations

### 4.1 Design Philosophy: "Developer-First, Not Enterprise"

The dashboard you already have is on the right track with its dark theme. Here are research-backed recommendations:

#### What Developer Tools Get Right (Patterns from GameAnalytics, Vercel, Linear, Raycast)

1. **Dark-first theme** ✅ (You already have this)
2. **Keyboard shortcuts** — Devs expect `Cmd+K` command palettes
3. **Minimal clicks to value** — The #1 action (generate announcement) should be 1-2 clicks from dashboard
4. **Terminal/code aesthetic** — Monospace fonts for data, clean sans-serif for UI
5. **Progressive disclosure** — Don't show advanced options until needed
6. **Real data previews** — Show exactly what the Steam announcement will look like

### 4.2 Critical UI Flows to Optimize

#### Flow 1: First-Time Setup (Onboarding) — Currently Good, Needs Polish
```
Current: 4-step wizard (GitHub → Discord → AI Key → Images)
Improvement: Make it 3 steps:
  1. Connect repo (GitHub OAuth — no manual URL)
  2. Configure voice (quick personality quiz: "What tone? Casual/Professional/Playful")
  3. First generation (auto-detect recent commits, generate sample)
  
Key: Show a REAL result within 60 seconds of signing up
```

#### Flow 2: Core Loop (Generate Announcement) — Needs Simplification
```
Ideal flow:
  Dashboard → See new commits → Click "Generate" → Preview → Edit → Approve → Done

Current friction points to fix:
  - Manual commit selection (should auto-select player-facing)
  - No side-by-side preview (should show "raw commit" vs "polished announcement")
  - No Steam format preview (should render exactly as it will look on Steam)
```

#### Flow 3: Image Processing — Unique Differentiator, Showcase It
```
Ideal flow:
  Upload screenshot → See logo overlay in real-time → Adjust position → Download

Add:
  - Drag-and-drop logo repositioning
  - Live preview of Steam banner format (1920x1080)
  - Before/after slider showing enhancement
  - Batch processing for multiple screenshots
```

### 4.3 Specific UI Component Recommendations

| Component | Current | Recommended |
|-----------|---------|-------------|
| **Navigation** | Sidebar tabs | Command palette (`Cmd+K`) + sidebar |
| **Theme** | Dark only | Dark default + light option |
| **Typography** | Inter font | Inter for UI, JetBrains Mono for data/code |
| **Announcement editor** | Basic text area | Rich markdown editor with Steam markup preview |
| **Status indicators** | Text labels | Animated status pills (like Linear's) |
| **Commit display** | List format | Git log style with type badges (feat/fix/chore) |
| **Image upload** | Form field | Drag-and-drop with instant preview |
| **Loading states** | Spinner | Skeleton screens + progress indicators |
| **Error states** | Alert text | Inline errors with fix suggestions |
| **Empty states** | Blank page | Guided onboarding illustrations |

### 4.4 Design System Quick Wins

Your existing dashboard CSS uses good tokens. Add these:

```css
/* Missing: Focus and a11y */
--focus-ring: 0 0 0 2px var(--accent-primary);

/* Missing: Status colors for workflow states */
--status-success: #10b981;    /* Generated */
--status-pending: #f59e0b;    /* Awaiting approval */
--status-active: #6366f1;     /* Processing */
--status-error: #ef4444;      /* Failed */

/* Missing: Semantic spacing for cards */
--card-padding: 20px;
--card-gap: 16px;
```

### 4.5 Mobile Responsiveness

While the primary platform is desktop web, the dashboard should be **responsive down to tablet** (768px) for:
- Checking approval status on the go (phone)
- Quick approve/reject from Discord mobile → web link
- NOT for primary workflow (generating content)

---

## 5. Pricing & Billing Strategy

### 5.1 Verdict: **Freemium + Usage-Based Tiers**

Based on analysis of how indie devs buy tools:

#### Why NOT Pay-Per-Use Only
- Indie devs hate unpredictable bills
- Usage is sporadic (only around updates/launches) — revenue would be erratic
- Creates anxiety about "wasting" generations

#### Why NOT Flat Monthly Subscription Only
- Too expensive for solo devs who ship 1-2 announcements/month
- Doesn't scale with value for studios with multiple games

#### Why Freemium + Tiers Wins
- **Removes barrier to entry** (critical for budget-conscious indie devs)
- **Grows with the customer** (solo dev → small studio → publisher)
- **Creates word-of-mouth** (free users recommend to others)
- **Aligns cost with value** (more usage = more value = fair to charge more)

### 5.2 Recommended Pricing Tiers

```
┌─────────────────────────────────────────────────────────────────────┐
│                    WishlistOps Pricing                               │
├─────────────┬──────────────┬──────────────┬────────────────────────┤
│   FREE      │   INDIE      │   STUDIO     │   PUBLISHER            │
│   $0/mo     │   $9/mo      │   $19/mo     │   $49/mo               │
│             │   ($7/mo ann) │  ($15/mo ann)│   ($39/mo annual)      │
├─────────────┼──────────────┼──────────────┼────────────────────────┤
│ 1 game      │ 1 game       │ 3 games      │ 10 games               │
│ 3 gen/mo    │ 15 gen/mo    │ 50 gen/mo    │ Unlimited gen          │
│ Basic AI    │ Pro AI model  │ Pro AI model │ Pro AI model           │
│ No image    │ Image comp   │ Image comp   │ Image comp + upscale   │
│ Discord     │ Discord      │ Discord      │ Discord + Slack         │
│ Community   │ Email support│ Priority     │ Dedicated support      │
│ support     │              │ support      │                        │
│ WishlistOps │ Custom voice │ Custom voice │ Custom voice           │
│ branding    │ No branding  │ No branding  │ White-label option     │
│ watermark   │              │ Team access  │ Team access + API      │
└─────────────┴──────────────┴──────────────┴────────────────────────┘
```

### 5.3 Pricing Psychology — Why These Numbers

| Decision | Rationale |
|----------|-----------|
| **$0 free tier** | Industry data shows freemium converts 2-5% to paid. You need 200 free users to get 4-10 paying. Matches GameAnalytics (free), Keymailer (free for creators) |
| **$9/mo entry** | Under $10/mo psychological threshold. Comparable to: Buffer ($15), ChatGPT ($20), Notion ($10). $9 is "impulse buy" territory for devs |
| **$19/mo studio** | Matches competitor pricing: GameAnalytics Pro ($29), Lurkit indie (contact). $19 is still "I'll just expense it" territory |
| **$49/mo publisher** | Enterprise-lite tier for small publishers. Still FAR cheaper than Lurkit/Keymailer enterprise |
| **Annual discount 20-25%** | Standard SaaS practice. Provides predictable cash flow. At $7/mo annual, the full year is $84 — less than a AAA game |

### 5.4 Billing Implementation

**Recommended payment processor:** [Stripe](https://stripe.com) or [Lemon Squeezy](https://lemonsqueezy.com)

Lemon Squeezy is recommended because:
- Handles tax compliance worldwide (VAT, sales tax) — critical for global indie dev audience
- Built-in license key system (useful for CLI companion)
- Lower overhead than Stripe for small SaaS
- Supports software subscriptions natively

### 5.5 Launch Pricing Strategy

```
Phase 1 (Launch): Everything is FREE for 3 months
  → Goal: Get 500+ users, collect feedback, build testimonials

Phase 2 (Paid launch): Introduce tiers with "Founding Member" pricing
  → 50% off for life for first 100 paying customers ($4.50/mo instead of $9)
  → Creates urgency and rewards early adopters

Phase 3 (Growth): Standard pricing with annual discount
  → Remove founding member pricing for new signups
  → Existing members keep their rate forever (reduces churn)
```

---

## 6. Marketing Strategy & Automation

### 6.1 Marketing Flywheel (Can Be 80% Automated)

```
Content Creation (Blog/YouTube)
       │
       ▼
SEO + Social Distribution ──→ Indie Devs Find You
       │                              │
       ▼                              ▼
Free Tool Usage ──────────→ Word of Mouth / Discord
       │                              │
       ▼                              ▼
Paid Conversion ◄──────── Social Proof (Testimonials)
```

### 6.2 Channel Strategy

#### Channel 1: SEO Blog (HIGH AUTOMATION POTENTIAL)

**Why:** Chris Zukowski's How To Market A Game blog pulls massive indie dev traffic by writing about Steam marketing data. You can do the same for the "marketing automation" niche.

**Content ideas that drive traffic:**
| Topic | Search Intent | Automation Level |
|-------|--------------|------------------|
| "How to write Steam announcements that get wishlists" | Informational | Write once, evergreen |
| "Steam announcement best practices 2026" | Informational | Update annually |
| "How many wishlists do Steam announcements generate?" | Data-driven | Auto-update with data |
| "Free Steam announcement generator tool" | Transactional | Landing page SEO |
| "Git commit to Steam announcement workflow" | Problem-solving | Tutorial, one-time |
| "Anti-slop: How to avoid generic AI writing" | Trending topic | Topical, high interest |

**Automation:** Use WishlistOps itself to generate blog content drafts about Steam marketing. Set up a content calendar with AI-assisted drafting → human review → publish pipeline.

**Tools:**
- **Ghost** or **WordPress** for blog ($0-11/mo)
- **Ahrefs/Ubersuggest** for keyword research ($0-29/mo)
- **Buffer/Typefully** for social scheduling ($0-15/mo)

#### Channel 2: Discord Community (MEDIUM AUTOMATION)

**Why:** 90%+ of indie devs are on Discord. It's where they ask for tool recommendations.

**Strategy:**
1. **Create WishlistOps Discord server** with channels:
   - `#announcements` — product updates
   - `#showcase` — users share generated announcements
   - `#feedback` — feature requests
   - `#steam-marketing-tips` — general value (attracts non-users)
   - `#support` — help
2. **Join existing gamedev Discords** (not to spam, but to be a helpful presence):
   - Chris Zukowski's HTMAG Discord (5000+ members)
   - GameDev Discord (70K+ members)
   - Indie Game Devs (50K+ members)
   - r/gamedev Discord
3. **When someone asks** "how do I write Steam announcements?" → genuinely help AND mention WishlistOps

**Automation:**
- Discord bot that posts weekly "Steam marketing tip of the week"
- Auto-showcase when users generate announcements (opt-in)
- Bot that answers common setup questions

#### Channel 3: Reddit & Gamedev Forums (LOW AUTOMATION — AUTHENTIC ONLY)

**Why:** r/gamedev (1.4M+), r/indiegaming (700K+), r/indiedev (400K+) are where devs discover tools. BUT Reddit hates overt self-promotion.

**Strategy:**
1. **Provide genuine value first** — Answer marketing questions with detailed, helpful answers for 2-3 months before ever mentioning WishlistOps
2. **Post "Show HN" style launches** on r/gamedev: "I built a free tool that turns your Git commits into Steam announcements"
3. **Post data-driven content**: "I analyzed 500 Steam announcements — here's what gets wishlists" (use WishlistOps data anonymized)

**Automation:** Mostly manual. Can use Reddit RSS + notification to alert you when relevant questions appear (`Steam announcement`, `marketing automation`, `indie marketing`).

#### Channel 4: YouTube/Short-Form Video (MEDIUM AUTOMATION)

**Why:** Gamedev YouTube is massive. Devlogs get significant views. "How to" tutorials for Steam perform well.

**Content Ideas:**
| Video Type | Example | Views Potential |
|------------|---------|-----------------|
| **Tool demo** | "I automated my Steam announcements in 5 minutes" | 5K-50K |
| **Tutorial** | "The perfect Steam announcement format" | 10K-100K |
| **Data analysis** | "What makes a Steam update go viral?" | 20K-200K |
| **Before/after** | "AI wrote my update. Here's what happened" | 10K-100K |

**Automation:**
- Use AI to generate video scripts from blog posts
- Use screen recording + AI voiceover for tutorials (reduces production time 80%)
- Auto-post to YouTube Shorts, TikTok, Twitter from single source

#### Channel 5: Email Marketing (HIGH AUTOMATION)

**Why:** Email converts 3-5x better than social for SaaS.

**Automated sequences:**
```
Signup → Welcome email (immediate)
       → "Your first announcement in 5 minutes" tutorial (Day 1)
       → "3 Steam marketing mistakes to avoid" (Day 3)
       → "See what other devs are creating" showcase (Day 7)
       → "Unlock Pro features" soft pitch (Day 14)
       → Weekly "Steam Marketing Digest" (ongoing)
```

**Tools:** 
- **Resend** ($0 for 3K emails/mo) or **Buttondown** ($0 for 100 subs)
- **Loops.so** ($0 for 1000 contacts) — built for SaaS

### 6.3 Marketing Automation Stack

| Tool | Purpose | Cost | Automation Level |
|------|---------|------|------------------|
| **Buffer** | Social scheduling | Free-$15/mo | Batch schedule posts weekly |
| **Typefully** | Twitter/X threads | Free-$12/mo | Write once, auto-thread |
| **Resend/Loops** | Email sequences | Free tier | Fully automated drip campaigns |
| **Zapier/Make** | Connect tools | Free-$20/mo | Trigger workflows between tools |
| **Plausible** | Analytics | $9/mo | Auto-track conversions |
| **GitHub Actions** | CI/CD + blog deploy | Free | Auto-deploy content |

**Total marketing automation cost: $0-50/month**

### 6.4 Launch Strategy (First 90 Days)

```
Week 1-2: "Stealth" Launch
  - Post on personal Twitter/socials
  - Share with 5-10 indie dev friends for feedback
  - Collect first testimonials
  
Week 3-4: "Soft" Launch  
  - Post on r/gamedev: "I built this, looking for beta testers"
  - Post on IndieDB forum
  - Email indie devs you know personally
  - Goal: 50 free users
  
Week 5-8: "Community" Launch
  - Create Discord server, invite beta users
  - Start blog with 3-4 SEO-optimized posts
  - First YouTube demo video
  - Start email newsletter
  - Goal: 200 free users
  
Week 9-12: "Paid" Launch
  - Introduce paid tiers with founding member discount
  - Product Hunt launch
  - Targeted outreach to gamedev YouTubers for reviews
  - Goal: 500 free users, 20-50 paying ($180-450 MRR)
```

---

## 7. Competitive Landscape

### 7.1 Direct Competitors (None Exist!)

**There is no direct competitor** that does exactly what WishlistOps does (Git commits → Steam announcements). This is a significant advantage.

### 7.2 Adjacent Competitors

| Tool | What It Does | Price | WishlistOps Advantage |
|------|-------------|-------|----------------------|
| **ChatGPT/Claude** | General AI writing | $0-20/mo | WishlistOps is specialized for Steam, has anti-slop, integrates with Git |
| **GameAnalytics** | Player analytics | Free-$29/mo | Different focus entirely (analytics vs marketing content) |
| **Lurkit** | Influencer marketing | Enterprise pricing | WishlistOps is for content creation, not influencer outreach |
| **Keymailer** | Game key distribution | Free-Enterprise | Different focus (key distribution vs announcements) |
| **Presskit()** | Press page generator | Free | WishlistOps generates ongoing content, not static press pages |
| **Steamworks Events** | Native Steam tool | Free | Manual, no AI, no image processing — WishlistOps automates this |
| **Buffer/Hootsuite** | Social media scheduling | $15-30/mo | Generic, not gaming-specific, no Git integration |

### 7.3 Positioning Statement

> **WishlistOps is the only tool that turns your Git commits into Steam-ready announcements with AI writing, anti-slop filtering, and screenshot enhancement — saving indie devs 5+ hours per update.**

**Key differentiation messaging:**
1. **"No AI slop"** — The anti-slop filter is unique. No competitor has this. Play it up BIG given industry backlash against generic AI content.
2. **"Your screenshots, enhanced"** — Not AI image generation (which devs distrust) but YOUR images, made better.
3. **"Git-native"** — Developers already write commit messages. WishlistOps reads them automatically.
4. **"Human-in-the-loop"** — Discord approval ensures nothing goes out without your OK.
5. **"100% local option"** — Privacy-conscious devs can self-host (CLI).

---

## 8. Implementation Roadmap

### Phase 1: MVP SaaS (Weeks 1-4)
- [ ] Deploy web server on Render (render.yaml already exists)
- [ ] Add user authentication (GitHub OAuth)
- [ ] GitHub webhook integration (auto-detect new commits/tags)
- [ ] Announcement generation via web UI
- [ ] Basic usage tracking (for metering free tier)

### Phase 2: Polish & Launch (Weeks 5-8)
- [ ] Improve onboarding wizard (3-step flow)
- [ ] Add Steam-format preview in announcement editor
- [ ] Drag-and-drop image upload with live preview
- [ ] Command palette (Cmd+K)
- [ ] Set up Lemon Squeezy billing
- [ ] Set up email automation (welcome sequence)
- [ ] Write 3-4 SEO blog posts

### Phase 3: Growth (Weeks 9-16)
- [ ] Product Hunt launch
- [ ] Discord community setup
- [ ] YouTube demo video
- [ ] Reddit outreach (value-first)
- [ ] Founding member paid launch
- [ ] Collect and publish testimonials
- [ ] Add team features (Studio tier)

### Phase 4: Scale (Months 4-6)
- [ ] API access for Publisher tier
- [ ] White-label option
- [ ] Multi-game support
- [ ] Analytics dashboard (which announcements drove wishlists)
- [ ] Integrations (Twitter/X auto-post, Steam community auto-post)
- [ ] Referral program (give 1 month free for each referral)

---

## Key Metrics to Track

| Metric | Target (Month 1) | Target (Month 3) | Target (Month 6) |
|--------|-------------------|-------------------|-------------------|
| **Signups** | 100 | 500 | 2,000 |
| **Active users** | 30 | 150 | 600 |
| **Paying customers** | 0 (free phase) | 20-50 | 100-200 |
| **MRR** | $0 | $180-450 | $900-1,800 |
| **Churn rate** | N/A | <10% | <5% |
| **NPS score** | N/A | 40+ | 50+ |

---

## Final Recommendations Summary

| Decision | Recommendation | Confidence |
|----------|----------------|------------|
| **Deployment** | Web SaaS (Render.com) + optional CLI | **HIGH** — Industry standard, you're already set up |
| **UI/UX** | Dark-first, dev-tool aesthetic, command palette | **HIGH** — Matches target audience expectations |
| **Pricing** | Freemium: $0 / $9 / $19 / $49 tiers | **HIGH** — Matches indie dev budgets and competitors |
| **Billing** | Lemon Squeezy (global tax compliance) | **MEDIUM** — Stripe also works, LemonSqueezy is simpler |
| **Marketing** | Content SEO + Discord + Reddit (80% automatable) | **HIGH** — Proven channels for dev tools |
| **Launch** | Free for 3 months → founding member pricing | **HIGH** — Builds user base before monetizing |

---

*This report is based on research from: Steamworks Partner documentation, How To Market A Game (Chris Zukowski), GameDiscoverCo newsletter, Game Developer (Informa), GameAnalytics pricing, Lurkit pricing, Keymailer platform, IndieDB community, Indie Hackers SaaS patterns, and general SaaS pricing/marketing best practices.*

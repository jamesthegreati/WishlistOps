# WishlistOps: Business Model Recommendations

**Date:** November 24, 2025  
**Purpose:** Strategic business model refinement for sustainable growth

---

## 📊 Current Business Model Critique

### What You Have Now
| Tier | Price | Features |
|------|-------|----------|
| Free | $0 | GitHub Action template, community support |
| Pro | $99 lifetime | Visuals, Steam integration, Discord support |
| Studio | $299 lifetime | Multi-game, team features, white-label |

### Problems with Current Model

#### 1. **Lifetime License = Death by Success**
If WishlistOps becomes popular:
- 1,000 customers × $99 = $99,000 (one-time)
- Support burden grows indefinitely
- Server costs increase (if any hosted features)
- No revenue after initial purchase
- Users expect lifetime updates for lifetime license

**Industry Lesson:** Many bootstrapped SaaS companies have failed with lifetime deals (LTD). AppSumo is full of abandoned products that couldn't sustain development after LTD revenue dried up.

#### 2. **BYOK Model Creates Hidden Costs**
"Bring Your Own Key" sounds developer-friendly but:
- Users misconfigure API keys (support tickets)
- API rate limits hit (frustrated users)
- Users blame WishlistOps for Google/Discord issues
- No visibility into usage patterns

#### 3. **Price Gap Too Large**
- Free → $99 is a 100% → ∞% increase
- No stepping stone for casual users
- Loses users who want "a little more" but don't need full Pro

---

## 💡 Recommended Business Model

### The "Open Core + Managed Service" Model

This combines the trust of open source with recurring revenue from convenience.

### Tier Structure

| Tier | Price | Target | Features |
|------|-------|--------|----------|
| **Community** | Free forever | Hobbyists, evaluators | Core automation, CLI, BYOK, community support |
| **Indie** | $9/month or $90/year | Solo devs, small projects | Managed API keys, web dashboard, email support |
| **Studio** | $29/month or $290/year | Small studios, multiple games | 5 games, team seats, priority support, analytics |
| **Publisher** | $99/month or $990/year | Publishers, agencies | Unlimited games, white-label, API access, dedicated support |

### Why This Works

1. **Free tier builds trust and adoption**
   - Developers can evaluate fully
   - Open source = inspectable, trustworthy
   - Community contributions improve product

2. **$9/month is impulse-buy territory**
   - Less than a fancy coffee
   - Easy to expense for employed devs
   - Low commitment, easy to upgrade

3. **Managed API keys are the killer feature**
   - No configuration headaches
   - WishlistOps handles rate limiting
   - Better UX = higher retention

4. **Annual discounts encourage commitment**
   - 17% discount for annual
   - Reduces churn
   - Predictable revenue

---

## 💰 Revenue Projections

### Conservative Scenario (Year 1)

| Month | Community | Indie | Studio | Publisher | MRR |
|-------|-----------|-------|--------|-----------|-----|
| 1 | 100 | 5 | 1 | 0 | $74 |
| 3 | 500 | 25 | 5 | 1 | $469 |
| 6 | 1,500 | 75 | 15 | 3 | $1,407 |
| 12 | 5,000 | 200 | 50 | 10 | $4,240 |

**Annual Revenue (Year 1):** ~$25,000

### Optimistic Scenario (Year 1)

| Month | Community | Indie | Studio | Publisher | MRR |
|-------|-----------|-------|--------|-----------|-----|
| 1 | 200 | 10 | 2 | 0 | $148 |
| 3 | 1,000 | 50 | 10 | 2 | $938 |
| 6 | 3,000 | 150 | 30 | 8 | $2,812 |
| 12 | 10,000 | 400 | 100 | 25 | $8,475 |

**Annual Revenue (Year 1):** ~$50,000

---

## 🎯 Monetization Strategies

### Primary: Subscription Revenue
As outlined above. Focus on Indie tier as volume driver.

### Secondary: Marketplace/Templates
Allow users to create and sell:
- Custom banner templates ($5-20 each)
- Voice/tone configurations ($5-10 each)
- Pre-built automation workflows ($10-30 each)

WishlistOps takes 30% commission.

**Why it works:** 
- Creates content creators who promote product
- Additional revenue without development cost
- Builds ecosystem moat

### Tertiary: Affiliate Partnerships

Partner with complementary services:
- **Keymailer** (key distribution) - 10% referral
- **IMPRESS.games** (influencer outreach) - 10% referral
- **Wise Wizard Games** (game festivals) - event partnerships

---

## 📈 Value Ladder Implementation

### Stage 1: Awareness
- Free GitHub template
- Blog posts on indie game marketing
- YouTube tutorials
- Reddit community presence

### Stage 2: Trial
- Free tier with full features (BYOK)
- 14-day trial of Indie tier (no CC required)
- Email onboarding sequence

### Stage 3: Conversion
- Friction points in BYOK (API config, rate limits)
- Clear upgrade path in dashboard
- "Try managed keys free for 7 days" prompt

### Stage 4: Retention
- Weekly usage emails ("You saved 4 hours this week!")
- Feature announcements
- Community Discord access

### Stage 5: Expansion
- Multi-game needs → Studio tier
- Team access needs → Studio/Publisher tier
- White-label needs → Publisher tier

---

## 🚫 What NOT to Do

### ❌ Don't Launch on AppSumo
Lifetime deals attract:
- Deal hunters (not your target)
- Users who never activate
- Support burden with no ongoing revenue

### ❌ Don't Compete on Price
IMPRESS.games is $19-99/month. Don't try to be "the cheap option." Be "the developer-native option."

### ❌ Don't Over-Promise Automation
Steam doesn't have posting API. Be honest:
- "AI-assisted drafting" ✅
- "Fully automated posting" ❌

### ❌ Don't Gate Core Features
Content filter, Git integration, CLI should all be free. Gate convenience (managed keys, dashboard, support).

---

## 💳 Payment Infrastructure

### Recommended: Stripe + LemonSqueezy

**Why LemonSqueezy:**
- Handles sales tax (VAT, GST) automatically
- Built for indie SaaS
- Software key delivery
- Affiliate program built-in

**Implementation:**
1. Free tier: No payment, email-only signup
2. Paid tiers: LemonSqueezy checkout
3. License validation: API key in dashboard

### Pricing Display
```
💰 Pricing

┌─────────────────────────────────────────────────────────┐
│  Community          │  Indie             │  Studio      │
│  Free forever       │  $9/month          │  $29/month   │
│                     │  $90/year (save)   │  $290/year   │
├─────────────────────┼────────────────────┼──────────────┤
│  ✅ Core automation │  ✅ Everything in  │  ✅ All Indie│
│  ✅ CLI & GitHub    │     Community      │  ✅ 5 games  │
│  ✅ Community forum │  ✅ Managed API    │  ✅ 3 team   │
│  ⚠️ BYOK required  │  ✅ Web dashboard  │  ✅ Analytics│
│                     │  ✅ Email support  │  ✅ Priority │
└─────────────────────┴────────────────────┴──────────────┘
```

---

## 📊 Key Metrics to Track

### Acquisition
- Website visitors
- GitHub stars
- Free tier signups

### Activation
- First announcement generated
- Discord integration completed
- Configuration saved

### Retention
- Weekly Active Users
- Monthly Active Users
- Announcements per user per month

### Revenue
- MRR (Monthly Recurring Revenue)
- ARPU (Average Revenue Per User)
- Churn rate
- LTV:CAC ratio

### Referral
- Net Promoter Score
- Referral signups
- Social shares

---

## 🎬 Implementation Roadmap

### Phase 1: Foundation (Month 1)
- [ ] Set up LemonSqueezy account
- [ ] Implement license validation API
- [ ] Create upgrade prompts in dashboard
- [ ] Build usage tracking

### Phase 2: Launch (Month 2)
- [ ] Launch Indie tier ($9/month)
- [ ] Enable free trials
- [ ] Set up onboarding emails
- [ ] Create pricing page

### Phase 3: Iterate (Month 3-6)
- [ ] Analyze conversion data
- [ ] A/B test pricing
- [ ] Launch Studio tier
- [ ] Build affiliate program

### Phase 4: Scale (Month 6-12)
- [ ] Launch Publisher tier
- [ ] Build marketplace
- [ ] Partner integrations
- [ ] Team/seat licensing

---

## 🏁 Conclusion

The path from "cool GitHub project" to "sustainable business" requires:

1. **Subscription model** for predictable revenue
2. **Value ladder** for natural upgrades
3. **Managed service** as key differentiator
4. **Honest positioning** about capabilities

Start with the Indie tier at $9/month. Validate with 100 paying customers before expanding tiers.

**North Star Metric:** Monthly Recurring Revenue (MRR)

**Target:** $5,000 MRR within 12 months (556 Indie customers or equivalent)

---

*Next steps: See MARKETING_STRATEGY.md for customer acquisition recommendations*

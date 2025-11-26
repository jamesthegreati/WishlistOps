# WishlistOps: Marketing Strategy & Distribution Plan

**Date:** November 24, 2025  
**Purpose:** Comprehensive go-to-market strategy for indie developer audience

---

## 🎯 Marketing Philosophy

### Core Principle: "Show, Don't Sell"

Indie developers are skeptical of marketing. They:
- Use ad blockers
- Distrust corporate messaging
- Value authenticity and transparency
- Trust peer recommendations

**Your marketing should feel like developer-to-developer conversation, not sales pitch.**

---

## 📊 Channel Analysis

### Tier 1: High ROI, Low Cost

| Channel | Effort | Reach | Conversion | Priority |
|---------|--------|-------|------------|----------|
| Reddit (r/gamedev, r/IndieDev) | Medium | High | 2-3% | 🔥 Critical |
| Twitter/X (gamedev community) | Low | Medium | 1-2% | ✅ Important |
| GitHub trending | Low | High | 5-10% | ✅ Important |
| YouTube tutorials | High | Medium | 3-5% | ✅ Important |
| Discord communities | Medium | Medium | 2-3% | ✅ Important |

### Tier 2: Medium ROI

| Channel | Effort | Reach | Conversion | Priority |
|---------|--------|-------|------------|----------|
| Dev.to / Hashnode blogs | Medium | Medium | 2-3% | 📝 Secondary |
| Indie game jams | Medium | Low | 5-10% | 📝 Secondary |
| Podcast appearances | Medium | Low | 1-2% | 📝 Secondary |
| Product Hunt | High | Medium | 1-2% | 📝 One-time |

### Tier 3: Avoid (Negative ROI)

| Channel | Why Avoid |
|---------|-----------|
| Google Ads | $15-30 CPC, not worth it for $9 product |
| Facebook Ads | Wrong audience demographics |
| LinkedIn | Too corporate, wrong persona |
| Cold email | Spam reputation, low conversion |
| Press releases | Journalists don't cover dev tools |

---

## 📅 Launch Plan: 12-Week Roadmap

### Week -2: Pre-Launch Preparation

**GitHub Repository:**
- [ ] Polish README with demo GIF
- [ ] Create .env.example template
- [ ] Add CONTRIBUTING.md
- [ ] Set up GitHub Discussions
- [ ] Add relevant topics (steam, gamedev, automation, ai)

**Content Creation:**
- [ ] Record 2-minute demo video
- [ ] Create before/after comparison images
- [ ] Write launch blog post
- [ ] Prepare Reddit post (multiple versions)

**Social Setup:**
- [ ] Twitter/X account (@WishlistOps)
- [ ] Discord server with channels
- [ ] YouTube channel

### Week -1: Beta Testing

- [ ] Recruit 10-20 beta testers from personal network
- [ ] Collect testimonials and feedback
- [ ] Fix critical bugs
- [ ] Prepare launch checklist

### Week 0: Launch Day

**Hour-by-Hour Schedule (Tuesday, 9 AM EST):**

| Hour | Activity | Platform |
|------|----------|----------|
| 0 | Post to r/IndieDev | Reddit |
| 1 | Post to r/gamedev | Reddit |
| 2 | Post to r/SideProject | Reddit |
| 3 | Tweet announcement thread | Twitter/X |
| 4 | Post to relevant Discord servers | Discord |
| 6 | Submit to Product Hunt | Product Hunt |
| 8-24 | Respond to ALL comments | All platforms |

**Why Tuesday?**
- Highest Reddit engagement day
- Not Friday (weekend = low engagement)
- Not Monday (too busy)

---

## 📝 Content Templates

### Reddit Post Template (r/gamedev)

```
Title: I built a GitHub Action that auto-generates Steam announcements using AI (open source, saves 2-4 hrs/week)

Hey r/gamedev!

I've been building my indie game for the past year, and I kept putting off marketing because I hated context-switching from code to the Steam dashboard.

So I built WishlistOps - a GitHub Action that:
✅ Watches your Git commits
✅ Generates Steam-ready announcements with AI
✅ Creates banner images with your game's logo
✅ Sends to Discord for approval before you publish

**Demo:** [GIF showing the workflow]

**GitHub:** [link]

**How it works:**
1. Push a tag (v1.0.0)
2. GitHub Action parses your commits
3. AI drafts announcement in your voice
4. Discord notification with download links
5. You review, copy/paste to Steam

**Important:** Steam doesn't have a posting API, so you still manually publish - but the content is ready in 30 seconds instead of 2 hours.

It's free and open source (MIT). You use your own API keys.

What other marketing tasks eat your time? I'm thinking about adding itch.io support next.

---
Tech stack: Python, GitHub Actions, Google Gemini API, Pillow, Discord webhooks
```

### Twitter Thread Template

```
1/ 🎮 Indie devs: Tired of context-switching from code to Steam marketing?

I built an open-source tool that turns your Git commits into Steam announcements.

Thread 🧵👇

2/ The problem:

Every version tag means:
- Write announcement
- Design banner
- Post to Steam
- Share on socials

That's 2-4 hours. Every. Single. Time.

3/ My solution: WishlistOps

It watches your Git repository and:
- Parses player-facing commits
- Generates announcements with AI
- Creates banner with your logo
- Sends to Discord for approval

[Demo GIF]

4/ Key features:

✅ AI-powered but human-approved
✅ Anti-slop filter (no buzzwords)
✅ Customizable voice/tone
✅ Works with any game genre
✅ 100% open source

5/ Why Discord approval?

AI makes mistakes. You ALWAYS review before publishing.

No "AI slop" reaches your players.
No surprises.
You stay in control.

6/ Tech stack:
- GitHub Actions (free)
- Google Gemini API (BYOK)
- Python + Pillow
- Discord webhooks

Total cost: $0 if you're under API limits

7/ Get it here:
🔗 GitHub: [link]
📖 Docs: [link]
💬 Discord: [link]

Star ⭐ if you think this could save you time!

8/ What's next?

Building:
- itch.io support
- Template marketplace
- Scheduled announcements

What features would you want? Reply below! 👇
```

### YouTube Video Script Outline

**Title:** "How I Automated My Steam Marketing (Save 4+ Hours/Week)"

**Structure:**
1. Hook (0-30s): "I spent 4 hours last week writing a Steam announcement. Never again."
2. Problem (30s-2m): Context switching pain, marketing debt
3. Solution Demo (2-5m): Show actual workflow
4. Setup Tutorial (5-10m): Step-by-step configuration
5. Results (10-12m): Before/after comparison
6. Call to Action (12m): "Link in description, star on GitHub"

---

## 🎪 Community Building Strategy

### Discord Server Structure

```
#welcome
#announcements
#showcase (users share their generated announcements)
#help
#feedback
#off-topic

Voice:
#office-hours (weekly AMAs)
```

### Weekly Content Calendar

| Day | Content | Platform |
|-----|---------|----------|
| Monday | Marketing tip thread | Twitter/X |
| Tuesday | User showcase | Discord + Twitter |
| Wednesday | Tutorial video | YouTube |
| Thursday | Blog post | Dev.to + own blog |
| Friday | Week recap | Newsletter |

### Community Incentives

1. **Early Adopter Badge:** First 100 users get special Discord role
2. **Testimonial Rewards:** Featured on website for detailed testimonials
3. **Bug Bounty:** Free Pro tier for 1 month for bug reports
4. **Contributor Recognition:** GitHub contributors highlighted

---

## 📈 Growth Loops

### Loop 1: Open Source Flywheel
```
Good Tool → GitHub Stars → 
Trending → New Users → 
Contributions → Better Tool
```

### Loop 2: Content Creator Flywheel
```
User Creates Announcement → 
Shares on Social → Tags WishlistOps →
Other Devs Discover → New Users
```

### Loop 3: Attribution Flywheel (Free Tier)
```
Free Tier User → Generated Announcement →
"Made with WishlistOps" footer →
Other Devs See → Click Link → New Users
```

### Implementation: Attribution Footer

For free tier, add to generated announcements:
```
---
📢 Announcement drafted with WishlistOps
🔗 Try it free: wishlistops.dev
```

Paid tiers can remove this.

---

## 🤝 Partnership Opportunities

### Complementary Tools (Non-Competing)

| Partner | Integration | Value Exchange |
|---------|-------------|----------------|
| **Keymailer** | Link to key distribution after announcement | Cross-promotion |
| **IMPRESS.games** | Refer for influencer campaigns | Affiliate revenue |
| **SteamDB** | Data enrichment for announcements | API partnership |
| **Godot/Unity** | Editor plugin | Distribution |

### Game Jam Partnerships

Sponsor indie game jams:
- Provide free Pro tier to participants
- Create "Best Marketing" category
- Collect testimonials from winners

Target jams:
- Ludum Dare
- Global Game Jam
- GMTK Game Jam
- Brackeys Game Jam

### Influencer Strategy

**Tier 1: Micro-influencers (5-50K followers)**
- More responsive
- Higher engagement rate
- Cheaper/free to work with

Target indie dev YouTubers:
- Jonas Tyroller
- ThinMatrix
- HeartBeast
- Game Maker's Toolkit (dream goal)

**Outreach Template:**
```
Hey [Name],

Love your work on [specific video/game]. 

I built an open-source tool that automates Steam announcement writing - thought it might save you time on [their game] updates.

Would you be interested in trying it? Happy to help you set it up and feature [their game] as a case study.

No strings attached - just think it might help!

[Your name]
```

---

## 📊 Metrics & Goals

### Launch Week Goals

| Metric | Target | Stretch |
|--------|--------|---------|
| GitHub Stars | 300 | 500 |
| Free Tier Signups | 50 | 100 |
| Discord Members | 100 | 200 |
| Reddit Upvotes (total) | 500 | 1,000 |
| Twitter Followers | 200 | 500 |

### Month 1 Goals

| Metric | Target | Stretch |
|--------|--------|---------|
| GitHub Stars | 1,000 | 2,000 |
| Free Tier Users | 200 | 500 |
| Paid Customers | 10 | 25 |
| MRR | $90 | $225 |
| NPS | >30 | >50 |

### Month 3 Goals

| Metric | Target | Stretch |
|--------|--------|---------|
| GitHub Stars | 3,000 | 5,000 |
| Free Tier Users | 1,000 | 2,000 |
| Paid Customers | 50 | 100 |
| MRR | $450 | $900 |
| Case Studies | 5 | 10 |

---

## 📰 Content Marketing

### Blog Post Ideas (SEO-Focused)

1. **"How to Write Steam Announcements That Players Actually Read"**
   - Keywords: steam announcement, steam update post, indie game marketing
   - Funnel: Awareness → WishlistOps mention at end

2. **"The 5-Minute Marketing Stack for Solo Indie Devs"**
   - Keywords: indie game marketing, solo dev marketing, game marketing tools
   - Funnel: List post, WishlistOps featured

3. **"Why Your Game Is Invisible on Steam (And How to Fix It)"**
   - Keywords: steam visibility, steam algorithm, indie game discoverability
   - Funnel: Problem-solution, WishlistOps as part of solution

4. **"I Analyzed 500 Successful Steam Announcements - Here's What Works"**
   - Keywords: steam announcement examples, steam marketing
   - Funnel: Data-driven, builds authority

5. **"Git-Based Marketing: How Developers Are Automating Game Promotion"**
   - Keywords: automated marketing, devops marketing, ci/cd marketing
   - Funnel: Category creation, positions WishlistOps as leader

### Guest Post Targets

- Gamasutra/GameDeveloper.com
- Kotaku (developer stories section)
- Indie game dev blogs
- Dev.to
- Hashnode

---

## 💰 Budget Allocation (If Any)

### $0 Budget (Bootstrap)

| Activity | Time Investment |
|----------|-----------------|
| Reddit posting | 2 hrs/week |
| Twitter engagement | 1 hr/day |
| Content creation | 4 hrs/week |
| Community management | 1 hr/day |
| **Total** | **~20 hrs/week** |

### $500/Month Budget

| Item | Cost | ROI |
|------|------|-----|
| YouTube thumbnail designer | $100 | Better CTR |
| Micro-influencer gift cards | $200 | Testimonials |
| Plausible Analytics | $9 | Data |
| Email marketing (Buttondown) | $9 | Retention |
| Buffer (social scheduling) | $15 | Time savings |
| **Reserve** | $167 | Experiments |

### $1,000/Month Budget

Add:
| Item | Cost | ROI |
|------|------|-----|
| Video editor (freelance) | $300 | Professional tutorials |
| Game jam sponsorship | $200 | Exposure |
| Conference tickets | Remaining | Networking |

---

## 🏁 Launch Checklist

### Week Before Launch
- [ ] Demo video recorded and uploaded
- [ ] README polished with GIF
- [ ] Discord server set up
- [ ] Twitter/X account active with content
- [ ] Beta testers have shared feedback
- [ ] Blog post written and scheduled
- [ ] Reddit posts drafted (3 versions)
- [ ] Email list set up (even if empty)

### Launch Day
- [ ] Wake up early (9 AM EST posts perform best)
- [ ] Post to Reddit first
- [ ] Tweet announcement thread
- [ ] Notify beta testers to support
- [ ] Monitor all channels for questions
- [ ] Respond to EVERY comment
- [ ] Screenshot metrics for later analysis
- [ ] Celebrate small wins!

### Week After Launch
- [ ] Thank all commenters/supporters
- [ ] Publish case study if available
- [ ] Analyze what worked/didn't
- [ ] Plan next content piece
- [ ] Reach out to interested parties for testimonials

---

## 🎯 Success Criteria

### Product-Market Fit Signals
- [ ] Users asking for features (not just reporting bugs)
- [ ] Organic word-of-mouth referrals
- [ ] Users creating content about WishlistOps
- [ ] Repeat usage (weekly/monthly)
- [ ] Willingness to pay (paid tier conversions)

### Red Flags to Watch
- High signup, low activation (product problem)
- High churn after first month (value problem)
- No organic mentions (marketing problem)
- Lots of bugs/support tickets (quality problem)

---

## 📚 Resources

### Marketing Inspiration
- "The Mom Test" by Rob Fitzpatrick (customer research)
- "Obviously Awesome" by April Dunford (positioning)
- "Traction" by Gabriel Weinberg (channel testing)
- Indie Hackers podcast

### Tools
- Plausible (privacy-friendly analytics)
- Buttondown (simple newsletters)
- Buffer (social scheduling)
- Canva (quick graphics)
- OBS (screen recording)

---

## 🏁 Conclusion

WishlistOps marketing should be:
1. **Authentic** - Developer-to-developer, not corporate
2. **Educational** - Provide value before asking for anything
3. **Community-driven** - Let users spread the word
4. **Patient** - Growth takes time, don't burn out

Start with Reddit and GitHub. Build from there.

**Remember:** Your product is the best marketing. Make it great, and users will talk about it.

---

*Next steps: Execute Week -2 preparation checklist*

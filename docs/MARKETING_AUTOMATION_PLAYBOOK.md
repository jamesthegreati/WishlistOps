# WishlistOps Marketing Automation Playbook

## Target audience (who pays)

Primary ICP:
- Indie game teams on Steam (solo to ~10 people)
- Shipping regular updates but inconsistent with announcements
- No dedicated community/marketing manager

They pay for:
- Time saved per update
- More consistent Steam communication
- Better quality update posts without hiring copy help

## Unique value to highlight

1. **Built for Steam update workflow**, not generic social-media writing.
2. **Git-to-announcement pipeline** from real commits.
3. **Human approval checkpoint in Discord** to avoid embarrassing auto-posts.
4. **Screenshot enhancement + logo compositing** without fake AI image generation.
5. **Anti-slop filter** to avoid generic AI voice.

## Absolute must-have features for seamless user experience

1. One-click onboarding wizard with connection tests for Discord/Google/Steam.
2. Commit picker with clear preview before generation.
3. Announcement quality score + quick fix suggestions.
4. Save-and-reuse voice templates by game.
5. Post-performance loop: track update date, type, and resulting wishlist trend notes.

## Automated marketing strategy (operator-light)

Use one system (n8n/Make/Zapier) with these automations:

### 1) Content engine (weekly)
Trigger: every week
- Pull one real update example from product logs (anonymized)
- Generate:
  - 1 long-form post ("how this patch note was improved")
  - 3 short posts for X/LinkedIn
  - 1 Discord community post
- Push to Buffer/Hypefury queue for scheduling

### 2) Lead capture + nurture
Trigger: new website signup
- Send onboarding email immediately
- Send day 2 "best Steam update templates" email
- Send day 5 case-study email
- Send day 9 trial-to-paid CTA

### 3) Product-led referral loop
Trigger: user sends 3+ approval requests in 14 days
- Offer referral reward (extra monthly credits)
- Auto-send personal referral link and prewritten share copy

### 4) Churn prevention
Trigger: no generation activity for 14 days
- Send reactivation email with one-click "generate from latest commits" prompt
- If still inactive at day 21, send downgrade option

## Distribution channels that fit this niche

1. Steamworks-focused creator communities and Discord servers
2. Indie dev subreddits and game-dev forums (value-first examples)
3. YouTube shorts: before/after announcement rewrite demos
4. Partnerships with indie publishers and launch consultants

## Offer and pricing test to start

- Free: 10 generations/month
- Pro: $29-49/month, 150 generations, team workflows
- Studio: $99+/month, multi-game/team analytics and priority support

## Metrics to track weekly

- Visitor -> signup conversion
- Signup -> first generated draft
- First draft -> first Discord approval send
- Approval send -> paid conversion
- 30-day retention by team

## Fast first campaign (14 days)

1. Publish 3 before/after examples from real commits.
2. DM 30 indie teams with personalized teardown offer.
3. Run one livestream: "Ship your next Steam update announcement in 5 minutes".
4. Collect objections and feed them into product roadmap.

# Product Requirements Document: Game

```yaml
# PRD Metadata (machine-readable for orchestrator)
metadata:
  schema_version: "2.0"
  project:
    name: "[Game Title]"
    type: game
    complexity: simple | moderate | complex
  mvp:
    target_date: "[YYYY-MM-DD or TBD]"
    feature_count: 0
  tech_stack:
    languages: []
    frameworks: []  # Phaser, Unity, Godot, custom
    databases: []
    infrastructure: []
  game:
    genre: "[Puzzle, Action, RPG, Strategy, Casual]"
    platform: browser | mobile | desktop | cross-platform
    session_length: "[e.g., 5-15 minutes]"
  constraints:
    team_size: 1
    timeline: "[e.g., 6 weeks]"
  tags: []
```

## Document Information

| Field | Value |
|-------|-------|
| **Project Name** | [Game Title] |
| **Document Version** | 2.0 |
| **Created** | [Date] |
| **Last Updated** | [Date] |
| **Author** | [Author] |
| **Status** | Draft / In Review / Approved |

---

## 1. Executive Summary

### 1.1 Game Concept
[One-paragraph description of the core game concept, what makes it fun, and what players will experience]

### 1.2 Genre & Platform

| Aspect | Value |
|--------|-------|
| **Genre** | [e.g., Puzzle, Action, RPG, Strategy, Casual] |
| **Sub-genre** | [e.g., Match-3, Roguelike, Tower Defense] |
| **Platform** | [Browser / Mobile / Desktop / Cross-platform] |
| **Target Rating** | [E / E10+ / T / M] |

### 1.3 Target Audience

| Attribute | Description |
|-----------|-------------|
| **Age Range** | [e.g., 13-35] |
| **Player Type** | [Casual / Mid-core / Hardcore] |
| **Session Length** | [e.g., 5-15 minutes] |
| **Play Frequency** | [Daily / Weekly / Binge] |

### 1.4 Unique Selling Points
1. [USP 1 - What makes this game different]
2. [USP 2]
3. [USP 3]

### 1.5 Success Metrics

| Metric | Target |
|--------|--------|
| [e.g., Day 1 Retention] | [e.g., 40%] |
| [e.g., Day 7 Retention] | [e.g., 20%] |
| [e.g., Average Session Length] | [e.g., 8 minutes] |
| [e.g., Sessions per Day] | [e.g., 3] |

---

## 2. Core Gameplay

### 2.1 Core Loop
```
[Action] → [Reward] → [Progression] → [New Challenge] → [Action]

Example:
Play Level → Earn Stars/Currency → Unlock New Levels → Increased Difficulty → Play Level
```

### 2.2 Core Mechanics

| Mechanic | Description | Player Action |
|----------|-------------|---------------|
| [Primary Mechanic] | [How it works] | [What player does] |
| [Secondary Mechanic] | [How it works] | [What player does] |
| [Tertiary Mechanic] | [How it works] | [What player does] |

### 2.3 Game Controls

| Platform | Control | Action |
|----------|---------|--------|
| Browser/Desktop | Mouse Click | [Action] |
| Browser/Desktop | [Key] | [Action] |
| Mobile | Tap | [Action] |
| Mobile | Swipe | [Action] |
| Mobile | Hold | [Action] |

### 2.4 Win/Lose Conditions

| Condition Type | Description |
|----------------|-------------|
| **Win Condition** | [How player wins/completes level] |
| **Lose Condition** | [How player fails] |
| **Partial Success** | [If applicable - e.g., star ratings] |

---

## 3. Game Structure

### 3.1 Game Modes

| Mode | Description | Priority |
|------|-------------|----------|
| [e.g., Campaign] | [Description] | Must Have |
| [e.g., Endless] | [Description] | Should Have |
| [e.g., Challenge] | [Description] | Nice to Have |

### 3.2 Level Design

| Aspect | Specification |
|--------|---------------|
| **Total Levels (MVP)** | [Number] |
| **Level Duration** | [Average time] |
| **Difficulty Curve** | [Description of progression] |
| **Level Structure** | [Worlds/Chapters/Linear] |

### 3.3 Difficulty Progression

| Level Range | Difficulty | New Mechanics Introduced |
|-------------|------------|--------------------------|
| 1-5 | Tutorial | Core mechanics |
| 6-15 | Easy | [Mechanic] |
| 16-30 | Medium | [Mechanic] |
| 31+ | Hard | [Mechanic combinations] |

---

## 4. Progression Systems

### 4.1 Player Progression

| System | Description | Impact |
|--------|-------------|--------|
| [e.g., Experience/Levels] | [How it works] | [What it unlocks] |
| [e.g., Achievements] | [How it works] | [Rewards] |
| [e.g., Unlockables] | [How it works] | [Content unlocked] |

### 4.2 Currency System

| Currency | Earned By | Spent On | Economy Notes |
|----------|-----------|----------|---------------|
| [Primary - e.g., Coins] | [Sources] | [Uses] | [Abundance] |
| [Premium - e.g., Gems] | [Sources] | [Uses] | [Scarcity] |

### 4.3 Upgrade Systems

| Upgrade Type | Description | Cost | Effect |
|--------------|-------------|------|--------|
| [e.g., Power-ups] | [Description] | [Currency/Amount] | [Gameplay effect] |
| [e.g., Character upgrades] | [Description] | [Currency/Amount] | [Stat changes] |

---

## 5. Game Feel & Polish

### 5.1 Visual Feedback

| Event | Feedback |
|-------|----------|
| Successful action | [e.g., Particle burst, screen flash] |
| Combo/Chain | [e.g., Escalating effects, multiplier display] |
| Failure | [e.g., Screen shake, color desaturation] |
| Level complete | [e.g., Celebration animation, confetti] |
| Achievement | [e.g., Badge animation, notification] |

### 5.2 Audio Feedback

| Event | Sound Type |
|-------|------------|
| Primary action | [e.g., Satisfying click/pop] |
| Success | [e.g., Ascending chime] |
| Failure | [e.g., Soft negative tone] |
| Background | [e.g., Ambient music matching theme] |
| UI interaction | [e.g., Subtle button sounds] |

### 5.3 Juice Elements

| Element | Implementation | Priority |
|---------|----------------|----------|
| Screen shake | [When/intensity] | Should Have |
| Particles | [Types/triggers] | Should Have |
| Animations | [Easing, timing] | Must Have |
| Haptic feedback | [Mobile - when/type] | Nice to Have |

---

## 6. User Interface

### 6.1 Screen Flow

```
Splash → Main Menu → Level Select → Gameplay → Results → Level Select
              ↓
          Settings
              ↓
          Shop (if applicable)
```

### 6.2 Key Screens

| Screen | Purpose | Key Elements |
|--------|---------|--------------|
| Main Menu | Entry point | Play button, settings, achievements |
| Level Select | Choose level | Level grid, progress indicators, locked states |
| Gameplay HUD | In-game info | Score, timer, pause button, resources |
| Pause Menu | Mid-game options | Resume, restart, quit, settings |
| Results | Post-level feedback | Score, stars, rewards, next/retry buttons |

### 6.3 HUD Requirements

| Element | Position | Information Displayed |
|---------|----------|----------------------|
| Score | [e.g., Top center] | Current score, combo multiplier |
| Resources | [e.g., Top left] | Lives, currency, power-ups |
| Timer | [e.g., Top right] | Time remaining/elapsed |
| Pause | [e.g., Top right corner] | Tap to pause |
| Objective | [e.g., Top] | Current goal progress |

---

## 7. Art & Visual Style

### 7.1 Art Direction

| Aspect | Description |
|--------|-------------|
| **Style** | [e.g., Pixel art, Flat design, 3D, Hand-drawn] |
| **Color Palette** | [Primary colors, mood] |
| **Theme** | [e.g., Fantasy, Sci-fi, Casual, Abstract] |
| **Tone** | [Playful, Serious, Whimsical, Dark] |

### 7.2 Asset Requirements

| Asset Type | Quantity | Priority |
|------------|----------|----------|
| Player/Character sprites | [Count] | Must Have |
| Enemy/Obstacle sprites | [Count] | Must Have |
| Environment tiles | [Count] | Must Have |
| UI elements | [Count] | Must Have |
| Effects/Particles | [Count] | Should Have |
| Backgrounds | [Count] | Must Have |

### 7.3 Animation Requirements

| Animation | Frames | Priority |
|-----------|--------|----------|
| [e.g., Player idle] | [Count] | Must Have |
| [e.g., Player action] | [Count] | Must Have |
| [e.g., Enemy behaviors] | [Count] | Must Have |
| [e.g., UI transitions] | [Count] | Should Have |

---

## 8. Audio Requirements

### 8.1 Music

| Track | Use | Duration | Mood |
|-------|-----|----------|------|
| Main theme | Menu | [X] sec loop | [Mood] |
| Gameplay | Levels | [X] sec loop | [Mood] |
| Victory | Win screen | [X] sec | [Mood] |
| [Additional tracks] | [Use] | [Duration] | [Mood] |

### 8.2 Sound Effects

| Category | Count Needed | Examples |
|----------|--------------|----------|
| UI sounds | [Count] | Click, hover, success, error |
| Gameplay | [Count] | Jump, collect, hit, destroy |
| Ambient | [Count] | Background loops |
| Voice/Alerts | [Count] | Announcer, warnings |

---

## 9. Technical Requirements

### 9.1 Platform Specifications

| Platform | Specification |
|----------|---------------|
| **Browser** | Chrome 90+, Firefox 88+, Safari 14+, Edge 90+ |
| **Mobile Web** | iOS Safari 14+, Chrome Android |
| **Resolution** | [e.g., Responsive, 1920x1080 base] |
| **Orientation** | [Portrait / Landscape / Both] |
| **Offline Support** | [Yes / No] |

### 9.2 Performance Targets

| Metric | Target |
|--------|--------|
| Frame Rate | 60 FPS (30 FPS minimum) |
| Load Time | < [X] seconds |
| Memory Usage | < [X] MB |
| Bundle Size | < [X] MB |

### 9.3 Technology Stack

| Component | Technology | Rationale |
|-----------|------------|-----------|
| Game Engine | [e.g., Phaser, PixiJS, Three.js, Canvas] | [Why] |
| Language | [e.g., TypeScript, JavaScript] | [Why] |
| Build Tool | [e.g., Vite, Webpack] | [Why] |
| Physics | [e.g., Matter.js, Box2D, Custom] | [Why] |

### 9.4 Save System

| Data | Storage | Sync |
|------|---------|------|
| Progress | [LocalStorage / Cloud] | [Yes/No] |
| Settings | [LocalStorage] | [Yes/No] |
| High Scores | [LocalStorage / Server] | [Yes/No] |

---

## 10. Monetization (If Applicable)

### 10.1 Monetization Model

| Model | Implementation | Priority |
|-------|----------------|----------|
| [e.g., Free-to-play + Ads] | [Details] | [Priority] |
| [e.g., Premium purchase] | [Details] | [Priority] |
| [e.g., In-app purchases] | [Details] | [Priority] |

### 10.2 Ad Placements (If F2P)

| Placement | Type | Frequency |
|-----------|------|-----------|
| [e.g., Level complete] | Interstitial | Every [X] levels |
| [e.g., Extra lives] | Rewarded | On demand |
| [e.g., Main menu] | Banner | Persistent |

### 10.3 IAP Catalog (If Applicable)

| Item | Price | Value |
|------|-------|-------|
| [e.g., Remove Ads] | [$X] | [Permanent] |
| [e.g., Currency Pack] | [$X] | [Amount] |

---

## 11. Analytics & Events

### 11.1 Key Events to Track

| Event | Parameters | Purpose |
|-------|------------|---------|
| `level_start` | level_id, attempt_number | Engagement |
| `level_complete` | level_id, score, time, stars | Progression |
| `level_fail` | level_id, reason, progress | Difficulty tuning |
| `purchase` | item_id, currency, amount | Economy balance |
| `ad_watched` | placement, completed | Ad revenue |

### 11.2 Key Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| FTUE Completion | % completing tutorial | > [X]% |
| Level Funnel | % reaching each level | [Define curve] |
| Session Length | Average play time | [X] minutes |
| DAU/MAU | Daily/Monthly ratio | > [X]% |

---

## 12. Accessibility

### 12.1 Accessibility Features

| Feature | Priority | Implementation |
|---------|----------|----------------|
| Colorblind modes | Should Have | [Patterns, icons, alternative palettes] |
| Scalable UI | Should Have | [Text size options] |
| Reduced motion | Should Have | [Disable particles, shake] |
| One-handed play | Should Have | [Control scheme] |
| Screen reader support | Nice to Have | [ARIA labels] |

---

## 13. Localization

### 13.1 Language Support

| Language | Priority |
|----------|----------|
| English | Must Have |
| [Additional languages] | [Priority] |

### 13.2 Localization Requirements

| Aspect | Consideration |
|--------|---------------|
| Text expansion | UI accommodates [X]% expansion |
| Cultural imagery | [Considerations] |
| Number formatting | [Locale-specific] |
| Date/Time | [Locale-specific] |

---

## 14. Testing Requirements

### 14.1 QA Focus Areas

| Area | Test Types |
|------|------------|
| Gameplay | Balance testing, difficulty curve |
| Performance | Frame rate, memory, load times |
| Compatibility | Cross-browser, cross-device |
| Edge cases | Save corruption, offline, interrupts |

### 14.2 Playtesting

| Phase | Goal | Participants |
|-------|------|--------------|
| Alpha | Core loop validation | Internal team |
| Beta | Balance, bugs, UX | Small external group |
| Soft launch | Live metrics | Limited market |

---

## 15. Release Planning

### 15.1 MVP Scope
- [Core mechanic implemented]
- [X] levels
- [Basic progression]
- [Essential UI screens]
- [Placeholder art acceptable]

### 15.2 Polish Phase
- [Final art and animations]
- [Sound effects and music]
- [Game feel polish]
- [Additional levels]

### 15.3 Post-Launch
- [Additional content]
- [Features based on feedback]
- [Events/seasonal content]

---

## 16. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Core loop not fun | Medium | Critical | Early playtesting |
| Difficulty too hard/easy | High | High | Analytics, iteration |
| Performance issues | Medium | Medium | Regular profiling |
| Scope creep | High | Medium | Strict MVP definition |

---

## 17. Open Questions

| Question | Owner | Resolution |
|----------|-------|------------|
| [Question] | [Person] | [Pending/Resolved] |

---

## 18. Appendices

### A. Reference Games

| Game | What to Learn |
|------|---------------|
| [Reference 1] | [Mechanic/Feel/Style to reference] |
| [Reference 2] | [Mechanic/Feel/Style to reference] |

### B. Glossary

| Term | Definition |
|------|------------|
| [Term] | [Definition] |

---

*Generated with Claudestrator PRD Generator*

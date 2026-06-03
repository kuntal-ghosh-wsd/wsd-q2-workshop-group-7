# Exploratory Testing — Session-Based Charters

Scripted tests check what you thought to write down. **Exploratory testing finds what you didn't.** It's structured improvisation: a charter sets the mission, a timebox bounds the work, and notes capture what was learned.

## Contents
- [Why exploratory matters](#why-exploratory-matters)
- [Session-based testing in one page](#session-based-testing-in-one-page)
- [Writing a charter](#writing-a-charter)
- [Charter examples by purpose](#charter-examples-by-purpose)
- [Running a session](#running-a-session)
- [Session notes — what to capture](#session-notes--what-to-capture)
- [Debriefing](#debriefing)
- [Common mistakes](#common-mistakes)

## Why exploratory matters

Scripted QA misses bugs that come from:

- **Unexpected sequences** the script didn't include (back button, refresh mid-flow, two tabs).
- **Combinatorial state** that's infeasible to enumerate (this filter + that toggle + this role).
- **Perception bugs** — the feature works but feels wrong (slow, confusing, ugly).
- **Adjacent features** the change accidentally broke.
- **Misalignment with intent** — the AC passes, but the user can't actually achieve their goal.

Plan for **both** scripted and exploratory. One alone isn't enough.

## Session-based testing in one page

A session has four ingredients:

1. **Charter** — a 1–3 sentence mission ("Explore dashboard sharing flows to find data-leak bugs").
2. **Timebox** — typically 60–120 minutes. Long enough to go deep; short enough to stay focused.
3. **Tester** — one person (sometimes two; ensemble exploration).
4. **Notes** — written during the session: what was tried, what was found, what was confusing.

After the session: a **debrief** — what was learned, what bugs were filed, what follow-up charters are needed.

This is **Session-Based Test Management (SBTM)** — the lightweight discipline that turns "monkey testing" into something repeatable.

## Writing a charter

A good charter has three parts:

```
Explore <area or feature>
with <resources, tools, or techniques>
to discover <information>.
```

The third part is the key: **what are you hoping to learn?** A charter without a learning goal becomes random clicking.

**Good charters:**

- Explore the dashboard sharing flow with two browser windows and varied roles to discover permission bypass scenarios.
- Explore the file upload feature with edge-case file types (0-byte, exactly-max-size, deeply nested zip) to discover crashes and validation gaps.
- Explore the checkout funnel on a slow 3G connection to discover responsiveness and abandonment risks.
- Explore the search results page across the 12 supported locales to discover layout breakage.
- Explore the new notification preferences UI with a screen reader to discover accessibility gaps.

**Bad charters:**

- Test the dashboard. (No focus, no learning goal.)
- Find bugs in the checkout. (Charter is "find bugs" — too generic.)
- Make sure everything works. (Confirmation bias; you'll see what you want to see.)

## Charter examples by purpose

Generate a small portfolio per release:

| Purpose | Example charter |
|---|---|
| **Permissions / security** | Explore <feature> as each role (admin, editor, viewer, guest) to discover access-control gaps. |
| **Concurrency** | Explore <feature> with two browser sessions acting simultaneously to discover race conditions. |
| **Error recovery** | Explore <feature> while flipping network on and off mid-action to discover broken recovery flows. |
| **Boundary inputs** | Explore <feature> with min/max/empty/oversized inputs to discover validation gaps. |
| **State transitions** | Explore <feature> by triggering uncommon state transitions (back, refresh, browser history) to discover stale-state bugs. |
| **Accessibility** | Explore <feature> using only keyboard (no mouse) and a screen reader to discover a11y gaps. |
| **Internationalization** | Explore <feature> across all supported locales to discover translation and layout issues. |
| **Mobile / responsive** | Explore <feature> on a small viewport with touch input to discover responsive breaks. |
| **Adjacent regression** | Explore <related-feature> that wasn't changed but might have been affected by this release. |
| **Goal-completion** | Walk through <user goal> end-to-end and note any friction or confusion. |

A typical release gets 3–6 charters; high-risk releases get more.

## Running a session

1. **Set a timer.** 60 or 90 minutes. Don't drift.
2. **Stay in the charter.** If you find something interesting outside it, note it down and come back later — open a separate charter if it's substantial.
3. **Vary inputs deliberately.** Don't follow the same path twice.
4. **Take notes as you go.** Don't rely on memory.
5. **Triage as you find issues.** Quick note → file the bug after the session (don't lose flow).
6. **Stop when the timer rings.** Tiredness is when assumptions creep in and quality drops.

## Session notes — what to capture

Minimum to capture per session:

- **Charter** (verbatim).
- **Date / start time / duration.**
- **Tester(s).**
- **Setup** — environment, build version, accounts used.
- **Test ideas tried** — bullets, brief.
- **Bugs found** — link to bug report.
- **Questions raised** — things to ask product / engineering.
- **Follow-up charters suggested** — areas worth deeper exploration.
- **Session rating** — 1-5, how productive the session felt.

Notes don't need to be polished prose. Bullet lists are fine. The discipline is **writing them at all**.

## Debriefing

After each session (or end-of-day for several):

1. **File bugs** found during sessions (see bug-reports reference).
2. **Skim notes** for patterns — same kind of issue across multiple sessions = systemic, not anecdotal.
3. **Update the test plan** — fold confirmed risk areas into next release's plan; remove resolved ones.
4. **Pair-debrief if possible** — explaining what you saw to someone else surfaces things you missed.

## Common mistakes

- **Charters that are just "test X".** No learning goal = no focus. Charters describe what you're trying to **discover**.
- **No timebox.** Sessions drift into hours, focus collapses, productivity drops.
- **No notes.** Without notes, sessions are unreproducible and findings are lost.
- **Exploring during automated test execution.** Two activities, one attention span. Separate them.
- **Skipping exploration "because we have automation".** Automation only catches what was thought of. Exploration is where the unknown unknowns live.
- **One-and-done.** Every release should get fresh charters — repeating the same charter every release yields diminishing returns.
- **No follow-up.** Exploration finds areas worth more attention. Capture those as new charters or test-plan additions, otherwise the work was wasted.

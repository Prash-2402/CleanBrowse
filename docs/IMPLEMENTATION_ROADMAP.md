# AI Parental Control System Roadmap

## 1. Project Goal

Build a real-time parental control system that combines:

- Chrome extension enforcement
- Local AI inference via Flask
- Rule-based fast-path detection
- Event logging and alerting
- Parent-facing reporting and controls

The system should block or soften unsafe content with low latency while avoiding obvious false positives.

## 2. Current Baseline

### Already working

- Chrome extension exists with:
  - `manifest.json`
  - `background.js`
  - `content.js`
  - `blocked.html`
  - `popup.html`
- URL keyword blocking exists in `background.js`
- DOM text blurring exists in `content.js`
- Flask API exists in `app.py`
- `/analyze-text` returns:
  - `toxicity_score`
  - `label`
- Text ML pipeline exists:
  - Kaggle toxic comment dataset
  - TF-IDF
  - Logistic Regression
  - `model.pkl`
  - `vectorizer.pkl`

### Known gaps

- Extension is not fully integrated with Flask text analysis yet
- No event logging endpoint yet
- No SQLite storage yet
- No parent alert flow yet
- No cache layer yet
- No image moderation yet
- No pre-load request blocking yet
- No bypass protection yet
- No parent dashboard yet

## 3. Target Architecture

```text
Browser Navigation / Page Load
        |
        v
Chrome Extension Background Script
        |
        +--> Pre-load URL blocking / reputation checks
        |
        v
Content Script
        |
        +--> Extract visible page text
        +--> Detect search box input
        +--> Watch DOM changes lazily
        |
        v
Local Flask API
        |
        +--> Rule-based keyword match
        +--> Cache lookup
        +--> ML text scoring
        +--> Event logging
        +--> Parent alert trigger
        |
        v
Decision Layer
        |
        +--> Allow
        +--> Blur
        +--> Replace
        +--> Block
        |
        v
SQLite Event Store
        |
        v
Parent Dashboard / Alerts / Reports
```

## 4. Priority Order

### Build now

1. Hybrid text filtering
2. Extension to Flask integration
3. Event logging with SQLite
4. Parent alerts
5. In-memory caching
6. Pre-load URL blocking improvements
7. Search monitoring
8. Bypass protection basics
9. Safety score and confidence UI

### Build after that

1. Age-based modes
2. Reputation scoring
3. Image moderation
4. Weekly reports
5. Parent dashboard
6. YouTube filtering
7. Safe search enforcement

### Defer for later

1. Full cross-platform sync
2. Video frame-by-frame filtering
3. Adaptive retraining from parent feedback
4. Full edge AI in browser
5. Multi-language support beyond architecture planning

## 5. Phase-by-Phase Roadmap

## Phase 0: Stabilize the Current Foundation

### Goal

Make the current extension + API easier to extend safely.

### Deliverables

- Consistent naming across extension and API
- Clear config/constants for:
  - blocked keywords
  - thresholds
  - API URL
  - feature toggles
- Basic developer documentation
- Repeatable local run flow

### Files likely involved

- `app.py`
- `background.js`
- `content.js`
- `manifest.json`
- `popup.html`
- new docs/config files

### Why this matters

The project is starting to span browser scripts, local API logic, ML artifacts, and future persistence. If constants and behavior stay scattered, every future change gets slower and riskier.

### Steps for me

1. Audit duplicated keyword lists and move them into clearer structures.
2. Document the runtime flow from browser to API.
3. Make extension and API contracts explicit before adding more endpoints.
4. Add a small "run + test" checklist to the repo.

### Steps for you

1. Decide the product name and keep file naming consistent.
2. Decide whether the first user experience is:
   - hard block by default
   - blur by default
   - warning screen first
3. Decide whether the system is fully local-only in the first milestone.

### Prompt for me

"Review the current Chrome extension and Flask app. Do not add new features yet. Clean up naming, shared constants, and configuration so the codebase is ready for hybrid filtering, event logging, and extension-to-API integration. Keep the current behavior working."

## Phase 1: Hybrid Text Filtering

### Goal

Use a fast rule-based shortcut before the ML model so the system catches obvious adult/slang text quickly and cheaply.

### Deliverables

- Unsafe keyword list in the API
- `/analyze-text` first checks keywords
- If keyword matches:
  - `toxicity_score = 1.0`
  - `label = "unsafe"`
- If no match:
  - run ML model as fallback
- Shared preprocessing rules between training and inference

### Why this matters

The current ML model is better at toxicity/threat language than adult content. Hybrid filtering closes that gap immediately while keeping latency low.

### Detailed implementation steps

1. Normalize input text consistently:
   - lowercase
   - remove special characters where appropriate
   - collapse spaces
2. Check a curated unsafe keyword list first.
3. Use word-boundary-safe matching to reduce false positives.
4. Only run `vectorizer.transform()` and `model.predict_proba()` when rule checks pass cleanly.
5. Return a consistent JSON response shape for both rule hits and ML hits.
6. Add trace metadata internally if useful, but keep public API simple unless needed.

### Risks

- Substring matching can create false positives.
- Overly small keyword lists will miss slang variants.
- Overly broad keyword lists can flag harmless educational content.

### Success criteria

- Clearly unsafe slang/adult text is caught instantly.
- Existing ML scoring still works for ambiguous text.
- API contract remains stable for the extension.

### Steps for you

1. Review and approve the first keyword set.
2. Decide whether educational/medical contexts should be:
   - allowed
   - blurred
   - warned but visible
3. Collect 20 to 30 real examples you want tested.

### Prompt for me

"Implement hybrid filtering in the Flask `/analyze-text` endpoint. Add a keyword fast-path before ML inference, keep the response contract stable, prefer word-safe matching over naive substring checks, and do not break existing model loading."

## Phase 2: Cache for Real-Time Performance

### Goal

Avoid repeated analysis of the same text.

### Deliverables

- In-memory cache in Flask
- Cache key based on normalized input text
- Reuse cached result for repeated text
- Optional cache stats for debugging

### Why this matters

DOM scanning can re-send repeated text many times. Without caching, the same paragraphs and UI labels will be analyzed again and again.

### Detailed implementation steps

1. Normalize text before cache lookup.
2. Use normalized text as the cache key.
3. Store:
   - toxicity score
   - label
   - source of decision if needed
4. Add a simple cache size limit or eviction strategy.
5. Skip caching empty or tiny strings if they create noise.

### Risks

- Unlimited cache growth will waste memory.
- Minor text variations may reduce cache hit rate.
- If thresholds change, stale cached results can linger during development.

### Success criteria

- Repeated text analysis is visibly faster.
- Memory usage stays reasonable.
- Behavior stays identical for uncached text.

### Steps for you

1. Decide whether a simple dictionary is enough for milestone one.
2. Decide if cache should reset on server restart.
3. Decide whether to cache safe-only, unsafe-only, or both.

### Prompt for me

"Add lightweight in-memory caching to the Flask text analysis pipeline. Use normalized text as the key, keep the implementation simple, prevent unbounded memory growth, and preserve the same `/analyze-text` API response."

## Phase 3: Extension to API Integration

### Goal

Make the Chrome extension call the local Flask API and react to its decisions.

### Deliverables

- `content.js` extracts text in chunks
- Requests sent to `http://127.0.0.1:5000/analyze-text`
- Extension receives `toxicity_score` and `label`
- Decision logic:
  - blur
  - replace
  - block
  - allow

### Why this matters

This turns the trained model into a live protection system instead of a standalone demo.

### Detailed implementation steps

1. Decide what unit of text is sent:
   - page-level
   - paragraph-level
   - visible block-level
2. Start with visible block-level scanning for better precision.
3. Debounce API calls to avoid flooding the local server.
4. Tag already-scanned nodes to avoid repeat work.
5. Apply action policy based on score thresholds.
6. Keep existing rule-based front-end blur behavior as a fallback.

### Risks

- Too many API calls can slow browsing.
- Large pages can overwhelm the API if scanned all at once.
- Sending whole-page text can reduce accuracy and context quality.

### Success criteria

- Text analysis works during normal browsing.
- Visible unsafe text gets blurred or blocked quickly.
- Browsing still feels responsive.

### Steps for you

1. Decide the first action policy:
   - blur at medium score
   - block at high score
2. Decide whether to analyze only visible elements first.
3. Test on:
   - news sites
   - forums
   - YouTube
   - search results pages

### Prompt for me

"Integrate the Chrome content script with the local Flask `/analyze-text` endpoint. Analyze visible text in controlled chunks, debounce requests, avoid rescanning the same nodes, and apply score-based blur/block behavior without freezing the page."

## Phase 4: Event Logging with SQLite

### Goal

Persist important safety events for reporting and alerts.

### Deliverables

- `POST /report-event`
- SQLite database initialization
- Events table:
  - `id`
  - `type`
  - `url`
  - `text`
  - `timestamp`
  - `severity`
- Extension sends events for:
  - blocked site
  - unsafe search
  - unsafe content
  - bypass attempt

### Why this matters

Without a persistent event store, there is no real parent monitoring layer.

### Detailed implementation steps

1. Create database initialization on app startup.
2. Validate incoming event payloads carefully.
3. Sanitize missing/empty fields.
4. Insert events into SQLite.
5. Return a clean success response.
6. Add one helper for database writes to keep API code clean.

### Risks

- Repeated DOM detections can spam the database.
- Large captured text blobs can make logs noisy.
- SQLite is fine early, but not ideal forever.

### Success criteria

- Every important unsafe event can be recorded.
- Logged events are easy to query later.
- The endpoint is stable enough for the extension to rely on.

### Steps for you

1. Decide how much text should be stored:
   - full text
   - snippet only
   - no text for privacy-sensitive cases
2. Decide severity rules for each event type.
3. Decide whether URLs should be stored exactly or by domain only.

### Prompt for me

"Add a `/report-event` Flask endpoint backed by SQLite. Validate the payload, initialize the database if needed, store events cleanly, and keep the schema simple enough to support future reporting and alerts."

## Phase 5: Parent Alert Simulation

### Goal

Trigger a parent-facing alert whenever a meaningful unsafe event is reported.

### Deliverables

- `send_parent_alert(event)` function
- Called automatically from `/report-event`
- Simulated console alert output for now

### Why this matters

This creates the real-time monitoring flow even before a parent app exists.

### Detailed implementation steps

1. Decide which event types trigger alerts immediately.
2. Decide whether severity affects alert behavior.
3. Call alert logic after successful database write.
4. Keep the alert interface generic so future email/SMS/push can plug in later.

### Risks

- Too many alerts will create fatigue.
- Alerting before deduplication can spam parents.

### Success criteria

- High-value unsafe events create alerts.
- Alert flow is easy to upgrade later.

### Steps for you

1. Decide which events are urgent:
   - blocked site
   - unsafe search
   - bypass attempt
2. Decide whether low-severity content should only be logged.

### Prompt for me

"Add a parent alert hook to the event reporting flow. Keep it simple for now with a simulated alert function, but design it so email, push, or SMS delivery can be added later without rewriting the event pipeline."

## Phase 6: Pre-Load Website Blocking

### Goal

Block unsafe sites before content renders.

### Deliverables

- Stronger request-time URL screening in `background.js`
- Warning/block screen before page content appears
- Category-aware reasons:
  - adult
  - violence
  - gambling

### Why this matters

Blocking after page render is weaker and produces a worse user experience than stopping the page early.

### Detailed implementation steps

1. Audit which Chrome APIs are available under Manifest V3 for interception.
2. Keep current keyword-based URL logic as the initial detection layer.
3. Add category labeling to blocked URL matches.
4. Pass reason metadata to `blocked.html`.
5. Later add reputation-based decisions without rewriting the flow.

### Risks

- Manifest V3 limitations may shape the interception method.
- Overblocking based on URL keywords alone can frustrate users.
- Some unsafe pages will not expose clear keywords in the URL.

### Success criteria

- Known unsafe URLs are blocked before rendering.
- The block page explains why the site was blocked.
- The background logic remains fast and stable.

### Steps for you

1. Decide whether warning screens should allow parent override.
2. Decide whether blocked reasons should be visible to the child.
3. Collect example URLs across adult, gambling, and violence categories.

### Prompt for me

"Upgrade the extension's background protection so unsafe URLs are blocked before page content renders. Keep the implementation compatible with Manifest V3, preserve the existing blocked page flow, and attach reason metadata for better UX."

## Phase 7: Search Monitoring + Safe Search

### Goal

Catch unsafe intent at the search box before or as results appear.

### Deliverables

- Detect search inputs on:
  - Google
  - YouTube
  - optionally Bing
- Match unsafe search queries
- Report `unsafe_search` events
- Enforce safe search where possible

### Why this matters

A lot of risky content starts as a search, not a directly typed URL.

### Detailed implementation steps

1. Identify search input selectors for major engines.
2. Watch submitted queries.
3. Apply rule-based search checks first.
4. Optionally route borderline searches to the local API later.
5. Log unsafe searches through `/report-event`.
6. Add safe-search enforcement if URL/query params allow it.

### Risks

- Search site DOM structures change often.
- Overaggressive query blocking can annoy users.
- Safe search enforcement differs by site.

### Success criteria

- Unsafe searches are detected reliably.
- Parent logs show searches clearly.
- Safe search stays enabled where supported.

### Steps for you

1. Decide which search engines matter first.
2. Decide whether unsafe searches should:
   - block
   - warn
   - just log

### Prompt for me

"Add search monitoring to the extension for Google and YouTube first. Detect unsafe search terms, report them through `/report-event`, and enable safe search where practical without breaking normal browsing."

## Phase 8: Bypass Protection

### Goal

Detect tampering and attempts to get around protection.

### Deliverables

- Detect incognito-related gaps where possible
- Detect extension disable or missing-heartbeat scenarios where possible
- Log `bypass_attempt` events
- Trigger parent alert for high-severity bypass behavior

### Why this matters

If the child can easily bypass the system, the rest of the protection stack matters less.

### Detailed implementation steps

1. Define what counts as a bypass attempt in technical terms.
2. Use the extension lifecycle signals available under Chrome's extension model.
3. Add heartbeat/state checks where realistic.
4. Log bypass events separately from content events.
5. Mark bypass events high severity by default.

### Risks

- Some disable attempts cannot be detected after the fact from inside the disabled extension.
- Incognito behavior depends on Chrome settings and permissions.
- Strong anti-tamper guarantees may require admin/device-level controls later.

### Success criteria

- Obvious tampering gaps are reduced.
- Monitoring surfaces likely bypass behavior.
- The parent system sees security-relevant events separately.

### Steps for you

1. Decide what "good enough" means for bypass detection in the first release.
2. Decide whether the first release targets home demo use or stricter device-managed use.

### Prompt for me

"Design and implement practical first-stage bypass protection for the extension. Focus on realistic signals available in Chrome, log high-severity bypass attempts, and avoid promising guarantees the browser platform cannot support."

## Phase 9: Confidence UI + Age Modes

### Goal

Make decisions transparent and adjustable.

### Deliverables

- Safety score shown in extension UI or warning screen
- Age-based profiles:
  - Kid
  - Teen
  - Custom
- Thresholds mapped to profiles

### Why this matters

A visible safety score builds trust, and age-based modes make the product usable for different families without rewriting logic.

### Detailed implementation steps

1. Define score thresholds for each mode.
2. Define what each mode changes:
   - URL strictness
   - text threshold
   - logging sensitivity
   - alert sensitivity
3. Surface the current mode in the UI.
4. Apply the chosen mode consistently across extension and API policy decisions.

### Risks

- Confusing score display can reduce trust.
- If the score seems arbitrary, parents may ignore it.

### Success criteria

- Parents can understand why content was blocked.
- Changing mode changes behavior in a predictable way.

### Steps for you

1. Define the strictness of Kid vs Teen mode.
2. Decide whether settings live locally first or later sync to cloud.

### Prompt for me

"Add a clear safety scoring and profile system to the extension experience. Support Kid, Teen, and Custom modes, and keep the thresholds understandable so parents can predict how the system will behave."

## Phase 10: Image Moderation

### Goal

Detect and blur unsafe images.

### Deliverables

- Initial image scanning architecture
- Image source collection from the DOM
- Cache for already-scanned image URLs
- Blur/hide action for unsafe images

### Why this matters

Text filtering alone will miss a large portion of unsafe browsing content.

### Detailed implementation steps

1. Start with static images before video.
2. Scan visible images first.
3. Cache per-image results aggressively.
4. Decide whether inference is local or external.
5. Blur/hide image elements with minimal layout disruption.

### Risks

- Image moderation can be computationally expensive.
- Remote image scanning raises privacy concerns.
- False positives on medical/educational imagery can be frustrating.

### Success criteria

- Unsafe images are blurred reliably.
- Normal browsing remains responsive.
- Repeated scans are minimized by caching.

### Steps for you

1. Decide whether image detection must stay fully local.
2. Decide whether medical/educational exceptions matter in v1.
3. Collect a small safe/unsafe image test set.

### Prompt for me

"Design the first image moderation pass for the parental control extension. Start with visible static images, cache results, prefer a low-latency approach, and avoid taking on video-frame moderation in this phase."

## Phase 11: Reporting + Dashboard

### Goal

Turn raw events into parent-friendly insight.

### Deliverables

- Summary statistics
- Weekly reports
- Basic dashboard view
- Most-visited categories
- Blocked-attempt counts
- Time-spent summaries if feasible

### Why this matters

Logs alone are not a usable parent product. Insight and summaries are the real value.

### Detailed implementation steps

1. Define reporting metrics from the existing events table.
2. Add aggregation queries.
3. Build a simple dashboard prototype.
4. Add weekly summary generation.
5. Keep notification noise low by emphasizing digest-style reporting.

### Risks

- Raw event quality affects report quality.
- Without deduplication, weekly reports may overcount.

### Success criteria

- Parents can understand behavior at a glance.
- Reports show trends, not just raw incidents.

### Steps for you

1. Decide the first dashboard platform:
   - local web page
   - separate web app
2. Decide the top 5 metrics parents care about most.

### Prompt for me

"Build the first parent-facing reporting layer on top of the logged events. Focus on useful summaries and weekly reports, not raw database dumps, and keep the first dashboard minimal but genuinely informative."

## 6. Feature Mapping

### Must-have features mapped to roadmap

- Smart website blocking: Phase 6
- AI text filtering: Phases 1 to 3
- Image moderation: Phase 10
- Real-time protection: Phases 2, 3, 6
- Context-aware filtering: Phases 1, 3, later model improvements
- Age-based modes: Phase 9
- Safe summary generator: later after Phase 9
- Activity monitoring: Phases 4, 5, 11
- Override protection: Phases 8 and 9
- Content scoring: Phase 9

### High-value additions mapped

- Bypass protection: Phase 8
- Pre-load protection: Phase 6
- URL and page reputation: after Phase 6
- Local cache: Phases 2 and 10
- Lazy scanning: Phase 3
- Confidence UI: Phase 9
- Safe search: Phase 7
- YouTube filtering: Phase 7 and later refinements
- Weekly report: Phase 11

### Deferred items

- Video content filtering: not now
- Full cross-platform sync: not now

## 7. Recommended Milestone Sequence

### Milestone 1: Make text protection usable

- Finish hybrid filtering
- Add caching
- Connect extension to `/analyze-text`
- Add score-based blur/block

### Milestone 2: Make it monitorable

- Add `/report-event`
- Add SQLite storage
- Add parent alert simulation

### Milestone 3: Make it harder to bypass

- Pre-load URL blocking
- Search monitoring
- Safe search
- Bypass attempt detection

### Milestone 4: Make it parent-friendly

- Safety score UI
- Age modes
- Weekly reports
- Simple dashboard

### Milestone 5: Expand coverage

- Image moderation
- Reputation scoring
- YouTube-specific filtering

## 8. Testing Plan You Should Follow

### Functional tests

1. Test safe pages with normal educational/news text.
2. Test unsafe pages with adult, violence, and gambling keywords.
3. Test mixed-content pages where only some sections are unsafe.
4. Test Google and YouTube searches.
5. Test repeated page loads to confirm caching works.
6. Test blocked-page behavior for known bad URLs.

### Performance tests

1. Test long articles.
2. Test comment-heavy pages.
3. Test infinite-scroll pages.
4. Measure:
   - time to first protection action
   - number of API calls
   - cache hit rate

### Safety quality tests

1. Build a small set of:
   - obvious unsafe text
   - borderline text
   - safe educational text
2. Track:
   - false positives
   - false negatives
   - mode-specific behavior

### Logging tests

1. Confirm every blocked event is stored.
2. Confirm alert simulation fires for the right severity.
3. Confirm duplicate events do not explode the database.

## 9. Decisions You Should Make Early

1. What score thresholds map to:
   - allow
   - blur
   - block
2. Whether the first version is:
   - fully local
   - local plus lightweight parent reporting
3. Whether the first release prioritizes:
   - strict protection
   - fewer false positives
4. Whether stored event text should be:
   - full
   - partial
   - omitted
5. Whether parent override exists in v1

## 10. Best Next Action

If you want the highest-value next implementation step, do this order:

1. Hybrid filtering in Flask
2. Cache layer
3. Extension calls `/analyze-text`
4. `/report-event` with SQLite
5. Parent alert simulation
6. Pre-load URL blocking improvements

## 11. Master Prompt for Future Build Steps

Use this prompt when you want me to implement the next milestone:

"Work inside this Chrome extension + Flask parental control project. Keep changes modular and production-minded. Prioritize low latency, hybrid filtering, and minimizing false positives. Before editing, inspect the current relevant files. Then implement the requested milestone end-to-end, update only the necessary files, and explain how to test it."


# BrandSentinel (Team Codestrom, FutureStack Round 2)

Review brand content before it is published. A creator pastes text or uploads an image; BrandSentinel checks it against the
organisation's approved facts, terminology, tone rules, accessibility rules and colour palette, explains every finding, and suggests
a fix. The creator decides. Content then goes through manager approval and (for high-risk content) authorised-reviewer sign-off.

The demo brand "Lumio Home" and all its facts are fictional.

## Run it
It is one static file. Open `index.html` in a browser, or host the folder on any static host (GitHub Pages, Netlify, Vercel).
No build step, no server, no API keys. Content never leaves the browser (stored in `localStorage`).

**GitHub Pages:** push this folder to a public repository, then Settings > Pages > Deploy from branch `main` / root.

## Try it (about one minute)
1. Choose a user at the top right (starts as the creator).
2. Open "Diwali offer - social post", click **Run BrandSentinel review**.
3. Click **Use approved wording** on the "40,000 hours" finding. Dismiss one finding (a reason is required).
4. Fix the rest, then **Submit for review**. Switch to the manager, then the reviewer, and approve.
5. As creator, **Mark publish-ready** to download the report. Open **Insights**.

## How the review works
- Terminology, absolute-claim, tone and accessibility checks: deterministic rules.
- Fact check: TF-IDF cosine similarity to approved facts (>= 0.30 = same topic); numbers equal = supported, differ = contradicted,
  no match = unsupported (a human decides; nothing is guessed).
- Contrast: WCAG relative-luminance ratio, 4.5:1 minimum. Images: dominant colours versus palette, size, alt text.
- No AI model or external API is used in this version.

## Tests
```
pip install playwright pillow && playwright install chromium
python3 tests/run_tests.py     # 27 end-to-end and engine checks, labelled set in tests/testset.json
python3 tests/make_screens.py  # screenshots
```

## Disclosure
An AI assistant (Claude by Anthropic) helped write and test this code. No third-party runtime libraries or templates are used.
Test tooling only: Playwright, Pillow.

## Round 3 plan
Shared multi-user backend (FastAPI + PostgreSQL); AI-grounded verification with Confidential mode and AI-disclosure ledger;
PDF/DOCX/OCR ingestion with logo and asset checks.

## Team
Codestrom. Team leader: Dilkesh Meena.

"""Regression tests for the BrandSentinel review engine and the full approval workflow.
Run:  python3 tests/run_tests.py   (needs: pip install playwright && playwright install chromium)"""
import asyncio, json, os, sys
from playwright.async_api import async_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
URL = "file://" + os.path.join(os.path.dirname(HERE), "index.html")
SHOTS = os.environ.get("SHOTS", os.path.join(HERE, "screens"))
os.makedirs(SHOTS, exist_ok=True)
results = []

def check(name, cond, detail=""):
    results.append((name, bool(cond), detail))
    print(("PASS " if cond else "FAIL ") + name + (" - " + detail if detail and not cond else ""))

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        ctx = await b.new_context(viewport={"width": 1280, "height": 900})
        pg = await ctx.new_page()
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        await pg.goto(URL)

        # ---------- A. engine accuracy on labelled set ----------
        cases = json.load(open(os.path.join(HERE, "testset.json")))
        tp = fp = fn = 0; exact = 0; wrong = []
        for c in cases:
            got = await pg.evaluate("t=>[...new Set(BS.reviewText(t).filter(f=>f.severity!=='info').map(f=>f.rule))]", c["t"])
            exp, got = set(c["e"]), set(got)
            tp += len(exp & got); fp += len(got - exp); fn += len(exp - got)
            if exp == got: exact += 1
            else: wrong.append((c["t"], sorted(exp), sorted(got)))
        prec = tp / (tp + fp) if tp + fp else 1; rec = tp / (tp + fn) if tp + fn else 1
        print(f"ENGINE cases={len(cases)} exact={exact} precision={prec:.3f} recall={rec:.3f}")
        for w in wrong: print("  MISS", w)
        json.dump({"cases": len(cases), "exact": exact, "tp": tp, "fp": fp, "fn": fn, "precision": prec, "recall": rec, "wrong": wrong},
                  open(os.path.join(SHOTS, "accuracy.json"), "w"))
        check("engine: no false alarms on clean on-brand sentences", not [w for w in wrong if not w[1] and w[2]], str([w for w in wrong if not w[1]]))

        # contrast
        r = await pg.evaluate("BS.contrast('#777777','#FFFFFF')")
        check("WCAG contrast #777 on white = 4.48", abs(r - 4.48) < 0.02, str(r))
        r = await pg.evaluate("BS.contrast('#000000','#FFFFFF')")
        check("WCAG contrast black on white = 21", abs(r - 21) < 0.01, str(r))

        # ---------- B. end-to-end workflow ----------
        async def role(r): await pg.select_option("#role", r)
        await pg.screenshot(path=f"{SHOTS}/01_content_list.png")
        await pg.click("tr[data-open]:has-text('Diwali')")
        await pg.click("[data-review]")
        await pg.wait_for_selector(".find")
        n_find = await pg.locator(".find").count()
        check("review shows findings with explanations", n_find >= 8, str(n_find))
        check("submit blocked while high findings open", await pg.locator("[data-submit]").is_disabled())
        await pg.screenshot(path=f"{SHOTS}/02_findings.png", full_page=True)

        # accept term suggestion
        before = await pg.inner_text("#docv")
        await pg.locator(".find:has-text('Lumio Lite') [data-accept]").first.click()
        after = await pg.inner_text("#docv")
        check("accepting suggestion edits text (Lumio Lite -> Lumio Glow)", "Lumio Lite" in before and "Lumio Lite" not in after and "Lumio Glow" in after)

        # accept approved wording for contradicted claim
        await pg.locator(".find:has-text('40,000') [data-accept]").first.click()
        check("contradicted figure replaced with approved fact", "25,000 hours" in await pg.inner_text("#docv"))

        # dismiss needs a reason
        first_dis = pg.locator(".find:has-text('guys') [data-dis]").first
        await first_dis.click()
        await pg.locator(".find:has-text('guys') [data-dis-ok]").first.click()
        check("dismiss without reason does nothing", await pg.locator(".find:has-text('guys') [data-dis-ok]").count() == 1)
        await pg.locator(".find:has-text('guys') input[id^=dr-]").first.fill("Casual tone is fine for this campaign")
        await pg.locator(".find:has-text('guys') [data-dis-ok]").first.click()
        check("dismiss with reason is recorded", await pg.locator("text=Casual tone is fine for this campaign").count() >= 1)

        # clear remaining high findings: ABS ones -> edit text manually
        await pg.click("[data-edit]")
        newtxt = "Meet Lumio Glow, an affordable smart bulb. Lumio Glow uses up to 80% less energy than a traditional incandescent bulb. Our bulbs last 25,000 hours. Order today."
        await pg.fill("#txt", newtxt)
        await pg.click("[data-review]")
        await pg.wait_for_selector(".find")
        check("clean text: submit enabled", await pg.locator("[data-submit]").is_enabled())
        await pg.screenshot(path=f"{SHOTS}/03_clean_review.png", full_page=True)
        await pg.click("[data-submit]")
        check("status = In review", await pg.locator("h2 .tag").inner_text() == "In review")

        # creator cannot approve
        check("creator sees no approve button", await pg.locator("[data-approve]").count() == 0)

        # manager: request changes needs comment
        await role("manager")
        await pg.click("[data-changes]")
        check("request changes without comment is blocked", await pg.locator("h2 .tag").inner_text() == "In review")
        await pg.fill("#chg", "Please add the Diwali offer dates.")
        await pg.click("[data-changes]")
        check("manager can request changes", await pg.locator("h2 .tag").inner_text() == "Changes requested")
        await pg.screenshot(path=f"{SHOTS}/04_changes_requested.png", full_page=True)

        # creator revises and resubmits
        await role("creator")
        await pg.click("[data-edit]")
        await pg.fill("#txt", newtxt + " Offer valid till 31 October.")
        await pg.click("[data-review]")
        await pg.wait_for_selector(".find")
        await pg.click("[data-submit]")
        # manager approves -> because high risk was flagged, goes to sign-off
        await role("manager")
        await pg.screenshot(path=f"{SHOTS}/05_manager_review.png", full_page=True)
        await pg.click("[data-approve]")
        check("high-risk content goes to sign-off", await pg.locator("h2 .tag").inner_text() == "Awaiting sign-off")
        await role("reviewer")
        await pg.click("[data-approve]")
        check("reviewer sign-off approves", await pg.locator("h2 .tag").inner_text() == "Approved")
        await role("creator")
        async with pg.expect_download() as dl:
            await pg.click("[data-publish]")
        d = await dl.value
        path = os.path.join(SHOTS, "report_sample.md"); await d.save_as(path)
        rep = open(path).read()
        check("report downloaded with AI disclosure and history", "AI disclosure" in rep and "Authorised reviewer signed off" in rep)
        check("status = Publish-ready", await pg.locator("h2 .tag").inner_text() == "Publish-ready")
        await pg.screenshot(path=f"{SHOTS}/06_publish_ready.png", full_page=True)

        # ---------- C. knowledge base + insights + persistence ----------
        await role("admin")
        await pg.click("[data-nav=kb]")
        await pg.fill("#nf", "Lumio Glow ships with a 3-year guarantee card. | Spec Sheet v5")
        await pg.click("[data-addfacts]")
        check("admin can add an approved fact", await pg.locator("text=3-year guarantee card").count() == 1)
        await pg.screenshot(path=f"{SHOTS}/07_knowledge_base.png", full_page=True)
        await role("creator")
        check("non-admin cannot edit KB", await pg.locator("[data-addfacts]").is_disabled())
        await pg.click("[data-nav=insights]")
        await pg.screenshot(path=f"{SHOTS}/08_insights.png", full_page=True)
        check("insights show human decisions", await pg.locator("text=human decisions recorded").count() == 1)
        await pg.reload()
        await pg.click("[data-nav=content]")
        check("state persists after reload", await pg.locator("text=Publish-ready").count() >= 1)

        # ---------- D. image + contrast checks ----------
        await pg.click("tr[data-open]:has-text('City launch')")
        await pg.click("summary:has-text('Image and colour checks')")
        await pg.fill("#fg", "#777777"); await pg.fill("#bg", "#FFFFFF")
        await pg.click("[data-review]")
        await pg.wait_for_selector(".find")
        check("low contrast flagged", await pg.locator(".find:has-text('Contrast ratio is 4.48')").count() == 1)
        # make a red test image
        from PIL import Image
        im = Image.new("RGB", (300, 200), (200, 20, 40)); imgp = os.path.join(SHOTS, "red.png"); im.save(imgp)
        await pg.set_input_files("#img", imgp)
        await pg.wait_for_selector("img.thumb")
        await pg.click("[data-review]")
        await pg.wait_for_selector(".find")
        check("off-palette colour flagged", await pg.locator(".find:has-text('not close to the approved palette')").count() >= 1)
        check("missing alt text flagged", await pg.locator(".find:has-text('no meaningful alternative text')").count() == 1)
        check("small image flagged", await pg.locator(".find:has-text('smaller than 400px')").count() == 1)
        await pg.screenshot(path=f"{SHOTS}/09_image_checks.png", full_page=True)

        check("no JavaScript errors in the whole run", not errs, str(errs))
        await b.close()
    passed = sum(1 for r in results if r[1])
    print(f"\nRESULT {passed}/{len(results)} checks passed")
    json.dump(results, open(os.path.join(SHOTS, "results.json"), "w"))
    sys.exit(0 if passed == len(results) else 1)
asyncio.run(main())

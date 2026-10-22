"""Creates the screenshots used in the Round 2 PDF."""
import asyncio, os
from playwright.async_api import async_playwright
HERE = os.path.dirname(os.path.abspath(__file__)); URL = "file://" + os.path.join(os.path.dirname(HERE), "index.html")
OUT = os.path.join(HERE, "shots")
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(); pg = await (await b.new_context(viewport={"width": 1280, "height": 860})).new_page()
        await pg.goto(URL)
        async def role(r): await pg.select_option("#role", r)
        # review all three seeds as creator
        for title in ("Diwali", "Warranty", "City launch"):
            await pg.click("tr[data-open]:has-text('%s')" % title); await pg.click("[data-review]"); await pg.wait_for_selector(".find, p.dim")
            if title == "Diwali":
                await pg.screenshot(path=f"{OUT}/findings.png", clip={"x": 0, "y": 0, "width": 1280, "height": 1250}, full_page=True)
                # decisions for insights: dismiss two tone items, accept one
                for w in ("OMG", "guys"):
                    await pg.locator(f".find:has-text('{w}') [data-dis]").first.click()
                    await pg.locator(f".find:has-text('{w}') input[id^=dr-]").first.fill("Informal voice is intended for this festive post")
                    await pg.locator(f".find:has-text('{w}') [data-dis-ok]").first.click()
                await pg.locator(".find:has-text('super') [data-accept]").first.click()
            await pg.click("[data-back]")
        # submit the warranty FAQ so manager has a queue
        await pg.click("tr[data-open]:has-text('Warranty')"); await pg.click("[data-submit]"); await pg.click("[data-back]")
        await pg.screenshot(path=f"{OUT}/list_creator.png", clip={"x": 0, "y": 0, "width": 1280, "height": 560})
        await role("manager")
        await pg.screenshot(path=f"{OUT}/list_manager.png", clip={"x": 0, "y": 0, "width": 1280, "height": 560})
        await pg.click("tr[data-open]:has-text('Warranty')")
        await pg.screenshot(path=f"{OUT}/manager_review.png", clip={"x": 0, "y": 0, "width": 1280, "height": 760}, full_page=True)
        await role("admin"); await pg.click("[data-nav=kb]")
        await pg.screenshot(path=f"{OUT}/kb.png", clip={"x": 0, "y": 0, "width": 1280, "height": 820}, full_page=True)
        await pg.click("[data-nav=insights]")
        await pg.screenshot(path=f"{OUT}/insights.png", clip={"x": 0, "y": 0, "width": 1280, "height": 830}, full_page=True)
        # image check
        await role("creator"); await pg.click("[data-nav=content]")
        from PIL import Image
        Image.new("RGB", (300, 200), (200, 20, 40)).save(f"{OUT}/red.png")
        await pg.click("tr[data-open]:has-text('City launch')")
        await pg.click("summary:has-text('Image and colour checks')")
        await pg.fill("#fg", "#777777"); await pg.fill("#bg", "#FFFFFF")
        await pg.set_input_files("#img", f"{OUT}/red.png"); await pg.wait_for_selector("img.thumb")
        await pg.click("[data-review]"); await pg.wait_for_selector(".find")
        await pg.screenshot(path=f"{OUT}/image_checks.png", clip={"x": 0, "y": 0, "width": 1280, "height": 1100}, full_page=True)
        await b.close()
asyncio.run(main())

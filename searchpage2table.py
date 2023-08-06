import asyncio
from playwright.async_api import async_playwright
from unstructured.partition.html import partition_html

async def load_with_playwright(url: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url)

        remove_selectors = ["header", "footer"]
        for selector in remove_selectors or []:
            elements = await page.locator(selector).all()
            for element in elements:
                if await element.is_visible():
                    await element.evaluate("element => element.remove()")
    
        elements = await page.locator("a").all()
        for element in elements:
            if await element.is_visible():
                await element.evaluate("""e => e.innerHTML = `url: ${e.href} ${e.innerText}`;""")

        pgc = await page.content()

        page_source = await page.content()
        elements = partition_html(text=page_source)
        text = "\n\n".join([str(el) for el in elements])

        print(text)
        return text


if __name__ == "__main__":
    asyncio.run(load_with_playwright("https://www.google.com/search?q=精神現象学&oq=%E7%B2%BE%E7%A5%9E%E7%8F%BE%E8%B1%A1%E5%AD%A6&aqs=chrome..69i57.4398j0j1&sourceid=chrome&ie=UTF-8"))

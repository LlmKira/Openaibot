# -*- coding: utf-8 -*-
# @Time    : 12/28/22 11:41 AM
# @FileName: broswer_test.py
# @Software: PyCharm
# @Github    ：sudoskys
import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        for browser_type in [p.chromium, p.firefox, p.webkit]:
            browser = await browser_type.launch()
            page = await browser.new_page()
            await page.goto('http://whatsmyuseragent.org/')
            await page.screenshot(path=f'example-{browser_type.name}.png')
            await browser.close()

asyncio.run(main())
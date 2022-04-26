import asyncio

import os
from playwright.async_api import Error, async_playwright, BrowserContext, Error
from mods.classes import Config
from mods.datamgr import DataManager

from mods.logouter import Logouter
from mods.settings import CHROMIUM_USER_DATA_DIR
from mods.utils import valid_filename


class Spider:

    def __init__(self, config, parser, saver) -> None:
        self.config: Config = config
        self.parser = parser
        self.saver = saver
        self.semaphore_crawl = asyncio.Semaphore(self.config.ccount)

    def run(self):
        Logouter.blue(f'开始爬取任务,引擎:{self.parser.name}')
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.start_crawl_task())
        Logouter.blue('信息爬取完成!')

        Logouter.blue('开始下载...')
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.saver.start_download_task())
        Logouter.blue('下载完成!')

        DataManager.savejson()

        Logouter.blue('开始压缩...')
        self.saver.zip_chapters()
        Logouter.blue('压缩完成')

    async def parse_chapters(self, chapter, context):
        async with self.semaphore_crawl:
            # 爬取每个章节图片
            categories_str = valid_filename(f'{chapter["categories"]}')
            chapter_str = valid_filename(f'{chapter["title"]}')

            chapter_dir = os.path.join(DataManager.get_maindir(), categories_str, chapter_str)
            test_zip_file = f'{chapter_dir}.zip'
            if os.path.exists(test_zip_file):
                chapter['status'] = 1

            #{'categories': '單話', 'title': '第13話(19p)', 'url': 'https://tw.manhuagui.com/comic/36962/550128.html', 'status': 0}
            if chapter['status'] == 0:

                await self.fetch_page(chapter['url'], context, self.parser.parse_chapter_page, param={'url': chapter['url'], 'categories': categories_str, 'chapter': chapter_str})
                chapter['status'] = 1

                Logouter.chapter_successed += 1
                Logouter.crawlog()
            else:
                Logouter.chapter_successed += 1
                Logouter.crawlog()

            DataManager.savejson()

    async def start_crawl_task(self):

        # DataManager.init_comic()

        async with async_playwright() as p:
            browser = await p.chromium.launch_persistent_context(user_data_dir=CHROMIUM_USER_DATA_DIR, headless=self.config.headless, accept_downloads=True, args=['--disable-blink-features=AutomationControlled'])

            # 首页爬取章节
            try:
                if self.config.checklogin:
                    await self.fetch_page(self.config.start_url, browser, self.parser.login, param={'url': self.config.start_url})

                await self.fetch_page(self.config.start_url, browser, self.parser.parse_main_page, param={'url': self.config.start_url})

                # 日志
                Logouter.comic_name = DataManager.get_comicdir()

                Logouter.chapter_total = DataManager.get_chapters_count()
                Logouter.pic_total = DataManager.get_pices_count()
                Logouter.pic_crawed = DataManager.get_pices_crawed()
                Logouter.crawlog()

                if not os.path.exists(DataManager.get_maindir()):
                    os.makedirs(DataManager.get_maindir())

                DataManager.savejson()

                async_tasks = []

                for _, chapter in DataManager.comic['chapters'].items():
                    async_task = asyncio.create_task(self.parse_chapters(chapter, browser))
                    async_tasks.append(async_task)

                await asyncio.gather(*async_tasks)

            finally:
                DataManager.savejson()
                await browser.close()

    # 爬取主页
    async def fetch_page(self, url, context: BrowserContext, parse_method, retry=0, param=None):
        page = await context.new_page()

        try:
            await page.goto(url, wait_until='domcontentloaded', timeout=100000)
            await parse_method(page, param)

        except (Error, AttributeError) as e:

            nretry = retry
            nretry += 1
            if nretry <= 5:
                Logouter.yellow(f'页面{url}打开错误,重试={nretry}')
                await asyncio.sleep(5)
                await self.fetch_page(url, context=context, parse_method=parse_method, retry=nretry, param=param)
            else:
                Logouter.red(e.message)
                Logouter.red(f'页面{url}打开错误,重试超过最大次数')

        finally:
            await page.close()

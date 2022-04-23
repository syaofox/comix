import asyncio
import urllib

from pyquery import PyQuery as pq
from mods.classes import Logtype
from mods.datamgr import DataManager
from mods.logouter import Logouter
from mods.utils import extrat_extname, md5
from parser.parser import Parser
from playwright.async_api import Page
import lzstring


class KlmangaParser(Parser):

    def __init__(self) -> None:
        super().__init__()

    @property
    def name(self):
        return 'klmanga'

    async def parse_main_page(self, page: Page, param=None):
        if await page.query_selector('#checkAdult'):
            await page.click('#checkAdult')

        await page.wait_for_selector('div.book-title')

        html = await page.content()
        doc = pq(html)

        # 基础信息

        name = doc('div.book-title>h1').text()
        author = doc('div.book-detail.pr.fr > ul> li:nth-child(2)>span:nth-child(2)> a').text()
        intro = doc('#intro-cut').text()
        cover_url = urllib.parse.urljoin(page.url, doc('p.hcover > img').attr('src'))

        DataManager.comic['comic'] = name if DataManager.comic['comic'] == '' else DataManager.comic['comic']
        DataManager.comic['author'] = author if DataManager.comic['author'] == '' else DataManager.comic['author']

        DataManager.comic['url'] = page.url
        DataManager.comic['intro'] = intro
        DataManager.comic['cover_url'] = {'url': cover_url, 'referer': '', 'fname': f'cover.{extrat_extname(cover_url)}', 'status': 0, 'categories': '', 'chapter': '', 'maintitle': ''}

        # 章节
        if await page.query_selector('#__VIEWSTATE'):
            lzstrings = doc('#__VIEWSTATE').attr('value')
            deslzstring = lzstring.LZString().decompressFromBase64(lzstrings)
            doc = pq(deslzstring)
            chapter_divs = doc('div.chapter-list')
            heads = [el.text() for el in doc('h4').items()]
        else:
            await page.wait_for_selector('div.chapter>div.chapter-list')
            chapter_divs = doc('div.chapter>div.chapter-list')
            heads = [el.text() for el in doc('body > div.w998.bc.cf> div.fl.w728 > div.chapter.cf.mt16 > h4').items()]

        for i, chapter_div in enumerate(chapter_divs.items()):
            els = chapter_div('li>a')
            categories = heads[i]

            for el in els.items():
                url = urllib.parse.urljoin(page.url, el.attr('href'))
                keystr = md5(url)
                chapterdata = DataManager.comic['chapters'].get(keystr, None)
                if not chapterdata:
                    title = f"{el.attr('title')}({el('span>i').text()})"
                    DataManager.comic['chapters'][keystr] = {'categories': categories, 'title': title, 'url': url, 'status': 0}
                    # 回传获得的章节数
                    # await callback(Logtype.chapter_total)

    async def parse_chapter_page(self, page: Page, param=None):
        if await page.query_selector('#checkAdult'):
            await page.click('#checkAdult')

        await page.wait_for_timeout(2000)

        await page.query_selector("#mangaFile")

        # javascript版

        page_count = await page.evaluate('cInfo.len')

        # 回传章节图片总数

        chapterkey = md5(page.url)
        DataManager.comic['chapters'][chapterkey]['pices'] = page_count

        Logouter.pic_total += page_count
        Logouter.crawlog()

        for i in range(0, page_count + 1):

            if i > 0:
                await page.evaluate('(x) => SMH.utils.goPage(x)', i)

            url = await page.evaluate('pVars.curFile')
            # print(url)
            file_name = f'{str(i).zfill(4)}.{extrat_extname(url)}'
            keystr = md5(url)

            pic = {'url': url, 'referer': 'https://www.manhuagui.com/', 'fname': file_name, 'status': 0, 'categories': param['categories'], 'chapter': param['chapter']}
            if not DataManager.comic['pices'].get(keystr):
                DataManager.comic['pices'][keystr] = pic

                # 回传已获得图片
                # callback(Logtype.pic_crawed)
                Logouter.pic_crawed += 1
                Logouter.crawlog()

            await asyncio.sleep(0.3)

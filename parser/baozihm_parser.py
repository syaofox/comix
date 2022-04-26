import urllib

from pyquery import PyQuery as pq
from mods.datamgr import DataManager
from mods.logouter import Logouter
from mods.utils import extrat_extname, md5
from parser.parser import Parser
from playwright.async_api import Page


class BaozimhParser(Parser):

    def __init__(self) -> None:
        super().__init__()

    @property
    def name(self):
        return 'baozimh'

    async def parse_main_page(self, page: Page, param=None):

        html = await page.content()
        doc = pq(html)

        # 基础信息

        name = doc('h1.comics-detail__title').text()
        if name is None:
            raise Exception('获取漫画名字失败')

        author = doc('h2.comics-detail__author').text()
        intro = doc('p.comics-detail__desc').text()

        cover_url = doc(f'img[alt="{name}"]').attr('src')

        DataManager.comic['comic'] = name if DataManager.comic['comic'] == '' else DataManager.comic['comic']
        DataManager.comic['author'] = author if DataManager.comic['author'] == '' else DataManager.comic['author']

        DataManager.comic['url'] = page.url
        DataManager.comic['intro'] = intro
        DataManager.comic['cover_url'] = {'url': cover_url, 'referer': page.url, 'fname': f'cover.{extrat_extname(cover_url)}', 'status': 0, 'categories': '', 'chapter': '', 'maintitle': ''}

        # 章节

        await page.locator('#button_show_all_chatper').click()

        for cpt in doc('#chapter-items>div>a').items():
            url = urllib.parse.urljoin(page.url, cpt.attr('href'))

            keystr = md5(url)
            title = cpt.text()

            if not DataManager.comic['chapters'].get(keystr, None):
                DataManager.comic['chapters'][keystr] = {'categories': '连载', 'title': title, 'url': url, 'status': 0}

        for cpt in doc('#chapters_other_list>div>a').items():
            url = urllib.parse.urljoin(page.url, cpt.attr('href'))

            keystr = md5(url)
            title = cpt.text()

            if not DataManager.comic['chapters'].get(keystr, None):
                DataManager.comic['chapters'][keystr] = {'categories': '连载', 'title': title, 'url': url, 'status': 0}

    async def parse_chapter_page(self, page: Page, param=None):

        html = await page.content()
        doc = pq(html)

        els = doc('div.chapter-main.scroll-mode > section > amp-img')

        page_count = len(els)

        chapterkey = md5(param['url'])
        DataManager.comic['chapters'][chapterkey]['pices'] = page_count

        Logouter.pic_total += page_count
        Logouter.crawlog()

        for i, el in enumerate(els.items()):
            url = el.attr('src').strip()
            file_name = f'{str(i).zfill(4)}.{extrat_extname(url)}'
            keystr = md5(url)

            pic = {'url': url, 'referer': page.url, 'fname': file_name, 'status': 0, 'categories': param['categories'], 'chapter': param['chapter']}
            if not DataManager.comic['pices'].get(keystr):
                DataManager.comic['pices'][keystr] = pic

                # 回传已获得图片
                # callback(Logtype.pic_crawed)
                Logouter.pic_crawed += 1
                Logouter.crawlog()

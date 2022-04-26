import urllib

from pyquery import PyQuery as pq
from mods.datamgr import DataManager
from mods.logouter import Logouter
from mods.utils import extrat_extname, md5
from parser.parser import Parser
from playwright.async_api import Page
import re


class Comic18Parser(Parser):

    def __init__(self) -> None:
        super().__init__()

    @property
    def name(self):
        return '18comic'

    @staticmethod
    def get_rows(aid, img_url):
        '''
        获取分割数量的函数
        '''
        #220980
        #268850
        pattern = '/([0-9]*)\.jpg'
        l = re.findall(pattern, img_url)[0]
        num = 0
        if aid < 220980:
            num = 0
        elif aid < 268850:
            num = 10
        else:
            num_str = str(aid) + l
            # num_str = num_str.encode()
            # num_str = hashlib.md5(num_str).hexdigest()
            num_str = md5(num_str)
            num = ord(num_str[-1])
            num %= 10
            num = num * 2 + 2
        return num

    async def login(self, page: Page, param=None):

        await page.wait_for_selector('#Comic_Top_Nav > div.container > div.navbar-header > a > img', timeout=100000)

        text = await page.content()
        doc = pq(text)
        is_login = not doc('span:contains("會員登入/註冊")').length
        if is_login:
            return
        await page.goto("https://18comic.vip/login")
        await page.wait_for_selector("text=個人資料", timeout=100000)
        print('logined')

    async def parse_main_page(self, page: Page, param=None):

        html = await page.content()
        doc = pq(html)

        # 基础信息

        name = doc('div.panel-heading').eq(0).text().strip('\n')
        if name is None:
            raise Exception('获取漫画名字失败')

        author = [a.text() for a in doc('div:contains("作者")>span[itemprop="author"]').items()][0]

        intro = doc('div.p-t-5:contains("敘述：")').text()
        cover_url = doc('#album_photo_cover img[itemprop*="image"]').attr('src')

        DataManager.comic['comic'] = name if DataManager.comic['comic'] == '' else DataManager.comic['comic']
        DataManager.comic['author'] = author if DataManager.comic['author'] == '' else DataManager.comic['author']

        DataManager.comic['url'] = page.url
        DataManager.comic['intro'] = intro
        DataManager.comic['cover_url'] = {'url': cover_url, 'referer': page.url, 'fname': f'cover.{extrat_extname(cover_url)}', 'status': 0, 'categories': '', 'chapter': '', 'maintitle': ''}

        # 章节

        categories = '连载'
        chapters = []
        episodes = doc('div.episode').eq(0)
        els = episodes('ul.btn-toolbar>a')
        for el in els.items():

            url = urllib.parse.urljoin(page.url, el.attr('href'))
            title = el('li').text().strip('\n').replace('最新 ', '')
            keystr = md5(url)
            if not DataManager.comic['chapters'].get(keystr, None):
                DataManager.comic['chapters'][keystr] = {'categories': '连载', 'title': title, 'url': url, 'status': 0}

        if len(els) <= 0:
            surl = doc('a.reading').attr('href')
            url = urllib.parse.urljoin(page.url, surl.strip('\n'))
            title = '全一卷'
            keystr = md5(url)
            if not DataManager.comic['chapters'].get(keystr, None):
                DataManager.comic['chapters'][keystr] = {'categories': '连载', 'title': title, 'url': url, 'status': 0}

        # for cpt in doc('ul.btn-toolbar>a').items():

        #     url = urllib.parse.urljoin(page.url, cpt.attr('href'))

        #     keystr = md5(url)

        #     title = cpt('li').text().strip('\n')
        #     DataManager.comic['chapters'][keystr] = {'categories': '连载', 'title': title, 'url': url, 'status': 0}

    async def parse_chapter_page(self, page: Page, param=None):

        await page.wait_for_selector('div.panel-body>div.row.thumb-overlay-albums>div>img')

        html = await page.content()
        doc = pq(html)

        els = doc('div.panel-body>div.row.thumb-overlay-albums>div>img')

        page_count = len(els)

        chapterkey = md5(page.url)
        DataManager.comic['chapters'][chapterkey]['pices'] = page_count

        Logouter.pic_total += page_count
        Logouter.crawlog()

        is_need_fix = False
        ids = re.search(r'<script>.*?var.*?scramble_id.*?=.*?(\d+);.*?var.*?aid.*?=.*?(\d+);', html, re.S)
        aid = 0
        if ids:
            scramble_id = int(ids.group(1))
            aid = int(ids.group(2))
            is_need_fix = (aid >= scramble_id)  # 判断是否需要修复分割打乱的图片

        for i, el in enumerate(els.items()):
            url = el.attr('data-original').strip()

            if 'media/photos' not in url:  # 对非漫画图片连接直接放行
                is_need_fix = False

            file_name = f'{str(i).zfill(4)}.{extrat_extname(url)}'
            keystr = md5(url)

            pic = {'url': url, 'referer': page.url, 'fname': file_name, 'status': 0, 'categories': param['categories'], 'chapter': param['chapter'], 'needfix': is_need_fix, 'fixparm': self.get_rows(aid, url)}

            if not DataManager.comic['pices'].get(keystr):
                DataManager.comic['pices'][keystr] = pic

                # 回传已获得图片
                # callback(Logtype.pic_crawed)
                Logouter.pic_crawed += 1
                Logouter.crawlog()

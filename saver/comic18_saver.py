import asyncio
import os
from mods.datamgr import DataManager
from mods.logouter import Logouter
from mods.picchecker import PicChecker
from mods.settings import CHROMIUM_USER_DATA_DIR
from mods.utils import valid_filename
from saver.saver import Saver
from playwright.async_api import async_playwright, Page
import math

from PIL import Image


class Comic18Saver(Saver):

    def __str__(self) -> str:
        return '18comic'

    @staticmethod
    def fix_jpg20(img_url, num=0):
        """
        该函数对某个文件夹下的图片进行解密并在指定文件夹存储
        """
        if num == 0:
            return img_url
        source_img = Image.open(img_url)
        w, h = source_img.size
        decode_img = Image.new("RGB", (w, h))
        remainder = h % num
        copyW = w
        try:
            for i in range(num):
                copyH = math.floor(h / num)
                py = copyH * i
                y = h - (copyH * (i + 1)) - remainder
                if i == 0:
                    copyH = copyH + remainder
                else:
                    py = py + remainder
                temp_img = source_img.crop((0, y, copyW, y + copyH))
                decode_img.paste(temp_img, (0, py, copyW, py + copyH))
            decode_img.save(img_url)
            return True
        except Exception:
            return False

    def down_done(self, future):
        return super().down_done(future)

    async def down(self, data, browser, retry=0):
        async with self.semaphore_down:
            page: Page = await browser.new_page()
            url = data['url']

            categories_str = valid_filename(f'{data["categories"]}')
            chapter_str = valid_filename(f'{data["chapter"]}')
            chapter_dir = os.path.join(DataManager.get_maindir(), categories_str, chapter_str)

            if not os.path.exists(chapter_dir):
                os.makedirs(chapter_dir)

            zipfile = f'{chapter_dir}.zip'
            if os.path.exists(zipfile):
                return 1

            fname = os.path.join(chapter_dir, data["fname"])

            if os.path.exists(fname):
                if PicChecker.valid_pic(fname):
                    return 1
                else:
                    os.remove(fname)

            try:
                response = await page.goto(url, wait_until='networkidle', timeout=100000)
                status_code = response.status

                if status_code != 200:
                    raise Exception(f'下载失败！状态码={status_code},url={data}')

                imgdata = await response.body()

                with open(fname, 'wb') as fd:
                    fd.write(imgdata)

                if not PicChecker.valid_pic(fname):
                    os.remove(fname)
                    raise Exception(f'下载失败！下载图片不完整={fname}')

                if data['needfix']:
                    Logouter.blue(f'fix {url}')

                    if not self.fix_jpg20(fname, data['fixparm']):
                        return 2

                data['status'] = 1

                return 1

            except Exception as e:
                nretry = retry
                nretry += 1
                if nretry <= 5:
                    Logouter.yellow(f'错误:{e},重试={nretry}')
                    await asyncio.sleep(5)
                    await self.down(data, nretry)

                else:
                    Logouter.red(f'错误:{e},重试超过最大次数，下载失败')
                    return

            finally:

                await page.close()

    async def start_download_task(self):

        async with async_playwright() as p:
            browser = await p.chromium.launch_persistent_context(user_data_dir=CHROMIUM_USER_DATA_DIR, headless=False, accept_downloads=True, args=['--disable-blink-features=AutomationControlled'], chromium_sandbox=False, ignore_https_errors=True)

            async_tasks = []
            pices = DataManager.comic.get('pices', None)
            if pices:

                for _, data in DataManager.comic['pices'].items():

                    async_task = asyncio.create_task(self.down(data, browser))
                    async_task.add_done_callback(self.down_done)
                    async_tasks.append(async_task)

            await asyncio.gather(*async_tasks)

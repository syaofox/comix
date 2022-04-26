import asyncio
import os
import aiohttp
from mods.datamgr import DataManager
from mods.logouter import Logouter
from mods.picchecker import PicChecker
from mods.utils import valid_filename
from mods.zipper import Zipper
'''
"url": "https://i.hamreus.com/ps3/v/15407/szdxj/第16话/v03_c16_005.jpg.webp?e=1651901140&m=s6lwwE0VvAkB2sl7_yKqWA",
"referer": "https://www.manhuagui.com/",
"fname": "0000.webp",
"status": 0,
"categories": "單話",
"chapter": "第16話(18p)",
'''


class Saver:

    def __init__(self, dcount=1, szip=False, fzip=False) -> None:

        self.semaphore_down = asyncio.Semaphore(dcount)
        self.szip = szip
        self.fzip = fzip

    async def down_deleay(self):
        pass

    def down_done(self, future):
        status = future.result()
        match status:
            case 1 : 
                Logouter.pic_downloaded +=1
                Logouter.downloadlog() 
            case 2 : 
                Logouter.pic_failed +=1
                Logouter.downloadlog()


    def count_dir(self, dir):

        return len(os.listdir(dir)) if os.path.exists(dir) else 0

    def get_pices_downloaded(self):

        total = 0
        for _, chapter in DataManager.comic['chapters'].items():
            categories_str = valid_filename(f'{chapter["categories"]}')
            chapter_str = valid_filename(f'{chapter["title"]}')
            chapter_dir = os.path.join(DataManager.get_maindir(), categories_str, chapter_str)
            total += self.count_dir(chapter_dir)

        return total

    def get_chapters_dirs(self):

        dirs = []
        for _, chapter in DataManager.comic['chapters'].items():
            categories_str = valid_filename(f'{chapter["categories"]}')
            chapter_str = valid_filename(f'{chapter["title"]}')
            chapter_dir = os.path.join(DataManager.get_maindir(), categories_str, chapter_str)
            if os.path.exists(chapter_dir):
                dirs.append(chapter_dir)

        return dirs

    


    async def down(self, data, retry=0):

        headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36  (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36'}

        try:
            
            async with self.semaphore_down:
                referer = data.get('referer', None)
                if referer:
                    headers.update({'referer': referer})
                categories_str = valid_filename(f'{data["categories"]}')
                chapter_str = valid_filename(f'{data["chapter"]}')
                chapter_dir = os.path.join(DataManager.get_maindir(), categories_str, chapter_str)
                
                # if data['status'] == 1:
                #     # Logouter.yellow(f'跳过{data}')                    
                #     return -1
                

                zipfile = f'{chapter_dir}.zip'
                fname = os.path.join(chapter_dir, data["fname"])

                if os.path.exists(zipfile):
                    # Logouter.yellow(f'{zipfile}已存在,跳过{fname}')                    
                    return 1

                if not os.path.exists(chapter_dir):
                    os.makedirs(chapter_dir)

                url = data['url']

                if os.path.exists(fname):
                    if PicChecker.valid_pic(fname):
                        # Logouter.yellow(f'{fname}已存在,跳过{fname}')  
                        
                        # Logouter.pic_downloaded +=1
                        # Logouter.downloadlog()
                        return 1
                    else:
                        os.remove(fname)

                async with aiohttp.ClientSession(headers=headers, connector=aiohttp.TCPConnector(verify_ssl=False)) as session:
                    async with session.get(url) as response:
                        status_code = response.status
                        if status_code != 200:
                            raise Exception(f'下载失败！状态码={status_code},url={data}')

                        with open(fname, 'wb') as fd:
                            while True:
                                chunk = await response.content.read(1024)
                                if not chunk:
                                    break
                                fd.write(chunk)

                        if not PicChecker.valid_pic(fname):
                            os.remove(fname)
                            raise Exception(f'下载失败！下载图片不完整={fname}')

                        data['status'] = 1
            
            await self.down_deleay()
            

            return 1

        except Exception as e:
            nretry = retry
            nretry += 1
            if nretry <= 5:
                Logouter.yellow(f'错误:{e} {data},重试={nretry}')
                await asyncio.sleep(5)
                await self.down(data, nretry)

            else:
                Logouter.red(f'错误:{e} {data},重试超过最大次数，下载失败')
                return 2

    async def start_download_task(self):



        async_tasks = []

        async_task = asyncio.create_task(self.down(DataManager.comic['cover_url']))
        async_task.add_done_callback(self.down_done)
        async_tasks.append(async_task)

        pices = DataManager.comic.get('pices',None)
        if pices:
            

            for _, data in DataManager.comic['pices'].items():
                # if data['status'] == 1:
                #     Logouter.pic_downloaded +=1
                #     Logouter.downloadlog()
                    
                #     continue

                async_task = asyncio.create_task(self.down(data))
                async_task.add_done_callback(self.down_done)
                async_tasks.append(async_task)

        await asyncio.gather(*async_tasks)

    def zip_chapters(self):
        if self.szip :
            Logouter.red('跳过压缩')
            return

        if Logouter.pic_failed > 0:

            done = False
            while not done:
                print(f"{Logouter.pic_failed} 张图片未下载，是否压缩?")
                print('输入任意字符表示不压缩')
                if input() != '' :
                    return
                
        dirs = self.get_chapters_dirs()
        dirs = sorted(list(set(dirs)), reverse=False)
        Zipper.zip(dirs)
import fire
import json
import os
from mods.settings import DOWNLOADS_DIR
from mods.spider import Spider
from mods.classes import Config
from parser.klmanga_parser import KlmangaParser
from parser.manhuagui_parser import ManhuaguiParser
from saver.manhuagui_saver import ManhuaguiSaver
from mods.datamgr import DataManager
from saver.saver import Saver


def parse_start_url(url):

    if url.endswith('json'):
        with open(url, 'r', encoding='utf-8') as load_f:
            data = json.load(load_f)

        DataManager.set_comic(data)
        DataManager.mdir = os.path.dirname(os.path.dirname(url))

        DataManager.comicdir = os.path.basename(os.path.dirname(url))

    else:

        DataManager.mdir = DOWNLOADS_DIR
        DataManager.comic['url'] = url

    return DataManager.comic['url']


def start_craw(start_url, headless=False, szip=False, fzip=False, fselect=False):

    start_url = parse_start_url(start_url)

    if ('manhuagui' in start_url) or ('mhgui' in start_url):

        parser = ManhuaguiParser()
        config = Config(start_url, parser.name, ccount=1, headless=headless, fselect=fselect)
        saver = ManhuaguiSaver(dcount=2, szip=szip, fzip=fzip)

    elif ('klmanga' in start_url):

        parser = KlmangaParser()
        config = Config(start_url, parser.name, ccount=5, headless=headless, fselect=fselect)
        saver = Saver(dcount=8, szip=szip, fzip=fzip)

    if parser == None: return
    if saver == None: return

    DataManager.parser_name = parser.name

    spider = Spider(config=config, parser=parser, saver=saver)
    spider.run()


if __name__ == "__main__":
    fire.Fire(start_craw)
import fire
from mods.spider import Spider
from mods.classes import Config
from parser.parser import Parser


def start_craw(start_url, headless=False, szip=False, fzip=False):

    config = Config(start_url)
    parser = Parser()

    spider = Spider(config=config, parser=parser)
    spider.run()


if __name__ == "__main__":
    fire.Fire(start_craw)
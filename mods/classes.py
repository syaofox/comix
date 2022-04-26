from enum import Enum


class Config:

    def __init__(self, start_url, parser_name, ccount=1, headless=False, fselect=False) -> None:
        """_summary_

        Args:
            start_url (string): 起始url
            ccount (int, optional): 爬取线程数. Defaults to 1.
            dcount (int, optional): 下载线程数. Defaults to 1.
            headless (bool, optional): 无头模式. Defaults to False.
            szip (bool, optional): 跳过压缩. Defaults to False.
            fzip (bool, optional): 强制压缩. Defaults to False.
            fselect (bool, optional): 选择章节. Defaults to False.
        """
        self.start_url = start_url
        self.parser_name = parser_name
        self.ccount = ccount

        self.headless = headless
        self.fselect = fselect


class Logtype(Enum):
    chapter_total = 1
    chapter_successed = 2
    chapter_passed = 3
    chapter_failed = 4

    pic_total = 5
    pic_crawed = 6
    pic_passed = 7
    pic_failed = 8
    pic_downloaded = 9
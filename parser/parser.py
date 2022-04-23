from playwright.async_api import Page


class Parser:

    def __init__(self) -> None:
        pass

    @property
    def name(self):
        return 'base'

    async def parse_main_page(self, page: Page, param=None):
        pass

    async def parse_chapter_page(self, page: Page, param=None):
        pass

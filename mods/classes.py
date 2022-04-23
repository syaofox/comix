class Config:

    def __init__(self,
                 start_url,
                 crawl_thread_count=1,
                 down_thread_count=1,
                 headless=False,
                 szip=False,
                 fzip=False,
                 fselect=False) -> None:
        self.start_url = start_url
        self.crawl_thread_count = crawl_thread_count
        self.down_thread_count = down_thread_count
        self.szip = szip
        self.fzip = fzip

        self.headless = headless
        self.fselect = fselect
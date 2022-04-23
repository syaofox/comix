from mods.classes import Config
from mods.logouter import Logouter


class Spider:

    def __init__(self, config, parser) -> None:
        self.config: Config = config
        self.parser = parser

    def run(self):
        # Logouter.red(self.config.start_url)
        Logouter.crawlog()
        Logouter.downloadlog()
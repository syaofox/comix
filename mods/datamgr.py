from mods.utils import valid_filename
import os
import json


class DataManager:
    mdir = ''
    comicdir = ''
    parser_name = 'base'
    comic = {
        "comic": "",
        "url": "",
        "author": "",
        "intro": "",
        "cover_url": {},
        "chapters": {},
        "pices": {},
    }

    @classmethod
    def set_comic(cls, data):
        cls.comic["comic"] = data.get("comic", "")
        cls.comic["url"] = data.get("url", "")
        cls.comic["author"] = data.get("author", "")
        cls.comic["intro"] = data.get("intro", "")

        cls.comic["cover_url"] = data.get("cover_url", {})

        cls.comic['chapters'] = data.get("chapters", {})
        cls.comic['pices'] = data.get("pices", {})

    @classmethod
    def jfname(cls):
        return os.path.join(cls.get_maindir(), f'{cls.parser_name}.json')

    @classmethod
    def savejson(cls):
        with open(cls.jfname(), 'w', encoding='utf-8') as f:
            json.dump(cls.comic, f, indent=4, ensure_ascii=False)

    @classmethod
    def get_maindir(cls):
        comicdir = cls.get_comicdir()
        return os.path.join(cls.mdir, comicdir)

    @classmethod
    def get_comicdir(cls):
        author = DataManager.comic['author']
        comic_title = DataManager.comic['comic']
        if cls.comicdir == '':
            return valid_filename(f'[{author}]{comic_title}' if author else comic_title)
        else:
            return cls.comicdir

    @classmethod
    def get_pices_count(cls):
        """从comic中获得图片总数信息
        """
        total = 0
        for _, chapter in cls.comic['chapters'].items():
            total += chapter.get('pices', 0)
        return total

    @classmethod
    def get_pices_crawed(cls):
        """从comic中获得已经爬取的图片信息
        """
        return len(cls.comic.get('pices', []))

    @classmethod
    def get_chapters_count(cls):
        """从comic中获得章节总数
        """
        return len(cls.comic.get('chapters', []))

    @classmethod
    def get_chapter_crawed(cls):
        """从comic中获得已经爬取的章节信息

        Returns:
            _type_: _description_
        """
        total = 0
        chapters = cls.comic.get('chapters', None)
        if not chapters:
            return 0
        for _, chapter in cls.comic['chapters'].items():
            total += 1 if chapter.get('pices', None) else 0
        return total

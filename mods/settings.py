import os

BASE_PATH = os.path.dirname(os.path.dirname(__file__))
STORAGE_PATH = os.path.join(BASE_PATH, 'storages')
if not os.path.exists(STORAGE_PATH):
    os.makedirs(STORAGE_PATH)

DOWNLOADS_DIR = os.path.join(os.path.expanduser("~"), r'Downloads', r'manga_man')

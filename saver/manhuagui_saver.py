import asyncio
from saver.saver import Saver


class ManhuaguiSaver(Saver):

    def __str__(self) -> str:
        return 'manhuagui'

    async def down_deleay(self):
        await asyncio.sleep(1)
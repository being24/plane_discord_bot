import logging
import pathlib
from datetime import datetime
from zoneinfo import ZoneInfo

import discord
from discord.ext import commands, tasks

logger = logging.getLogger("discord")


class CogTemplate(commands.Cog, name="コグのテンプレート"):
    """
    コグのテンプレート
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

        self.master_path = pathlib.Path(__file__).parents[1]

        self.local_timezone = ZoneInfo("Asia/Tokyo")

        self.timer_task.stop()
        self.timer_task.start()

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        """on_guild_join時に発火する関数"""
        pass

    @tasks.loop(minutes=1.0)
    async def timer_task(self):
        now = datetime.now(self.local_timezone)
        hour_minute = now.strftime("%H:%M")

        if hour_minute == "04:00":
            # do something
            pass

    @timer_task.before_loop
    async def before_printer(self):
        print("template waiting...")
        await self.bot.wait_until_ready()

    @commands.Cog.listener(name="on_message")
    async def watch_dog(self, _):
        """watch dog"""
        if not self.timer_task.is_running():
            logger.warning("timer_task is not running!")
            self.timer_task.start()


async def setup(bot):
    # await bot.add_cog(CogTemplate(bot))
    pass

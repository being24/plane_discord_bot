import logging
import pathlib
import time
from datetime import datetime
from zoneinfo import ZoneInfo

import discord
from discord.ext import commands, tasks

from .utils.common import CommonUtil

logger = logging.getLogger("discord")


class Admin(commands.Cog, name="管理用コマンド群"):
    """
    管理用のコマンドです
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.c = CommonUtil()

        self.master_path = pathlib.Path(__file__).parents[1]

        self.local_timezone = ZoneInfo("Asia/Tokyo")

        self.auto_backup.stop()
        self.auto_backup.start()

    async def cog_check(self, ctx: commands.Context):
        return ctx.guild and await self.bot.is_owner(ctx.author)

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        """on_guild_join時に発火する関数"""
        embed = discord.Embed(
            title="サーバーに参加しました", description=f"テンプレートbot {self.bot.user.display_name}", color=0x2FE48D
        )
        embed.set_author(name=f"{self.bot.user.name}", icon_url=f"{self.bot.user.avatar.replace(format='png').url}")
        try:
            await guild.system_channel.send(embed=embed)
        except discord.Forbidden:
            pass

    @commands.command(aliases=["re"], hidden=True)
    async def reload(self, ctx: commands.Context):
        reloaded_list = []
        for cog in self.master_path.glob("cogs/*.py"):
            try:
                await self.bot.unload_extension(f"cogs.{cog.stem}")
                await self.bot.load_extension(f"cogs.{cog.stem}")
                reloaded_list.append(cog.stem)
            except Exception as error:
                print(error)
                await ctx.reply(str(error), mention_author=False)

        await ctx.reply(f"{' '.join(reloaded_list)}をreloadしました", mention_author=False)

    @commands.command(aliases=["st"], hidden=True)
    async def status(self, ctx: commands.Context, word: str = "plane bot"):
        try:
            await self.bot.change_presence(activity=discord.Game(name=word))
            await ctx.reply(f"ステータスを{word}に変更しました", mention_author=False)

        except discord.Forbidden or discord.HTTPException:
            logger.warning("ステータス変更に失敗しました")

    @commands.command(aliases=["p"], hidden=False, description="疎通確認")
    async def ping(self, ctx: commands.Context):
        """Pingによる疎通確認を行うコマンド"""
        start_time = time.time()
        mes = await ctx.reply("Pinging....")
        await mes.edit(content="pong!\n" + str(round(time.time() - start_time, 3) * 1000) + "ms")

    @commands.command(aliases=["wh"], hidden=True)
    async def where(self, ctx: commands.Context):
        server_list = [i.name.replace("\u3000", " ") for i in ctx.bot.guilds]
        server_list_str = f"現在入っているサーバーは以下の通りです\n{' '.join(server_list)}"

        if len(server_list_str) <= 2000:
            await ctx.reply(server_list_str, mention_author=False)
        else:
            messages = [server_list_str[i : i + 2000] for i in range(0, len(server_list_str), 2000)]
            for message in messages:
                await ctx.reply(message, mention_author=False)

    @commands.command(hidden=True)
    async def back_up(self, ctx: commands.Context):
        data_files = list(self.master_path.glob("data/*.sqlite3"))

        discord_files = [discord.File(file) for file in data_files]

        await ctx.send(files=discord_files)

        log_file = self.master_path / "log" / "discord.log"
        discord_log = discord.File(log_file)

        await ctx.send(files=[discord_log])

    @commands.command(hidden=True)
    async def restore_one(self, ctx: commands.Context):
        if ctx.message.attachments is None:
            await ctx.send("ファイルが添付されていません")

        for attachment in ctx.message.attachments:
            await attachment.save(self.master_path / "data" / attachment.filename)
            await ctx.send(f"{attachment.filename}を追加しました")

    @tasks.loop(minutes=1.0)
    async def auto_backup(self):
        now = datetime.now(self.local_timezone)
        hour_minute = now.strftime("%H:%M")

        if hour_minute == "04:00":
            channel = self.bot.get_channel(745128369170939965)

            data_files = list(self.master_path.glob("data/*.sqlite3"))

            discord_files = [discord.File(file) for file in data_files]
            log_file = self.master_path / "log" / "discord.log"
            discord_log = discord.File(log_file)

            if isinstance(channel, discord.abc.Messageable):
                await channel.send(files=discord_files)
                await channel.send(files=[discord_log])

    @auto_backup.before_loop
    async def before_printer(self):
        print("admin waiting...")
        await self.bot.wait_until_ready()

    @commands.Cog.listener(name="on_message")
    async def watch_dog(self, _):
        """watch dog"""
        if not self.auto_backup.is_running():
            logger.warning("auto_backup is not running!")
            self.auto_backup.start()


async def setup(bot):
    await bot.add_cog(Admin(bot))

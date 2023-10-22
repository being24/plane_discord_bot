import logging
import sys
import traceback

import discord
from discord.ext import commands

from .utils.common import CommonUtil

logger = logging.getLogger("discord")


class CommandErrorHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.c = CommonUtil()

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        """The event triggered when an error is raised while invoking a command.
        ctx   : Context
        error : Exception"""

        if hasattr(ctx.command, "on_error"):  # ローカルのハンドリングがあるコマンドは除く
            return

        if isinstance(error, commands.CommandNotFound):
            return

        elif isinstance(error, commands.DisabledCommand):
            msg = await ctx.reply(f"{ctx.command} has been disabled.")
            await self.c.delete_after(msg)
            return

        elif isinstance(error, commands.CheckFailure):
            await ctx.reply(f"you have no permission to execute {ctx.command}.")
            return

        elif isinstance(error, commands.NoPrivateMessage):
            try:
                return await ctx.reply(f"{ctx.command} can not be used in Private Messages.")
            except discord.HTTPException:
                print("couldn't send direct message")

        elif isinstance(error, commands.BadArgument):
            msg = await ctx.reply("無効な引数です")
            await self.c.delete_after(msg)

        elif isinstance(error, commands.MissingRequiredArgument):
            msg = await ctx.reply("引数が足りません")
            await self.c.delete_after(msg)

        else:
            error = getattr(error, "original", error)
            print("Ignoring exception in command {}:".format(ctx.command), file=sys.stderr)
            traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
            error_content = f"error content: {error}\nmessage_content: {ctx.message.content}\nmessage_author : {ctx.message.author}\n{ctx.message.jump_url}"

            logger.error(error_content, exc_info=True)


async def setup(bot):
    await bot.add_cog(CommandErrorHandler(bot))

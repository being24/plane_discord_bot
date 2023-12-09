import logging
import pathlib
import re
from datetime import datetime
from zoneinfo import ZoneInfo

import discord
from discord.ext import commands, tasks

logger = logging.getLogger("discord")


regex_discord_message_url = (
    "(?!<)https://(ptb.|canary.)?discord(app)?.com/channels/"
    "(?P<guild>[0-9]{17,21})/(?P<channel>[0-9]{17,21})/(?P<message>[0-9]{17,21})(?!>)"
)


class ExpandMessage(commands.Cog, name="メッセージの展開"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

        self.master_path = pathlib.Path(__file__).parents[1]

        self.local_timezone = ZoneInfo("Asia/Tokyo")

        # self.timer_task.stop()
        # self.timer_task.start()

    async def get_message_from_ids(
        self, guild: discord.Guild, channel_id: int, message_id: int
    ) -> discord.Message | None:
        """サーバーID、チャンネルID、メッセージIDからメッセージを取得する関数

        Args:
            guild (discord.Guild): メッセージが送信されたサーバー
            channel_id (int): メッセージが送信されたチャンネル
            message_id (int): メッセージのID

        Returns:
            discord.Message | None: メッセージオブジェクト or None
        """

        # チャンネルIDからチャンネルを取得
        channel = guild.get_channel_or_thread(channel_id)

        # キャッシュにチャンネルが存在しない場合はチャンネルをAPIから取得
        if channel is None:
            channel = await guild.fetch_channel(channel_id)

        # チャンネルが取得できない場合は終了: abc.Messageableはメッセージを送信できるチャンネルの基底クラス
        if not isinstance(channel, discord.abc.Messageable):
            # logを出力
            logger.warning(
                f"Unable to get messageable channel. {guild.id}/{channel_id} @get_message_from_ids"
            )
            return

        try:
            # メッセージを取得
            message = await channel.fetch_message(message_id)
        except discord.NotFound or discord.Forbidden or discord.HTTPException as e:
            # エラーが発生した場合はlogを出力
            logger.warning(
                f"Unable to get message. {guild.id}/{channel_id}/{message_id} error:{e} @get_message_from_ids"
            )
            return

        return message

    async def fetch_messages(self, message: discord.Message) -> list[discord.Message]:
        """メッセージに含まれるメッセージのURLからURLのメッセージを取得する関数

        Args:
            message (discord.Message): メッセージオブジェクト

        Returns:
            list[discord.Message]: メッセージオブジェクトのリスト
        """

        # messageを保存するリストの作成
        messages = []

        # メッセージが送信されたサーバーが取得できない場合は終了
        if not isinstance(message.guild, discord.Guild):
            logger.warning("Unable to get guild. @fetch_messages")
            return messages

        # メッセージのURLを正規表現で抽出
        for matched in re.finditer(regex_discord_message_url, message.content):
            # メッセージのURLに含まれるサーバーIDが一致しない場合は終了
            if message.guild.id != int(matched["guild"]):
                continue

            # それぞれのidをint型で取得
            guild_id = int(matched["guild"])
            channel_id = int(matched["channel"])
            message_id = int(matched["message"])

            # サーバーIDからサーバーを取得
            guild = self.bot.get_guild(guild_id)

            # 対象のメッセージが送信されたサーバーが取得できない場合は終了
            if guild is None:
                # logを出力
                logger.warning(f"Unable to get guild. {guild_id} @fetch_messages")

                # エラーメッセージを送信、5秒後に削除
                msg = await message.channel.send("サーバーが見つかりませんでした。")
                await msg.delete(delay=5)
                continue

            # メッセージを取得
            fetched_message = await self.get_message_from_ids(
                guild, channel_id, message_id
            )

            # メッセージが取得できない場合はこのループを終了
            if fetched_message is None:
                continue

            # メッセージをリストに追加
            messages.append(fetched_message)

        return messages

    def create_embeds(self, messages: list[discord.Message]) -> list[discord.Embed]:
        """メッセージオブジェクトのリストからEmbedオブジェクトのリストを作成する関数

        Args:
            messages (list[discord.Message]): メッセージオブジェクトのリスト

        Returns:
            list[discord.Embed]: Embedオブジェクトのリスト
        """

        # embedを保存するリストの作成
        embeds = []

        # メッセージオブジェクトのリストからメッセージを取り出す
        for message in messages:
            if message.guild is None:
                continue

            # embedを作成
            # descriptionにメッセージの内容を追加
            # timestampにメッセージの送信日時を追加
            embed = discord.Embed(
                description=message.content,
                timestamp=message.created_at,
            )

            # ユーザーのアバターがない場合はデフォルトのアバターを使用
            if message.author.avatar is None:
                avatar_url = "https://cdn.discordapp.com/embed/avatars/0.png"
            else:
                avatar_url = message.author.avatar.replace(format="png").url

            # embedにユーザーを追加
            embed.set_author(
                name=message.author.display_name,
                icon_url=avatar_url,
                url=message.jump_url,
            )

            # サーバーのアイコンがない場合はデフォルトのアイコンを使用
            if message.guild.icon is None:
                guild_icon_url = "https://cdn.discordapp.com/embed/avatars/0.png"
            else:
                guild_icon_url = message.guild.icon.url

            # channel名を設定
            if isinstance(message.channel, discord.DMChannel):
                channel_name = "DM"
            elif isinstance(message.channel, discord.PartialMessageable):
                channel_name = "PartialMessage"
            else:
                channel_name = message.channel.name

            embed.set_footer(text=f"#{channel_name}", icon_url=guild_icon_url)

            # メッセージに画像が含まれている場合はembedに画像を追加
            if message.attachments and message.attachments[0].proxy_url:
                embed.set_image(url=message.attachments[0].proxy_url)

            # embedをリストに追加
            embeds.append(embed)

            # メッセージに画像が複数含まれている場合はembedsに画像を追加
            for attachment in message.attachments[1:]:
                img_embed = discord.Embed()
                img_embed.set_image(url=attachment.proxy_url)
                embeds.append(img_embed)

            # メッセージにembedが埋め込まれている場合はembedsにembedを追加
            if message.embeds:
                embeds.extend(message.embeds)

            # embedsが10個以上の場合は、10個になるまでembedsから要素を削除
            if len(embeds) > 10:
                embeds = embeds[:10]

        return embeds

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        """on_guild_join時に発火する関数"""
        pass

    @commands.Cog.listener(name="on_message")
    async def on_message(self, message: discord.Message):
        """on_message時に発火する関数"""
        # botのメッセージは無視
        if message.author.bot:
            return

        # メッセージに含まれるメッセージのURLからメッセージを取得
        messages = await self.fetch_messages(message)

        # メッセージからEmbedオブジェクトを作成
        embeds = self.create_embeds(messages)

        # メッセージが送信されたチャンネルにメッセージを送信
        for embed in embeds:
            await message.channel.send(
                embed=embed, allowed_mentions=discord.AllowedMentions.none()
            )

    # @tasks.loop(minutes=1.0)
    # async def timer_task(self):
    #     now = datetime.now(self.local_timezone)
    #     hour_minute = now.strftime("%H:%M")

    #     if hour_minute == "04:00":
    #         # do something
    #         pass

    # @timer_task.before_loop
    # async def before_printer(self):
    #     print("expand waiting...")
    #     await self.bot.wait_until_ready()

    # @commands.Cog.listener(name="on_message")
    # async def watch_dog(self, _):
    #     """watch dog"""
    #     if not self.timer_task.is_running():
    #         logger.warning("timer_task is not running!")
    #         self.timer_task.start()


async def setup(bot):
    await bot.add_cog(ExpandMessage(bot))

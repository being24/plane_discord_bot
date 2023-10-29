import logging  # log用
import logging.handlers  # loggingのheader設定用
import pathlib  # Pathを扱うためのライブラリ
import traceback  # エラー表示用
from os import getenv  # 環境変数を扱うための関数

import discord  # discord.py
from discord.ext import commands  # discord.pyのコマンドフレームワーク
from dotenv import load_dotenv  # .envファイルを扱うためのライブラリ


class TokenNotFoundError(Exception):
    pass


class MyBot(commands.Bot):
    def __init__(self, command_prefix):
        # コマンドプレフィックス(コマンドの前につける記号)と、discordAPIから受け取るイベント(intents)を設定
        super().__init__(
            command_prefix=command_prefix,
            intents=intents,
        )

    async def setup_hook(self) -> None:
        # cogsフォルダにある.pyファイルを読み込む(要解説)
        for cog in current_path.glob("cogs/*.py"):
            try:
                # cogファイルを読み込む
                await self.load_extension(f"cogs.{cog.stem}")
            except Exception:
                traceback.print_exc()

    async def on_ready(self):
        # 起動時にターミナルにログイン通知が表示される
        print("-----")
        print("Logged in as")
        if self.user:
            print(self.user.name)
            print(self.user.id)
        print("------")
        # ログファイルに再起動を記録
        logger.warning("rebooted")
        # activity(botの名前の下に出るやつ)を設定
        await bot.change_presence(activity=discord.Game(name="リアクション集計中"))


if __name__ == "__main__":
    # .envファイルを読み込む(要解説)
    dotenv_path = pathlib.Path(__file__).parents[0] / ".env"
    load_dotenv(dotenv_path)

    token = getenv("DISCORD_BOT_TOKEN")

    # ログファイルのパスを設定(要解説)
    logfile_path = pathlib.Path(__file__).parents[0] / "log" / "discord.log"

    # tokenを取得できなかった場合はエラーを出す
    if token is None:
        raise TokenNotFoundError("Token not found error!")

    # ログファイルの設定
    # loggerの取得、loggerの名前をdiscordにすることで名前空間が異なっていてもログを単一ファイルにまとめることができる
    logger = logging.getLogger("discord")

    # ログレベルの設定
    logger.setLevel(logging.WARNING)

    # discord.httpのログレベルを設定
    logging.getLogger("discord.http").setLevel(logging.WARNING)

    # ログの形式を設定
    handler = logging.handlers.RotatingFileHandler(
        filename=logfile_path,  # ログファイルのパス
        encoding="utf-8",  # ログファイルのエンコード
        maxBytes=32 * 1024,  # 32KBごとにログファイルをローテーション
        backupCount=5,  # ログファイルのバックアップを5つにする
    )
    # ログの時刻のフォーマット
    dt_fmt = "%Y-%m-%d %H:%M:%S"
    # ログのフォーマットを設定
    formatter = logging.Formatter("[{asctime}] [{levelname:<8}] {name}: {message}", dt_fmt, style="{")
    # ログのフォーマットを適用
    logger.addHandler(handler)

    # cogファイルにアクセスするため、現在のファイルのパスを取得
    current_path = pathlib.Path(__file__).parents[0]

    # intentsの設定(要解説)
    # インテントの設定をすることで、botがどのようなイベントを受け取るかを設定できる
    # とりあえずdiscordのdefaultの設定を使う
    intents = discord.Intents.default()

    # メンバーを受け取ることで、メンバーの情報を取得できるようになる
    intents.members = True
    # typingイベントを受け取らないようにする
    intents.typing = False
    # integrationsイベントを受け取るようにする
    intents.integrations = True
    # メッセージの内容を受け取るようにする
    intents.message_content = True

    # botのインスタンスを作成
    # コマンドプレフィックスを"/"に設定
    # コマンドプレフィックスから始まるメッセージと、botへのメンションをコマンドとして認識する
    bot = MyBot(command_prefix=commands.when_mentioned_or("/"))

    # botを起動
    # token、ログハンドラー、ログフォーマッター、ログレベルを設定
    bot.run(token, log_handler=handler, log_formatter=formatter, log_level=logging.WARNING)

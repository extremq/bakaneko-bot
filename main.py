import discord
from discord import app_commands
from dotenv import load_dotenv
import os
import sqlite3
import logging
import logging.handlers


import commands.dice
import commands.translate
import commands.uranai
import commands.hanashi

logger = logging.getLogger("discord")
logger.setLevel(logging.INFO)
logging.getLogger("discord.http").setLevel(logging.INFO)

handler = logging.handlers.RotatingFileHandler(
    filename="discord.log",
    encoding="utf-8",
    maxBytes=32 * 1024 * 1024,  # 32 MiB
    backupCount=5,  # Rotate through 5 files
)
dt_fmt = "%Y-%m-%d %H:%M:%S"
formatter = logging.Formatter(
    "[{asctime}] [{levelname:<8}] {name}: {message}", dt_fmt, style="{"
)
handler.setFormatter(formatter)
logger.addHandler(handler)

load_dotenv()


class BakaNekoBot(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)
        self.db_path = "./baka.db"
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        self._initialize_db()

    def _initialize_db(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_data (
                user_id INTEGER,
                date TEXT,  -- Store as TEXT in 'YYYY-MM-DD' format (UTC or JST, but only date part)
                choice INTEGER,
                PRIMARY KEY (user_id, date)  -- Composite primary key to allow one entry per user per day
            )
        """)
        self.conn.commit()

    async def setup_hook(self):
        await self.tree.sync()

    async def on_ready(self):
        logger.info(f"Logged in as {self.user}")

    def get_db_connection(self):
        return self.conn

    def get_db_cursor(self):
        return self.cursor


bot = BakaNekoBot()


async def help_command(interaction: discord.Interaction):
    help_message = "## **利用可能なコマンド:**\n"
    for cmd, info in COMMANDS.items():
        help_message += f"- /{cmd}: {info['hint']}\n"
    await interaction.response.send_message(help_message)


################# commands

COMMANDS = {
    "uranai": {
        "hint": "Tell your fortune!",
        "function": commands.uranai.uranai_command,
    },
    "うらない": {
        "hint": "おみくじを引きます！",
        "function": commands.uranai.uranai_command,
    },
    "translate": {
        "hint": "Can translate to Japanese, or to other language using `target_language` (ex: RO, EN, FR).",
        "function": commands.translate.translate_command,
    },
    "ほんやく": {
        "hint": "日本語に翻訳することも、`target_language` を使用して他の言語に翻訳することもできます (例: RO、EN、FR)。",
        "function": commands.translate.translate_command,
    },
    "dice": {
        "hint": "Roll dice in the format xdy (e.g. 1d6 2d20 d10)",
        "function": commands.dice.dice_command,
    },
    "ダイス": {
        "hint": "ダイスを振ります(例: 1d6 2d20 d10)",
        "function": commands.dice.dice_command,
    },
    "uranai_stats": {
        "hint": "Shows your fortune record",
        "function": commands.uranai.uranai_stats_command,
    },
    "うらない記録": {
        "hint": "あなたの運勢記録（最長連続記録、平均運勢、同じ運勢の連続記録など）を表示します。",
        "function": commands.uranai.uranai_stats_command,
    },
    "help": {
        "hint": "利用可能なすべてのコマンドとその説明を表示します。",
        "function": help_command,
    },
    "talk": {
        "hint": "Talk to an LLM.",
        "function": commands.hanashi.talk_command,
    },
    "はなし": {
        "hint": "LLMと話してみる。",
        "function": commands.hanashi.talk_command,
    },
    "clear_history": {
        "hint": "Clear LLM history",
        "function": commands.hanashi.clear_history,
    },
}

for k, v in COMMANDS.items():
    bot.tree.command(name=k, description=v["hint"])(v["function"])

bot.run(token=os.getenv("DISCORD_TOKEN"), log_handler=None)

import discord
from discord import app_commands
from dotenv import load_dotenv
import os
import sqlite3

import commands.dice
import commands.translate
import commands.uranai

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
        print(f"Logged in as {self.user}")

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
        "hint": "Shows your fortune record (longest consecutive record, average fortune, consecutive records of the same fortune, etc.)",
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
}

for k, v in COMMANDS.items():
    bot.tree.command(name=k, description=v["hint"])(v["function"])

bot.run(os.getenv("DISCORD_TOKEN"))

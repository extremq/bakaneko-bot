import discord
from discord import app_commands
from dotenv import load_dotenv
import os

import commands.dice
import commands.translate
import commands.uranai

load_dotenv()


class BakaNekoBot(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()

    async def on_ready(self):
        print(f"Logged in as {self.user}")


bot = BakaNekoBot()


async def help_command(interaction: discord.Interaction):
    help_message = "## **利用可能なコマンド:**\n"
    for cmd, info in COMMANDS.items():
        help_message += f"- /{cmd}: {info['hint']}\n"
    await interaction.response.send_message(help_message)


################# commands

COMMANDS = {
    "uranai": {"hint": "Tell your fortune!", "function": commands.uranai.uranai_command},
    "うらない": {"hint": "おみくじを引きます！", "function": commands.uranai.uranai_command},
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
    "ダイス": {"hint": "ダイスを振ります(例: 1d6 2d20 d10)", "function": commands.dice.dice_command},
    "help": {
        "hint": "利用可能なすべてのコマンドとその説明を表示します。",
        "function": help_command,
    },
}

for k, v in COMMANDS.items():
    bot.tree.command(name=k, description=v["hint"])(v["function"])

bot.run(os.getenv("DISCORD_TOKEN"))

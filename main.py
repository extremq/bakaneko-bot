import discord
from discord import app_commands
import random
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
import os

load_dotenv()

FORTUNES = ["大吉", "吉", "中吉", "小吉", "末吉", "凶", "大凶"]


class UranaiBot(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()

    async def on_ready(self):
        print(f"Logged in as {self.user}")


bot = UranaiBot()


def get_japan_date():
    # JST is UTC+9
    jst = timezone(timedelta(hours=9))
    return datetime.now(jst).date()


def get_daily_fortune(user_id: int) -> str:
    # Use user_id and today's date in Japan as seed
    seed = f"{user_id}{get_japan_date()}"
    random.seed(seed)
    return random.choice(FORTUNES)


async def uranai_command(interaction: discord.Interaction):
    fortune = get_daily_fortune(interaction.user.id)
    await interaction.response.send_message(fortune)


bot.tree.command(name="uranai", description="Tell your fortune!")(uranai_command)
bot.tree.command(name="うらない", description="おみくじを引きます！")(uranai_command)

bot.run(os.getenv("DISCORD_TOKEN"))

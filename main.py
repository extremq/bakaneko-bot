import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import sys
import logging
import logging.handlers


import cogs.dice
import cogs.translate
import cogs.uranai
import cogs.talk
import cogs.voice

# ------------------------
# Logging setup
# ------------------------
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

stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setFormatter(formatter)
logger.addHandler(stdout_handler)

# ------------------------
# .env 
# ------------------------
load_dotenv()


# ------------------------
# Client class
# ------------------------
class BakaNekoBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.add_cog(cogs.voice.VoiceCog(self))
        await self.add_cog(cogs.dice.DiceCog(self))
        await self.add_cog(cogs.translate.TranslateCog(self))
        await self.add_cog(cogs.uranai.UranaiCog(self))
        await self.add_cog(cogs.talk.TalkCog(self))

        await self.tree.sync()

    async def on_ready(self):
        logger.info(f"Logged in as {self.user}")



bot = BakaNekoBot()
bot.run(token=os.getenv("DISCORD_TOKEN"), log_handler=None)

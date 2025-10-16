import random
from datetime import datetime, timezone, timedelta
import discord

FORTUNES = ["大吉 :heart_eyes_cat:", "吉 :smiley:", "中吉 :+1:", "小吉 :pensive:", "末吉 :thinking:", "凶 :worried:", "大凶 :skull:"]

def get_japan_date():
    jst = timezone(timedelta(hours=9))
    return datetime.now(jst).date()


def get_daily_fortune(user_id: int) -> str:
    seed = f"{user_id}{get_japan_date()}"
    random.seed(seed)
    return random.choice(FORTUNES)


async def uranai_command(interaction: discord.Interaction):
    fortune = get_daily_fortune(interaction.user.id)
    await interaction.response.send_message(fortune)
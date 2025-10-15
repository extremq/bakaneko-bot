import discord
from discord import app_commands
import random
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
import requests
import os
import re

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


async def translate_command(interaction: discord.Interaction, message: str, target_language: str = "JA"):
    api_key = os.getenv("DEEPL_TOKEN")
    if not api_key:
        await interaction.response.send_message(
            "翻訳サービスが構成されていません。"
        )
        return

    url = "https://api-free.deepl.com/v2/translate"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"DeepL-Auth-Key {api_key}",
    }
    data = {"text": [message], "target_lang": target_language}

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        data = response.json()
        translated = data["translations"][0]["text"]
        detected_language = data["translations"][0]["detected_source_language"]
        await interaction.response.send_message(f"{detected_language} -> {target_language}:\n{translated}")
    except Exception as e:
        await interaction.response.send_message("翻訳に失敗しました.")
        print(e)

async def dice_command(interaction: discord.Interaction, dice_list: str):
    dice_pattern = re.compile(r'(\d*)d(\d+)')
    matches = dice_pattern.findall(dice_list.lower())

    if not matches:
        await interaction.response.send_message("無効なダイス形式です。`1d6`, `2d20`, `d10` のような形式で入力してください。")
        return
    
    if len(matches) > 10:
        await interaction.response.send_message("一度に振れるダイスの種類は10個までです。")
        return

    message = "サイコロを振ってみましょう！\n"

    total_sum = 0
    for num, faces in matches:
        num = int(num) if num else 1
        faces = int(faces)

        if num > 10:
            await interaction.response.send_message(f"`{num}d{faces}`: 1回のコマンドで10回以上振ることはできません。\n")
            return 

        rolls = [random.randint(1, faces) for _ in range(num)]
        total_sum += sum(rolls)
        message += f"- `{num}d{faces}`: `{rolls}` (合計: {sum(rolls)})\n"

    message += f"**全体の合計: {total_sum}**\n"
    await interaction.response.send_message(message)

bot.tree.command(name="uranai", description="Tell your fortune!")(uranai_command)
bot.tree.command(name="うらない", description="おみくじを引きます！")(uranai_command)
bot.tree.command(name="translate", description="Can translate to Japanese, or to other language using `target_language` (ex: RO, EN, FR).")(translate_command)
bot.tree.command(name="ほんやく", description="日本語に翻訳することも、`target_language` を使用して他の言語に翻訳することもできます (例: RO、EN、FR)。")(translate_command)
bot.tree.command(name="dice", description="Roll dice in the format xdy (e.g. 1d6 2d20 d10)")(dice_command)
bot.tree.command(name="ダイス", description="ダイスを振ります(例: 1d6 2d20 d10)")(dice_command)

bot.run(os.getenv("DISCORD_TOKEN"))

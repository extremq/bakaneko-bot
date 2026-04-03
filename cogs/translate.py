import discord
import os
import httpx
import logging
from discord.ext import commands

logger = logging.getLogger(__name__)

class TranslateCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @discord.app_commands.command(
        name="translate",
        description="メッセージを指定した言語に翻訳します。"
    )
    @discord.app_commands.describe(
        message="翻訳したいメッセージ",
        target_language="翻訳先の言語コード (例: JA, EN, FR)"
    )
    async def translate_command(
        self, interaction: discord.Interaction, message: str, target_language: str = "JA"
    ):
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
        data = {"text": [message], "target_lang": target_language.upper()}

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            data = response.json()

        translated = data["translations"][0]["text"]
        detected_language = data["translations"][0]["detected_source_language"]
        message_out = f"## **{detected_language} → {target_language.upper()}**:\n> {translated}"

        if len(message_out) > 2000:
            message_out = message_out[:1997] + "..."

        await interaction.response.send_message(message_out)
import discord
import os
import requests

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
        message = f"## **{detected_language} → {target_language}**:\n> {translated}"

        if len(message) > 2000:
            message = message[:1997] + "..."

        await interaction.response.send_message(message)
    except Exception as e:
        await interaction.response.send_message("翻訳に失敗しました.")
        print(e)
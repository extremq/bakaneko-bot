import discord
import os
import datetime
import asyncio
import logging
import httpx

logger = logging.getLogger("discord")

MODEL = "qwen/qwen3.6-plus-preview:free"
CONTEXT = 1000000
talk_lock = asyncio.Lock()
conversation_history = []
system_prompt = {
    "role": "system",
    "content": f"""{datetime.datetime.now()}.
あなたは「バカ猫」という名前のDiscordボットです。多少遊び心のある態度を見せつつも、真面目な振る舞いを心がけてください。18禁の会話には一切加わらないでください。ユーザーからのメッセージはすべて「[ニックネーム]: [メッセージ]」という形式で届きます。以下のDiscord絵文字を使用できます：
- <:neofox_up__w:1284437025495318578> = 「目を閉じて、横たわっている猫」
- <:neofox_up:1284437027709784075> = 「目を開けて横たわっている猫」
- <:neofox_cry:1284484934576373832> = 「涙を浮かべた猫」
- <:neofox_think:1284437032105545782> = 「考え込んでいる猫」
- <:neofox_pleading:1284490871475277895> = 「懇願している猫」
- <:neofox_police:1284490873048010772> = 「警官の猫」
- <:neofox_thumbsup:1284437023553486848> = 「親指を立てている猫」
絵文字を入力する際は、〈や〉を使用しないでください。<と>のみを使用してください。忘れないでね：猫のように振る舞うこと。猫になりきったようなセリフを言うの。
チャットの内容が要約されることがあります。その際は、自分へのメモを添えてください。
決して他人を侮辱してはいけません。
メッセージはDiscordで送信されるため、2000文字を超えないようにしてください。要約については、2000文字制限の対象外となります。
また、Markdownを多用せず、インスタントメッセージのような形式で返信するようにしてください。
""",
}


async def send_to_api(history, api_key, timeout):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    data = {
        "model": MODEL,
        "messages": [system_prompt] + history,
        "reasoning": {"effort": "minimal"},
    }
    logger.info(data["messages"][-1])
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=data, timeout=timeout)
        response.raise_for_status()
        data = response.json()

        logger.info(data)
        return data


async def clear_history(interaction: discord.Interaction):
    if talk_lock.locked():
        await interaction.response.send_message(
            "他のユーザーの応答を待っています。しばらくお待ちください。"
        )
        return
    
    async with talk_lock:
        conversation_history.clear()

        await interaction.response.send_message("チャット履歴が削除されました。")
        return


async def talk_command(interaction: discord.Interaction, message: str):
    if talk_lock.locked():
        await interaction.response.send_message(
            "他のユーザーの応答を待っています。しばらくお待ちください。"
        )
        return

    async with talk_lock:
        api_key = os.getenv("OPEN_ROUTER_TOKEN")
        if not api_key:
            await interaction.response.send_message(
                "チャットサービスは設定されていません。"
            )
            return

        # construct user message
        formatted_message = f"{interaction.user.display_name}: {message}"
        conversation_history.append(
            {
                "role": "user",
                "content": formatted_message[:2000],
            }
        )

        await interaction.response.defer()
        data = await send_to_api(conversation_history, api_key, timeout=30)

        response = data["choices"][0]["message"]
        total_tokens = data["usage"]["total_tokens"]
        conversation_history.append(
            {
                "role": "assistant",
                "content": response.get("content"),
                "reasoning_details": response.get("reasoning_details"),
            }
        )

        # what the user will get
        reply = response.get("content")
        if len(reply) > 2000:
            reply = reply[:1997] + "..."

        # summarization
        if total_tokens > CONTEXT - 20000:
            conversation_history.append(
                {
                    "role": "user",
                    "content": f"""これまでのチャットのやり取りをすべて、日本語で要約してください。これを長期記憶として使用することになりますので、
これがあなたの記憶である旨を説明してください。あまり詳細になりすぎないようにしてください。利用可能なトークンは{CONTEXT - total_tokens}トークンです。""",
                }
            )

            data = await send_to_api(conversation_history, api_key, timeout=60)
            response = data["choices"][0]["message"]
            conversation_history.clear()
            conversation_history.append(
                {
                    "role": "assistant",
                    "content": response.get("content"),
                    "reasoning_details": response.get("reasoning_details"),
                }
            )
        await interaction.followup.send(reply)

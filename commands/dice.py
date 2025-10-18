import re
import discord
import random

async def dice_command(interaction: discord.Interaction, dice_list: str):
    dice_pattern = re.compile(r'(\d*)d(\d+)')
    matches = dice_pattern.findall(dice_list.lower())

    if not matches:
        await interaction.response.send_message("無効なダイス形式です。`1d6`, `2d20`, `d10` のような形式で入力してください。")
        return
    
    if len(matches) > 10:
        await interaction.response.send_message("一度に振れるダイスの種類は10個までです。")
        return

    message = "## **サイコロを振ってみましょう！**\n"

    total_sum = 0
    for num, faces in matches:
        num = int(num) if num else 1
        faces = int(faces)

        if num > 10:
            await interaction.response.send_message(f"{num}d{faces}: 1回のコマンドで10回以上振ることはできません。\n")
            return 

        rolls = [random.randint(1, faces) for _ in range(num)]
        total_sum += sum(rolls)
        message += f"- {num}d{faces}: {", ".join(map(str, rolls))} (合計: {sum(rolls)})\n"

    message += f"全体の合計: {total_sum}\n"

    if len(message) > 2000:
        message = message[:1997] + "..."
    await interaction.response.send_message(message)
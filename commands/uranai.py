import random
from datetime import datetime, timezone, timedelta
import discord
from enum import Enum

class Fortune(Enum):
    DAIKICHI = (0, "大吉 :heart_eyes_cat:")
    KICHI = (1, "吉 :smiley:")
    SHOKICHI = (2, "小吉 :+1:")
    HANKICHI = (3, "半吉 :slight_smile:")
    SUEKICHI = (4, "末吉 :thinking:")
    SUESHOKICHI = (5, "末小吉 :worried:")
    KYOU = (6, "凶 :skull:")

    @classmethod
    def get_fortune(cls, index):
        for fortune in cls:
            if fortune.value[0] == index:
                return fortune.value[1]
        raise ValueError("Invalid fortune index")

def get_japan_date():
    jst = timezone(timedelta(hours=9))
    return datetime.now(jst).date()

async def uranai_command(interaction: discord.Interaction):
    db_cursor = interaction.client.get_db_cursor()
    db_conn = interaction.client.get_db_connection()

    # Get current time in JST
    JST = timezone(timedelta(hours=+9))
    now_jst = datetime.now(JST)
    date_jst = now_jst.strftime('%Y-%m-%d')

    # Roll a random fortune (0-6)
    random.seed(f"{interaction.user.id}{date_jst}")
    choice = random.randint(0, 6)
    fortune_text = Fortune.get_fortune(choice)

    # Save to DB
    db_cursor.execute('''
        INSERT OR REPLACE INTO user_data (user_id, date, choice)
        VALUES (?, ?, ?)
    ''', (interaction.user.id, date_jst, choice))
    db_conn.commit()

    # Calculate streak and total days
    db_cursor.execute('''
        SELECT date FROM user_data
        WHERE user_id = ?
        ORDER BY date DESC
    ''', (interaction.user.id,))
    dates = [row[0] for row in db_cursor.fetchall()]

    # Calculate streak
    streak = 0
    if dates:
        streak = 1
        for i in range(1, len(dates)):
            prev_date = datetime.strptime(dates[i-1], '%Y-%m-%d').date()
            curr_date = datetime.strptime(dates[i], '%Y-%m-%d').date()
            if (prev_date - curr_date).days == 1:
                streak += 1
            else:
                break

     # Total days is just the count of all entries for the user
    total_days = len(dates)

    # Send response in Japanese
    response = (
        f"今日のあなたの運勢は… **{fortune_text}** です！\n"
        f"現在の連続記録は **{streak}日** です！\n"
        f"これまでに **{total_days}回** 運勢を確認しています。\n"
        f"明日もお楽しみに！ :sparkles:"
    )

    await interaction.response.send_message(response)

async def uranai_stats_command(interaction: discord.Interaction):
    db_cursor = interaction.client.get_db_cursor()

    # Fetch all user data
    db_cursor.execute('''
        SELECT date, choice FROM user_data
        WHERE user_id = ?
        ORDER BY date ASC
    ''', (interaction.user.id,))
    rows = db_cursor.fetchall()

    if not rows:
        await interaction.response.send_message("まだ運勢を引いた記録がありません。今日から始めてみませんか？")
        return

    dates = [row[0] for row in rows]
    choices = [row[1] for row in rows]

    # Calculate total days
    total_days = len(dates)

    # Calculate longest streak
    longest_streak = 0
    current_streak = 1
    for i in range(1, len(dates)):
        prev_date = datetime.strptime(dates[i-1], '%Y-%m-%d').date()
        curr_date = datetime.strptime(dates[i], '%Y-%m-%d').date()
        if (curr_date - prev_date).days == 1:
            current_streak += 1
            longest_streak = max(longest_streak, current_streak)
        else:
            current_streak = 1
    longest_streak = max(longest_streak, current_streak)  # In case the longest streak is the last one

    # Calculate average luck (mean of choices)
    avg_luck = sum(choices) / len(choices)
    avg_luck_enum = min(6, round(avg_luck))  # Round and clamp to 0-6
    avg_luck_text = Fortune.get_fortune(avg_luck_enum)

    # Calculate longest streak of same-luck fortunes
    longest_same_luck_streak = 0
    current_same_luck_streak = 1
    for i in range(1, len(choices)):
        if choices[i] == choices[i-1]:
            current_same_luck_streak += 1
            longest_same_luck_streak = max(longest_same_luck_streak, current_same_luck_streak)
        else:
            current_same_luck_streak = 1
    longest_same_luck_streak = max(longest_same_luck_streak, current_same_luck_streak)

    # Prepare response
    response = (
        f"あなたの運勢記録をお知らせします！\n"
        f"合計日数: {total_days}日\n"
        f"最長連続記録: {longest_streak}日\n"
        f"平均運勢: {avg_luck_text}\n"
        f"同じ運勢の最長連続記録: {longest_same_luck_streak}日\n"
        f"明日も引き続きお楽しみください！ :heart_eyes_cat:"
    )
    await interaction.response.send_message(response)
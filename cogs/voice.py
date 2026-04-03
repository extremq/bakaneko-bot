import discord
from discord.ext import commands
import httpx
import io
import asyncio
import os
import re
import logging

logger = logging.getLogger("discord")
VOICEVOX_URL = os.getenv("VOICEVOX_URL") or "http://127.0.0.1:50021"

class VoiceCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.guild_channels = {}  # guild_id -> text channel
        self.guild_queues = {}  # guild_id -> asyncio.Queue
        self.guild_tasks = {}  # guild_id -> asyncio.Task
        self.http_client = httpx.AsyncClient()

        # Default voice settings
        self.speaker_id = 2
        self.speed = 1.0
        self.pitch = 0.0
        self.max_kana = 50

    @discord.app_commands.command(
        name="voice_config",
        description="ボイス設定を変更します (SPEAKER_ID, SPEED, PITCH, MAX_KANA)"
    )
    @discord.app_commands.describe(
        speaker_id="話者ID (整数)",
        speed="話す速度 (例: 1.2)",
        pitch="ピッチ (例: 0.0)",
        max_kana="一度に発話する最大かな数"
    )
    async def voice_config(
        self,
        interaction: discord.Interaction,
        speaker_id: int = None,
        speed: float = None,
        pitch: float = None,
        max_kana: int = None
    ):
        # Update only the provided values
        if speaker_id is not None:
            self.speaker_id = speaker_id
        if speed is not None:
            self.speed = speed
        if pitch is not None:
            self.pitch = pitch
        if max_kana is not None:
            self.max_kana = max_kana

        await interaction.response.send_message(
            f"ボイス設定を更新しました:\n"
            f"- SPEAKER_ID: {self.speaker_id}\n"
            f"- SPEED: {self.speed}\n"
            f"- PITCH: {self.pitch}\n"
            f"- MAX_KANA: {self.max_kana}"
        )

    @commands.hybrid_command(name="baka_vc", help="テキスト読み上げ")
    async def bakavc_command(self, ctx: commands.Context):
        guild_id = ctx.guild.id
        msg_channel = ctx.channel
        voice_state = ctx.author.voice

        if not voice_state or not voice_state.channel:
            await ctx.send("You are not in a voice channel", ephemeral=True)
            return

        voice_channel = voice_state.channel
        voice_client = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)

        # If already in the same channel, leave
        if voice_client and voice_client.is_connected() and voice_client.channel == voice_channel:
            await voice_client.disconnect()
            self.guild_channels.pop(guild_id, None)
            task = self.guild_tasks.pop(guild_id, None)
            if task:
                task.cancel()
            self.guild_queues.pop(guild_id, None)
            await ctx.send("Left the voice channel", ephemeral=True)
            return

        # Move or connect
        if voice_client and voice_client.is_connected():
            await voice_client.move_to(voice_channel)
        else:
            await voice_channel.connect()

        # Initialize queue and worker
        if guild_id not in self.guild_queues:
            self.guild_queues[guild_id] = asyncio.Queue()
        if guild_id not in self.guild_tasks:
            self.guild_tasks[guild_id] = asyncio.create_task(
                self.audio_worker(ctx.guild)
            )
        self.guild_channels[guild_id] = msg_channel

        await ctx.send(f"Joined {voice_channel.name}", ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.guild or message.author.bot:
            return

        if self.guild_channels.get(message.guild.id) != message.channel:
            return

        vc = discord.utils.get(self.bot.voice_clients, guild=message.guild)
        if not (vc and vc.is_connected()):
            return

        # Prepare VOICEVOX audio query
        text = self.process_message(message)
        audio_query_resp = await self.http_client.post(
            f"{VOICEVOX_URL}/audio_query",
            params={"speaker": self.speaker_id, "text": text},
        )
        audio_query_resp.raise_for_status()
        data = audio_query_resp.json()

        data["speedScale"] = self.speed
        data["pitchScale"] = self.pitch
        data["outputStereo"] = True
        self.cut_off_kana(data)

        synthesis = await self.http_client.post(
            f"{VOICEVOX_URL}/synthesis",
            params={"speaker": self.speaker_id},
            json=data,
        )
        synthesis.raise_for_status()

        wav_bytes = synthesis.content
        queue = self.guild_queues.get(message.guild.id)
        await queue.put(wav_bytes)

    async def audio_worker(self, guild: discord.Guild):
        queue = self.guild_queues[guild.id]
        logger.info(f"Started audio worker for guild {guild.id}")

        while True:
            wav_bytes = await queue.get()
            vc = discord.utils.get(self.bot.voice_clients, guild=guild)
            if not vc or not vc.is_connected():
                continue

            wav_io = io.BytesIO(wav_bytes)
            source = discord.FFmpegPCMAudio(wav_io, pipe=True)
            done = asyncio.Event()

            def after_playing(error):
                if error:
                    logger.error(f"Playback error: {error}")
                self.bot.loop.call_soon_threadsafe(done.set)

            vc.play(source, after=after_playing)
            await done.wait()

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.bot:
            return

        for vc in self.bot.voice_clients:
            if vc.guild != member.guild:
                continue
            guild_id = vc.guild.id
            if vc.is_connected():
                channel = vc.channel
                if len(channel.members) == 1 and channel.members[0] == self.bot.user:
                    await vc.disconnect()
                    self.guild_channels.pop(guild_id, None)
                    task = self.guild_tasks.pop(guild_id, None)
                    if task:
                        task.cancel()
                    self.guild_queues.pop(guild_id, None)

    def process_message(self, message: discord.Message) -> str:
        text = message.clean_content
        url_pattern = r"https?://[^\s<>\"']+"
        text = re.sub(url_pattern, "リンク", text)
        if message.attachments:
            text += "。ファイル"
        return text

    def cut_off_kana(self, query: dict):
        kana_count = 0
        cut_off_point = len(query["accent_phrases"])
        for idx, obj in enumerate(query["accent_phrases"]):
            kana_count += len(obj["moras"])
            if kana_count > self.max_kana:
                cut_off_point = idx
                break
        query["accent_phrases"] = query["accent_phrases"][:cut_off_point]
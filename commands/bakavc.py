import discord

async def bakavc_command(interaction: discord.Interaction, dice_list: str):
    voice_state = interaction.user.voice
    if not voice_state or not voice_state.channel:
        await interaction.response.send_message("You are not in a voice channel", ephemeral=True)
        return
    
    channel = voice_state.channel

    vc = discord.utils.get(interaction.client.voice_clients, guild=interaction.guild)
    if vc and vc.is_connected():
        await vc.move_to(channel)
    else:
        await channel.connect()

    await interaction.response.send_message(f"Joined {channel.name}", ephemeral=True)
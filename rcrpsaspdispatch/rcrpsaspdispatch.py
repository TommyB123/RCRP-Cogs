import discord
import inspect
from redbot.core import commands
from redbot.core.bot import Red

sasp_guild_id = 1366843374228996187
rcrp_guild_id = 93142223473905664
sasp_unit_channel_category_id = 1381876971449090078
sasp_tac_channel_category_id = 1381877321375416381
logging_channel_id = 1376455862662598746


def voice_channel_sorter(channel: discord.VoiceChannel):
    return channel.name


class RCRPDispatch(commands.Cog, name='SASP Dispatch'):
    def __init__(self, bot: Red):
        self.bot = bot
        self.on_duty: dict[int, str] = {}
        self.unit_channels: dict[str, int] = {}

    @commands.Cog.listener()
    async def on_rcrp_relay_message(self, message: discord.Message, **data):
        if len(data['function']):
            func = getattr(self, data['function'])
            if func is None:
                await self.send_log_message(f"Invalid function passed to rcrpsaspdispatch cog. ({data['function']})")
                return

            if inspect.iscoroutinefunction(func):
                await func(**data)
            else:
                func(**data)

        await message.delete()

    async def send_sasp_radio_message(self, color: int, message: str):
        samp_message = {
            "message_content": message,
            "message_color": color,
            "callback": "DispatchRadioMessage"
        }
        await self.bot.get_cog('RCRP Relay').send_rcrp_relay_message(samp_message)

    async def send_samp_player_message(self, discordid: int, color: int, message: str):
        samp_message = {
            "player_discord_id": str(discordid),
            "message_content": message,
            "message_color": color,
            "callback": "SendPlayerMessageFromDiscord"
        }

        await self.bot.get_cog('RCRP Relay').send_rcrp_relay_message(samp_message)

    async def send_log_message(self, message: str):
        channel = self.bot.get_channel(logging_channel_id)
        await channel.send(message)

    async def channel_boot_cleanup(self, **kwargs):
        unit_category_channel = self.bot.get_channel(sasp_unit_channel_category_id)
        if unit_category_channel is not None:
            for voice_channel in unit_category_channel.voice_channels:
                await voice_channel.delete()

        tac_category_channel = self.bot.get_channel(sasp_tac_channel_category_id)
        if tac_category_channel is not None:
            for voice_channel in tac_category_channel.voice_channels:
                await voice_channel.delete()

    async def cleanup_unit_channels(self, **kwargs):
        unit_category_channel = self.bot.get_channel(sasp_unit_channel_category_id)
        for voice_channel in unit_category_channel.voice_channels:
            if len(voice_channel.members) or voice_channel.name in list(self.on_duty.values()):
                continue
            else:
                await voice_channel.delete()

    async def member_duty_update(self, **kwargs):
        unit_tag: str = kwargs.get('sasp_unit_tag')
        if unit_tag is None:
            return

        unit_member_id = int(kwargs.get('unit_discord_id'))
        if unit_member_id is None:
            return

        sasp_guild = self.bot.get_guild(sasp_guild_id)
        unit_member = sasp_guild.get_member(unit_member_id)
        if unit_member is None:
            return

        state: bool = kwargs.get('duty_state')
        if state is None:
            return

        if state is True:
            self.on_duty[unit_member.id] = unit_tag
            await self.add_unit_channel(unit_tag)
        else:
            if self.on_duty.get(unit_member.id):
                del self.on_duty[unit_member.id]

    async def add_unit_channel(self, unit_tag: str):
        unit_category_channel = self.bot.get_channel(sasp_unit_channel_category_id)
        if unit_tag in [channel.name for channel in unit_category_channel.voice_channels]:
            return

        new_channel = await unit_category_channel.create_voice_channel(unit_tag)
        self.unit_channels[new_channel.name] = new_channel.id

        voice_channels = unit_category_channel.voice_channels
        voice_channels.sort(key=voice_channel_sorter)

        position = 0
        for channel in voice_channels:
            await channel.edit(position=position)
            position += 1

    async def remove_unit_channel(self, **kwargs):
        unit_tag: str = kwargs.get('sasp_unit_tag')
        if unit_tag is None:
            return

        unit_category_channel = self.bot.get_channel(sasp_unit_channel_category_id)
        voice_channel = next((channel for channel in unit_category_channel.voice_channels if channel.name == unit_tag), None)
        if voice_channel is None:
            return

        del self.unit_channels[voice_channel.name]
        await voice_channel.delete()

    async def move_unit_to_unit_channel(self, **kwargs):
        unit_tag: str = kwargs.get('sasp_unit_tag')
        if unit_tag is None:
            return

        unit_member_id = int(kwargs.get('unit_discord_id'))
        if unit_member_id is None:
            return

        sasp_guild = self.bot.get_guild(sasp_guild_id)
        unit_member = sasp_guild.get_member(unit_member_id)
        if unit_member is None:
            return

        if unit_member.voice is None:
            return

        unit_category_channel = self.bot.get_channel(sasp_unit_channel_category_id)
        for voice_channel in unit_category_channel.voice_channels:
            if voice_channel.name == unit_tag:
                await unit_member.move_to(voice_channel)
                break

    async def add_tac_channel(self, **kwargs):
        tac_channel_category = self.bot.get_channel(sasp_tac_channel_category_id)
        tac_channel_number = len(tac_channel_category.voice_channels) + 1
        tac_channel_name = f'TAC-{tac_channel_number}'

        new_channel = await tac_channel_category.create_voice_channel(tac_channel_name)
        await self.send_sasp_radio_message(0x079992FF, f'TAC CHANNEL: TAC-{tac_channel_number}.')

        unit_member_id = int(kwargs.get('unit_discord_id'))
        if unit_member_id is None:
            return

        sasp_guild = self.bot.get_guild(sasp_guild_id)
        unit_member = sasp_guild.get_member(unit_member_id)
        if unit_member is not None and unit_member.voice is not None:
            await unit_member.move_to(new_channel)

        voice_channels = tac_channel_category.voice_channels
        voice_channels.sort(key=voice_channel_sorter)

        position = 0
        for channel in voice_channels:
            await channel.edit(position=position)
            position += 1

    async def remove_tac_channel(self, **kwargs):
        tac_channel_number = int(kwargs.get('tac_channel_number'))
        if tac_channel_number is None:
            return

        unit_discord_id = int(kwargs.get('unit_discord_id'))
        if unit_discord_id is None:
            return

        tac_channel_name = f'TAC-{tac_channel_number}'
        tac_channel_category = self.bot.get_channel(sasp_tac_channel_category_id)
        tac_channel = next((channel for channel in tac_channel_category.voice_channels if channel.name == tac_channel_name), None)
        if tac_channel is None:
            await self.send_samp_player_message(unit_discord_id, 0xA2C8DCFF, f'TAC-{tac_channel_number} is not currently active.')
            return

        for member in tac_channel.members:
            unit_name = self.on_duty.get(member.id)
            if unit_name is None:
                continue

            voice_channel_id = self.unit_channels.get(unit_name)
            if voice_channel_id is None:
                continue

            voice_channel = self.bot.get_channel(voice_channel_id)
            if voice_channel:
                await member.move_to(voice_channel)

        await tac_channel.delete()

        sasp_guild = self.bot.get_guild(sasp_guild_id)
        unit_member = sasp_guild.get_member(unit_discord_id)
        await self.send_sasp_radio_message(0x079992FF, f'{unit_member.nick} has cleared TAC-{tac_channel_number}.')

    async def move_unit_to_tac_channel(self, **kwargs):
        unit_member_id = int(kwargs.get('unit_discord_id'))
        sasp_guild = self.bot.get_guild(sasp_guild_id)
        unit_member = sasp_guild.get_member(unit_member_id)

        if unit_member is None:
            return

        if unit_member.voice is None:
            await self.send_samp_player_message(unit_member_id, 0xA2C8DCFF, 'You need to be connected to a unit channel in order to be moved to a TAC channel.')
            return

        tac_channel_number = int(kwargs.get('tac_channel_number'))
        tac_channel_category = self.bot.get_channel(sasp_tac_channel_category_id)

        channel_found = False
        for voice_channel in tac_channel_category.voice_channels:
            if voice_channel.name == f'TAC-{tac_channel_number}':
                await unit_member.move_to(voice_channel)
                channel_found = True
                break

        if channel_found is False:
            await self.send_samp_player_message(unit_member_id, 0xA2C8DCFF, f'TAC-{tac_channel_number} is not a currently active.')

    async def unit_leave_tac_channel(self, **kwargs):
        unit_member_id = int(kwargs.get('unit_discord_id'))
        if unit_member_id is None:
            return

        saspguild = self.bot.get_guild(sasp_guild_id)
        unit_member = saspguild.get_member(unit_member_id)
        if unit_member is None:
            return

        if unit_member.voice is None:
            return

        channel_name = self.on_duty.get(unit_member_id)
        unit_channel_category = self.bot.get_channel(sasp_unit_channel_category_id)
        for voice_channel in unit_channel_category.voice_channels:
            if voice_channel.name == channel_name:
                await unit_member.move_to(voice_channel)
                return

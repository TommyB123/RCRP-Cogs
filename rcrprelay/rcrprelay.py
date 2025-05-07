import discord
import json
from redbot.core import commands, Config
from redbot.core.bot import Red


class RCRP_Relay(commands.Cog, name="RCRP Relay"):
    def __init__(self, bot: Red):
        self.bot = bot

        default_global = {
            "relay_channel": None,
        }
        self.config = Config.get_conf(self, 87582156741681152)
        self.config.register_global(**default_global)

    async def send_rcrp_relay_message(self, data: dict):
        data['origin'] = 'rudy'
        relay_channel = await self.config.relay_channel()
        channel = self.bot.get_channel(relay_channel)
        if channel:
            await channel.send(json.dumps(data))

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.id == self.bot.user.id:
            return

        relay_channel = await self.config.relay_channel()
        if relay_channel is not None and relay_channel == message.channel.id:
            data = json.loads(message.content)
            if data and data.get('destination') == 'rudy':
                self.bot.dispatch('on_rcrp_relay_message', message, data)

    @commands.command()
    @commands.mod_or_permissions(manage_guild=True)
    async def setrelaychannel(self, ctx: commands.Context, channel: discord.TextChannel):
        if channel is None:
            await ctx.reply('Invalid channel')
            return

        await self.config.relay_channel.set(channel.id)
        await ctx.send(f'RCRP relay messages will now go to and be watched from {channel.mention}')

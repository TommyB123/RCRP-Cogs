import discord
import aiomysql
import json
from redbot.core import commands
from redbot.core.bot import Red

# guild id for the prison guild
prisonguildid = 558036120743706625


async def prison_check(ctx: commands.Context):
    return ctx.guild is not None and ctx.guild.id == prisonguildid


class RCRPPrison(commands.Cog, name="RCRP Prison"):
    def __init__(self, bot: Red):
        self.bot = bot

    async def cog_load(self):
        self.mysqlinfo = await self.bot.get_shared_api_tokens('mysql')

    @commands.group()
    @commands.guild_only()
    @commands.check(prison_check)
    async def prison(self, ctx: commands.Context):
        """Various prison-related commands"""
        pass

    @prison.command()
    @commands.guild_only()
    @commands.check(prison_check)
    async def inmates(self, ctx: commands.Context):
        """Fetches a list of inmates that are currently in-game"""
        async with aiomysql.connect(**self.mysqlinfo) as sql:
            async with sql.cursor() as cursor:
                rows = await cursor.execute("SELECT p.Name, m.Username, value, extra FROM psettings ps LEFT JOIN players p ON ps.entityid = p.id LEFT JOIN masters m ON p.MasterAccount = m.id WHERE `key` = 'CSET_PRISON' AND p.Online = 1")
                if rows == 0:
                    await ctx.send('There are currently no online prisoners.')
                    return

                prisonstring = ''
                data = await cursor.fetchall()
                for prisoner in data:
                    char_name, ma_name, time, extra = prisoner
                    extra_data = json.loads(extra)
                    minutes = "minutes" if time != 1 else "minute"
                    prisonstring += f"{char_name.replace('_', ' ')} ({ma_name}) - Cell {extra_data['PRISON_CELL']} ({time} {minutes} remaining)\n"

                embed = discord.Embed(title=f'Online Prisoners ({rows})', description=prisonstring, color=0xe74c3c)
                embed.timestamp = ctx.message.created_at
                await ctx.send(embed=embed)

    @prison.command()
    @commands.guild_only()
    @commands.check(prison_check)
    async def guards(self, ctx: commands.Context):
        """Fetches a list of guards that are currently in-game"""
        await ctx.send("wip")

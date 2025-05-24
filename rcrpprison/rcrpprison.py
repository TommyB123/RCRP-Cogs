import discord
import aiomysql
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
                rows = await cursor.execute("SELECT players.Name, masters.Username, settingval, extra1 FROM psettings LEFT JOIN players ON psettings.sqlid = players.id LEFT JOIN masters ON players.MasterAccount = masters.id WHERE setting = 6 AND players.Online = 1")
                if rows == 0:
                    await ctx.send('There are currently no online prisoners.')
                    return

                prisonstring = ''
                data = await cursor.fetchall()
                for prisoner in data:
                    minutes = "minutes" if cursor.rowcount != 1 else "minute"
                    prisonstring += f"{prisoner['Name'].replace('_', ' ')} ({prisoner['Username']}) - Cell {prisoner['settingval']} ({prisoner['extra1']} {minutes} remaining)\n"

                embed = discord.Embed(title=f'Online Prisoners ({cursor.rowcount})', description=prisonstring, color=0xe74c3c)
                embed.timestamp = ctx.message.created_at
                await ctx.send(embed=embed)

    @prison.command()
    @commands.guild_only()
    @commands.check(prison_check)
    async def guards(self, ctx: commands.Context):
        """Fetches a list of guards that are currently in-game"""
        await ctx.send("wip")

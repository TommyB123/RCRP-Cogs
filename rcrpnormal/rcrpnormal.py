import discord
import aiomysql
import json
from redbot.core import commands, app_commands
from redbot.core.utils import menus
from redbot.core.bot import Red
from ..rcrprelay.rcrprelay import send_rcrp_relay_message

# rcrp guild ID
rcrpguildid = 93142223473905664

# roles
adminrole = 293441894585729024
managementrole = 310927289317588992
ownerrole = 293303836125298690
staffroles = [ownerrole, adminrole, managementrole]

# lol this is so ghetto
path = __file__
path = path.replace('rcrpnormal.py', '')

# ID of the rcrp guild
rcrpguildid = 93142223473905664


async def rcrp_check(interaction: discord.Interaction):
    return interaction.guild is not None and interaction.guild.id == rcrpguildid


class RCRPCommands(commands.Cog):
    def __init__(self, bot: Red):
        self.bot = bot

    async def cog_load(self):
        self.mysqlinfo = await self.bot.get_shared_api_tokens('mysql')

    @commands.command()
    @commands.guild_only()
    async def players(self, ctx: commands.Context):
        async with aiomysql.connect(**self.mysqlinfo) as sql:
            async with sql.cursor() as cursor:
                rows = await cursor.execute("SELECT Name FROM players WHERE Online = 1 ORDER BY Name ASC")
                if rows == 0:
                    await ctx.send('There are currently no players in-game.')
                    return

                totalcount = 0
                counter = 0
                embeds = []
                string = ""
                async for player in cursor.fetchall():
                    string += f'{player[0]}\n'
                    counter += 1
                    totalcount += 1
                    if counter == 25 or totalcount == cursor.rowcount:
                        embed = discord.Embed(title=f'Online Players - {cursor.rowcount}', description=string, color=0xe74c3c, timestamp=ctx.message.created_at)
                        embed.set_footer(text='Use the !player command to view if a specific player is online.', icon_url=self.bot.user.avatar.url)
                        embeds.append(embed)
                        string = ""
                        counter = 0

                message = await ctx.send(embed=discord.Embed(description='Formatting the player list. Please wait.'))
                menus.start_adding_reactions(message, menus.DEFAULT_CONTROLS)
                await menus.menu(ctx, embeds, menus.DEFAULT_CONTROLS, message)

                # try to delete the message after the timeout in the event that the user didn't close the menu
                try:
                    await message.delete()
                except discord.Forbidden:
                    pass
                except discord.HTTPException:
                    pass

    @app_commands.command(description='View online player count and server IP')
    @app_commands.guild_only()
    async def server(self, interaction: discord.Interaction):
        async with aiomysql.connect(**self.mysqlinfo) as sql:
            async with sql.cursor(aiomysql.DictCursor) as cursor:
                count = await cursor.execute("SELECT NULL FROM players WHERE Online = 1")
                embed = discord.Embed(title="Red County Roleplay")
                embed.set_thumbnail(url=interaction.guild.icon.url)
                embed.add_field(name="Players", value=count, inline=True)
                embed.add_field(name="IP Address", value="server.redcountyrp.com", inline=True)
                embed.set_footer(text="Use the /player command to view if a specific player is online")
                await interaction.response.send_message(embed=embed)

    @app_commands.command(description='View a list of in-game administrators')
    @app_commands.guild_only()
    async def admins(self, interaction: discord.Interaction):
        async with aiomysql.connect(**self.mysqlinfo) as sql:
            async with sql.cursor(aiomysql.DictCursor) as cursor:
                rows = await cursor.execute("SELECT m.Username AS mastername, p.Name AS charactername, (SELECT ps.settingval FROM psettings ps WHERE sqlid = p.id AND ps.setting = 'CSET_AHIDE') AS hidden FROM masters m JOIN players p ON p.MasterAccount = m.id WHERE p.Online = 1 AND m.AdminLevel != 0")
                if rows == 0:
                    await interaction.response.send_message('There are currently no administrators in-game.', ephemeral=True)
                    return

                embed = discord.Embed(title='In-game Administrators', color=0xf21818, timestamp=interaction.created_at)
                visible = 0
                async for admin in cursor.fetchall():
                    if admin['hidden'] != 1:
                        embed.add_field(name=admin['mastername'], value=admin['charactername'])
                        visible += 1

                if visible != 0:
                    await interaction.response.send_message(embed=embed)
                else:
                    await interaction.response.send_message('There are currently no administrators in-game.', ephemeral=True)

    @app_commands.command(description='View a list of in-game helpers')
    @app_commands.guild_only()
    async def helpers(self, interaction: discord.Interaction):
        async with aiomysql.connect(**self.mysqlinfo) as sql:
            async with sql.cursor() as cursor:
                rows = await cursor.execute("SELECT m.Username AS mastername, p.Name AS charactername FROM masters m JOIN players p ON p.MasterAccount = m.id WHERE Helper != 0 AND Online = 1")
                if rows == 0:
                    await interaction.response.send_message('There are currently no helpers in-game.', ephemeral=True)
                    return

                embed = discord.Embed(title='Ingame Helpers', color=0xe74c3c, timestamp=interaction.created_at)
                async for helper in cursor.fetchall():
                    embed.add_field(name=helper['mastername'], value=helper['charactername'])

                await interaction.response.send_message(embed=embed)

    @app_commands.command(description='Queries the SA-MP server to see if a player with the specified name is in-game')
    @app_commands.describe(player='The name of the player you wish to check')
    @app_commands.guild_only()
    async def player(self, interaction: discord.Interaction, *, player: str):
        player = player.replace(' ', '_')
        player = discord.utils.escape_mentions(player)
        async with aiomysql.connect(**self.mysqlinfo) as sql:
            async with sql.cursor() as cursor:
                await cursor.execute("SELECT NULL FROM players WHERE Name = %s AND Online = 1", (player, ))

                if cursor.rowcount == 0:  # player is not in-game
                    await interaction.response.send_message(f'{player} is not currently in-game.', ephemeral=True)
                else:
                    await interaction.response.send_message(f'{player} is currently in-game.', ephemeral=True)

    @app_commands.command(description='Fetches all information related to a vehicle model from the SA-MP server')
    @app_commands.describe(vehicle='The vehicle model name you wish to fetch information of')
    @app_commands.guild_only()
    async def vehicleinfo(self, interaction: discord.Interaction, vehicle: str):
        rcrp_message = {
            "callback": "FetchVehicleInfoForDiscord",
            "vehicle": vehicle,
            "channel": str(interaction.channel.id)
        }

        message = json.dumps(rcrp_message)
        await send_rcrp_relay_message(message)

    download = app_commands.Group(name='download', description='Download various SA-MP-related files')

    @download.command(name='samp', description='SA-MP 0.3.DL installer')
    @app_commands.guild_only()
    @app_commands.check(rcrp_check)
    async def samp(self, interaction: discord.Interaction):
        await interaction.response.send_message("Download the latest `omp-launcher-setup.exe` file from [here.](https://github.com/openmultiplayer/launcher/releases)\nInstall to your game directory and then make sure to select 0.3.DL when joining the server.")

    @download.command(name='codsmp', description='Cods MP mod')
    @app_commands.guild_only()
    @app_commands.check(rcrp_check)
    async def codsmp(self, interaction: discord.Interaction):
        file = discord.File(f'{path}/files/codsmp.zip')
        await interaction.response.send_message(file=file)

    @download.command(name='gta', description='GTA: SA Clean Copy Backup')
    @app_commands.guild_only()
    @app_commands.check(rcrp_check)
    async def gta(self, interaction: discord.Interaction):
        await interaction.response.send_message('https://amii.ir/files/gtasac.7z')

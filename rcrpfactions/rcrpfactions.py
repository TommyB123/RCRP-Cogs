import discord
import aiomysql
from redbot.core import commands, Config
from redbot.core.bot import Red
from typing import TypedDict, Union

# roles
adminrole = 293441894585729024
managementrole = 310927289317588992
ownerrole = 293303836125298690

# guild ID for main RCRP guild
rcrpguildid = 93142223473905664

# all rcrp admin roles
staffroles = [ownerrole, adminrole, managementrole]


def admin_check(ctx: commands.Context):
    if ctx.guild is not None and ctx.guild.id == rcrpguildid:
        for role in ctx.author.roles:
            if role.id in staffroles:
                return True
        return False
    else:
        return True


def rcrp_check(ctx: commands.Context):
    return (ctx.guild is not None and ctx.guild.id == rcrpguildid)


async def management_check(ctx: commands.Context):
    if ctx.guild is not None and ctx.guild.id == rcrpguildid:
        role_ids = [role.id for role in ctx.author.roles]
        if managementrole in role_ids or ownerrole in role_ids:
            return True
        else:
            return False
    else:
        return True


async def strawman_check(ctx: commands.Context):
    config = Config.get_conf(RCRPFactions(commands.Cog), 87582156741681152)
    async with config.suppliers() as suppliers:
        if ctx.message.author.id in suppliers:
            return True

    return False


def member_is_admin(member: discord.Member):
    for role in member.roles:
        if role.id in staffroles:
            return True
    return False


class RCRPWeapon(TypedDict):
    name: str
    weaponid: int
    ammo: int


strawman_weapons: list[RCRPWeapon] = [
    {"name": "Knife", "weaponid": 4, "ammo": 5},
    {"name": "9mm", "weaponid": 22, "ammo": 85},
    {"name": "Silenced Pistol", "weaponid": 23, "ammo": 85},
    {"name": "Desert Eagle", "weaponid": 24, "ammo": 70},
    {"name": "Shotgun", "weaponid": 25, "ammo": 50},
    {"name": "Micro Uzi (Mac 10)", "weaponid": 28, "ammo": 200},
    {"name": "Tec9", "weaponid": 32, "ammo": 200}
]


def resolve_strawman_weapon(search: Union[int, str]) -> Union[RCRPWeapon, None]:
    for weapon in strawman_weapons:
        if isinstance(search, str):
            if weapon['name'].lower().find(search.lower()) != -1:
                return weapon
        elif isinstance(search, int):
            if weapon['weaponid'] == search:
                return weapon
        else:
            pass

    return None


class RCRPFactions(commands.Cog, name="Faction Commands"):
    def __init__(self, bot: Red):
        default_guild = {
            "factionid": None
        }

        default_global = {
            "suppliers": []
        }

        self.bot = bot
        self.config = Config.get_conf(self, 87582156741681152)
        self.config.register_guild(**default_guild)
        self.config.register_global(**default_global)

    async def return_faction_name(self, factionid: int):
        mysqlconfig = await self.bot.get_shared_api_tokens('mysql')
        sql = await aiomysql.connect(**mysqlconfig)
        cursor = await sql.cursor()
        await cursor.execute("SELECT FactionName FROM factions WHERE id = %s", (factionid, ))

        if cursor.rowcount == 0:
            await cursor.close()
            sql.close()
            print(f"An invalid faction ID was passed to return_faction_name ({factionid})")
            return "Unknown"

        data = await cursor.fetchone()
        await cursor.close()
        sql.close()
        return data[0]

    async def return_character_id(self, character: str):
        character = character.replace(' ', '_')
        mysqlconfig = await self.bot.get_shared_api_tokens('mysql')
        sql = await aiomysql.connect(**mysqlconfig)
        cursor = await sql.cursor()
        await cursor.execute("SELECT id FROM players WHERE Name = %s", (character, ))
        rows = cursor.rowcount
        data = await cursor.fetchone()
        await cursor.close()
        sql.close()

        if rows == 0:
            return 0

        return data[0]

    async def return_master_id_from_discordid(self, id: int):
        mysqlconfig = await self.bot.get_shared_api_tokens('mysql')
        sql = await aiomysql.connect(**mysqlconfig)
        cursor = await sql.cursor()
        await cursor.execute("SELECT id FROM masters WHERE discordid = %s", (id, ))
        rows = cursor.rowcount
        data = await cursor.fetchone()
        await cursor.close()
        sql.close()

        if rows == 0:
            return 0

        return data[0]

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        if await self.config.guild(guild).factionid() is not None:
            await self.config.guild(guild).factionid.set(None)

    @commands.group()
    @commands.guild_only()
    async def faction(self, ctx: commands.Context):
        """Various faction-related commands"""
        pass

    @faction.command()
    @commands.guild_only()
    @commands.check(rcrp_check)
    @commands.check(admin_check)
    async def factions(self, ctx: commands.Context):
        """Lists all of the current factions on the server"""
        mysqlconfig = await self.bot.get_shared_api_tokens('mysql')
        sql = await aiomysql.connect(**mysqlconfig)
        cursor = await sql.cursor()

        await cursor.execute("SELECT id, FactionName FROM factions ORDER BY id ASC")
        if cursor.rowcount == 0:
            await ctx.send("There are apparently no factions currently.")
            await cursor.close()
            sql.close()
            return

        data = await cursor.fetchall()
        await cursor.close()
        sql.close()

        factionstring = []
        for faction in data:
            factionstring.append(f'{faction[1]} (ID {faction[0]})')
        factionstring = '\n'.join(factionstring)
        embed = discord.Embed(title='RCRP Factions', description=factionstring, color=0xe74c3c, timestamp=ctx.message.created_at)
        await ctx.send(embed=embed)

    @faction.command()
    @commands.guild_only()
    @commands.is_owner()
    async def guilds(self, ctx: commands.Context):
        """Lists guild IDS associated with factions."""
        embed = discord.Embed(title='Linked Factions', color=0xe74c3c, timestamp=ctx.message.created_at)
        guilds = await self.config.all_guilds()
        for guild in guilds:
            factionid = guilds[guild]['factionid']
            factionname = await self.return_faction_name(factionid)
            embed.add_field(name=f'{factionname} ({factionid})', value=guild)
        await ctx.send(embed=embed)

    @faction.command()
    @commands.guild_only()
    @commands.is_owner()
    async def register(self, ctx: commands.Context, factionid: int):
        """Registers a Discord server as a faction Discord with the provided faction ID."""
        if await self.config.guild(ctx.guild).factionid() is not None:
            await ctx.send("This discord server is already linked to a faction.")
            return

        guilds = await self.config.all_guilds()
        for guild in guilds:
            if guilds[guild]['factionid'] == factionid:
                await ctx.send("This faction is already linked to another discord server.")
                return

        mysqlconfig = await self.bot.get_shared_api_tokens('mysql')
        sql = await aiomysql.connect(**mysqlconfig)
        cursor = await sql.cursor()
        await cursor.execute("SELECT NULL FROM factions WHERE id = %s", (factionid, ))

        if cursor.rowcount == 0:
            await cursor.close()
            sql.close()
            await ctx.send('Invalid faction ID.')
            return

        await cursor.close()
        sql.close()

        await self.config.guild(ctx.guild).factionid.set(factionid)
        factionname = await self.return_faction_name(factionid)
        await ctx.send(f'This discord server is now linked to {factionname}!')

    @faction.command()
    @commands.guild_only()
    @commands.is_owner()
    async def unregister(self, ctx: commands.Context):
        """Removes a Discord's faction association."""
        factionid = await self.config.guild(ctx.guild).factionid()
        if factionid is None:
            await ctx.send('This server is not linked to a faction.')
            return

        await self.config.guild(ctx.guild).factionid.set(None)
        factionname = await self.return_faction_name(factionid)
        await ctx.send(f'This server is no longer linked to {factionname}.')

    @faction.command()
    @commands.guild_only()
    async def members(self, ctx: commands.Context):
        """Lists all online members of a faction in verified, faction-specific discords"""
        factionid = await self.config.guild(ctx.guild).factionid()
        if factionid is None:
            await ctx.send('This command can only be used in verified, faction-specific Discord servers.')
            return

        mysqlconfig = await self.bot.get_shared_api_tokens('mysql')
        sql = await aiomysql.connect(**mysqlconfig)
        cursor = await sql.cursor()
        await cursor.execute("SELECT Name, factionranks.rankname, masters.Username FROM players LEFT JOIN factionranks ON players.Faction = factionranks.fid LEFT JOIN masters ON masters.id = players.MasterAccount WHERE Faction = %s AND factionranks.slot = FactionRank AND Online = 1 ORDER BY FactionRank DESC", (factionid, ))

        if cursor.rowcount == 0:
            await cursor.close()
            sql.close()
            await ctx.send('There are currently no members online.')
            return

        members = await cursor.fetchall()
        memberstring = []
        for member in members:
            memberstring.append(f'{member[1]} {member[0]} ({member[2]})')
        memberstring = '\n'.join(memberstring)
        memberstring = memberstring.replace('_', ' ')

        embed = discord.Embed(title=f'Online Members ({cursor.rowcount})', description=memberstring, color=0xe74c3c)
        embed.timestamp = ctx.message.created_at
        await ctx.send(embed=embed)

        await cursor.close()
        sql.close()

    @faction.command()
    @commands.guild_only()
    @commands.cooldown(1, 60)
    @commands.check(rcrp_check)
    async def online(self, ctx: commands.Context):
        """Collects a list of factions and their online member counts"""
        mysqlconfig = await self.bot.get_shared_api_tokens('mysql')
        sql = await aiomysql.connect(**mysqlconfig)
        cursor = await sql.cursor(aiomysql.DictCursor)
        await cursor.execute("SELECT COUNT(players.id) AS members, COUNT(IF(Online = 1, 1, NULL)) AS onlinemembers, factions.FNameShort AS name FROM players JOIN factions ON players.Faction = factions.id WHERE Faction != 0 GROUP BY Faction ORDER BY Faction ASC")
        factiondata = await cursor.fetchall()
        await cursor.close()
        sql.close()

        embed = discord.Embed(title="Faction List", color=0xe74c3c, timestamp=ctx.message.created_at)
        for factioninfo in factiondata:
            embed.add_field(name=factioninfo['name'], value=f"{factioninfo['onlinemembers']}/{factioninfo['members']}", inline=True)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.guild_only()
    @commands.check(rcrp_check)
    @commands.check(management_check)
    async def makesupplier(self, ctx: commands.Context, member: discord.Member):
        """Assign strawman supplier permission to a Discord account"""
        if member_is_admin(member) is False:
            await ctx.send("You can't assign strawman supplier to non-staff.")
            return

        async with self.config.suppliers() as suppliers:
            if member.id in suppliers:
                suppliers.remove(member.id)
                await ctx.send(f'You have removed {member.mention} from strawman suppliers.')
            else:
                suppliers.append(member.id)
                await ctx.send(f'You have made {member.mention} a strawman supplier.')

    @commands.command()
    @commands.guild_only()
    @commands.check(rcrp_check)
    @commands.check(admin_check)
    @commands.check(strawman_check)
    async def strawman(self, ctx: commands.Context, character_name: str, *, guns: str):
        character_id = await self.return_character_id(character_name)
        if character_id == 0:
            await ctx.send(f'{character_name} is not a valid character.')
            return

        admin_master_id = await self.return_master_id_from_discordid(ctx.author.id)
        if admin_master_id == 0:
            # unlikely to happen since you need to have an admin role on the discord, but y'know
            return

        mysqlconfig = await self.bot.get_shared_api_tokens('mysql')
        sql = await aiomysql.connect(**mysqlconfig)
        cursor = await sql.cursor()

        final_weapons = ""
        for gun in guns.split(' '):
            weapon = resolve_strawman_weapon(gun)
            if weapon is None:
                await ctx.send(f"An invalid weapon was supplied ({gun}). This weapon will not be processed, but any other valid weapon included will be.")
                continue

            final_weapons += f"{weapon['name']}, "
            await cursor.execute('INSERT INTO refunds_gtac (refund_player_id, refund_admin_id, refund_type, refund_itemtype, refund_subtype, refund_infratype, refund_amount, refund_reason) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)',
                                 (character_id, admin_master_id, 1, weapon['weaponid'], 8, 0, weapon['ammo'], f'Strawman weapon provided by {ctx.author.display_name}'))

        final_weapons = final_weapons.rstrip(', ')
        await ctx.send(f'You have issued the following strawman weapons to {character_name}: {final_weapons}')
        await cursor.close()
        sql.close()

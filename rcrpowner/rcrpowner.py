import discord
import aiomysql
from redbot.core import commands
from redbot.core.utils.chat_formatting import pagify
from redbot.core.bot import Red

# weapon origins
origins = {
    1: "Admin Refunded Weapons",
    2: "Illegal Weapons",
    3: "Faction Weapons",
    4: "Licensed Weapons",
    7: "Storebought Items",
    8: "Strawman Weapons"
}

# weapon names
weaponnames = {
    0: "Fist",
    1: "Brass Knuckles",
    2: "Golf Club",
    3: "Nightstick",
    4: "Knife",
    5: "Baseball Bat",
    6: "Shovel",
    7: "Pool Cue",
    8: "Katana",
    9: "Chainsaw",
    10: "Purple Dildo",
    11: "Small White Vibrator",
    12: "Big White Vibrator",
    13: "Small Silver Vibrator",
    14: "Flowers",
    15: "Cane",
    16: "Grenade",
    17: "Teargas",
    18: "Molotov Cocktail",
    19: "",
    20: "",
    21: "Heavy Armor",
    22: "9mm",
    23: "Silenced Pistol",
    24: "Desert Eagle",
    25: "Shotgun",
    26: "Sawn-off Shotgun",
    27: "SPAS-12",
    28: "Micro Uzi (Mac 10)",
    29: "MP5",
    30: "AK-47",
    31: "M4",
    32: "Tec9",
    33: "Country Rifle",
    34: "Sniper Rifle",
    35: "Rocket Launcher (RPG)",
    36: "Heat-Seeking Rocket Launcher",
    37: "Flamethrower",
    38: "Minigun",
    39: "Satchel Charges",
    40: "Detonator",
    41: "Spray Can",
    42: "Fire Extinguisher",
    43: "Camera",
    44: "Night Vision Goggles",
    45: "Thermal Goggles",
    46: "Parachute",
    47: "",
    48: "",
    49: "",
    50: "",
    51: "",
    52: "",
    53: "",
    54: "",
    55: "Beanbag Shotgun"
}

drug_names = {
    'INV_COCAINE': 'High Grade Cocaine',
    'INV_CRACK': 'High Grade Crack',
    'INV_WEED': 'Marijuana',
    'INV_HEROIN': 'Heroin'
}


class OwnerCog(commands.Cog):
    """Cog containing owner commands for the RCRP discord"""

    def __init__(self, bot: Red):
        self.bot = bot

    async def cog_load(self):
        self.mysqlinfo = await self.bot.get_shared_api_tokens('mysql')

    @commands.command()
    @commands.guild_only()
    @commands.is_owner()
    async def dms(self, ctx: commands.Context):
        """Gives an imgur album showing why my DMs are not open."""
        await ctx.send("<https://imgur.com/a/yYK5dnZ>")

    @commands.command()
    @commands.guild_only()
    @commands.is_owner()
    async def legit(self, ctx: commands.Context):
        """Proof of riches"""
        await ctx.send('MY CASH IS LEGIT BABY https://i.imgur.com/z5pwmj4.gifv')

    @commands.command()
    @commands.guild_only()
    @commands.is_owner()
    async def economy(self, ctx: commands.Context):
        """Collects statistics about the server's economy"""
        async with ctx.typing():
            async with aiomysql.connect(**self.mysqlinfo) as sql:
                async with sql.cursor() as cursor:
                    await cursor.execute("SELECT SUM(Bank), SUM(Check1), SUM(Check2), SUM(Check3) FROM players")
                    banksum, check1sum, check2sum, check3sum = await cursor.fetchone()

                    await cursor.execute("SELECT SUM(BankBalance) FROM factions WHERE id != 3")
                    factionbank, = await cursor.fetchone()

                    await cursor.execute("SELECT SUM(value) FROM inventory_player WHERE `key` = 'INV_MONEY'")
                    inhandcash, = await cursor.fetchone()

                    await cursor.execute("SELECT SUM(value) FROM inventory_house WHERE `key` = 'INV_MONEY'")
                    housecash, = await cursor.fetchone()

                    await cursor.execute("SELECT SUM(value) FROM inventory_bizz WHERE `key` = 'INV_MONEY'")
                    bizzcash, = await cursor.fetchone()

                    await cursor.execute("SELECT SUM(value) FROM inventory_vehicle WHERE `key` = 'INV_MONEY'")
                    vehiclecash, = await cursor.fetchone()

                    cashsum = inhandcash + banksum + check1sum + check2sum + check3sum + factionbank + housecash + bizzcash + vehiclecash

                    embed = discord.Embed(title='RCRP Economy Statistics', color=0xe74c3c, timestamp=ctx.message.created_at)
                    embed.add_field(name="In-Hand Cash", value='${:,}'.format(inhandcash))
                    embed.add_field(name="Player Banks", value='${:,}'.format(banksum))
                    embed.add_field(name="Check Slot 1", value='${:,}'.format(check1sum))
                    embed.add_field(name="Check Slot 2", value='${:,}'.format(check2sum))
                    embed.add_field(name="Check Slot 3", value='${:,}'.format(check3sum))
                    embed.add_field(name='Faction Banks (excluding ST)', value='${:,}'.format(factionbank))
                    embed.add_field(name='Stored House Cash', value='${:,}'.format(housecash))
                    embed.add_field(name='Stored Business Cash', value='${:,}'.format(bizzcash))
                    embed.add_field(name='Stored Vehicle Cash', value='${:,}'.format(vehiclecash))
                    embed.add_field(name='Total', value='${:,}'.format(cashsum))
                    await ctx.send(embed=embed)

    @commands.command()
    @commands.guild_only()
    @commands.is_owner()
    async def drugs(self, ctx: commands.Context):
        """Collects statistics related to how many drugs are on the server"""
        async with ctx.typing():
            async with aiomysql.connect(**self.mysqlinfo) as sql:
                async with sql.cursor() as cursor:
                    await cursor.execute("SELECT ROUND(SUM(JSON_EXTRACT(extra, '$.BASE_FLOAT'))), `key` FROM (SELECT * FROM inventory_player UNION SELECT * FROM inventory_house UNION SELECT * FROM inventory_bizz UNION SELECT * FROM inventory_vehicle) t WHERE `key` IN ('INV_COCAINE', 'INV_CRACK', 'INV_WEED', 'INV_HEROIN') GROUP BY `key`")
                    data = await cursor.fetchall()
                    embed = discord.Embed(title='RCRP Drug Statistics', color=0xe74c3c, timestamp=ctx.message.created_at)
                    for drug in data:
                        quantity, drug = drug
                        embed.add_field(name=drug_names[drug], value='{:,}'.format(quantity))
                    await ctx.send(embed=embed)

    @commands.command()
    @commands.guild_only()
    @commands.is_owner()
    async def weapons(self, ctx: commands.Context, origin: int):
        """Queries the database for weapon statistics depending on its origin"""
        async with aiomysql.connect(**self.mysqlinfo) as sql:
            async with sql.cursor() as cursor:
                rows = await cursor.execute("SELECT COUNT(*), WeaponID FROM weapons WHERE WeaponOrigin = %s AND Deleted = 0 GROUP BY WeaponID ORDER BY WeaponID", (origin, ))
                if rows == 0:
                    await ctx.send("Invalid origin type.")
                    return

                data = await cursor.fetchall()

                embed = discord.Embed(title=f'RCRP Weapon Statistics ({origins[origin]})', color=0xe74c3c, timestamp=ctx.message.created_at)
                totalweps = 0
                for weapon in data:
                    weapons, weaponid = weapon
                    embed.add_field(name=weaponnames[weaponid], value='{:,}'.format(weapons))
                    totalweps += weapons
                embed.add_field(name='Total', value='{:,}'.format(totalweps))
                await ctx.send(embed=embed)

    @commands.command()
    @commands.is_owner()
    async def mysql(self, ctx: commands.Context, *, query: str):
        """Sends a MySQL query straight to the RCRP database"""
        async with ctx.typing():
            async with aiomysql.connect(**self.mysqlinfo) as sql:
                async with sql.cursor() as cursor:
                    try:
                        if query.lower().startswith('update') or query.lower().startswith('delete'):
                            await cursor.execute(query)
                            await ctx.send(f'{cursor.rowcount} {"rows" if cursor.rowcount != 1 else "row"} affected.')
                        else:
                            await cursor.execute(query)
                            data = None
                            if cursor.rowcount == 0:
                                await ctx.send("No results.")
                                return
                            elif cursor.rowcount == 1:
                                data = await cursor.fetchone()
                            else:
                                data = await cursor.fetchall()

                            string = []
                            for row in data:
                                string.append(f'{row}\n')
                            string = ''.join(string)
                            string = string.replace('(', '')
                            string = string.replace(')', '')
                            for page in pagify(string):
                                await ctx.send(page)
                    except Exception as e:
                        embed = discord.Embed(title='MySQL Error', description=f'{e}', color=0xe74c3c, timestamp=ctx.message.created_at)
                        await ctx.send(embed=embed)

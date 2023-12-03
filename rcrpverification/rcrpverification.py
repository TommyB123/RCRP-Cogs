import discord
import aiomysql
import bcrypt
from typing import Union
from redbot.core import commands, app_commands
from redbot.core.bot import Red

# rcrp guild ID
rcrpguildid = 93142223473905664

# various role IDs
ownerrole = 293303836125298690
managementrole = 310927289317588992
verifiedrole = 293441047244308481
helperrole = 293441873945821184
adminrole = 293441894585729024
testerrole = 293441807055060993

# verification channel ID
verify_channel = 466976078443839488

# url of the dashboard. sent to players when they try to verify
dashboardurl = "https://redcountyrp.com/user/dashboard"


class RcrpLogin(discord.ui.Modal, title='RCRP account login'):
    username_entry = discord.ui.TextInput(label='Enter your RCRP account name.', placeholder='CoolGuy123', max_length=30)
    password_entry = discord.ui.TextInput(label='Enter your RCRP password.', max_length=128)

    async def on_submit(self, interaction: discord.Interaction[Red]):
        bot = interaction.client
        username = self.username_entry.value

        mysqlconfig = await bot.get_shared_api_tokens('mysql')
        sql = await aiomysql.connect(**mysqlconfig)
        cursor = await sql.cursor(aiomysql.DictCursor)

        await cursor.execute('SELECT id, Password, State, Helper, Tester, AdminLevel, discordid FROM masters WHERE Username = %s', (username, ))
        data = await cursor.fetchone()

        if data is None:
            await interaction.response.send_message("Invalid account name.", ephemeral=True)
            return

        if data['State'] != 1:
            await interaction.response.send_message("You cannot verify your Master Account if you have not been accepted into the server.\nIf you're looking for help with the registration process, visit our forums at https://forum.redcountyrp.com", ephemeral=True)
            return

        if data['discordid'] != 0:
            await interaction.response.send_message("This master account has already been verified before. If you are trying to verify a new discord account, please create a support ticket at https://redcountyrp.com/user/tickets.", ephemeral=True)
            return

        password_input = self.password_entry.value.encode()
        stored_password = data['Password'].encode()
        password_match = bcrypt.checkpw(password_input, stored_password)

        if password_match is False:
            await interaction.response.send_message("Invalid password supplied. If you've forgotten your password, please submit a password reset at https://redcountyrp.com/password/reset.", ephemeral=True)
            return

        verified_member: discord.Member = interaction.user
        newroles = []
        newroles.append(interaction.guild.get_role(verifiedrole))
        if data['Helper'] == 1:  # guy is helper
            newroles.append(interaction.guild.get_role(helperrole))
        if data['Tester'] == 1:  # guy is tester
            newroles.append(interaction.guild.get_role(testerrole))
        if data['AdminLevel'] != 0:  # guy is admin
            newroles.append(interaction.guild.get_role(adminrole))
        if data['AdminLevel'] == 4:  # guy is management
            newroles.append(interaction.guild.get_role(managementrole))
        await verified_member.add_roles(*newroles)

        await cursor.execute("UPDATE masters SET discordid = %s WHERE id = %s", (verified_member.id, data['id'], ))
        await cursor.close()
        sql.close()

        await interaction.response.send_message(f'You have successfully linked your Discord account ({interaction.user.mention}) to the RCRP account {username}!', ephemeral=True)


# command checks
async def rcrp_check(check: Union[commands.Context, discord.Interaction]):
    if isinstance(check, commands.Context):
        ctx = check
        return ctx.guild is not None and ctx.guild.id == rcrpguildid
    elif isinstance(check, discord.Interaction):
        interaction = check
        return interaction.guild is not None and interaction.guild_id == rcrpguildid


async def management_check(ctx: commands.Context):
    if ctx.guild is not None and ctx.guild.id == rcrpguildid:
        role_ids = [role.id for role in ctx.author.roles]
        if managementrole in role_ids or ownerrole in role_ids:
            return True
        else:
            return False
    else:
        return True


async def verify_channel_check(interaction: discord.Interaction):
    return interaction.channel_id is not None and interaction.channel_id == verify_channel


def member_is_verified(member: discord.Member):
    return verifiedrole in [role.id for role in member.roles]


class RCRPVerification(commands.Cog, name="RCRP Verification"):
    def __init__(self, bot: Red):
        self.bot = bot

    async def account_linked_to_discord(self, discordid: int):
        mysqlconfig = await self.bot.get_shared_api_tokens('mysql')
        sql = await aiomysql.connect(**mysqlconfig)
        cursor = await sql.cursor()
        await cursor.execute("SELECT NULL FROM masters WHERE discordid = %s", (discordid, ))
        data = await cursor.fetchone()
        await cursor.close()
        sql.close()

        return (data is not None)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.guild is not None and message.guild.id == rcrpguildid and message.channel.id == verify_channel:
            await message.delete()

    @app_commands.command()
    @app_commands.guild_only()
    @app_commands.check(verify_channel_check)
    @app_commands.checks.cooldown(1, 60)
    async def verify(self, interaction: discord.Interaction[Red]):
        """Verify an RCRP account"""

        if await self.account_linked_to_discord(interaction.user.id):
            await interaction.response.send_message('This Discord account is already linked to an RCRP account.', ephemeral=True)
            return

        modal = RcrpLogin(title='Link your Discord and RCRP account')
        await interaction.response.send_modal(modal)

    @commands.command()
    @commands.guild_only()
    @commands.check(rcrp_check)
    @commands.check(management_check)
    async def manualverify(self, ctx: commands.Context, member: discord.Member, masteraccount: str):
        """Manually link a discord account to an RCRP account"""
        if member_is_verified(member) is True:
            await ctx.send(f"{member.mention} is already verified.")
            return

        if await self.account_name_valid(masteraccount) is False:
            await ctx.send("Invalid MA name")
            return

        if await self.account_verified(masteraccount) is True:
            await ctx.send("MA is already verified")
            return

        mysqlconfig = await self.bot.get_shared_api_tokens('mysql')
        sql = await aiomysql.connect(**mysqlconfig)
        cursor = await sql.cursor()
        await cursor.execute("UPDATE masters SET discordid = %s, discordcode = 0 WHERE Username = %s", (member.id, masteraccount))
        await cursor.close()
        sql.close()

        await member.add_roles(ctx.guild.get_role(verifiedrole))
        await ctx.send(f"{member.mention} has been manually verified as {masteraccount}")

    @commands.command()
    @commands.guild_only()
    @commands.check(rcrp_check)
    @commands.check(management_check)
    async def unverify(self, ctx: commands.Context, member: discord.Member):
        """Remove a discord account's verification status and unlinks their RCRP account."""
        if member_is_verified(member) is False:
            await ctx.send("This user is not verified")
            return

        mysqlconfig = await self.bot.get_shared_api_tokens('mysql')
        sql = await aiomysql.connect(**mysqlconfig)
        cursor = await sql.cursor()
        await cursor.execute("DELETE FROM discordroles WHERE discorduser = %s", (member.id, ))
        await cursor.execute("UPDATE masters SET discordid = 0 WHERE discordid = %s", (member.id, ))
        await cursor.close()
        sql.close()

        await ctx.send(f"{member.mention} has been unverified.")

    @commands.command()
    @commands.guild_only()
    @commands.check(rcrp_check)
    @commands.check(management_check)
    async def softunverify(self, ctx: commands.Context, discordid: int):
        """Unlinks an RCRP account from a Discord ID. Useful for when a Discord account no longer exists or is no longer used by its owner"""
        mysqlconfig = await self.bot.get_shared_api_tokens('mysql')
        sql = await aiomysql.connect(**mysqlconfig)
        cursor = await sql.cursor()
        await cursor.execute("UPDATE masters SET discordid = 0 WHERE discordid = %s", (discordid, ))

        if cursor.rowcount != 0:
            await ctx.send(f"Discord ID {discordid} has been unlinked from its MA.")
        else:
            await ctx.send(f"There are no accounts linked to Discord ID {discordid}")

        await cursor.close()
        sql.close()

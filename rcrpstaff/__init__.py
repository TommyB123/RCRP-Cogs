from .rcrpstaff import RCRPStaffCommands


async def setup(bot):
    await bot.add_cog(RCRPStaffCommands(bot))

from .rcrpnormal import RCRPCommands


async def setup(bot):
    await bot.add_cog(RCRPCommands(bot))

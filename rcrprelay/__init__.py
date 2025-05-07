from .rcrprelay import RCRP_Relay


async def setup(bot):
    await bot.add_cog(RCRP_Relay(bot))

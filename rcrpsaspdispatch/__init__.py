from .rcrpsaspdispatch import RCRPDispatch


async def setup(bot):
    await bot.add_cog(RCRPDispatch(bot))

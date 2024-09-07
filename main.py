import os
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv
from config import check_connection
from typing import Literal, Optional


load_dotenv()

check_connection()

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

async def load_extensions():
    for cog in ['cogs.volunteer', 'cogs.schedule']:
        try:
            await bot.load_extension(cog)
            print(f"Loaded cog: {cog}")
        except Exception as e:
            print(f"Failed to load cog {cog}: {e}")

@bot.event
async def on_ready():
    print(f"Bot is ready. Logged in as {bot.user}")

# Sync command for manual command synchronization. code from https://about.abstractumbra.dev/discord.py/2023/01/29/sync-command-example.html
@bot.command()
@commands.guild_only() 
@commands.is_owner() 
async def sync(ctx: commands.Context, guilds: commands.Greedy[discord.Object], spec: Optional[Literal["~", "*", "^"]] = None) -> None:
    if not guilds:
        if spec == "~":  
            synced = await ctx.bot.tree.sync(guild=ctx.guild)
        elif spec == "*": 
            ctx.bot.tree.copy_global_to(guild=ctx.guild)
            synced = await ctx.bot.tree.sync(guild=ctx.guild)
        elif spec == "^": 
            ctx.bot.tree.clear_commands(guild=ctx.guild)
            await ctx.bot.tree.sync(guild=ctx.guild)
            synced = []
        else:  # Sync globally
            synced = await ctx.bot.tree.sync()

        await ctx.send(f"Synced {len(synced)} commands {'globally' if spec is None else 'to the current guild.'}")
        return


    ret = 0
    for guild in guilds:
        try:
            await ctx.bot.tree.sync(guild=guild)
        except discord.HTTPException:
            pass
        else:
            ret += 1

    await ctx.send(f"Synced the tree to {ret}/{len(guilds)} guild(s).")


if __name__ == '__main__':
    asyncio.run(load_extensions())
    bot.run(os.getenv('DISCORD_TOKEN'))

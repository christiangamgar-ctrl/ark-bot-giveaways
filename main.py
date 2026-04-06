import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from database import init_db

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.reactions = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    init_db()
    await bot.load_extension("cogs.giveaways")
    await bot.load_extension("cogs.mysterybox")
    await bot.tree.sync()
    print(f"✅ Bot conectado como {bot.user}")

bot.run(os.getenv("DISCORD_TOKEN"))

import os
from discord.ext import commands, tasks
from pymongo import MongoClient
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")

# Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client['volunteerBot']
volunteers_collection = db['volunteers']

bot = commands.Bot(command_prefix="!")



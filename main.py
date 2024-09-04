import os
import discord
from config import MONGO_URI, check_connection
from discord.ext import tasks
from discord import app_commands
from pymongo import MongoClient
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta

# Load environment variables from the .env file
load_dotenv()

# Check MongoDB connection using the function defined in config.py
check_connection()

# Connect to MongoDB using the MONGO_URI retrieved from config.py
mongo_client = MongoClient(MONGO_URI)
db = mongo_client['wordBot']  
volunteers_collection = db['volunteers']  #  'volunteers' collection

# Define intents and create the bot client  Used ChatGPT to setup
intents = discord.Intents.default() 
intents.members = True 
class MyBot(discord.Client):  
    def __init__(self):
        super().__init__(intents=intents)  
        self.tree = app_commands.CommandTree(self) 

    async def setup_hook(self) -> None:  
        await self.tree.sync()  

# Initialize the bot
bot = MyBot()

# Command to add a volunteer to the database
@bot.tree.command(name="volunteeradd", description="Add a volunteer to the database")
@app_commands.describe(member="The member to add", name="The name of the volunteer")
async def add_volunteer(interaction: discord.Interaction, member: discord.Member, name: str) -> None:
    discord_id = str(member.id)  # member's ID to string
    volunteer = volunteers_collection.find_one({"discordId": discord_id})  # Check if volunteer exists in the database

    if not volunteer:  # If volunteer is not found in the database
        volunteers_collection.insert_one({
            "discordId": discord_id,
            "name": name,
            "hours": 0,
            "meetings": []
        })  # Add the volunteer to the database
        await interaction.response.send_message(f"Volunteer {name} (ID: {member.display_name}) added to the database!")
    else:
        await interaction.response.send_message(f"Volunteer {name} (ID: {member.display_name}) already exists in the database.")

#  command to log volunteer hours
@bot.tree.command(name="loghours", description="Log volunteer hours")
@app_commands.describe(hours="Number of hours to log")
async def log_hours(interaction: discord.Interaction, hours: int) -> None:
    discord_id = str(interaction.user.id)  # Convert user's ID to string
    volunteer = volunteers_collection.find_one({"discordId": discord_id})  # Find the volunteer in the database

    if volunteer:  # If the volunteer exists
        new_hours = volunteer["hours"] + hours  # Update the hours
        volunteers_collection.update_one(
            {"discordId": discord_id},
            {"$set": {"hours": new_hours}}  # Set the new hours in the database
        )
        await interaction.response.send_message(f"Logged {hours} hours for {volunteer['name']}. Total hours: {new_hours}")
    else:
        await interaction.response.send_message("Volunteer not found in the database.")

# Command to schedule a volunteer meeting
@bot.tree.command(name="schedulemeeting", description="Schedule a volunteer meeting")
@app_commands.describe(meeting_time="Time of the meeting (YYYY-MM-DD HH:MM)")
async def schedule_meeting(interaction: discord.Interaction, meeting_time: str) -> None:
    try:
        meeting_date = datetime.strptime(meeting_time, "%Y-%m-%d %H:%M")  # Parse the provided date and time
    except ValueError:
        await interaction.response.send_message("Please provide a valid date in the format 'YYYY-MM-DD HH:MM'.")  # Handle invalid date format
        return

    discord_id = str(interaction.user.id)  # Convert user's ID to string
    volunteer = volunteers_collection.find_one({"discordId": discord_id})  # Find the volunteer in the database

    if volunteer:  # If the volunteer exists
        volunteers_collection.update_one(
            {"discordId": discord_id},
            {"$push": {"meetings": {"date": meeting_date}}}  # Add the meeting date to the 'meetings' array
        )
        await interaction.response.send_message(f"Meeting scheduled for {meeting_time}.")
    else:
        await interaction.response.send_message("Volunteer not found in the database.")

# Command to show the volunteer's meeting schedule
@bot.tree.command(name="showschedule", description="Show your volunteer meeting schedule")
async def show_schedule(interaction: discord.Interaction) -> None:
    discord_id = str(interaction.user.id)  # Convert user's ID to string
    volunteer = volunteers_collection.find_one({"discordId": discord_id})  # Find the volunteer in the database

    if volunteer:  # If the volunteer exists
        if volunteer["meetings"]:  # If the volunteer has scheduled meetings
            meetings = "\n".join([f"Meeting at {meeting['date']}" for meeting in volunteer["meetings"]])  # Format meeting list
            await interaction.response.send_message(f"Your upcoming meetings:\n{meetings}")
        else:
            await interaction.response.send_message("You have no upcoming meetings.")  # If no meetings are found
    else:
        await interaction.response.send_message("Volunteer not found in the database.")

# Function to send reminders for meetings that are starting in 30 minutes
async def send_reminder() -> None:
    now = datetime.now()  # Get the current time
    upcoming = now + timedelta(minutes=30)  # Meetings starting in 30 minutes

    # Find all volunteers who have meetings between now and the upcoming 30 minutes
    volunteers = volunteers_collection.find({"meetings.date": {"$gte": now, "$lte": upcoming}})

    for volunteer in volunteers:  # Loop through the volunteers
        meetings = [m['date'] for m in volunteer['meetings'] if now <= m['date'] <= upcoming]  # Find meetings starting soon
        if meetings: 
            user = await bot.fetch_user(int(volunteer['discordId']))  # Fetch the user by their Discord ID
            for meeting in meetings:  # Loop through the meetings
                await user.send(f"Reminder: You have a meeting at {meeting} in 30 minutes!")  # Send a reminder to the user


# Schedule the send_reminder function to run every 1 minute
scheduler = AsyncIOScheduler()  # Create  scheduler
scheduler.add_job(send_reminder, "interval", minutes=1)  #Remind to run every minute
scheduler.start()  # Start  scheduler



DISCORD_TOKEN = os.getenv("DISCORD")


bot.run(DISCORD_TOKEN)

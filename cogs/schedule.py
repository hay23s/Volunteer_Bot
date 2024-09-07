import discord
from discord.ext import commands
from discord import app_commands  # For slash commands
from apscheduler.schedulers.asyncio import AsyncIOScheduler  # Scheduler
from datetime import datetime, timedelta  # For handling date and time
from pymongo import MongoClient  # MongoDB connection
from config import MONGO_URI  # MongoDB connection string

# MongoDB setup
mongo_client = MongoClient(MONGO_URI)
db = mongo_client['wordBot']  # Use the 'wordBot' database
volunteers_collection = db['volunteers']  # Collection for volunteers data

class Schedule(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot  # Store the bot instance
        self.scheduler = AsyncIOScheduler()  # Initialize the scheduler
        # Schedule the reminder task to run every minute
        self.scheduler.add_job(self.send_reminder, "interval", minutes=1)
        self.scheduler.start()  # Start the scheduler

    # Schedule a volunteer meeting (slash command)
    @app_commands.command(name="schedulemeeting", description="Schedule a volunteer meeting")
    @app_commands.describe(
        year="Year of the meeting (YYYY)",
        month="Month of the meeting (MM)",
        day="Day of the meeting (DD)",
        hour="Hour of the meeting (HH, 24-hour format)",
        minute="Minute of the meeting (MM)",
        participants="Other participants (optional, mention users or roles)"
    )
    async def schedule_meeting(
        self,
        interaction: discord.Interaction,
        year: int,
        month: int,
        day: int,
        hour: int,
        minute: int,
        participants: str = None  # Optional argument for participants (users/roles)
    ):
        try:
            # Create a datetime object with the provided year, month, day, hour, and minute
            meeting_date = datetime(year, month, day, hour, minute)
        except ValueError:
            await interaction.response.send_message("Please provide valid date and time values.")
            return

        discord_id = str(interaction.user.id)  # Get the ID of the user scheduling the meeting

        # Collect participants: Mentioned users or provided Discord IDs
        participant_ids = [discord_id]  # Start with the scheduler's ID

        # If additional participants are mentioned, extract their IDs from the mentions
        if participants:
            mentions = participants.split()  # Split by spaces to extract each mention
            for mention in mentions:
                # If mention is a user mention, strip the <@!> and get the ID
                if mention.startswith('<@') and mention.endswith('>'):
                    participant_id = mention.strip('<@!>')
                    if participant_id.isdigit():
                        participant_ids.append(participant_id)

                # If mention is a role mention, fetch the members with that role
                elif mention.startswith('<@&') and mention.endswith('>'):
                    role_id = mention.strip('<@&>')
                    guild = interaction.guild  # Get the guild (server)
                    role = discord.utils.get(guild.roles, id=int(role_id))  # Find the role by ID
                    if role:
                        for member in role.members:
                            participant_ids.append(str(member.id))  # Add each member's ID from the role

        # Store the meeting data, including the participants
        meeting_data = {"date": meeting_date, "participants": participant_ids}

        # Update the scheduler's record and add the meeting
        scheduler = volunteers_collection.find_one({"discordId": discord_id})
        if scheduler:
            volunteers_collection.update_one(
                {"discordId": discord_id},
                {"$push": {"meetings": meeting_data}}
            )
        else:
            await interaction.response.send_message("Scheduler not found in the database.")
            return

        # update the meeting in each participant's record in the database
        for participant_id in participant_ids:
            volunteer = volunteers_collection.find_one({"discordId": participant_id})
            if volunteer:
                # Add the meeting to each participant's 'meetings' array
                volunteers_collection.update_one(
                    {"discordId": participant_id},
                    {"$push": {"meetings": meeting_data}}
                )
            else:
                await interaction.followup.send(f"Participant with ID {participant_id} not found in the database.")
        await interaction.response.send_message(f"Meeting scheduled for {meeting_date} with {len(participant_ids)} participant(s).")

    # Show the volunteer's meeting schedule
    @app_commands.command(name="showschedule", description="Show your meeting schedule")
    async def show_schedule(self, interaction: discord.Interaction):
        discord_id = str(interaction.user.id) 
        volunteer = volunteers_collection.find_one({"discordId": discord_id})
        if volunteer and "meetings" in volunteer and volunteer["meetings"]:
            meetings = "\n".join([f"Meeting at {meeting['date']}" for meeting in volunteer["meetings"]])
            await interaction.response.send_message(f"Your upcoming meetings:\n{meetings}")
        else:
            await interaction.response.send_message("You have no upcoming meetings.")

    # Function to send reminders for meetings starting in the next 30 minutes
    async def send_reminder(self):
        now = datetime.now()  # Get the current time
        upcoming = now + timedelta(minutes=30)  # 30 minutes from now
        # Find all meetings that start in the next 30 minutes
        volunteers = volunteers_collection.find({"meetings.date": {"$gte": now, "$lte": upcoming}})
        
        for volunteer in volunteers:  # Iterate through each volunteer with upcoming meetings
            meetings = [m for m in volunteer['meetings'] if now <= m['date'] <= upcoming]
            for meeting in meetings:  # Iterate through each meeting
                # Send reminders to all participants of the meeting
                for participant_id in meeting["participants"]:
                    user = await self.bot.fetch_user(int(participant_id))
                    await user.send(f"Hey <@{participant_id}>, you have a meeting at {meeting['date']} in 30 minutes!")


async def setup(bot: commands.Bot):
    await bot.add_cog(Schedule(bot)) 

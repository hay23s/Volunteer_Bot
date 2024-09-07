import discord
from discord.ext import commands
from discord import app_commands
from pymongo import MongoClient
from config import MONGO_URI

mongo_client = MongoClient(MONGO_URI)
db = mongo_client['wordBot']  
volunteers_collection = db['volunteers'] 


class Volunteer(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot  

    # Add a volunteer to the database
    @app_commands.command(name="volunteeradd", description="Add a volunteer to the database")
    @app_commands.describe(member="The member to add", name="The name of the volunteer")
    async def add_volunteer(self, interaction: discord.Interaction, member: discord.Member, name: str):
        discord_id = str(member.id)  # Convert discord ID to string
        volunteer = volunteers_collection.find_one({"discordId": discord_id})  # Check if the volunteer exists in the database

        if not volunteer:  # If the volunteer does not exist
            # Insert the new volunteer into the database
            volunteers_collection.insert_one({
                "discordId": discord_id,
                "name": name,
                "hours": 0,
                "meetings": []
            })
            await interaction.response.send_message(f"Volunteer {name} added to the database!") 
        else:
            await interaction.response.send_message(f"Volunteer {name} already exists in the database.")  

    # Log volunteer hours
    @app_commands.command(name="loghours", description="Log volunteer hours")
    @app_commands.describe(hours="Number of hours to log")
    async def log_hours(self, interaction: discord.Interaction, hours: int):
        discord_id = str(interaction.user.id)  #  Convert discord ID to string
        volunteer = volunteers_collection.find_one({"discordId": discord_id})   # Check if the volunteer exists in the database

        if volunteer:  
            new_hours = volunteer["hours"] + hours  # Update the hours
            # Update the hours in the database
            volunteers_collection.update_one(
                {"discordId": discord_id},
                {"$set": {"hours": new_hours}}  # Set the new hours value
            )
            await interaction.response.send_message(f"Logged {hours} hours for {volunteer['name']}. Total hours: {new_hours}")
        else:
            await interaction.response.send_message("Volunteer not found in the database.")  

async def setup(bot: commands.Bot):
    await bot.add_cog(Volunteer(bot))  

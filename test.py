import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
# Set up so API not needed
load_dotenv()
TOKEN=os.getenv('DISCORD_TOKEN')

intents = discord.Intents.all()
intents.message_content = True
intents.members = True

# Defines prefix as ;
bot = commands.Bot(command_prefix=';', intents=intents)
 # Prints to console to make sure bot active
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')

@bot.command()
@commands.has_permissions(kick_members=True)

async def kick(ctx, member: discord.Member, *, reason=None):
    # Kick a member from the server
    try:
        await member.kick(reason=reason)
        # Send a confirmation message
        await ctx.send(f"Successfully kicked {member.mention}")
        # Alert for needed permissions
    except discord.Forbidden:
        await ctx.send("I don't have permission to kick members.")
    except discord.HTTPException:
        await ctx.send("Kicking the member failed.")

# Error handler for permission errors
@kick.error
async def kick_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You don't have permission to kick members.")

bot.run(TOKEN)



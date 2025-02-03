import discord
from discord.ext import commands
import threading
import os
from dotenv import load_dotenv
import asyncio
import re
from flask import Flask, redirect, session, request, render_template
from flask_pymongo import PyMongo
from pymongo.mongo_client import MongoClient
from google_auth_oauthlib.flow import Flow
import requests

# Load environment variables
load_dotenv()

# Discord Bot Setup
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
TOKEN=os.getenv('DISCORD_TOKEN')


bot = commands.Bot(command_prefix=';', intents=intents)

# Verification Tracking
verification_requests = {}

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
@bot.event
async def on_member_join(member):
    """Prompt new member for verification when they join the server"""
    try:
        # Send DM to initiate verification process
        verification_link = generate_verification_link(member)
        await member.send(
            "Welcome to the UFL Discord! "
            "To access the server, you must verify your UFL email. "
            f"Click this link to verify: {verification_link}"
        )

        # Create a temporary verification record
        verification_requests[member.id] = {
            'member': member,
            'verified': False,
            'attempts': 0
        }
    except discord.Forbidden:
        # If DMs are closed, send a message in the default channel
        default_channel = member.guild.system_channel
        if default_channel:
            await default_channel.send(
                f"{member.mention} Please enable DMs to receive verification instructions!"
            )


def generate_verification_link(member):
    """Generate a unique verification link for the member"""
    # In a real implementation, this would be a secure, time-limited token
    verification_token = f"verify-{member.id}-{hash(str(member))}"
    return f"https://smhcristian.pythonanywhere.com/verify?token={verification_token}"


# Flask Web Application for Verification
app = Flask(__name__)
app.secret_key = os.urandom(24)

# MongoDB Setup
# MongoDB Setup
client = MongoClient('mongodb+srv://cristiansgarcia05:MY5Jc7AS1ztQ1wTf@cluster0.e3siy.mongodb.net/discord_verification?retryWrites=true&w=majority')
db = client.discord_verification
verified_users = db.verified_users

try:
    client.admin.command('ping')
except Exception as e:
    print(f"MongoDB connection error: {e}")

# Google OAuth Configuration
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
GOOGLE_REDIRECT_URI = 'https://smhcristian.pythonanywhere.com/callback'

SCOPES = [
    'openid',
    'https://www.googleapis.com/auth/userinfo.email'
]


@app.route('/verify')
def verification_page():
    """Display verification page"""
    token = request.args.get('token')
    if not token:
        return "Invalid verification request", 400

    return render_template('verify.html', token=token)


@app.route('/login')
def login():
    """Initiate Google OAuth login"""
    flow = Flow.from_client_secrets_file(
        'client_secrets.json',
        scopes=SCOPES,
        redirect_uri=GOOGLE_REDIRECT_URI
    )
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        prompt='consent'
    )
    session['state'] = state
    session['verification_token'] = request.args.get('token')
    return redirect(authorization_url)


@app.route('/callback')
async def callback():
    """Handle Google OAuth callback and verify UFL email"""
    # Validate state to prevent CSRF
    if 'state' not in session or request.args.get('state') != session['state']:
        return 'Invalid state parameter', 401

    # Extract verification token
    verification_token = session.get('verification_token')
    if not verification_token:
        return 'No verification token found', 400

    # Extract user ID from token
    try:
        member_id = int(verification_token.split('-')[1])
    except (IndexError, ValueError):
        return 'Invalid verification token', 400

    # Complete OAuth flow
    flow = Flow.from_client_secrets_file(
        'client_secrets.json',
        scopes=SCOPES,
        redirect_uri=GOOGLE_REDIRECT_URI
    )
    flow.fetch_token(authorization_response=request.url)

    # Fetch user info
    userinfo = requests.get(
        'https://openidconnect.googleapis.com/v1/userinfo',
        headers={'Authorization': f'Bearer {flow.credentials.token}'}
    ).json()

    # Verify UFL email
    email = userinfo.get('email', '')
    if not email.endswith('@ufl.edu'):
        return 'Only UFL email addresses are allowed', 403

    # Find the member and complete verification
    member = verification_requests.get(member_id, {}).get('member')
    if member:
        # Add verified role
        verified_role = discord.utils.get(member.guild.roles, name="Verified")
        if verified_role:
            await member.add_roles(verified_role)

        # Update verification status
        verification_requests[member_id]['verified'] = True

        # Optionally store in database
        verified_users.insert_one({
            'discord_id': member.id,
            'email': email
        })

        # Send confirmation message
        await member.send("You have been successfully verified!")

    return "Verification complete! You can now access the server."


# Discord Bot Command for Manual Verification
@bot.command()
async def reverify(ctx):
    """Allow users to restart the verification process"""
    # Generate and send new verification link
    verification_link = generate_verification_link(ctx.author)
    await ctx.author.send(
        "Click this link to verify your UFL email: " + verification_link
    )


# Error handling for verification
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandInvokeError):
        await ctx.send("An error occurred during verification.")


# Run both Discord bot and Flask app
if __name__ == '__main__':
    # Start Flask app in a separate thread
    flask_thread = threading.Thread(
        target=lambda: app.run(
            host='0.0.0.0',
            port=5000,
            debug=False,
            use_reloader=False
        )
    )
    flask_thread.start()

    # Start Discord bot in the main thread
    bot.run(os.getenv('DISCORD_TOKEN'))
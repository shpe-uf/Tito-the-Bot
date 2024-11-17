from typing import Final
import os
from dotenv import load_dotenv
from discord import Intents, Client, Message
from responses import get_response
import datetime
from googleapiclient.discovery import build
from dateutil import parser

# SCOPES are no longer needed with API key access
load_dotenv()
TOKEN: Final[str] = os.getenv('DISCORD_TOKEN')
CALENDAR_API_KEY: Final[str] = os.getenv('CALENDAR_API_KEY')

# BOT SETUP
intents: Intents = Intents.default()
intents.message_content = True
client: Client = Client(intents=intents)

# MESSAGE FUNCTIONALITY
async def send_message(message: Message, user_message: str) -> None:
    if not user_message:
        print('(Message was empty because intents were not enabled probably)')
        return

    is_private = user_message[0] == '?'
    if is_private:
        user_message = user_message[1:]

    try:
        response: str = get_response(user_message)
        await message.author.send(response) if is_private else await message.channel.send(response)
    except Exception as e:
        print(e)

# HANDLING STARTUP FOR OUR BOT
@client.event
async def on_ready() -> None:
    print(f'{client.user} is now running!')

# HANDLING INCOMING MESSAGES
@client.event
async def on_message(message: Message) -> None:
    if message.author == client.user:
        return
    username: str = str(message.author)
    user_message: str = message.content
    channel: str = str(message.channel)

    print(f'[{channel}] {username}: "{user_message}"')
    if user_message.lower() == 'events':
        await send_upcoming_events(message)
    else:
        await send_message(message, user_message)

# Initialize Google Calendar API service with API key
def get_calendar_service():
    return build('calendar', 'v3', developerKey=CALENDAR_API_KEY)

# Fetch upcoming events from a public calendar using the API key
def get_upcoming_events():
    service = get_calendar_service()
    calendar_id = 'calendar.shpeuf@gmail.com'  # Replace with your public calendar ID
    now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
    try:
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=now,
            maxResults=10,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        events = events_result.get('items', [])
        return events  # Return the list of events instead of printing them
    except Exception as e:
        print(f"Error fetching events: {e}")
        raise

def format_event(event):
    start = event['start'].get('dateTime', event['start'].get('date'))
    if 'dateTime' in event['start']:
        start_time = datetime.datetime.fromisoformat(event['start']['dateTime']).strftime('%Y-%m-%d %H:%M')
    else:
        start_time = event['start']['date']
    return f"{start_time} - {event['summary']}"

# Send upcoming events in response to "events" command
async def send_upcoming_events(message: Message) -> None:
    try:
        service = get_calendar_service()
        now = datetime.datetime.utcnow().isoformat() + 'Z'
        events_result = service.events().list(calendarId='calendar.shpeuf@gmail.com', timeMin=now,
                                              maxResults=10, singleEvents=True,
                                              orderBy='startTime').execute()
        events = events_result.get('items', [])

        if not events:
            await message.channel.send('No upcoming events.')
            return

        response_lines = []
        for event in events:
            start_str = event['start'].get('dateTime', event['start'].get('date'))
            end_str = event['end'].get('dateTime', event['end'].get('date'))
            start = parser.parse(start_str)
            end = parser.parse(end_str)
            date_format = start.strftime('%A, %B %-d')
            start_time = start.strftime('%-I:%M %p') if start.minute != 0 else start.strftime('%-I %p')
            end_time = end.strftime('%-I:%M %p') if end.minute != 0 else end.strftime('%-I %p')

            if 'dateTime' in event['start']:
                response_lines.append(f"{date_format}, {start_time} to {end_time}: {event['summary']}")
            else:
                response_lines.append(f"{date_format}: {event['summary']} (All day)")

        response = "\n".join(response_lines)
        await message.channel.send(f"Upcoming events:\n{response}")
    except Exception as e:
        await message.channel.send(f'Error fetching events: {e}')

# MAIN ENTRY POINT
def main() -> None:
    client.run(TOKEN)

if __name__ == '__main__':
    main()

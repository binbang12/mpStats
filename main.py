from datetime import datetime
import discord
from discord.ext import commands
import os
import sqlite3
import requests

# Define the intents your bot will use
intents = discord.Intents.default()
intents.message_content = True  # Enable message content intent

# Create a bot instance with the desired command prefix and intents
bot = commands.Bot(command_prefix='!', intents=intents)

def get_db_connection():
    conn = sqlite3.connect('stats.db')
    return conn

def get_now():
    now = datetime.utcnow().strftime('%Y/%m/%d')
    return now

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_member_counts (
            date TEXT PRIMARY KEY,
            member_count INTEGER
        )
    ''')
    await bot.tree.sync()

@bot.tree.command(name="date", description="Shows the current date in YYYY/MM/DD format")
async def date(interaction: discord.Interaction):
    now = get_now()
    await interaction.response.send_message(f"Today's date is {now}")

@bot.tree.command(name="insert", description="insert a new value into the database")
async def insert(interaction: discord.Interaction, date: str, members: int):
    conn = get_db_connection()
    cursor = conn.cursor()

    if date == "today":
        date = get_now()

    cursor.execute('''
        SELECT member_count FROM daily_member_counts WHERE date = ?
    ''', (date,))

    count = cursor.fetchone()

    if count:
        await interaction.response.send_message(f"{date} already has value of {count[0]}. Use /update to change it")
        return

    cursor.execute('''
        INSERT INTO daily_member_counts (date, member_count)
        VALUES (?, ?)
    ''', (date, members,))
    conn.commit()
    conn.close()

    await interaction.response.send_message(f"Recorded {members} members on {date}")

@bot.tree.command(name="show", description="Shows the member count on YYYY/MM/DD")
async def show(interaction: discord.Interaction, date: str):
    conn = get_db_connection()
    cursor = conn.cursor()

    if date == "today":
        date = get_now()

    cursor.execute('''
        SELECT member_count
        FROM daily_member_counts
        WHERE date = ?
    ''', (date,))

    members = cursor.fetchone()
    conn.close()

    await interaction.response.send_message(f"On {date}, there were {members[0]} members")

@bot.tree.command(name="update", description="Updates the member count on YYYY/MM/DD")
async def update(interaction: discord.Interaction, date: str, members: int):
    conn = get_db_connection()
    cursor = conn.cursor()

    if date == "today":
        date = get_now()

    cursor.execute('''
        SELECT member_count FROM daily_member_counts WHERE date = ?
    ''', (date,))

    result = cursor.fetchone()
    if not result:
        await interaction.response.send_message(f"No data found for {date}. To add a value, use /insert")
        return

    cursor.execute('''
        UPDATE daily_member_counts
        SET member_count = ?
        WHERE date = ?
    ''', (members, date))

    conn.commit()
    conn.close()

    await interaction.response.send_message(f"Updated {members} members on {date}")

@bot.tree.command(name="delete", description="Deletes the member count on YYYY/MM/DD")
async def delete(interaction: discord.Interaction, date: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    if date == "today":
        date = get_now()

    cursor.execute('''
        SELECT member_count FROM daily_member_counts WHERE date = ?
    ''', (date,))

    result = cursor.fetchone()

    cursor.execute('''
        DELETE FROM daily_member_counts
        WHERE date = ?
    ''', (date,))

    conn.commit()
    conn.close()

    if result:
        await interaction.response.send_message(f"Deleted values at {date}. Value was {result[0]}.")
    else:
        await interaction.response.send_message(f"No data found for {date}. Nothing has changed.")

@bot.tree.command(name="milestone", description="Gives the date where a given milestone was acheived!")
async def milestone(interaction: discord.Interaction, milestone: int):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT date
        FROM daily_member_counts
        WHERE member_count >= ?
        ORDER BY date ASC
        LIMIT 1
    ''', (milestone,))

    result = cursor.fetchone()

    conn.close()

    if result:
        await interaction.response.send_message(f"{milestone} members was acheived on {result[0]}") 
    else:
        await interaction.response.send_message(f"No data found for {milestone} members. Either there is no data or the milestone has not been reached yet.")

@bot.tree.command(name="current", description="Shows the current member count.")
async def all(interaction: discord.Interaction):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT date, member_count
        FROM daily_member_counts
        ORDER BY member_count DESC
        LIMIT 1
    ''')
    results = cursor.fetchone()
    cursor.execute('''
        SELECT member_count, date
        FROM daily_member_counts
        ORDER BY date DESC
        LIMIT 1
    ''')
    comeback = cursor.fetchone()
    conn.close()

    await interaction.response.send_message(f"Highest ever member count is {results[1]} on {results[0]}. Current member count is {comeback[0]} on {comeback[1]}")


# Run the bot with the token from environment variables
bot.run(os.getenv('TOKEN'))

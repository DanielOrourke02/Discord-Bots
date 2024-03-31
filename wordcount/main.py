# PROGRAMMED BY mal023

# auto install modules
try:
    from discord.ext import commands
    import discord
except ModuleNotFoundError:
    import os
    os.system('pip install git+https://github.com/Rapptz/discord.py')
    
from discord.ext import commands
from discord import app_commands
import discord
import json
import time


prefix = '.' # ignore this the prefix is slash commands anyway
bot = commands.Bot(command_prefix=prefix, intents=discord.Intents.all())


# Load the existing word count data from the JSON file, if it exists
try:
    with open('wordcount.json', 'r') as file:
        wordcount_data = json.load(file)
except FileNotFoundError:
    wordcount_data = {}


# Load the config

# Load the config file
with open('config.json', 'r') as file:
    config = json.load(file)

# Accessing individual values from the config
bot_token = config["BOT_TOKEN"]
author = config["AUTHOR"]
max_wordcount = config["MAX_WORDCOUNT"]
status = config["STATUS"]
footer_status = config["AUTHOR_FOOTER"]

# Load word count data from JSON file
def load_wordcount_data():
    try:
        with open('wordcount.json', 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

# Save word count data to JSON file
def save_wordcount_data(data):
    with open('wordcount.json', 'w') as file:
        json.dump(data, file, indent=4)


@bot.event
async def on_ready():
    print(f"Ready and online - {bot.user.display_name}\n")

    # Lists every guild the bot is in

    try:
        guild_count = 0

        for guild in bot.guilds:
            print(f"- {guild.id} (name: {guild.name})\n")

            guild_count = guild_count + 1

        print(f"{bot.user.display_name} is in " + str(guild_count) + " guilds.\n")

        synced = await bot.tree.sync() # Loads/syncs commands
        print(f"Synced {len(synced)} command(s)")

        # listing
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=status))

        # watching, unhash the line bellow. 
        #await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=status))

        # playing, unhash the line bellow. 
        #await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name=status))

        # streaming, unhash the line bellow. 
        #await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.streaming, name=status))


    except Exception as e:
        print(e)


# Simple Test command
@bot.tree.command(name="ping")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message('Pong! {0}'.format(round(bot.latency, 1)), ephemeral=True)


@bot.tree.command(name="help")
async def help_command(interaction: discord.Interaction):
    # Define the list of commands with descriptions
    commands_list = [
        {"name": "wordcount", "description": "Set your current word count"},
        {"name": "servertotal", "description": "The total server word count"},
        {"name": "leaderboard", "description": "List the top 10 users with the highest word count"},
        {"name": "getwordc", "description": "Get a user's word count"},
        {"name": "reset", "description": "Clear wordcount.json (admin only)"},
        {"name": "setwordc", "description": "Set a user's word count (admin only)"},
        # Add more commands as needed with their descriptions
    ]

    # Construct the help message as an embed
    embed = discord.Embed(title="Bot Commands", color=discord.Colour.blue())
    for command in commands_list:
        embed.add_field(name=f"/{command['name']}", value=command['description'], inline=False)
    embed.set_footer(text=f"Use /help <command> for more information on a command.")

    # Send the help message as an ephemeral response
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="wordcount")
async def wordcount_command(interaction: discord.Interaction, count: int):
    # Load word count data
    wordcount_data = load_wordcount_data()

    if count > max_wordcount:
        # Construct the confirmation message as an embed with red color
        confirmation_embed = discord.Embed(
            title="Word count too big!",
            description=f"The max word count is set to {max_wordcount}",
            color=discord.Colour.red()
        )
    else:
        # Update user's word count
        user_id = str(interaction.user.id)
        current_count = wordcount_data.get(user_id, 0)  # Get current user's word count, default to 0 if not found
        wordcount_data[user_id] = current_count + count  # Add the new count to the current count

        # Calculate user's total word count
        user_total = wordcount_data[user_id]

        # Calculate total word count for the entire server
        server_total = sum(wordcount_data.values())

        # Save the updated data back to the JSON file
        save_wordcount_data(wordcount_data)

        # Construct the confirmation message as an embed with green color
        confirmation_embed = discord.Embed(
            title="Word Count Recorded",
            description=f"Your word count has been recorded as {count}.\n"
                        f"Your total word count is {user_total}.\n",
            color=discord.Colour.blue()
        )
    if footer_status == 'true':
        confirmation_embed.set_footer(text=f"Made by {author}")

    # Send the confirmation message as an ephemeral response
    await interaction.response.send_message(embed=confirmation_embed)


@bot.tree.command(name="servertotal")
async def servertotal_command(interaction: discord.Interaction):
    # Load word count data
    wordcount_data = load_wordcount_data()

    # Calculate total word count for the entire server
    server_total = sum(wordcount_data.values())

    # Construct the embed message
    embed = discord.Embed(
        title="Server Total Word Count",
        description=f"The total word count for the entire server is {server_total}.",
        color=discord.Colour.blue()
    )

    # Set footer
    if footer_status == 'true':
        embed.set_footer(text=f"Made by {author}")

    # Send the embed message
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="leaderboard")
async def leaderboard_command(interaction: discord.Interaction):
    # Load the word count data from the JSON file
    with open('wordcount.json', 'r') as file:
        wordcount_data = json.load(file)

    # Sort the word count data based on the word count in descending order
    sorted_wordcount = sorted(wordcount_data.items(), key=lambda x: x[1], reverse=True)

    # Get the top 10 users with the highest word count
    top_10 = sorted_wordcount[:10]

    # Construct the leaderboard message as an embed with blue color
    leaderboard_embed = discord.Embed(
        title="Top 10 Users with Highest Word Count",
        color=discord.Colour.blue()
    )
    for index, (user_id, word_count) in enumerate(top_10, start=1):
        user = bot.get_user(int(user_id))
        if user:
            leaderboard_embed.add_field(name=f"{index}. {user.name}", value=f"{word_count} words", inline=False)
        else:
            leaderboard_embed.add_field(name=f"{index}. Unknown User ({user_id})", value=f"{word_count} words", inline=False)
            
    if footer_status == 'true':
        leaderboard_embed.set_footer(text=f"Made by {author}")

    # Send the leaderboard message as an ephemeral response
    await interaction.response.send_message(embed=leaderboard_embed)


@bot.tree.command(name="getwordc")
async def getwordc_command(interaction: discord.Interaction, user: discord.User = None):
    # Load the word count data from the JSON file
    with open('wordcount.json', 'r') as file:
        wordcount_data = json.load(file)

    # If no user is mentioned, use the user who invoked the command
    if user is None:
        user = interaction.user

    # Get the user's ID
    user_id = str(user.id)

    # Get the user's current word count
    current_word_count = wordcount_data.get(user_id, 0)

    # Calculate the user's total word count
    user_total_word_count = current_word_count

    # Construct the message
    message = f"{user.name}'s current word count is {current_word_count} words.\n"
    message += f"{user.name}'s total word count is {user_total_word_count} words."

    # Construct the message as an embed with blue color
    wordcount_embed = discord.Embed(
        title="Word Count",
        description=message,
        color=discord.Colour.blue()
    )

    if footer_status == 'true':
        wordcount_embed.set_footer(text=f"Made by {author}")

    # Send the message with the user's word count as an ephemeral response
    await interaction.response.send_message(embed=wordcount_embed)


# ----------------------------------------------ADMIN COMMANDS----------------------------------------------


@bot.tree.command(name="reset")
async def reset(interaction: discord.Interaction):
    # Check if the user invoking the command has Administrator permission
    if not interaction.user.guild_permissions.administrator:
        message = "You do not have permission to use this command."
    else:
        message = "Please run `/reset_confirm` to reset the global wordcount!"

    # Construct the message as an embed with blue color
    reset_embed = discord.Embed(
        title="Reset Confirmation",
        description=message,
        color=discord.Colour.blue()
    )
    if footer_status == 'true':
        reset_embed.set_footer(text=f"Made by {author}")

    # Send the message as an ephemeral response
    await interaction.response.send_message(embed=reset_embed, ephemeral=True)


@bot.tree.command(name="reset_confirm")
async def reset_confirm(interaction: discord.Interaction):
    # Check if the user invoking the command has Administrator permission
    if not interaction.user.guild_permissions.administrator:
        message = "You do not have permission to use this command."
    else:
        # Reset the word count data by clearing the JSON file
        with open('wordcount.json', 'w') as file:
            file.write('{}')  # Write an empty JSON object

        message = "Global word count has been reset."

    # Construct the message as an embed with blue color
    reset_confirm_embed = discord.Embed(
        title="Reset Confirmation",
        description=message,
        color=discord.Colour.blue()
    )
    if footer_status == 'true':
        # Add the "Made by larryhiatus" message at the bottom
        reset_confirm_embed.set_footer(text=f"Made by {author}")

    # Send the message as an ephemeral response
    await interaction.response.send_message(embed=reset_confirm_embed)


@bot.tree.command(name="setwordc")
async def setwordc_command(interaction: discord.Interaction, user: discord.User = None, count: int = None):
    # Check if the user invoking the command has Administrator permission
    if not interaction.user.guild_permissions.administrator:
        message = "You do not have permission to use this command."
    else:
        # Check if the user ID or count is empty
        if user is None or count is None:
            message = "Error: You need to ping the person you want to set their wordcount to and specify the count."
        else:
            # Load the word count data from the JSON file
            try:
                with open('wordcount.json', 'r') as file:
                    wordcount_data = json.load(file)
            except FileNotFoundError:
                wordcount_data = {}

            # Set the user's word count to the specified count
            wordcount_data[str(user.id)] = count

            # Save the updated data back to the JSON file
            with open('wordcount.json', 'w') as file:
                json.dump(wordcount_data, file, indent=4)

            message = discord.Embed(
                title="Word Count Set Confirmation",
                description=f"{user.name}'s word count has been set to {count}.",
                color=discord.Colour.blue()
            )

    if footer_status == 'true':
        # Add the "Made by larryhiatus" message at the bottom
        message.set_footer(text=f"Made by {author}")
    
    # Send the message as an ephemeral response
    await interaction.response.send_message(embed=message)


bot.run(bot_token)
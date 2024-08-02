# PROGRAMMED BY mal023

from discord.ext.pages import Paginator
from discord import Option
import discord
import json
import time


intents = discord.Intents.all()
bot = discord.Bot(intents=intents)

# Load the existing word count data from the JSON file, if it exists
try:
    with open('wordcount.json', 'r') as file:
        wordcount_data = json.load(file)
except FileNotFoundError:
    wordcount_data = {}

# Load the config
with open('config.json', 'r') as file:
    config = json.load(file)

# Accessing individual values from the config
bot_token = config["BOT_TOKEN"]
max_wordcount = config["MAX_WORDCOUNT"]
status = config["STATUS"]

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
        
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=status))
    except Exception as e:
        print(e)


# Simple Test command
@bot.slash_command(name="ping", description="Ping the bot")
async def ping(ctx):
    await ctx.respond('Pong! {0}'.format(round(bot.latency, 1)), ephemeral=True)


@bot.slash_command(name="help", description="Lists all commands")
async def help_command(ctx: discord.ApplicationContext):
    # Get the list of command names and descriptions
    command_info = [(command.name, command.description) for command in bot.commands]
    # Split the commands into chunks of 15
    chunks = [command_info[i:i + 15] for i in range(0, len(command_info), 15)]
    # Create pages with the command names and descriptions
    pages_list = [
        discord.Embed(
            title="List of commands:",
            description="\n".join([f"`/{name}` - {description}" for name, description in chunk]),
            color=discord.Color.blurple()
        ) for chunk in chunks
    ]

    # Create the paginator
    paginator = Paginator(pages=pages_list, loop_pages=True)

    # Respond with the paginated message
    await paginator.respond(ctx.interaction, ephemeral=False)


@bot.slash_command(name="wordcount", description="Set your current word count")
async def wordcount(ctx: discord.ApplicationContext, count: Option(int, description="Set your wordcount", required=True)): # type: ignore
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
        user_id = str(ctx.user.id)
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
            color=discord.Color.blurple()
        )

    # Send the confirmation message as an ephemeral response
    await ctx.respond(embed=confirmation_embed)


@bot.slash_command(name="servertotal", description="The total server word count")
async def servertotal_command(ctx: discord.ApplicationContext):
    # Load word count data
    wordcount_data = load_wordcount_data()

    # Calculate total word count for the entire server
    server_total = sum(wordcount_data.values())

    # Construct the embed message
    embed = discord.Embed(
        title="Server Total Word Count",
        description=f"The total word count for the entire server is {server_total}.",
        color=discord.Colour.blurple()
    )

    # Send the embed message
    await ctx.respond(embed=embed)


@bot.slash_command(name="leaderboard", description="List the top 10 users with the highest word count")
async def leaderboard_command(ctx: discord.ApplicationContext):
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
        color=discord.Colour.blurple()
    )
    for index, (user_id, word_count) in enumerate(top_10, start=1):
        user = bot.get_user(int(user_id))
        if user:
            leaderboard_embed.add_field(name=f"{index}. {user.name}", value=f"{word_count} words", inline=False)
        else:
            leaderboard_embed.add_field(name=f"{index}. Unknown User ({user_id})", value=f"{word_count} words", inline=False)

    # Send the leaderboard message as an ephemeral response
    await ctx.respond(embed=leaderboard_embed)


@bot.slash_command(name="getwordc", description="Get a user's word count")
async def getwordc_command(ctx: discord.ApplicationContext, user: discord.User=None):
    # Load the word count data from the JSON file
    with open('wordcount.json', 'r') as file:
        wordcount_data = json.load(file)

    # If no user is mentioned, use the user who invoked the command
    if user is None:
        user = ctx.user

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
        color=discord.Colour.blurple()
    )

    # Send the message with the user's word count as an ephemeral response
    await ctx.respond(embed=wordcount_embed)


# ----------------------------------------------ADMIN COMMANDS----------------------------------------------


@bot.slash_command(name="reset", description="Clear wordcount.json (admin only)")
async def reset(ctx: discord.ApplicationContext):
    # Check if the user invoking the command has Administrator permission
    if not ctx.user.guild_permissions.administrator:
        message = "You do not have permission to use this command."
    else:
        message = "Please run `/reset_confirm` to reset the global wordcount!"

    # Construct the message as an embed with blue color
    reset_embed = discord.Embed(
        title="Reset Confirmation",
        description=message,
        color=discord.Colour.blurple()
    )

    # Send the message as an ephemeral response
    await ctx.respond(embed=reset_embed, ephemeral=True)


@bot.slash_command(name="reset_confirm", description="Confirm the reset of wordcount.json (admin only)")
async def reset_confirm(ctx: discord.ApplicationContext):
    # Check if the user invoking the command has Administrator permission
    if not ctx.user.guild_permissions.administrator:
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
        color=discord.Colour.blurple()
    )

    # Send the message as an ephemeral response
    await ctx.respond(embed=reset_confirm_embed)


@bot.slash_command(name="setwordc", description="Set a user's word count (admin only)")
async def setwordc_command(ctx, user: discord.User, count: Option(int, description="Enter the users wordcount", required=True)): # type: ignore
    # Check if the user invoking the command has Administrator permission
    if not ctx.user.guild_permissions.administrator:
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
                color=discord.Colour.blurple()
            )
    
    # Send the message as an ephemeral response
    await ctx.respond(embed=message)


bot.run(bot_token)

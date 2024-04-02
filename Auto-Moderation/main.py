from discord.ext import commands
from discord import app_commands
import discord
import json


prefix = '.' # ignore this the prefix is slash commands anywa
bot = commands.Bot(command_prefix=prefix, intents=discord.Intents.all())


# Load the config file
with open('config.json', 'r') as file:
    config = json.load(file)

# Accessing individual values from the config
bot_token = config["BOT_TOKEN"]
link_ban = config["LINK_BAN"]


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
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="/help"))

    except Exception as e:
        print(e)


@bot.event
async def on_message(message):
    # List of forbidden words
    forbidden_words = ["badword1", "badword2", "badword3"]

    # Check if any forbidden words are present in the message
    for word in forbidden_words:
        if word in message.content.lower():
            # Delete the message containing the forbidden word
            await message.delete()

            # Send an embed informing the user about the deletion
            embed = discord.Embed(
                title="Forbidden Word Detected!",
                description=f"{message.author.mention} Usage of forbidden words is not allowed in this server.",
                color=discord.Color.red()
            )
            embed.set_footer(text=f"Made by mal023")

            await message.channel.send(embed=embed)
            return  # Exit the function after handling the message
        

    if link_ban == 'true':
        # Check if the message contains a discord link
        if "discord.gg" in message.content:
            # Delete the message containing the discord link
            await message.delete()

            # Send an embed informing the user about the deletion
            embed = discord.Embed(
                title="Discord Links Are Forbidden!",
                description=f"{message.author.mention} Discord links are not allowed in this server.",
                color=discord.Color.red()
            )

            embed.set_footer(text=f"Made by mal023")

            await message.channel.send(embed=embed)

        # Continue processing other commands and events
        await bot.process_commands(message)


# Simple Test command
@bot.tree.command(name="ping")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message('Pong! {0}'.format(round(bot.latency, 1)), ephemeral=True)


@bot.tree.command(name="help")
async def help_command(interaction: discord.Interaction):
    # Define the list of commands with descriptions
    commands_list = [
        {"name": "help", "description": "Sends this message"},
        {"name": "ping", "description": "Ping the bot, test if its online"},
        {"name": "dis_automod", "description": "Disables auto-moderation"},
        # Add more commands as needed with their descriptions
    ]

    # Construct the help message as an embed
    embed = discord.Embed(title="Bot Commands", color=discord.Colour.blue())
    for command in commands_list:
        embed.add_field(name=f"/{command['name']}", value=command['description'], inline=False)
    embed.set_footer(text=f"Use /help <command> for more information on a command.")

    # Send the help message as an ephemeral response
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="dis_automod")
async def dis_automoderation(interaction: discord.Interaction):
    if link_ban == "true":
         # Construct the help message as an embed
        embed = discord.Embed(title="Disabled Automoderation", color=discord.Colour.blue())
        embed.add_field(name="Disabled Automoderation", value=f"Automoderation (blocks certain words and discord links) has been enabled.", inline=False)

        embed.set_footer(text=f"Made by mal023")       
    else:
        # Construct the help message as an embed
        embed = discord.Embed(title="Disabled Automoderation", color=discord.Colour.red())
        embed.add_field(name="Disabled Automoderation", value=f"Automoderation (blocks certain words and discord links) has been disabled.", inline=False)

        embed.set_footer(text=f"Made by mal023")

    # Send the help message as an ephemeral response
    await interaction.response.send_message(embed=embed)

bot.run(bot_token)

from discord.ext.pages import Paginator
from discord.ext import commands
from discord import Option
import discord
import sqlite3
import json
import time

intents = discord.Intents.all()
bot = discord.Bot(intents=intents)

conn = sqlite3.connect('wordcount.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS wordcount (
    user_id TEXT PRIMARY KEY,
    count INTEGER
)
''')
conn.commit()

with open('config.json', 'r') as file:
    config = json.load(file)

bot_token = config["BOT_TOKEN"]
max_wordcount = config["MAX_WORDCOUNT"]

def get_wordcount(user_id):
    cursor.execute('SELECT count FROM wordcount WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    return result[0] if result else 0

def set_wordcount(user_id, count):
    cursor.execute('INSERT OR REPLACE INTO wordcount (user_id, count) VALUES (?, ?)', (user_id, count))
    conn.commit()

def get_server_total():
    cursor.execute('SELECT SUM(count) FROM wordcount')
    result = cursor.fetchone()
    return result[0] if result else 0

def get_leaderboard():
    cursor.execute('SELECT user_id, count FROM wordcount ORDER BY count DESC LIMIT 10')
    return cursor.fetchall()

@bot.event
async def on_ready():
    print(f"Ready and online - {bot.user.display_name}\n")
    try:
        guild_count = 0
        for guild in bot.guilds:
            print(f"- {guild.id} (name: {guild.name})\n")
            guild_count += 1
        print(f"{bot.user.display_name} is in " + str(guild_count) + " guilds.\n")
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="/help"))
    except Exception as e:
        print(e)

@bot.slash_command(name="ping", description="Ping the bot")
async def ping(ctx):
    await ctx.respond('Pong! {0}'.format(round(bot.latency, 1)), ephemeral=True)

@bot.slash_command(name="help", description="Lists all commands")
async def help_command(ctx: discord.ApplicationContext):
    command_info = [(command.name, command.description) for command in bot.commands]
    chunks = [command_info[i:i + 15] for i in range(0, len(command_info), 15)]
    pages_list = [
        discord.Embed(
            title="List of commands:",
            description="\n".join([f"`/{name}` - {description}" for name, description in chunk]),
            color=discord.Color.blurple()
        ) for chunk in chunks
    ]
    paginator = Paginator(pages=pages_list, loop_pages=True)
    await paginator.respond(ctx.interaction, ephemeral=False)

@bot.slash_command(name="wordcount", description="Set your current word count")
async def wordcount(ctx: discord.ApplicationContext, count: Option(int, description="Set your wordcount", required=True)): # type: ignore
    user_id = str(ctx.user.id)
    current_count = get_wordcount(user_id)
    if count > max_wordcount:
        confirmation_embed = discord.Embed(
            title="Word count too big!",
            description=f"The max word count is set to {max_wordcount}",
            color=discord.Colour.red()
        )
    else:
        set_wordcount(user_id, current_count + count)
        user_total = get_wordcount(user_id)
        server_total = get_server_total()
        confirmation_embed = discord.Embed(
            title="Word Count Recorded",
            description=f"Your word count has been recorded as {count}.\nYour total word count is {user_total}.\n",
            color=discord.Color.blurple()
        )
    await ctx.respond(embed=confirmation_embed)

@bot.slash_command(name="servertotal", description="The total server word count")
async def servertotal_command(ctx: discord.ApplicationContext):
    server_total = get_server_total()
    embed = discord.Embed(
        title="Server Total Word Count",
        description=f"The total word count for the entire server is {server_total}.",
        color=discord.Colour.blurple()
    )
    await ctx.respond(embed=embed)

@bot.slash_command(name="leaderboard", description="List the top 10 users with the highest word count")
async def leaderboard_command(ctx: discord.ApplicationContext):
    top_10 = get_leaderboard()
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
    await ctx.respond(embed=leaderboard_embed)

@bot.slash_command(name="getwordc", description="Get a user's word count")
async def getwordc_command(ctx: discord.ApplicationContext, user: discord.User=None):
    if user is None:
        user = ctx.user
    user_id = str(user.id)
    current_word_count = get_wordcount(user_id)
    message = f"{user.name}'s current word count is {current_word_count} words."
    wordcount_embed = discord.Embed(
        title="Word Count",
        description=message,
        color=discord.Colour.blurple()
    )
    await ctx.respond(embed=wordcount_embed)

@bot.slash_command(name="reset", description="Clear wordcount data (admin only)")
@commands.is_owner()
async def reset(ctx: discord.ApplicationContext):
    reset_embed = discord.Embed(
        title="Reset Confirmation",
        description="Please run `/reset_confirm` to reset the global wordcount!",
        color=discord.Colour.blurple()
    )
    await ctx.respond(embed=reset_embed, ephemeral=True)

@bot.slash_command(name="reset_confirm", description="Confirm the reset of wordcount data (admin only)")
@commands.is_owner()
async def reset_confirm(ctx: discord.ApplicationContext):
    cursor.execute('DELETE FROM wordcount')
    conn.commit()
    reset_confirm_embed = discord.Embed(
        title="Reset Confirmation",
        description="Global word count has been reset.",
        color=discord.Colour.blurple()
    )
    await ctx.respond(embed=reset_confirm_embed)

@bot.slash_command(name="setwordc", description="Set a user's word count (admin only)")
@commands.is_owner()
async def setwordc_command(ctx, user: discord.User, count: Option(int, description="Enter the user's wordcount", required=True)): # type: ignore
    set_wordcount(str(user.id), count)
    message = discord.Embed(
        title="Word Count Set Confirmation",
        description=f"{user.name}'s word count has been set to {count}.",
        color=discord.Colour.blurple()
    )
    await ctx.respond(embed=message)

bot.run(bot_token)
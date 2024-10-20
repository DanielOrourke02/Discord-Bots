import discord
from discord.ext import commands
import psutil
import json

# Load configuration from JSON file
with open('config.json', 'r') as config_file:
    config = json.load(config_file)

# Load variables from config.json
token = config.get("BOT_TOKEN")

bot = discord.Bot(ntents=discord.Intents.default())


@bot.event
async def on_ready():
    print(f'Ready and online! - {bot.user.display_name}')


@bot.command()
async def help(ctx):
    # Define help embed
    embed = discord.Embed(title="Help", description="List of available commands:", color=0x00FFFF)
    embed.add_field(name=f"`/help`", value="Shows this message", inline=False)
    embed.add_field(name=f"`/ping`", value="Shows bot latency", inline=False)
    embed.add_field(name=f"`/usage`", value="Shows system CPU and memory usage", inline=False)

    await ctx.send(embed=embed)


@bot.command()
async def ping(ctx: discord.ApplicationContext):
    # Calculate bot latency
    latency = bot.latency * 1000  # Convert to milliseconds
    embed = discord.Embed(title="Pong! 🏓", description=f"Latency: {latency:.2f}ms", color=0x00FFFF)

    await ctx.send(embed=embed)


@bot.command()
async def usage(ctx: discord.ApplicationContext):
    # Get CPU and memory usage
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()

    embed = discord.Embed(title="System Usage", color=0x00FFFF)
    embed.add_field(name="CPU Usage", value=f"{cpu_percent}%", inline=False)
    embed.add_field(name="Memory Usage", value=f"Total: {humanize_bytes(memory.total)}, "
                                                f"Available: {humanize_bytes(memory.available)}", inline=False)

    await ctx.send(embed=embed)


# Helper function to convert bytes to a human-readable format
def humanize_bytes(bytesize, precision=2):
    abbrevs = ((1 << 50, 'PB'), (1 << 40, 'TB'), (1 << 30, 'GB'), (1 << 20, 'MB'), (1 << 10, 'KB'), (1, 'bytes'))
    if bytesize == 1:
        return '1 byte'
    for factor, suffix in abbrevs:
        if bytesize >= factor:
            break
    return f"{bytesize / factor:.{precision}f} {suffix}"


bot.run(token)

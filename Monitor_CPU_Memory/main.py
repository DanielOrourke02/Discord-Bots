import discord
from discord.ext import commands
import psutil  # For getting system usage information
import json

# Load configuration from JSON file
with open('config.json', 'r') as config_file:
    config = json.load(config_file)

# Load variables from config.json
token = config.get("BOT_TOKEN")
prefix = config.get("PREFIX")

bot = commands.Bot(command_prefix=prefix, intents=discord.Intents.all(), help_command=None)


@bot.event
async def on_ready():
    print(f'Ready and online! - {bot.user.display_name}')


@bot.command()
async def help(ctx):
    # Define help embed
    embed = discord.Embed(title="Help", description="List of available commands:", color=0x00FFFF)  # Cyan color
    embed.add_field(name=f"{prefix}help", value="Shows this message", inline=False)
    embed.add_field(name=f"{prefix}ping", value="Shows bot latency", inline=False)
    embed.add_field(name=f"{prefix}usage", value="Shows system CPU and memory usage", inline=False)
    
    embed.set_footer(text=f"Made by mal023")

    await ctx.send(embed=embed)


@bot.command()
async def ping(ctx):
    # Calculate bot latency
    latency = bot.latency * 1000  # Convert to milliseconds
    embed = discord.Embed(title="Pong! 🏓", description=f"Latency: {latency:.2f}ms", color=0x00FFFF)  # Cyan color

    embed.set_footer(text=f"Made by mal023")

    await ctx.send(embed=embed)


@bot.command()
async def usage(ctx):
    # Get CPU and memory usage
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()

    embed = discord.Embed(title="System Usage", color=0x00FFFF)  # Cyan color
    embed.add_field(name="CPU Usage", value=f"{cpu_percent}%", inline=False)
    embed.add_field(name="Memory Usage", value=f"Total: {humanize_bytes(memory.total)}, "
                                                f"Available: {humanize_bytes(memory.available)}", inline=False)

    embed.set_footer(text=f"Made by mal023")

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

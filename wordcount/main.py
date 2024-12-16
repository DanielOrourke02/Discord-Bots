from discord.ext.pages import Paginator
from discord.ext import commands
from discord import Option
import discord
import sqlite3
import json
import time
from datetime import datetime, timedelta

class WordCountBot(discord.Bot):
    def __init__(self):
        super().__init__(intents=discord.Intents.all())
        self.start_time = datetime.now()
        self.db = Database()
        self.load_config()

    def load_config(self):
        with open('config.json', 'r') as file:
            self.config = json.load(file)
            self.max_wordcount = self.config["MAX_WORDCOUNT"]

    def get_uptime(self):
        delta = datetime.now() - self.start_time
        days = delta.days
        hours, remainder = divmod(delta.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{days}d {hours}h {minutes}m {seconds}s"

class Database:
    def __init__(self):
        self.conn = sqlite3.connect('wordcount.db')
        self.cursor = self.conn.cursor()
        self.setup_database()

    def setup_database(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS wordcount (
                user_id TEXT PRIMARY KEY,
                count INTEGER DEFAULT 0,
                last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                daily_goal INTEGER DEFAULT 0,
                streak INTEGER DEFAULT 0,
                last_streak_update DATE
            )
        ''')
        self.conn.commit()

    def get_wordcount(self, user_id: str) -> int:
        self.cursor.execute('SELECT count FROM wordcount WHERE user_id = ?', (user_id,))
        result = self.cursor.fetchone()
        return result[0] if result else 0

    def set_wordcount(self, user_id: str, count: int):
        self.cursor.execute('''
            INSERT OR REPLACE INTO wordcount 
            (user_id, count, last_update) 
            VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', (user_id, count))
        self.conn.commit()

    def get_server_total(self) -> int:
        self.cursor.execute('SELECT SUM(count) FROM wordcount')
        result = self.cursor.fetchone()
        return result[0] if result[0] else 0

    def get_leaderboard(self, limit: int = 10):
        self.cursor.execute('''
            SELECT user_id, count, last_update 
            FROM wordcount 
            ORDER BY count DESC 
            LIMIT ?
        ''', (limit,))
        return self.cursor.fetchall()

    def get_all_writers(self):
        self.cursor.execute('SELECT DISTINCT user_id FROM wordcount WHERE count > 0')
        return self.cursor.fetchall()

    def reset_database(self):
        self.cursor.execute('DELETE FROM wordcount')
        self.conn.commit()

bot = WordCountBot()

@bot.event
async def on_ready():
    print(f"╔{'═' * 50}╗")
    print(f"║ {bot.user.display_name} is Ready!{' ' * (50 - len(bot.user.display_name) - 11)}║")
    print(f"║ Serving {len(bot.guilds)} servers{' ' * (50 - len(str(len(bot.guilds))) - 15)}║")
    print(f"╚{'═' * 50}╝")
    
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="writers create! | /help"
        )
    )

@bot.slash_command(name="ping", description="Check bot latency")
async def ping(ctx):
    embed = discord.Embed(
        title="🏓 Pong!",
        description=f"Bot Latency: **{round(bot.latency * 1000)}ms**",
        color=discord.Color.green()
    )
    await ctx.respond(embed=embed, ephemeral=True)

@bot.slash_command(name="wordcount", description="Add to your word count")
async def wordcount(ctx: discord.ApplicationContext, 
                   count: Option(int, "Enter your word count", required=True, min_value=1)): # type: ignore
    try:
        user_id = str(ctx.user.id)
        current_count = bot.db.get_wordcount(user_id)

        if count > bot.max_wordcount:
            embed = discord.Embed(
                title="❌ Excessive Word Count",
                description=f"Maximum allowed word count per update is **{bot.max_wordcount:,}**",
                color=discord.Color.red()
            )
        else:
            new_total = current_count + count
            bot.db.set_wordcount(user_id, new_total)
            server_total = bot.db.get_server_total()

            embed = discord.Embed(
                title="✍️ Progress Updated!",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="📈 Words Added",
                value=f"**+{count:,}** words",
                inline=True
            )
            
            embed.add_field(
                name="📚 Your Total",
                value=f"**{new_total:,}** words",
                inline=True
            )
            
            embed.add_field(
                name="🌍 Server Total",
                value=f"**{server_total:,}** words",
                inline=True
            )

        await ctx.respond(embed=embed)

    except Exception as e:
        await ctx.respond(
            embed=discord.Embed(
                title="❌ Error",
                description=f"An error occurred: {str(e)}",
                color=discord.Color.red()
            ),
            ephemeral=True
        )

@bot.slash_command(name="leaderboard", description="View the word count leaderboard")
async def leaderboard(ctx: discord.ApplicationContext):
    try:
        top_users = bot.db.get_leaderboard()
        server_total = bot.db.get_server_total()

        embed = discord.Embed(
            title="📊 Word Count Rankings",
            description=f"Total Words Written: **{server_total:,}**",
            color=discord.Color.blue()
        )

        medals = {1: "🥇", 2: "🥈", 3: "🥉"}
        
        for index, (user_id, count, last_update) in enumerate(top_users, 1):
            user = bot.get_user(int(user_id))
            username = user.name if user else f"User-{user_id}"
            
            medal = medals.get(index, "➡️")
            last_update_str = datetime.strptime(last_update, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %H:%M')
            
            embed.add_field(
                name=f"{medal} #{index} - {username}",
                value=f"**{count:,}** words\n*Last Update: {last_update_str}*",
                inline=False
            )

        embed.set_footer(text="Keep writing to climb the rankings!")
        await ctx.respond(embed=embed)

    except Exception as e:
        await ctx.respond(
            embed=discord.Embed(
                title="❌ Error",
                description=str(e),
                color=discord.Color.red()
            ),
            ephemeral=True
        )

@bot.slash_command(name="info", description="View bot information and statistics")
async def info_command(ctx: discord.ApplicationContext):
    try:
        server_total = bot.db.get_server_total()
        total_writers = len(bot.db.get_all_writers())
        
        embed = discord.Embed(
            title="📝 Writer's Assistant",
            description="Helping writers track their progress and stay motivated!",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )

        # Bot Stats
        stats = f"**Servers:** {len(bot.guilds)}\n"
        stats += f"**Active Writers:** {total_writers}\n"
        stats += f"**Words Written:** {server_total:,}\n"
        stats += f"**Uptime:** {bot.get_uptime()}"
        
        embed.add_field(
            name="📊 Statistics",
            value=stats,
            inline=False
        )

        # Features
        features = "• Track your daily word count\n"
        features += "• Compete on the leaderboard\n"
        features += "• Monitor server progress\n"
        features += "• Set personal writing goals"
        
        embed.add_field(
            name="✨ Features",
            value=features,
            inline=False
        )

        # Quick Guide
        guide = "`/wordcount` - Update your progress\n"
        guide += "`/leaderboard` - View top writers\n"
        guide += "`/help` - List all commands"
        
        embed.add_field(
            name="📚 Quick Start",
            value=guide,
            inline=False
        )

        embed.set_footer(text="Happy writing! 📖✍️")
        await ctx.respond(embed=embed)

    except Exception as e:
        await ctx.respond(
            embed=discord.Embed(
                title="❌ Error",
                description=str(e),
                color=discord.Color.red()
            ),
            ephemeral=True
        )

@bot.slash_command(name="help", description="View all available commands")
async def help_command(ctx: discord.ApplicationContext):
    embed = discord.Embed(
        title="📚 Available Commands",
        description="Here's everything you can do:",
        color=discord.Color.blue()
    )

    commands = [
        ("📝 Writing", [
            ("wordcount", "Add to your word count", "/wordcount <number>"),
            ("getwordc", "View your or someone's word count", "/getwordc [user]")
        ]),
        ("📊 Statistics", [
            ("leaderboard", "View top writers", "/leaderboard"),
            ("servertotal", "View total server words", "/servertotal"),
            ("info", "Bot information and stats", "/info")
        ])
    ]

    for category, cmds in commands:
        commands_text = ""
        for cmd_name, desc, usage in cmds:
            commands_text += f"**/{cmd_name}**\n"
            commands_text += f"↳ {desc}\n"
            commands_text += f"↳ Usage: `{usage}`\n\n"
        
        embed.add_field(
            name=category,
            value=commands_text,
            inline=False
        )

    embed.set_footer(text="Need help? Join our support server!")
    await ctx.respond(embed=embed)

@bot.slash_command(name="servertotal", description="View total server word count")
async def servertotal_command(ctx: discord.ApplicationContext):
    server_total = bot.db.get_server_total()
    total_writers = len(bot.db.get_all_writers())
    
    embed = discord.Embed(
        title="📚 Server Writing Progress",
        color=discord.Color.blue()
    )
    
    embed.add_field(
        name="📊 Total Words",
        value=f"**{server_total:,}** words written",
        inline=False
    )
    
    embed.add_field(
        name="✍️ Active Writers",
        value=f"**{total_writers}** writers contributing",
        inline=False
    )
    
    if server_total > 0 and total_writers > 0:
        avg_per_writer = server_total // total_writers
        embed.add_field(
            name="📈 Average per Writer",
            value=f"**{avg_per_writer:,}** words",
            inline=False
        )
    
    embed.set_footer(text="Keep writing and watch these numbers grow!")
    await ctx.respond(embed=embed)

@bot.slash_command(name="getwordc", description="Get a user's word count")
async def getwordc_command(ctx: discord.ApplicationContext, user: discord.User=None):
    if user is None:
        user = ctx.user
    
    word_count = bot.db.get_wordcount(str(user.id))
    
    embed = discord.Embed(
        title="📖 Writer Stats",
        color=discord.Color.blue()
    )
    
    embed.add_field(
        name="👤 Writer",
        value=user.mention,
        inline=True
    )
    
    embed.add_field(
        name="📝 Total Words",
        value=f"**{word_count:,}** words",
        inline=True
    )
    
    # Get position on leaderboard
    leaderboard = bot.db.get_leaderboard()
    position = next((i for i, (uid, _, _) in enumerate(leaderboard, 1) 
                    if uid == str(user.id)), None)
    
    if position:
        embed.add_field(
            name="🏆 Ranking",
            value=f"#{position} on leaderboard",
            inline=True
        )
    
    embed.set_thumbnail(url=user.display_avatar.url)
    await ctx.respond(embed=embed)

bot.run(bot.config["BOT_TOKEN"])
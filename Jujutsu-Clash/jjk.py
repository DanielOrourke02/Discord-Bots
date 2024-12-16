import discord
from discord.ext import commands, tasks
import random
import aiohttp
import datetime

BUG_REPORT_CHANNEL_ID = 1234
USER_REPORT_CHANNEL_ID = 1234
ANIME_QUESTION_CHANNEL_ID = 1234

intents = discord.Intents.default()
intents.messages = True

class AnimeBot(discord.Bot):
    def __init__(self):
        super().__init__(intents=intents)
        self.start_time = datetime.datetime.utcnow()

    def get_uptime(self):
        delta = datetime.datetime.utcnow() - self.start_time
        days = delta.days
        hours, remainder = divmod(delta.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{days}d {hours}h {minutes}m {seconds}s"

bot = AnimeBot()

@bot.event
async def on_ready():
    print(f"╔{'═' * 50}╗")
    print(f"║ {bot.user.name} is Ready!{' ' * (50 - len(bot.user.name) - 11)}║")
    print(f"║ Serving {len(bot.guilds)} servers{' ' * (50 - len(str(len(bot.guilds))) - 15)}║")
    print(f"╚{'═' * 50}╝")
    
    post_anime_question.start()
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="anime | /help"
        )
    )

@bot.event
async def on_application_command_error(ctx, error: discord.DiscordException):
    if isinstance(error, commands.CommandOnCooldown):
        embed = discord.Embed(
            description=f"<a:denied:1300812792085090435> {error}",
            color=discord.Color.red()
        )
        await ctx.respond(embed=embed)
    else:
        raise error

@bot.slash_command(name="ping", description="Check the bot's latency")
@commands.cooldown(1, 4, commands.BucketType.user)
async def ping(ctx: discord.ApplicationContext):
    latency = round(bot.latency * 1000)
    embed = discord.Embed(
        title="🏓 Pong!",
        description=f"**Latency:** {latency} ms\n**API Latency:** {round(ctx.bot.latency * 1000)} ms",
        color=discord.Color.green()
    )
    embed.set_footer(text="🏃‍♂️ Keep up the great work!")
    
    await ctx.respond(embed=embed)

@bot.slash_command(name="info", description="View bot information and statistics")
@commands.cooldown(1, 4, commands.BucketType.user)
async def info(ctx: discord.ApplicationContext):
    embed = discord.Embed(
        title="🤖 Bot Information",
        description="Your friendly anime discussion bot!",
        color=discord.Color.blue(),
        timestamp=datetime.datetime.utcnow()
    )

    # General Stats
    stats = f"""```yml
Servers: {len(bot.guilds)}
Users: {sum(g.member_count for g in bot.guilds)}
Commands: {len(bot.application_commands)}
Uptime: {bot.get_uptime()}```"""

    embed.add_field(
        name="📊 Statistics",
        value=stats,
        inline=False
    )

    # Features
    features = """```yml
• Daily Anime Questions
• Bug Reporting System
• Player Report System
• Quick Response Times
• Admin Controls```"""

    embed.add_field(
        name="✨ Features",
        value=features,
        inline=False
    )

    embed.set_footer(text="Thanks for using our bot! | /help for commands")
    await ctx.respond(embed=embed)

@bot.slash_command(name="bugreport", description="Report a bug")
@commands.cooldown(1, 360, commands.BucketType.user)
async def report_bug(ctx: discord.ApplicationContext, 
                    bug_description: discord.Option(str, "Describe the bug in detail", required=True)): # type: ignore
    bug_report_channel = bot.get_channel(BUG_REPORT_CHANNEL_ID)

    if not bug_report_channel:
        embed = discord.Embed(description="<a:denied:1300812792085090435> Error: Report channel not found", color=discord.Color.red())
        await ctx.respond(embed=embed)
        return

    report_embed = discord.Embed(
        title="🐛 Bug Report",
        color=discord.Color.red(),
        timestamp=datetime.datetime.utcnow()
    )

    report_embed.add_field(
        name="Report Details",
        value=f"""```yml
Reporter: {ctx.author}
User ID: {ctx.author.id}
Server: {ctx.guild.name if ctx.guild else 'DM'}
Time: {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}```""",
        inline=False
    )

    report_embed.add_field(
        name="Bug Description",
        value=f"```{bug_description}```",
        inline=False
    )

    await bug_report_channel.send(embed=report_embed)
    
    confirm_embed = discord.Embed(
        description="<a:checked:1300790851944845377> Bug report submitted successfully!",
        color=discord.Color.green()
    )
    await ctx.respond(embed=confirm_embed)


@bot.slash_command(name="playerreport", description="Report a player")
@commands.cooldown(1, 360, commands.BucketType.user) 
async def player_report(
    ctx: discord.ApplicationContext, 
    user: discord.Option(discord.Member, description="User you wish to report", required=True),  # type: ignore
    report: discord.Option(str, description="Description of the issue", required=True) # type: ignore
): 
    user_report_channel = bot.get_channel(USER_REPORT_CHANNEL_ID)
    
    if not user_report_channel:
        embed = discord.Embed(
            description="<a:denied:1300812792085090435> Player report channel not found.",
            color=discord.Color.red()
        )
        
        await ctx.respond(embed=embed)
        return

    embed = discord.Embed(
        title="🛠️ New Player Report",
        description=f"**Reported User:** {user.mention}\n**Reason:** {report}",
        color=discord.Color.red()
    )
    embed.set_footer(text=f"📮 Reported by: {ctx.author.name}#{ctx.author.discriminator}")

    await user_report_channel.send(embed=embed)
    
    confirmation_embed = discord.Embed(
        description="<a:checked:1300790851944845377> Thank you for your report! Our staff will review it shortly.",
        color=discord.Color.green()
    )
    await ctx.respond(embed=confirmation_embed)

async def fetch_random_anime_question():
    questions = [
        "Who is your favorite character from the anime **{anime_title}**?",
        "What is your favorite moment from **{anime_title}**?",
        "If you could have one power from **{anime_title}**, what would it be?",
        "Which character from **{anime_title}** do you relate to the most?",
        "What do you think about the ending of **{anime_title}**?",
        "If you could change one thing in **{anime_title}**, what would it be?",
        "Which character's journey in **{anime_title}** inspired you the most?",
        "What would you do if you were in the world of **{anime_title}**?",
        "How would you rate **{anime_title}** on a scale of 1 to 10 and why?",
        "Which is your favorite episode of **{anime_title}** and why?",
        "What lesson did you learn from **{anime_title}**?",
        "Who do you think is the strongest character in **{anime_title}**?",
        "If you could be any character from **{anime_title}**, who would it be?",
        "What do you think makes **{anime_title}** unique compared to other anime?",
        "Which character's development did you enjoy the most in **{anime_title}**?",
        "If you could create a spin-off series of **{anime_title}**, what would it be about?",
        "Who do you think had the best character design in **{anime_title}**?",
        "What was your initial impression of **{anime_title}** when you first watched it?",
        "Which relationship in **{anime_title}** do you find the most interesting?",
        "What is your favorite quote from **{anime_title}**?",
        "Which theme in **{anime_title}** resonates with you the most?",
        "If you could rewrite any part of **{anime_title}**, what would you change?",
        "What character do you think deserves more screen time in **{anime_title}**?",
        "What do you think the main message of **{anime_title}** is?",
        "Which fight scene in **{anime_title}** was the most epic?",
        "How do you think **{anime_title}** has influenced the anime industry?",
        "If you could ask any character from **{anime_title}** one question, what would it be?",
        "What is your favorite opening or ending song from **{anime_title}**?",
        "Which character's backstory do you find the most compelling in **{anime_title}**?",
        "If you had to describe **{anime_title}** in three words, what would they be?",
        "What do you think would happen if two characters from **{anime_title}** swapped roles?",
        "Which character's personality do you find the most relatable in **{anime_title}**?",
        "What is one thing you wish you could experience from **{anime_title}**?",
        "Which arc in **{anime_title}** did you enjoy the most?",
        "If you could bring any character from **{anime_title}** to life, who would it be?",
        "What was the biggest twist in **{anime_title}** that surprised you?",
        "Which side character in **{anime_title}** do you think is underrated?",
        "What do you think about the character dynamics in **{anime_title}**?",
        "If you could have a conversation with any character from **{anime_title}**, who would it be?",
        "Which moment in **{anime_title}** made you laugh the most?",
        "If you could live in the world of **{anime_title}**, what would your role be?",
        "Which character from **{anime_title}** would you want as your best friend?",
        "What’s your favorite theory about **{anime_title}**?",
        "What aspect of **{anime_title}** do you think has the best world-building?",
        "How do you think **{anime_title}** portrays friendship?",
        "What do you think is the biggest challenge faced by the main character in **{anime_title}**?",
        "What do you think the future holds for the characters in **{anime_title}**?",
        "Which character's quote has impacted you the most from **{anime_title}**?",
        "If you could change the ending of **{anime_title}**, how would you do it?",
        "What’s the most emotional scene in **{anime_title}** for you?",
        "If you could have any item or weapon from **{anime_title}**, what would it be?",
        "What do you love the most about **{anime_title}**?",
        "Which character's decision in **{anime_title}** do you disagree with the most?",
        "What do you think is the most memorable moment in **{anime_title}**?",
        "Which song would you associate with **{anime_title}**?",
        "What would be your strategy if you were a character in **{anime_title}**?"
    ]

    try:
        async with aiohttp.ClientSession() as session:
            query = '''
            query {
                Page(page: 1, perPage: 50) {  # Increased perPage for more variety
                    media(sort: POPULARITY_DESC, type: ANIME) {
                        title {
                            romaji
                            english
                        }
                    }
                }
            }
            '''
            async with session.post('https://graphql.anilist.co', json={'query': query}) as response:
                data = await response.json()
                anime_list = data['data']['Page']['media']
                
                if not anime_list:
                    return "What is your favorite anime?"  # Fallback question

                # Choose a random anime from the list
                anime = random.choice(anime_list)
                anime_title = anime['title']['romaji']  # Use romaji title
                
                random_question = random.choice(questions)
                return random_question.format(anime_title=anime_title)
    except Exception as e:
        print(f"Error fetching anime question: {e}")
        return "What is your favorite anime?"

@tasks.loop(hours=24)  
async def post_anime_question():
    channel = bot.get_channel(ANIME_QUESTION_CHANNEL_ID)
    if channel:
        question = await fetch_random_anime_question()
        
        embed = discord.Embed(
            title="🎉 Question of the Day! 🎉",
            description=f"🤔 **Here's your anime question:**\n\n{question}",
            color=discord.Color.blue()
        )
        embed.set_footer(text="💬 Share your thoughts in the chat!")
        embed.timestamp = discord.utils.utcnow() 

        await channel.send(embed=embed)


@bot.slash_command(name="send_daily_anime_question", description="Send a new daily anime question (Admin only)")
@commands.has_permissions(administrator=True)
async def send_daily_anime_question(ctx: discord.ApplicationContext):
    question = await fetch_random_anime_question()
    
    embed = discord.Embed(
        title="🎉 New Anime Question! 🎉",
        description=f"🤔 **Here's your anime question:**\n\n{question}",
        color=discord.Color.blue()
    )
    embed.set_footer(text="💬 Share your thoughts in the chat!")
    embed.timestamp = discord.utils.utcnow()

    channel = bot.get_channel(ANIME_QUESTION_CHANNEL_ID)
    if channel:
        await channel.send(embed=embed)
        embed = discord.Embed(
            description="<a:checked:1300790851944845377> The daily anime question has been sent!",
            color=discord.Color.green()
        )
        
        await ctx.respond(embed=embed)
    else:
        embed = discord.Embed(
            description="<a:denied:1300812792085090435> Anime Channel could not be found.",
            color=discord.Color.red()
        )
        
        await ctx.respond(embed=embed)


@bot.slash_command(name="help", description="List all available commands")
@commands.cooldown(1, 4, commands.BucketType.user)
async def help_command(ctx: discord.ApplicationContext):
    embed = discord.Embed(
        title="📚 Command Guide",
        description="Here are all available commands:",
        color=discord.Color.blue()
    )

    general_commands = """```yml
/ping:
  Description: Check bot latency
  Usage: /ping

/info:
  Description: View bot information
  Usage: /info

/help:
  Description: Show this menu
  Usage: /help```"""

    report_commands = """```yml
/bug_report:
  Description: Report a bug
  Usage: /bug_report <description>
  Cooldown: 360s

/player_report:
  Description: Report a player
  Usage: /player_report <user> <reason>
  Cooldown: 360s```"""

    admin_commands = """```yml
/send_daily_anime_question:
  Description: Send anime question
  Usage: /send_daily_anime_question
  Permission: Administrator```"""

    embed.add_field(name="🎮 General Commands", value=general_commands, inline=False)
    embed.add_field(name="🛠️ Report Commands", value=report_commands, inline=False)
    embed.add_field(name="⚡ Admin Commands", value=admin_commands, inline=False)

    embed.set_footer(text="Need help? Contact server staff!")
    await ctx.respond(embed=embed)


bot.run("YOUR_BOT_TOKEN")

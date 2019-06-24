import discord
from discord.ext import commands
from discord.abc import Snowflake, GuildChannel

prefix = "!"
bot = commands.Bot(command_prefix = prefix)

# Initialize global variable for cached invites
cached_invites = {}

async def cache_all_invites():
    '''
    Cache all server invites (on ready)
    '''
    global cached_invites
    cached_invites = {}
    for guild in bot.guilds:
        if guild not in cached_invites:
            cached_invites[guild.id] = []
        try:
            for channel in guild.channels:
                if not isinstance(channel, discord.channel.CategoryChannel):
                    invites = await GuildChannel.invites(channel)
                    cached_invites[guild.id].extend(invites)
        except discord.Forbidden:
            print("Missing manage_guilds perm in {}".format(guild))

async def cache_server_invites(guild: str):
    '''
    Cache the server's invite in which the command was called in
    '''
    cached_invites = []
    try:
        for channel in guild.channels:
            if not isinstance(channel, discord.channel.CategoryChannel):
                invites = await GuildChannel.invites(channel)
                cached_invites.extend(invites)
    except discord.Forbidden:
        print("Missing manage_guilds perm in {}".format(guild))
        raise
    return cached_invites

@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))

    await cache_all_invites()

@bot.event
async def on_member_join(member):
    '''
    Detect which invite was used when a new member joins
    '''
    try:
        updated_invites = await cache_server_invites(member.guild)
        # for invite in updated_invites:
        #     print("updated" + str(invite.uses))
    except discord.Forbidden:
        updated_invites = []
    old_invites = cached_invites[member.guild.id]
    # for invite in old_invites:
    #     print("old" + str(invite.uses))

    for new in updated_invites:
        for old in old_invites:
            if new.id == old.id and new.uses > old.uses:
                print("{} joined using invite {} at {} uses".format(member, new.code, new.uses))



@bot.command()
async def potato(ctx):
    '''
    Manually update this server's invite cache
    '''
    global cached_invites
    try:
        invites = await cache_server_invites(ctx.guild)
        cached_invites[ctx.guild.id] = invites
    except discord.Forbidden:
        await ctx.send("Please give me the manage_guilds permission!")


@bot.command()
async def ppotato(ctx):
    '''
    Print the cached invites to console
    '''
    print(cached_invites)

@bot.command()
async def ping(ctx):
    '''
    This text will be shown in the help command
    '''

    # Get the latency of the bot
    latency = bot.latency  # Included in the Discord.py library
    # Send it to the user
    await ctx.send(latency)

@bot.command()
async def echo(ctx, *, content:str):
    await ctx.send(content)

bot.run('NTc0NjkzMzU5OTM2MDc3ODM5.XM9H_Q.kFaOUpk-nMXmFuIcU4DFyjywoE0')

'''
client = discord.Client()

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('!hello'):
        await message.channel.send('Hello!')



@client.event
async def on_member_join(member):
    print(member.name + " joined")

client.run('NTc0NjkzMzU5OTM2MDc3ODM5.XM9H_Q.kFaOUpk-nMXmFuIcU4DFyjywoE0')
'''
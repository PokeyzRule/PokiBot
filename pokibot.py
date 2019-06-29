import discord
from discord.ext import commands
from discord.abc import Snowflake, GuildChannel
import json

prefix = "!"
bot = commands.Bot(command_prefix = prefix)

with open("token.txt") as file:
    token = file.readline().strip("\n")

# Initialize global variable for cached invites
cached_invites = {}

# Initialize global variable for role to assign for an invite
invite_to_roles = {}

with open("data_file.json") as read_file:
    invite_to_roles = json.load(read_file)
    print(invite_to_roles)

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
        except discord.Forbidden as e:
            print("Missing manage_guilds perm in {}: ".format(guild.name) + str(e))

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
        return

    old_invites = cached_invites[member.guild.id]
    # for invite in old_invites:
    #     print("old" + str(invite.uses))

    for new in updated_invites:
        for old in old_invites:
            if new.id == old.id and new.uses > old.uses:
                print("{} joined {} using invite {} at {} uses".format(member, member.guild, new.code, new.uses))
                if new.code in invite_to_roles[str(member.guild.id)]:
                    try:
                        await member.add_roles(member.guild.get_role(invite_to_roles[str(member.guild.id)][new.code]))
                        return
                    except discord.Forbidden as e:
                        print("Error assigning role: " + str(e))

@bot.command()
async def inviterole(ctx, invite_code: str, *, role_name: str):
    '''
    TODO
    '''

    global invite_to_roles
    
    if ctx.guild.id not in invite_to_roles:
        invite_to_roles[ctx.guild.id] = {}

    role_to_add = discord.utils.get(ctx.guild.roles, name = role_name)
    
    if role_to_add is None:
        message = "Role not found"
        await ctx.send(message)
        return

    invite_to_roles[ctx.guild.id][invite_code] = role_to_add.id

    with open("data_file.json", "w") as write_file:
        json.dump(invite_to_roles, write_file)

    message = "Successfully updated invite code **{}** to apply the role **{}** upon member join!".format(invite_code, role_name)
    await ctx.send(message)

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

bot.run(token)

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

client.run(token)
'''
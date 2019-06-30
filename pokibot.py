import discord
from discord.ext import commands
from discord.abc import Snowflake, GuildChannel
import json

default_prefix = "!"
bot = commands.Bot(command_prefix=default_prefix)

with open("token.txt") as file:
    token = file.readline().strip("\n")

# Initialize global variable for cached invites
cached_invites = {}

# Initialize global variable for role to assign for an invite
invite_to_role = {}

invitefile = "invite_to_role.json"
try:
    with open(invitefile, "r") as read_file:
        invite_to_role = json.load(read_file)
except json.decoder.JSONDecodeError:
    pass


async def cache_server_invites(guild:discord.Guild):
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
        print("Missing manage_guilds perm in {0.name}".format(guild))
        raise
    return cached_invites


@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))

    global cached_invites
    cached_invites = {}
    for guild in bot.guilds:
        print("Caching invites for {}".format(guild.name))
        cached_invites[guild.id] = await cache_server_invites(guild)


@bot.event
async def on_guild_join(guild):
    global cached_invites

    try:
        cached_invites[guild.id] = await cache_server_invites(guild)
    except discord.Forbidden:
        return


@bot.event
async def on_guild_remove(guild):
    global cached_invites
    global invite_to_role

    cached_invites.pop(guild.id)
    invite_to_role.pop(str(guild.id))

    with open(invitefile, "w") as write_file:
        json.dump(invite_to_role, write_file)


@bot.event
async def on_member_join(member):
    '''
    Detect which invite was used when a new member joins
    '''

    global cached_invites
    guild_id = str(member.guild.id)

    old_invites = cached_invites[member.guild.id]

    try:
        cached_invites[member.guild.id] = await cache_server_invites(member.guild)
    except discord.Forbidden:
        return

    for new in cached_invites[member.guild.id]:
        for old in old_invites:
            if new.id == old.id and new.uses > old.uses:
                print("{0} joined {0.guild} using invite {1.code} at {1.uses} uses".format(member, new))
                if new.code in invite_to_role[guild_id]:
                    try:
                        await member.add_roles(member.guild.get_role(invite_to_role[guild_id][new.code]))
                        return
                    except discord.Forbidden as e:
                        print("Error assigning role: " + str(e))


@bot.command()
async def inviterole(ctx, mode:str="list", invite_code:str=None, *, role_name:str=None):
    '''
    Designate a role to be added if a specified invite link is used
    modes: add, remove, list[WIP]

    Example: !inviterole add AbCdEfG role name
    '''

    global invite_to_role
    guild_id = str(ctx.guild.id)
    
    if mode == "add":
        if invite_code == None:
            await ctx.send("Please include an invite code and role name!")
            return
        elif role_name == None:
            await ctx.send("Please include the role name you wish to add!")
            return

        if guild_id not in invite_to_role:
            invite_to_role[guild_id] = {}

        role_to_add = discord.utils.get(ctx.guild.roles, name = role_name)
        
        if role_to_add is None:
            message = "Role not found"
            await ctx.send(message)
            return

        invite_to_role[guild_id][invite_code] = role_to_add.id

        with open(invitefile, "w") as write_file:
            json.dump(invite_to_role, write_file)

        message = "Successfully updated invite code **{}** to apply the role **{}**!".format(invite_code, role_name)
        await ctx.send(message)

    elif mode == "remove":
        if invite_code == None:
            await ctx.send("Please include an invite code!")
            return
        try:
            invite_to_role[guild_id].pop(invite_code)

            with open(invitefile, "w") as write_file:
                json.dump(invite_to_role, write_file)
        except KeyError:
            await ctx.send("Invite code not found in list.")

    elif mode == "list":
        await ctx.send("List feature to be implemented...")

    else:
        await ctx.send("Please provde a valid mode")


bot.run(token)

import discord
from discord.ext import commands
from discord.abc import Snowflake, GuildChannel
import json

prefix = "!"
bot = commands.Bot(command_prefix=prefix)

with open("token.txt") as file:
    token = file.readline().strip("\n")

# Initialize global variable for cached invites
cached_invites = {}

# Initialize global variable for role to assign for an invite
invite_to_roles = {}

invitefile = "invite_to_role.json"
try:
    with open(invitefile, "r") as read_file:
        invite_to_roles = json.load(read_file)
        print(invite_to_roles)
except json.decoder.JSONDecodeError:
    pass

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

async def cache_server_invites(guild:str):
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

    global cached_invites
    guild_id = str(member.guild.id)

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
                if new.code in invite_to_roles[guild_id]:
                    try:
                        await member.add_roles(member.guild.get_role(invite_to_roles[guild_id][new.code]))
                        cached_invites = updated_invites
                        return
                    except discord.Forbidden as e:
                        print("Error assigning role: " + str(e))

@bot.command()
async def inviterole(ctx, mode:str="list", invite_code:str=None, *, role_name:str=None):
    '''
    TODO
    '''

    global invite_to_roles
    guild_id = str(ctx.guild.id)
    
    if mode == "add":
        if invite_code == None:
            await ctx.send("Please include an invite code and role name!")
            return
        elif role_name == None:
            await ctx.send("Please include the role name you wish to add!")
            return

        if guild_id not in invite_to_roles:
            invite_to_roles[guild_id] = {}

        role_to_add = discord.utils.get(ctx.guild.roles, name = role_name)
        
        if role_to_add is None:
            message = "Role not found"
            await ctx.send(message)
            return

        invite_to_roles[guild_id][invite_code] = role_to_add.id

        with open(invitefile, "w") as write_file:
            json.dump(invite_to_roles, write_file)

        message = "Successfully updated invite code **{}** to apply the role **{}**!".format(invite_code, role_name)
        await ctx.send(message)

    elif mode == "remove":
        if invite_code == None:
            await ctx.send("Please include an invite code!")
            return
        try:
            invite_to_roles[guild_id].pop(invite_code)

            with open(invitefile, "w") as write_file:
                json.dump(invite_to_roles, write_file)
        except KeyError:
            await ctx.send("Invite code not found in list.")

    elif mode == "list":
        await ctx.send("To be implemented...")

    else:
        await ctx.send("Please provde a valid mode")

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


bot.run(token)

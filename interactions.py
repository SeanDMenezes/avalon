import discord
import random

token = "NTU3MDQwOTIwNDc5MDA2NzIw.XLvG_w.zK4Bt_VEj5P58O3del5rwm73qP8"
client = discord.ext.commands.Bot(command_prefix="!")

# MESSAGES
commands_cmd = "commands - take a wild guess\n"
avalon = "avalon - enters setup mode\n"
roles = "roles - displays character options for various party sizes\n"
role_cmd = "role [character] - displays role description for 'character'\n"
general = [commands_cmd, avalon, roles, role_cmd]

join = "join - join the party\n"
leave = "leave - leave the party\n"
choices = "choices - choose a different set of characters to play with\n"
current = "current - display current game settings\n"
start = "start - begin the game\n"
save = "save - saves the current state of the game (current players and missions)\n"
load = "load - loads the most recently saved game state\n"
setup_mode = [join, leave, choices, current, start]#, save, load]

history = "history - display past missions\n"
votes = "votes - shows number of approves/disapproves for a mission\n"
in_game = [history, votes]

## ROLE DESCRIPTIONS
roles = {"resistance": "You are part of the Resistance. Lacking any special gifts, you must figure out the roles of other players. If successful on your missions, the spies will try to assassinate Merlin and topple the Resistance. By impersonating Merlin, you can save Avalon.",
          "oberon": "You are a spy. Unlike the other spies however, your role is not known to Merlin, nor the other spies. Use your concealment to your advantage, deceiving Merlin while helping your fellow spies. Conceal your role, and know that you revel in secrecy.",
          "assassin": "You are a spy. It is your role infiltrate the Resistance, gain their trust, and bring their downfall by failing missions. If the Resistance foils your plan, you may redeem yourself by assassinating Merlin. Be warned, assassinating the wrong player results in total defeat.",
          "merlin": "You are part of the Resistance. It is your job to guide the Resistance to victory using your knowledge of the spies’ identities. Be warned, if you do succeed they will attempt to assassinate you. Conceal your role, be as discreet as possible.",
          "morgana": "You are a spy. As an enchantress, it is your job to deceive the Resistance. Percival knows your special role, but does not know if you are Merlin or Morgana. Deduce Percival’s identity, and pretend to be Merlin in order to gain their trust. ",
          "percival": "You are part of the Resistance. you have been gifted knowledge of which players are Merlin and Morgana, but the fates are fickle. You must deduce who has each role, then aide Merlin and impede Morgana. If successful on your missions, the spies will try to assassinate Merlin and topple the Resistance. By impersonating Merlin, you can save Avalon."}

@client.command()
async def role(ctx, char=""):
    if char.lower() not in ["resistance", "oberon", "assassin", "merlin", "percival", "morgana"]:
        await ctx.send("That isn't a valid character.")
        return
    await ctx.send(roles[char.lower()])

@client.command()
async def commands(ctx):
    embed=discord.Embed(title="Available Commands",color=0xff8000)
    embed.add_field(name="General", value="".join(general), inline=False)
    embed.add_field(name="Setup Mode", value="".join(setup_mode), inline=False)
    embed.add_field(name="In Game", value="".join(in_game), inline=False)
    await ctx.send(embed=embed)

import time
import copy
import random
import discord
from discord.ext import commands
from typing import List
import pickle

import interactions
import characters
from characters import *

client = interactions.client

# GAME CONSTANTS
MISSIONS = {5:[2,3,2,3,3], 6:[2,3,4,3,4], 7:[2,3,3,4,4]}
ROLES = {5:[[Resistance(), Merlin(), Percival(), Morgana(), Assassin()],
            [Resistance(), Merlin(), Percival(), Morgana(), Oberon()]],
        6:[[Resistance(), Resistance(), Merlin(), Percival(), Morgana(), Assassin()],
           [Resistance(), Resistance(), Merlin(), Percival(), Morgana(), Oberon()]]}

# EMOJIS
PASS = '\U00002705'
FAIL = '\U0000274C'
LETTER_A = '\U0001F1E6'
LETTER_B = '\U0001F1E7'
LETTER_C = '\U0001F1E8'
LETTER_D = '\U0001F1E9'
LETTER_E = '\U0001F1EA'
LETTER_F = '\U0001F1EB'
LETTER_G = '\U0001F1EC'
LETTERS = [LETTER_A, LETTER_B, LETTER_C, LETTER_D, LETTER_E, LETTER_F, LETTER_G]

class Player:
    def __init__(self, name: discord.user, role=None):
        self.name = name
        self.role = role
    def __eq__(self, other):
        return self.name == other.name
    def __repr__(self):
        return self.name.mention
    def pickle(self):
        return self.name.mention
    async def unpickle(self, ctx, val):
        self.name = await commands.UserConverter().convert(ctx, val)

class Mission:
    def __init__(self, participants: List[Player], num_pass=0, num_fail=0):
        self.participants = participants
        self.num_pass = num_pass
        self.num_fail = num_fail

    def __repr__(self):
        on_mission = ""
        for p in self.participants:
            on_mission += " {0}".format(p.name.mention)
        rv = on_mission + "- {0} passes, {1} fails.".format(self.num_pass, self.num_fail)
        return rv

    def pickle(self):
        pickled_players = []
        for p in self.participants:
            pickled_players.append(p.pickle())
        return (pickled_players, self.num_pass, self.num_fail)

    async def unpickle(self, ctx, val):
        new_players = []
        for p in val[0]:
            temp = Player(ctx.author)
            await temp.unpickle(ctx, p)
            new_players.append(temp)
        self.participants = new_players
        self.num_pass = val[1]
        self.num_fail = val[2]

class Game:
    # Game is a listof Players, listof Roles, list of Missions, discord user for lotl in game or not
    def __init__(self, players=[], roles=[], missions=[], lotl=None):
        '''
        players: list(Player), roles: list(Character), missions: list(Mission) 

        '''
        self.players = players
        self.roles = roles
        self.missions = missions
        self.lotl = lotl
    
    def __repr__(self):
        if len(self.players) == 0:
            return "Nobody has joined yet!"
        rv = "Players: "
        for p in self.players:
            rv += repr(p) + " "
        rv += "\nRoles: "
        for r in self.roles:
            rv += "{0} ".format(r)
        return rv

    def pickle(self): # just pickles players for now
        pickled_players = []
        for p in self.players:
            pickled_players.append(p.pickle())
        pickled_missions = []
        for m in self.missions:
            pickled_missions.append(m.pickle())
        return (pickled_players, pickled_missions)
    
    async def unpickle(self, ctx, val):
        new_players = []
        new_missions = []
        for p in val[0]:
            temp = Player(ctx.author)
            await temp.unpickle(ctx, p)
            new_players.append(temp)
        for m in val[1]:
            temp = Mission([])
            await temp.unpickle(ctx, m)
            new_missions.append(temp)
        self.players = new_players
        self.missions = new_missions

@client.event
async def on_ready():
    print("Logged in")
    game = discord.Game("Avalon")
    await client.change_presence(status=discord.Status.online,activity=game)

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    await client.process_commands(message)


# HELPERS FOR IN GAME
# Choosing players for a mission and Merlin pick for Assassin
async def choose_players(ctx, players, chosen, num_needed):
    def check(reaction, user):
        msg.reactions = reaction.message.reactions
        return str(reaction.emoji) in LETTERS and reaction.message.id == msg.id

    ppl = discord.Embed(title="Your Choices", color=0xff8000)
    ppl_dict = {}
    for i in range(len(players)):
        ppl.add_field(name=LETTERS[i], value="Choose " +players[i].name.mention, inline=False)
        ppl_dict[LETTERS[i]] = players[i]
    msg = await chosen.name.send(embed=ppl)
    for i in range(len(players)):
        await msg.add_reaction(LETTERS[i])
    
    count = 0
    while count != (len(players) + num_needed):
        await client.wait_for('reaction_add', check=check)
        temp = [react.count for react in msg.reactions if react.emoji in LETTERS]
        count = sum(temp)
    on_mission = []
    for react in msg.reactions:
        if react.count == 2:
            on_mission.append(ppl_dict[react.emoji])
    return on_mission

# Approve/disapprove a mission
async def approve(ctx, inform, num_ppl):
    @client.command()
    async def votes(ctx):
        ppl = "Approved:"
        for p in passed:
            ppl += " {0}".format(p.mention)
        ppl += "\nDisapproved:"
        for f in failed:
            ppl += " {0}".format(f.mention)
        await ctx.send(ppl)
        

    def check(reaction, user):
        msg.reactions = reaction.message.reactions
        if str(reaction.emoji) in [PASS, FAIL] and reaction.message.id == msg.id:
            if user in voted:
                return False
            if not user.bot: 
                voted.append(user)
                if reaction.emoji == PASS:
                    passed.append(user)
                else:
                    failed.append(user)
            return True

    msg = await ctx.send(embed=inform)
    voted = []
    passed = []
    failed = []
    majority = num_ppl // 2 + 1
    await msg.add_reaction(PASS)
    await msg.add_reaction(FAIL)
    while (len(voted) != num_ppl + 2):
        await client.wait_for('reaction_add', check=check)
        if len(voted) > 0 and not voted[-1].bot:
            await ctx.send("{0} has just voted!".format(voted[-1].mention))
                
        await ctx.send("There are now {0} approves and {1} disapproves.".format(len(passed), len(failed)))
        if len(passed) == majority or len(failed) == majority:
            break
    client.remove_command("votes")
    return len(passed) > len(failed)

# Pass/fail a mission
async def pass_fail(ctx, inform):
    def check(reaction, user):
        msg.reactions = reaction.message.reactions
        return str(reaction.emoji) in [PASS, FAIL] and reaction.message.id == msg.id

    msg = await ctx.send(embed=inform)
    await msg.add_reaction(PASS)
    await msg.add_reaction(FAIL)
    
    count = 0
    p_count = 0
    f_count = 0

    while count != 3:
        await client.wait_for('reaction_add', check=check)
        for react in msg.reactions:
            if react.emoji == PASS: p_count = react.count
            if react.emoji == FAIL: f_count = react.count
        count = p_count + f_count
    return p_count > f_count

# Roles command
@client.command()
async def roles(ctx):
    # dict of list of lists
    embed = discord.Embed(title="Character Options", color=0xff8000)
    for size in ROLES:
        chars = ""
        for role in ROLES[size]:
            for char in role:
                chars += "{0} ".format(char)
            chars += "\n"
        embed.add_field(name="Party size of {0}".format(str(size)),value=chars,inline=False)
    await ctx.send(embed=embed)

# Choosing which selection of characters to play with
async def choose_chars(ctx, num):
    def check(reaction, user):
        msg.reactions = reaction.message.reactions
        return str(reaction.emoji) in LETTERS and reaction.message.id == msg.id

    if num not in [5,6]:
        raise(Exception)

    embed = discord.Embed(title="Character Options for Party of {0}".format(num), color=0xff8000)
    num_options = len(ROLES[num])
    for i in range(num_options):
        chars = ""
        for char in ROLES[num][i]:
            chars += "{0} ".format(char)
        embed.add_field(name=LETTERS[i], value=chars, inline=False)

    msg = await ctx.send(embed=embed)
    for i in range(num_options):
        await msg.add_reaction(LETTERS[i])
    count = 0
    while count != num_options + 1:
        await client.wait_for('reaction_add', check=check)
        temp = [react.count for react in msg.reactions if react.emoji in LETTERS]
        count = sum(temp)
    for react in msg.reactions:
        if react.count == 2:
            return LETTERS.index(react.emoji)
    raise(Exception("can't find react"))
            
# SETUP MODE
@client.command()
async def avalon(ctx):
    await setup(ctx)

ROLE_CHOICE = 0
async def setup(ctx, g=Game()):
    ''' enters setup mode'''
    for cmd in ["join", "leave", "current", "save", "load", "start", "choices", "lotl"]:
        client.remove_command(cmd)
    # handle multiple instances of game
    global ROLE_CHOICE
    og = ctx
    await og.send("Welcome to Avalon. Join the party to be included in the next game.")

    def update_roles():
        try:
            g.roles = ROLES[len(g.players)][ROLE_CHOICE]
        except:
            print("Not supported for that many ppl")
            
    @client.command()
    async def join(ctx):
        ''' joins the party '''
        if Player(ctx.author) in g.players:
            await og.send("{0} is already in the party.".format(ctx.author.mention))
        else:
            g.players.append(Player(ctx.author))
            await og.send("{0} successfully joined the party.".format(ctx.author.mention))
            ROLE_CHOICE = 0
            update_roles()
    
    @client.command()
    async def leave(ctx):
        try: 
            g.players.remove(Player(ctx.author))
            await og.send("{0} successfully left the party.".format(ctx.author.mention))
            update_roles()
        except: 
            await og.send("{0} is not in the party.".format(ctx.author.mention))
    
    @client.command()
    async def choices(ctx):
        global ROLE_CHOICE
        if len(g.players) < 5:
            await og.send("Not enough players to choose characters yet.")
            return
        try:
            ROLE_CHOICE = await choose_chars(ctx, len(g.players))
            await og.send("Switched to option {0}".format(LETTERS[ROLE_CHOICE]))
            update_roles()
        except:
            print("Something went wrong")

    #@client.command()
    async def lotl(ctx):
        if g.lotl == None:
            g.lotl = ctx.author
        else:
            g.lotl = None

    @client.command()
    async def current(ctx):
        await og.send(repr(g))
        if g.lotl == None:
            await og.send("Lady of the Lake is not in the game.")
        else:
            await og.send("Lady of the Lake is in the game.")

    #@client.command()
    async def save(ctx):
        pickle.dump(g.pickle(), open("savefile.txt", "wb"))
        await ctx.send("Save successful.")
    
    #@client.command()
    async def load(ctx):
        try:
            await g.unpickle(ctx, pickle.load(open("savefile.txt", "rb")))
            update_roles()
            await ctx.send("Load successful.")
            # if len(g.missions) > 0:
            #     await ctx.send("Continuing game at mission {0}".format(len(g.missions)))
            #     await play(g, ctx)
        except:
            await ctx.send("Load unsuccessful.")

    @client.command()
    async def start(ctx):
        if len(g.players) < 5:
            await og.send("Not enough players to start the game!")
            return

        spies = []
        rez = []
        role_temp = copy.deepcopy(g.roles)
        for p in g.players:
            role = random.choice(role_temp)
            role.name = p.name
            p.role = role
            role_temp.remove(role)
            if role.allegiance == "spy":
                spies.append([p.name, str(p.role)])
            else:
                rez.append([p.name, str(p.role)])
            await p.name.send("Your role is {0}.".format(p.role))
        for p in g.players:
            p.role.spies = spies
            p.role.rez = rez
        for p in g.players:
            await p.name.send(p.role.display_message())
        await og.send("Starting the game")
        for cmd in ["join", "leave", "current", "save", "load", "start", "choices", "lotl"]:
            client.remove_command(cmd)
        await play(g, ctx)
        

# ACTUAL GAME
async def play(g: Game, ctx):
    @client.command()
    async def reset(ctx):
        await ctx.send("exiting game...")
        game = False

    @client.command()
    async def history(ctx):
        if len(g.missions) == 0:
            await ctx.send("No missions yet!")
            return
        for i in range(len(g.missions)):
            await ctx.send("MISSION {0}: {1}".format(i + 1, repr(g.missions[i])))

    def save():
        pickle.dump(g.pickle(), open("savefile.txt", "wb"))

    def next_player(prev):
        last = len(g.players) - 1
        try: 
            ind = g.players.index(prev)
            return g.players[0] if ind == last else g.players[ind + 1]
        except:
            print("Something went terribly wrong...")

    m_list = MISSIONS[len(g.players)]
    m_num = len(g.missions)
    consec_disapproves = 0
    failure = len(list(filter(lambda x: x.num_fail > 0, g.missions)))
    success = len(g.missions) - failure
    game = True
    chosen = random.choice(g.players)
    #chosen = Player(ctx.author)

    while m_num <= 4 and success < 3 and failure < 3 and game:
        if consec_disapproves == 5:
            break
        elif consec_disapproves >= 1:
            await ctx.send("There are now {0} disapproved missions in a row.".format(consec_disapproves))

        # choosing ppl to go on mission
        await ctx.send("{0}, select {1} people to go on the mission.".format(chosen.name.mention, m_list[m_num]))
        on_mission = await choose_players(ctx, g.players, chosen, m_list[m_num])

        # approve or disapprove of these choices
        desc = "{0} has chosen the following people for this mission:\n\nON MISSION\n".format(chosen.name.mention)
        for p in on_mission:
            desc += "{0}\n".format(p.name.mention)
        desc += "\nReact {0} to approve this mission.\nReact {1} to disapprove this mission.".format(PASS,FAIL)
        inform = discord.Embed(title="Approve/Disapprove", description=desc, color=0xff8000)
        results = await approve(ctx, inform, len(g.players)) # NEED TO HANDLE MULTIPLE VOTES FROM SAME PERSON

        # results true iff approves > disapproves
        if not results: # MISSION DISAPPROVED
            await ctx.send("Mission disapproved!")
            consec_disapproves += 1
            chosen = next_player(chosen)
            continue
        # MISSION APPROVED
        # PPL ON MISSION CAN PASS OR FAIL
        await ctx.send("Mission approved!")
        consec_disapproves = 0
        pass_count = 0
        fail_count = 0
        for p in on_mission:
            desc = "React {0} if you'd like to pass the mission.\n".format(PASS)
            desc += "React {0} if you'd like to fail the mission.".format(FAIL)
            inform = discord.Embed(title="Pass/Fail", description=desc, color=0xff8000)
            if await pass_fail(p.name, inform):
                pass_count += 1
                await p.name.send("Pass received.")
            else:
                fail_count += 1
                await p.name.send("Fail received.")
        # depends on number of ppl and mission number*****
        # INTERPRET RESULTS, UPDATE VALUES
        if fail_count > 0:
            if fail_count > 1: await ctx.send("Mission failed! {0} people failed that mission!".format(fail_count))
            else: await ctx.send("Mission failed! {0} person failed that mission!".format(fail_count))
            failure += 1
        else:
            await ctx.send("Mission passed!")
            success += 1
        await ctx.send("There are now {0} successful mission(s) and {1} failed mission(s)."
                           .format(success,failure))
        g.missions.append(Mission(on_mission, pass_count, fail_count))

        # UPDATE VARS
        m_num += 1
        chosen = next_player(chosen)
        # save()
        # END OF ROUND

    # END OF GAME
    spies = g.players[0].role.spies
    rez = g.players[0].role.rez
    for r in rez:
        if r[1] == "Oberon":
            spies.append(r)
            rez.remove(r)
    for p in g.players:
        if p.role in ["Assassin", "Oberon"]:
            assassin = p
        elif p.role == "Merlin":
            merl = p
    sps = "The spies were "
    for s in spies:
        sps += "{0} ".format(s[0].mention)
    sps += "."

    if consec_disapproves == 5:
        await ctx.send("There were 5 consecutive disapproves. Spies win!")
        await ctx.send(sps)
    elif success == 3: # resistance wins
        # assassination attempt
        await ctx.send("3 missions have succeeded! The spies now get a chance to assassinate Merlin.")
        await ctx.send(sps + " {0} gets the final decision.".format(assassin))
        rez_list = list(map(lambda x: Player(x[0]), rez))
        selection = await choose_players(ctx, rez_list, assassin, 1)
        await ctx.send("The spies have chosen {0}...".format(selection[0].name.mention))
        time.sleep(2)
        if selection[0].name == merl.name:
            await ctx.send("Correct! Spies win!")
        else:
            await ctx.send("Incorrect, {0} was Merlin. Resistance wins!".format(merl.name.mention))
    else:
        await ctx.send("3 missions have failed! The spies win!")
        await ctx.send(sps)

    g.missions = []
    client.remove_command("history")
    client.remove_command("reset")
    await setup(ctx, g)
    

client.run(interactions.token)

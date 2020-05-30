import sys
import asyncio
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
setup_commands = ["join", "leave", "current", "save", "load", "start", "choices",\
                  "lotl", "spectate", "spectators", "clear"]

# GAME CONSTANTS
MISSIONS = {5:[2,3,2,3,3], 6:[2,3,4,3,4], 7:[2,3,3,4,4]}
ROLES = {5:[[Resistance(), Merlin(), Percival(), Morgana(), Assassin()],
            [Resistance(), Merlin(), Percival(), Morgana(), Oberon()],
            [Resistance(), Resistance(), Merlin(), Assassin(), Spy()]],
        6:[[Resistance(), Resistance(), Merlin(), Percival(), Morgana(), Assassin()],
           [Resistance(), Resistance(), Merlin(), Percival(), Morgana(), Oberon()],
           [Resistance(), Resistance(), Resistance(), Merlin(), Assassin(), Spy()]],
        7: [[Resistance(), Resistance(), Merlin(), Percival(), Morgana(), Oberon(), Assassin()],
            [Resistance(), Resistance(), Resistance(), Merlin(), Assassin(), Spy(), Spy()],
            [Resistance(), Resistance(), Percival(), Merlin(), Assassin(), Morgana(), Spy()]]}

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
LETTER_H = '\U0001F1ED'
LETTERS = [LETTER_A, LETTER_B, LETTER_C, LETTER_D, LETTER_E, LETTER_F, LETTER_G, LETTER_H]

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
        players: list(Player), roles: list(Character), missions: list(Mission), lotl: Lady 

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
        return pickled_players
    
    async def unpickle(self, ctx, val):
        new_players = []
        for p in val:
            temp = Player(ctx.author)
            await temp.unpickle(ctx, p)
            new_players.append(temp)
        self.players = new_players

@client.event
async def on_ready():
    print("Logged in")
    game = discord.Game("Avalon")
    await client.change_presence(status=discord.Status.online, activity=game)

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
    while (len(voted) != num_ppl):
        await client.wait_for('reaction_add', check=check)
        if len(voted) > 0 and not voted[-1].bot:
            await ctx.send("{0} has just voted!".format(voted[-1].mention))
                
        await ctx.send("There are now {0} approves and {1} disapproves.".format(len(passed), len(failed)))
        if len(passed) == majority or len(failed) == majority or len(voted) == num_ppl:
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

    if num not in [5,6,7]:
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

# choosing which LOTL option to use
async def choose_lotl(ctx):
    def check(reaction, user):
        msg.reactions = reaction.message.reactions
        return str(reaction.emoji) in LETTERS and reaction.message.id == msg.id

    embed = discord.Embed(title="Lady of the Lake Options", color=0xff8000)
    ladies = [RegularLOTL(ctx.author), ParodyLOTL(ctx.author), ClebLOTL(ctx.author), "None"]
    num_options = len(ladies)
    for i in range(num_options):
        embed.add_field(name=LETTERS[i], value=ladies[i], inline=False)

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
            ind = LETTERS.index(react.emoji)
            return ladies[ind]
    raise(Exception("can't find react"))
            
# SETUP MODE
@client.command()
async def avalon(ctx):
    await setup(ctx)

ROLE_CHOICE = 0
async def setup(ctx, g=Game(), spec=[]):

    def update_roles():
        try:
            g.roles = ROLES[len(g.players)][ROLE_CHOICE]
        except:
            print("Not supported for that many ppl")
    
    def clear_commands():
        for cmd in setup_commands:
            client.remove_command(cmd)
    
    def reset():
        global ROLE_CHOICE
        ROLE_CHOICE = 0
        g.lotl = None
        g.players = []
        g.roles = []
        g.missions = []
        spec.clear()
    
    global ROLE_CHOICE
    clear_commands()
    og = ctx
    await og.send("Welcome to Avalon. Join the party to be included in the next game.")

    
    @client.command()
    async def join(ctx):
        ''' joins the party '''
        if Player(ctx.author) in g.players:
            await og.send("{0} is already in the party.".format(ctx.author.mention))
        elif ctx.author in spec:
            await og.send("{0} is currently spectating, so cannot join the party.".format(ctx.author.mention))
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
    async def spectate(ctx):
        if Player(ctx.author) in g.players:
            await og.send("{0} is currently in the party. Leave the party to spectate the next game.".\
                format(ctx.author.mention))
        elif ctx.author in spec:
            await og.send("{0} successfully left spectate mode.".\
                format(ctx.author.mention))
            spec.remove(ctx.author)
        else:
            await og.send("{0} successfully joined spectate mode.".format(ctx.author.mention))
            spec.append(ctx.author)
        
    
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

    @client.command()
    async def lotl(ctx):
        try:
            choice = await choose_lotl(ctx)
            if choice == "None":
                g.lotl = None
                await og.send("Lady of the Lake is not in the game.")
                return
            else:
                g.lotl = choice
                await og.send("{0} is in the game.".format(g.lotl))
        except:
            print("Lotl something went wrong")

    @client.command()
    async def current(ctx):
        cur = discord.Embed(title="Current Settings", color=0xff8000)
        players = ""
        if len(g.players) == 0:
            players += "Nobody has joined yet!"
        else:
            for p in g.players:
                players += repr(p) + "\n"

        roles = ""
        if len(g.roles) == 0:
            roles += "Roles have not been set yet!"
        else:
            for r in g.roles:
                roles += "{0}\n".format(r)
    
        specs = ""
        if len(spec) == 0:
            specs += "Nobody is currently in spectate mode!"
        else:
            for s in spec:
                specs += s.mention + "\n"
        
        lady = ""
        if g.lotl == None:
            lady += "LOTL is disabled!"
        else:
            lady += str(g.lotl)
        
        cur.add_field(name="Players", value=players, inline=True)
        cur.add_field(name="Roles", value=roles, inline=True)
        cur.add_field(name="Lady of the Lake", value=lady, inline=True)
        cur.add_field(name="Spectators", value=specs, inline=True)
        await og.send(embed=cur)

    @client.command()
    async def spectators(ctx):
        if len(spec) == 0:
            await og.send("Nobody is currently in spectate mode!")
        else:
            msg = "Spectators: "
            for s in spec:
                msg += s.mention + " "
            await og.send(msg)

    @client.command()
    async def save(ctx):
        pickle.dump(g.pickle(), open("savefile.txt", "wb"))
        await ctx.send("Save successful.")
    
    @client.command()
    async def load(ctx):
        try:
            reset()
            await g.unpickle(ctx, pickle.load(open("savefile.txt", "rb")))
            update_roles()
            await ctx.send("Load successful.")
        except:
            await ctx.send("Load unsuccessful.")

    @client.command()
    async def clear(ctx):
        reset()        
        await og.send("{0} has reset all current game settings.".format(ctx.author.mention))
        await og.send("Exiting game...")
        clear_commands()

    @client.command()
    async def start(ctx):
        if len(g.players) < 5:
            await og.send("Not enough players to start the game!")
            return

        spies = []
        rez = []
        role_temp = copy.deepcopy(g.roles)
        random.shuffle(g.players)
        for p in g.players:
            role = random.choice(role_temp)
            role.name = p.name
            p.role = role
            role_temp.remove(role)
            if role.allegiance == "spy":
                spies.append([p.name, str(p.role)])
            else:
                rez.append([p.name, str(p.role)])
        for p in g.players:
            p.role.spies = spies
            p.role.rez = rez

        spec_embed = discord.Embed(title="Spectator Mode", color=0xff8000)
        spec_msg = ""
        for p in g.players:
            spec_msg += p.name.mention + ": " + str(p.role) + "\n"

            player_msg = "Your role is {0}.\n".format(p.role)
            temp = p.role.display_message()
            player_embed = discord.Embed(title=player_msg, description=temp, color=0xff8000)
            player_embed.set_image(url=p.role.url)
            await p.name.send(embed=player_embed)

        spec_embed.add_field(name="Roles", value=spec_msg, inline=False)
        
        for s in spec:
            await s.send(embed=spec_embed)
                
        await og.send("Starting the game...")
        clear_commands()
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
        msg = ""
        for i in range(len(g.missions)):
            msg += "MISSION {0}: {1}\n".format(i + 1, repr(g.missions[i]))
        embed = discord.Embed(title="Mission History", description=msg, color=0xff8000)
        await ctx.send(embed=embed)

    async def disapproved(ctx):
        pass


    def save():
        pickle.dump(g.pickle(), open("savefile.txt", "wb"))

    def next_player(prev):
        last = len(g.players) - 1
        try: 
            ind = g.players.index(prev)
            return g.players[0] if ind == last else g.players[ind + 1]
        except:
            print("Something went terribly wrong...")

    # INITIALIZE GAME VARIABLES
    m_list = MISSIONS[len(g.players)]
    m_num = len(g.missions)
    consec_disapproves = 0
    failure = len(list(filter(lambda x: x.num_fail > 0, g.missions)))
    success = len(g.missions) - failure
    game = True
    chosen = random.choice(g.players)
    #chosen = Player(ctx.author)

    # SET LOTL OWNER
    if g.lotl != None:
        if str(g.lotl) == "ClebLOTL":
            spies = []
            rez = []
            for p in g.players:
                if str(p.role) in ["Oberon", "Assassin", "Morgana"]:
                    spies.append(p)
                else:
                    rez.append(p)

            ind = random.randint(0, 1)
            if ind == 1:
                g.lotl.owner = random.choice(spies)
            else:
                g.lotl.owner = random.choice(rez)
        else:
            g.lotl.owner = next_player(chosen)

        await ctx.send("{0} currently has the Lady of the Lake token".format(g.lotl.owner.name.mention))
    
    # MAIN GAME LOOP
    while m_num <= 4 and success < 3 and failure < 3 and game:
        # LADY OF THE LAKE ON MISSIONS 2, 3 AND 4
        if m_num in [2,3,4] and g.lotl != None and consec_disapproves == 0:
            num_ppl = 2 if str(g.lotl) == "ParodyLOTL" else 1
            await ctx.send("{0} now gets the chance to use the Lady of the Lake token on {1} person/people."\
                .format(g.lotl.owner.name.mention, num_ppl))

            possible = g.players[:]
            possible.remove(g.lotl.owner)
            use_on = await choose_players(ctx, possible, g.lotl.owner, num_ppl) # should be a list of Player
            await g.lotl.owner.name.send(g.lotl.action(use_on))
            recap = "{0} used the Lady of the Lake token on {1}".format(g.lotl.owner.name.mention, \
                                                                        use_on[0].name.mention)
            if str(g.lotl) == "ParodyLOTL": 
                recap += " and {0}.".format(use_on[1].name.mention)
            else:
                recap += "."
            await ctx.send(recap)

            g.lotl.owner = use_on[0]
            await ctx.send("{0} currently has the Lady of the Lake token.".format(g.lotl.owner.name.mention))

        # SPIES WIN IF THERE ARE 5 CONSECUTIVELY DISAPPROVED MISSIONS
        if consec_disapproves == 5:
            break
        elif consec_disapproves >= 1:
            await ctx.send("There are now {0} disapproved missions in a row.".format(consec_disapproves))

        # CHOOSING PPL TO GO ON MISSION
        await ctx.send("{0}, select {1} people to go on the mission.".format(chosen.name.mention, m_list[m_num]))
        on_mission = await choose_players(ctx, g.players, chosen, m_list[m_num])

        # APPROVE OR DISAPPROVE OF THESE CHOICES
        desc = "{0} has chosen the following people for this mission:\n\nON MISSION\n".format(chosen.name.mention)
        for p in on_mission:
            desc += "{0}\n".format(p.name.mention)
        desc += "\nReact {0} to approve this mission.\nReact {1} to disapprove this mission.".format(PASS,FAIL)
        inform = discord.Embed(title="Approve/Disapprove", description=desc, color=0xff8000)
        results = await approve(ctx, inform, len(g.players)) # NEED TO HANDLE MULTIPLE VOTES FROM SAME PERSON

        # RESULTS TRUE IFF APPROVES > DISSAPROVES
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
            if len(g.players) >= 7 and m_num == 3:
                if fail_count >= 2: await ctx.send("Mission failed! {0} people failed that mission!".format(fail_count))
                else: await ctx.send("Mission passed!")

            elif fail_count > 1: await ctx.send("Mission failed! {0} people failed that mission!".format(fail_count))
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
        save()
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

    all_roles = discord.Embed(title="Game Over!", color=0xff8000)
    msg = ""
    for p in g.players:
        msg += p.name.mention + ": " + str(p.role) + "\n"
    all_roles.add_field(name="Roles", value=msg, inline=False)

    sps = "The spies were"
    for i in range(len(spies)):
        if i == len(spies) - 1:
            sps += " and"
        sps += " {0}".format(spies[i][0].mention)
    sps += "."

    # 5 CONSEC DISAPPROVES, SPIES WIN
    if consec_disapproves == 5:
        await ctx.send("There were 5 consecutive disapproves. Spies win!")
    # RESISTANCE WINS
    elif success == 3: # resistance wins
        # ASSASSINATION ATTEMPT
        await ctx.send("3 missions have succeeded! The spies now get a chance to assassinate Merlin.")
        await ctx.send(sps + " {0} gets the final decision.".format(assassin))
        rez_list = list(map(lambda x: Player(x[0]), rez))
        selection = await choose_players(ctx, rez_list, assassin, 1)
        await ctx.send("The spies have chosen {0}...".format(selection[0].name.mention))
        time.sleep(2)
        # SPIES WIN
        if selection[0].name == merl.name:
            await ctx.send("Correct! Spies win!")
        # RESISTANCE WINS
        else:
            await ctx.send("Incorrect, {0} was Merlin. Resistance wins!".format(merl.name.mention))
    # SPIES WIN
    else:
        await ctx.send("3 missions have failed! The spies win!")

    await ctx.send(embed=all_roles)

    g.missions = []
    client.remove_command("history")
    client.remove_command("reset")
    await setup(ctx, g)

client.run(interactions.token)

import random

class Character:
    def __init__(self):
        self.name = None
        self.spies = [] # list of (discord.user, role)
        self.rez = [] # list of (discord.user, role)
        self.url = None
    def __str__(self):
        return self.__class__.__name__
    def __eq__(self, other):
        return str(self) == str(other)


class Resistance(Character):
    def __init__(self):
        super().__init__()
        self.allegiance = "rez"
        self.url = "https://i.imgur.com/1Cc1liX.png"
    
    def display_message(self):
        return "You are part of the Resistance. Your job is to pass 3 out of the 5 possible missions.\n"

class Spy(Character):
    def __init__(self):
        super().__init__()
        self.allegiance = "spy"
        self.url = "https://i.imgur.com/c8uPuTU.png"
    
    def display_message(self):
        other_spies = []
        for s in self.spies:
            if s[0] != self.name:
                other_spies.append(s[0])
        if len(other_spies) == 0:
            return "You are a spy. The other spy/spies are not known to you.\n"
        elif len(other_spies) == 1:
            return "You are a spy. The other spy is {0}.\n".format(other_spies[0].mention)
        else:
            spies = ""
            for s in other_spies:
                spies += "{0} ".format(s.mention)
            return "You are a spy. The other spies are " + spies + ".\n"

class Assassin(Spy):
    def __init__(self):
        super().__init__()
        self.url = "https://i.imgur.com/PPREXAj.png"

    def display_message(self):
        msg = Spy.display_message(self)
        return msg + "You will get a chance to assassinate Merlin at the end of the game."

class Morgana(Spy):
    def __init__(self):
        super().__init__()
        self.url = "https://i.imgur.com/NtzlpDs.png"
    
    def display_message(self):
        msg = Spy.display_message(self)
        return msg + "Deceive Percival by pretending you are Merlin."

class Oberon(Resistance):
    def __init__(self):
        super().__init__()
        self.url = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR7Tw_E5B4txX_7zUPti6bWD7zGEQQ8wmdiVOROwUPkyy4SEQTR&s"
    
    def display_message(self):
        msg = "You are a spy. There are other spies in this game not known to you."
        return msg

class Merlin(Resistance):
    def __init__(self):
        super().__init__()
        self.url = "https://i.imgur.com/j5PRT7G.png"
    
    def display_message(self):
        rv = Resistance.display_message(self)
        rv += "The known spies in this game are: "
        for s in self.spies:
            rv += s[0].mention
            rv += " "
        rv += ". If Oberon is in the game, their identity is still unknown."
        return rv

class Percival(Resistance):
    def __init__(self):
        super().__init__()
        self.url = "https://i.imgur.com/nCNxgKJ.png"
    
    def display_message(self):
        for s in self.spies:
            if s[1] == "Morgana":
                morg = s[0]
        
        for r in self.rez:
            if r[1] == "Merlin":
                merl = r[0]

        x = random.randint(0,1)
        if x == 0:
            return "Keep an eye on {0} and {1}. One of them is Merlin and one of them is Morgana"\
            .format(merl.mention, morg.mention)
        return "Keep an eye on {0} and {1}. One of them is Merlin and one of them is Morgana"\
            .format(morg.mention, merl.mention)

class Lady:
    def __init__(self, owner):
        self.owner = owner
    def __str__(self):
        return self.__class__.__name__
    def action(self, parameter_list):
        raise NotImplementedError

class RegularLOTL(Lady):
    def __init__(self, owner):
        self.owner = owner

    # use_on is a list of Player
    def action(self, use_on):
        if use_on[0].role in ["Oberon", "Morgana", "Assassin"]:
            return "{0} is a Spy.".format(use_on[0].name.mention)
        else:
            return "{0} is on the side of the Resistance.".format(use_on[0].name.mention) 

class ParodyLOTL(Lady):
    def __init__(self, owner):
        self.owner = owner

    def action(self, use_on):
        bad_count = 0
        for p in use_on:
            if p.role in ["Oberon", "Morgana", "Assassin"]:
                bad_count += 1
        if bad_count in [0, 2]:
            return "{0} and {1} are both on the same team.".format(use_on[0].name.mention, use_on[1].name.mention)
        else:
            return "{0} and {1} are on opposite teams.".format(use_on[0].name.mention, use_on[1].name.mention)

class ClebLOTL(RegularLOTL):
    def __init__(self, owner):
        self.owner = owner   


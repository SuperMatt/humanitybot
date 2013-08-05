import re
from datetime import datetime
from datetime import timedelta
import cards
from random import shuffle

def actioner(g, line, username, channel, gamechannel):

    lower = line.lower()

    messages = []

    if g.inprogress:          
        if lower == "start":
            messages.append({"message": "Could not start because game is already in progress", "channel": gamechannel})
    else:
        if lower == "start":
            if len(g.players) >= g.minplayers:
                starttime = datetime.now()
                timetostart = 2
                g.starttime = datetime.now() + timedelta(seconds = timetostart)
                messages.append({"message": "Starting game in %s seconds" % timetostart, "channel": gamechannel})
            else:
                messages.append({"message": "Could not start because there aren't enough players", "channel": gamechannel})


    if lower == "stop":
        stopmessage = g.stop()
        messages.append({"message": stopmessage, "channel": gamechannel})


    elif lower == "gamestatus":
        messages.append({"message": g.inprogress, "channel": gamechannel})

    elif lower == "players":
        if g.players:
            playernames = []
            for player in g.players:
                playernames.append(player.username)
            playerstring = " ".join(playernames)
            messages.append({"message": "Players: %s" % playerstring, "channel": gamechannel})
        else:
            messages.append({"message": "No players have joined the game", "channel": gamechannel})

    elif lower == "join":
        newplayer = g.getPlayerByName(username)
        block = 0
        for player in g.players:
            if username == player.username:
                block = 1
        if block == 1:
            messages.append({"message": "Error, cannot join game, you're already in it", "channel": gamechannel})
        else:
            newPlayer = Player(username)
            g.players.append(newPlayer)
            messages.append({"message": "%s joined the game" %username, "channel": gamechannel})
            g.dealCards()

    # elif lower == "part":
    #     for player in g.players:
    #         if player.username == username:
    #             g.players.remove(player)
    #             messages.append({"message": "%s left the game" %username, "channel": gamechannel})

    elif lower == "czar":
        if g.inprogress:
            messages.append({"message": "The Card Czar is %s" %g.czar.username, "channel": gamechannel})
        else:
            messages.append({"message": "There is no Card Czar yet", "channel": gamechannel})
    elif lower[:5] == "kill ":
        messages.append({"message": "DIE %s DIE!" % line[5:].upper(), "channel": gamechannel})

    elif lower == "cards":
        player = g.getPlayerByName(username)
        messages += player.printCards()

    elif lower == "countcards":
        messages.append({"message": "There are %s cards remaining" % len(g.wcards), "channel": gamechannel})

    elif lower == "$playedcards":
        messages.append({"message": g.playedCards, "channel": channel})

    elif lower == "scores":
        messages.append({"message": "The scores are as follows:", "channel": channel})
        for player in g.players:
            messages.append({"message": "%s: %s" %(player.username, player.score), "channel": channel})

    elif lower == "test":
        messages.append({"message": "testing functions", "channel": gamechannel})
    elif lower == "wcards":
        print g.wcards
    elif lower == "bcards":
        print g.bcards
    elif lower == "bcards2":
        print g.bcards2


    return messages

def gameLogic(g, line, username, channel, gamechannel):
    if line:
        lower = line.lower()
    messages = []

    if len(g.players) < g.minplayers:
        if g.starttime or g.inprogress:
            g.stop()


    if g.starttime:
        currtime = datetime.now()
        if currtime > g.starttime:
            g.starttime = None
            g.inprogress = True
            messages.append({"message": "Starting game now!", "channel": gamechannel})

    elif g.newround > g.round:
        if not g.czar:
            g.czar = g.players[0]
        mess = "Starting round %s" % g.newround
        g.round = g.newround
        messages.append({"message": "Starting round %s. The Card Czar is %s" %(g.newround, g.czar.username), "channel": gamechannel})
        g.dealCards()
        g.blackcard = g.bcards.pop(0)
        for player in g.players:
            if not g.czar == player:
                messages += [{"message": g.blackcard, "channel": player.username}]
                messages += player.printCards()
        messages.append({"message": g.blackcard, "channel": gamechannel})
        g.waitPlayers = 1

    elif g.waitPlayers > 0:
        #print g.playedCards
        if g.waitPlayers == 1:
            messages.append({"message": "The Players must each pick a card, by messaging the number to humanitybot", "channel": gamechannel})
            g.waitPlayers = 2
        if len(g.playedCards) == len(g.players) - 1:
            g.waitPlayers = 0
            g.waitCzar = 1
        elif line:
            if re.search("^[0-9]+$", line) and not username == g.czar.username:
                id = int(line)
                print id
                if id == 0:
                    id = 10
                id -= 1
                if id < 10 and id >= 0:
                    player = g.getPlayerByName(username)
                    card = player.hand.pop(id)
                    g.playedCards.append({"card": card, "owner": player})
    elif g.waitCzar > 0:
        if g.waitCzar == 1:
            shuffle(g.playedCards)
            messages.append({"message": "The Czar, %s, must pick a card" % g.czar.username, "channel": gamechannel})
            messages.append({"message": g.blackcard, "channel": gamechannel})
            i = 1
            spacer = "  "
            for card in g.playedCards:
                if i > 9:
                    spacer = " "
                messages.append({"message": "%s)%s%s" %(i, spacer, card["card"]),"channel": gamechannel})
                i += 1
            g.waitCzar = 2
        elif line and g.waitCzar == 2:
            if re.search("^[0-9]+$", line) and username == g.czar.username:
                cardID = int(line) - 1
                if cardID < len(g.playedCards) and cardID >= 0:
                    cardText = g.playedCards[cardID]["card"]
                    cardOwner = g.playedCards[cardID]["owner"]
                    messages.append({"message": "The Czar picked card %s: %s %s has won the round!" %(cardID + 1, cardText, cardOwner.username), "channel": gamechannel})
                    cardOwner.score += 1
                    g.waitCzar = 0
                    g.newround += 1
                    g.playedCards = []
                    i = 0
                    for player in g.players:
                        if player == g.czar:
                            czarid = i
                        i += 1
                    czarid +=1
                    if czarid > len(g.players) -1:
                        czarid = 0
                    g.czar = g.players[czarid]

    return messages

class Player():
    def __init__ (self, username):
        self.username = username
        self.hand = []
        self.score = 0

    def printCards(self):
        messages = [{"message": "Your cards are:", "channel": self.username}]
        i = 1
        cards = ""
        for card in self.hand:
            cards += "%s) %s " % (i,card)
            i += 1
        messages.append({"message": cards, "channel": self.username})
        return messages



class Game():
    def __init__(self):
        self.inprogress = False
        self.players = []
        self.starttime = None
        self.inchannel = False
        self.minplayers = 3
        self.round = 0
        self.newround = 1
        self.played = []
        self.czar = None
        self.wcards = cards.wcards()
        self.bcards = cards.bcards()
        self.bcards2 = cards.bcards2()
        self.playedCards = []
        self.blackcard = None
        shuffle(self.wcards)
        shuffle(self.bcards)

    def stop(self):
        self.__init__()
    #    self.inprogress = False
    #    self.starttime = None
    #    self.players = []
    #    self.round = 0
    #    self.czar = 0
    #    self.wcards = cards.wcards()
    #    self.bcards = cards.bcards()
    #    self.bcards2 = cards.bcards2()
    #    self.waitPlayers = 0
    #    self.playedCards = []
    #    self.newround = 1
    #    
    #    shuffle(self.wcards)
        
        return "Stopping game"
    def dealCards(self):
        for player in self.players:
            toDeal = 10 - len(player.hand)
            while toDeal > 0:
                card = self.wcards.pop()
                player.hand.append(card)
                toDeal -= 1

    def getPlayerByName(self, username):
        for player in self.players:
            if player.username == username:
                return player
        return False


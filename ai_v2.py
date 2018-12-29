##version 0.2
import random
import numpy as np
import itertools
import operator
import json



class logger:
    DEBUG = 0
    INFO = 1
    WARNING = 2
    CRITICAL = 3

    @staticmethod
    def log(level,*args):
        if (level > 1):
            print (*args)

class Card:
  RANKS = (2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14)
  #SUITS = ('?', '?', '?', '?')
  SUITS = ('a', 'b', 'c', 'd')

  def __init__ (self, rank, suit):
    self.rank = rank
    self.suit = suit

  def __repr__(self):
    return self.__str__()

  def __str__ (self):
    if self.rank == 14:
      rank = 'A'
    elif self.rank == 13:
      rank = 'K'
    elif self.rank == 12:
      rank = 'Q'
    elif self.rank == 11:
      rank = 'J'
    else:
      rank = self.rank
    return str(rank) + self.suit

  def __eq__ (self, other):
    return (self.rank == other.rank)

  def __ne__ (self, other):
    return (self.rank != other.rank)

  def __lt__ (self, other):
    return (self.rank < other.rank)

  def __le__ (self, other):
    return (self.rank <= other.rank)

  def __gt__ (self, other):
    return (self.rank > other.rank)

  def __ge__ (self, other):
    return (self.rank >= other.rank)

class Dealer:
    def __init__ (self):
        self.deck = []
        for suit in Card.SUITS:
            for rank in Card.RANKS:
                card = Card (rank, suit)
                self.deck.append(card)

    def shuffle (self):
        random.shuffle (self.deck)

    def __len__ (self):
        return len (self.deck)

    def deal(self,count = 1):
        if count == 1:
            return self.deck.pop(0)

        cards = []
        if len(self) >= count:
            for i in range(count):
                cards.append(self.deck.pop(0))
        return cards

class Player:
	id = 0
	money = 0
	cards = []
	dividend = 0
	

	def __init__(self,id):
		self.id = id
		
	def withdrawAllMoneyByLimit(self,limit):
		m = min(self.money,limit)
		self.money -= m
		return m
	def deal(self,cards):
		self.cards = cards
	def getMoney(self):
		return self.money
		
	def setDividends(self,pot):
		self.dividend = pot
		if pot > 0:
			self.money += pot
	def getDividends(self):
		return self.dividend

class Poker:
    HANDS = ('High Card','Pair','Two pair','Three of a kind','Straight','Flush','Full house','Four of a kind','Straight flush','Royal flush')
    FOLD  = 0
    ALLIN = 1
    SBTURN = 0
    BBTURN = 1
    ENDROUND = 2
    GAMEOVER = 3
    TOTAL_ENTRYBET = 1.5

    def __init__(self):
        self.players = []

	##control the game
    def addPlayer(self):
        id = len(self.players)
        self.players.append(Player(id))
        return id

    def reset(self):
        for player in self.players:
            player.money = 10

        self._isFinishRound  = False
        self.sb = 0
        self.bb = 1
        self.roundWinners = []

    def deal(self):
        self.dealer = Dealer()
        self.dealer.shuffle()
        self.sb = (self.sb +1) % len(self.players)
        self.bb = (self.sb +1) % len(self.players)
        self.effetivePot = min(self.players[0].getMoney(),self.players[1].getMoney())

        self.pot = self.players[self.sb].withdrawAllMoneyByLimit(0.5) + self.players[self.bb].withdrawAllMoneyByLimit(1.0)
        self.players[self.sb].deal(sorted(self.dealer.deal(2), key=operator.attrgetter('rank')) )
        self.players[self.bb].deal(sorted(self.dealer.deal(2), key=operator.attrgetter('rank')) )
        logger.log(logger.INFO,"player 1: ", self.players[0].cards)        
        logger.log(logger.INFO,"player 2: ", self.players[1].cards)     
        self._gameState = 0
        self.winnersIDs = []
        

    def setAction(self,action):
        if (self._gameState == Poker.SBTURN):
            if (action == Poker.FOLD):
                self.winnersIDs = [self.bb]
                logger.log(logger.INFO,"state 0: player",self.sb,"folds")
                self.setEndStatus() 
            elif (action == Poker.ALLIN):
                self.pot += self.players[self.sb].withdrawAllMoneyByLimit(self.players[self.bb].getMoney())
                logger.log(logger.INFO,"state 0:  player",self.sb,"allin")
                self._gameState = Poker.BBTURN
            else:
                logger.log(logger.INFO,'Unknown action... try again. pot: ' + str(self.pot))
        elif (self._gameState == Poker.BBTURN):
            if (action == Poker.FOLD):
                self.winnersIDs = [self.sb]
                logger.log(logger.INFO,"state 1:  player",self.bb,"folds")
                self.setEndStatus()
            elif (action == Poker.ALLIN):
                self.pot += self.players[self.bb].withdrawAllMoneyByLimit(self.pot - Poker.TOTAL_ENTRYBET)
                self.showDown()
                logger.log(logger.INFO,"state 1:  player",self.bb,"all in")
                self.setEndStatus()
            else:
                logger.log(logger.CRITICAL,'Unknown action... try again. pot: ')
        else:
            logger.log(logger.CRITICAL,'Unknown action... try again. pot: ')

	###internal functions#####
    def setEndStatus(self):


        if len(self.winnersIDs) == self.getPlayersCount():
            self.players[0].setDividends(self.pot / 2)
            self.players[1].setDividends(self.pot / 2)
        elif self.winnersIDs[0] == 0:
            self.players[0].setDividends(self.pot)
            self.players[1].setDividends(-self.pot)
        elif self.winnersIDs[0] == 1:
            self.players[0].setDividends(-self.pot)
            self.players[1].setDividends(self.pot)
        else:
            raise Exception("very bad for you")

        if self.players[self.bb].getMoney() < 0.5 or self.players[self.sb].getMoney() < 1.0:
            self._gameState = Poker.GAMEOVER
        else:
            self._gameState = Poker.ENDROUND

        #logger.log(1,"winner",self.winnersIDs,self.players[self.bb].getMoney(),self.players[self.sb].getMoney())
        self.roundWinners.append(self.winnersIDs)

    def showDown(self):
        flop = self.dealer.deal(5)
        sbhand,sbscore,sbrank = self.getBestHandByScore(flop + self.players[self.sb].cards)
        bbhand,bbscore,bbrank = self.getBestHandByScore(flop + self.players[self.bb].cards)

        if (sbscore > bbscore):
            self.winnersIDs =  [self.sb]
        elif (sbscore < bbscore):
            self.winnersIDs = [self.bb]
        else:
            self.winnersIDs = [self.sb,self.bb]

	##get game info
    def getplayerIDTurn(self):
        if (self._gameState == Poker.BBTURN):
            return self.bb
        else:
            return self.sb

    def getPlayersCount(self):
        return len(self.players)

    def printStatus(self):
        logger.log(logger.INFO,"gameover",self.roundWinners)

    def getPot(self):
        return self.pot

    def getWinnerIDs(self):
        return self.winnersIDs

    def getPlayerState(self,id):
        return (self.players[id].cards,self.sb == id,self.players[id].getMoney())

    def isRoundFinished(self):
        return self._gameState == Poker.ENDROUND

    def isGameover(self):
        return self._gameState == Poker.GAMEOVER

    def getRoundDividends(self,id):
        return self.players[id].getDividends()

    def getBestHandByScore(self,largehand):
        hands = list(itertools.combinations(largehand,5))
        scores = []
        ranks = []
        for hand in hands:
            rank,score = self.getHandScore(hand)
            scores.append(score)
            ranks.append(rank)
        index = scores.index(max(scores))
        return hands[index],scores[index],ranks[index]

    def getHandScore(self,hand):
        sortedHand=sorted(hand,reverse=True)
        ranksCount = {}
        for card in sortedHand:
            if(card.rank not in ranksCount.keys()):
                ranksCount[card.rank] = 0
            ranksCount[card.rank] += 1

        score = self.isRoyal(sortedHand,ranksCount)
        finalscore = 0
        zeroes = 10
        for i in score:
            finalscore += i * (10**zeroes)
            zeroes -= 2

        return (self.HANDS[score[0]],finalscore)

    def isRoyal(self,hand,ranksCount):
        flushSuit = hand[0].suit #d
        currRank = 14
        
        for card in hand:
            if card.suit == flushSuit and card.rank == currRank:
                currRank -= 1
            else:
                return self.isStraightFlush(hand,ranksCount)
        return (9,currRank+1)

    def isStraightFlush(self,hand,ranksCount):
        flushSuit = hand[0].suit #d
        currRank = hand[0].rank #14
        
        for card in hand:
            if card.suit == flushSuit and card.rank == currRank:
                currRank -= 1
            else:
                return self.isFour(hand,ranksCount)
        return (8,currRank+1)

    def isFour(self,hand,ranksCount):
        ranks = list(ranksCount.keys())
        if (ranksCount[ranks[0]] == 4):
            return (7,ranks[0],ranks[1])
        
        if (ranksCount[ranks[1]] == 4):
            return (7,ranks[1],ranks[0])

        return self.isFull(hand,ranksCount)

    def isFull(self,hand,ranksCount):
        ranks =  sorted(ranksCount, key=ranksCount.get,reverse=True)
        if (ranksCount[ranks[0]] == 3 and ranksCount[ranks[1]] == 2):
            return (6,ranks[0],ranks[1])

        return self.isFlush(hand,ranksCount)

    def isFlush(self,hand,ranksCount):
        flushSuit = hand[0].suit #d
        
        for card in hand:
            if card.suit != flushSuit:
                return self.isStraight(hand,ranksCount)

        return (5,hand[0].rank,hand[1].rank,hand[2].rank,hand[3].rank,hand[4].rank)

    def isStraight(self,hand,ranksCount):
        currRank = hand[0].rank
        
        for card in hand:
            if card.rank == currRank:
                currRank -= 1
            else:
                return self.isThree(hand,ranksCount)
        return (4,currRank+1)

    def isThree(self,hand,ranksCount):
        ranks =  sorted(ranksCount, key=ranksCount.get,reverse=True)
        if (ranksCount[ranks[0]] == 3):
            return (3,ranks[0],ranks[1],ranks[2])

        return self.isTwo(hand,ranksCount)
     
    def isTwo(self,hand,ranksCount):
        ranks =  sorted(ranksCount, key=ranksCount.get,reverse=True)
        if (ranksCount[ranks[0]] == 2 and ranksCount[ranks[1]] == 2 ):
            return (2,ranks[0],ranks[1],ranks[2])

        return self.isOne(hand,ranksCount)
     
    def isOne(self,hand,ranksCount):
        ranks =  sorted(ranksCount, key=ranksCount.get,reverse=True)
        if (ranksCount[ranks[0]] == 2):
            return (1,ranks[0],ranks[1],ranks[2],ranks[3])

        return self.isHigh(hand,ranksCount)
   
    def isHigh(self,hand,ranksCount):
        ranks =  sorted(ranksCount, key=ranksCount.get,reverse=True)
        return (0,ranks[0],ranks[1],ranks[2],ranks[3],ranks[4])

epochs = 200
filepath = ''

class Agent:
    

    def __init__(self,id):
        self.wins = [0] * (epochs)
        self.id = id

    def evalAct(self):
        pass

    def setReward(self,state,reward):
        pass

    def getId(self):
        return self.id

    def saveTable(self):
        pass

    def getAgentClass(self):
        return __class__.__name__

class LinearQAgent(Agent):
    #qtable = np.random.random((13*7*2,2))
    def __init__(self,id):
        super().__init__(id)
        self.qtable = np.random.random((7)) 
        #self.qtable = [-3.14287454,  0.55278789,  0.72301699,  0.78947968,  0.68598076, -2.29934659, 0.56422474]
        self.qtable = [9.63250365,  6.16764962, -1.34843332, -2.72533963,  0.22571655, -0.15230302,  0.14547532]
        self.alpha = 0.001
        self.waitingReward = False
        self.epsilon = 0.001
        self.sbPhi = 0
        self.sbQhat = 0

    def getLinearIndex(self,indices):
        return p.ravel_multi_index([indices[0] -1, indices[2] -1,indices[3]-1],[13,7,2])

    def createFeatureVector(self,state, Allin):
        rank1, rank2,isSuited, isSB = state[0][0].rank,state[0][1].rank,state[0][0].suit == state[0][1].suit, state[1]

        return np.array([1,
                     rank2/14.0 if Allin else 0,
                     rank1/14.0 if Allin else 0,
                     abs(rank2-rank1)**0.25 if Allin else 0,
                     1 if (isSuited and Allin) else 0,
                     1 if isSB else 0,
                     1 if isSB and Allin else 0,
                    ], dtype=np.float64)

    def evalAct(self,state):
        #qvalue = qtable[getLinearIndex(state)] 
        qAllin = self.createFeatureVector(state,True)
        qFold = self.createFeatureVector(state,False)
        qAllinValue  = np.sum(qAllin * self.qtable)
        qfoldValue  = np.sum(qFold * self.qtable)
        self.waitingReward = True

        goallIn = qAllinValue > qfoldValue
        if (np.random.rand() < self.epsilon):
            goallIn = not goallIn
        #bug here
        if (goallIn):
            self.sbPhi = qAllin
            self.sbQhat = qAllinValue
            return 1  
        else:
            self.sbPhi = qFold
            self.sbQhat = qfoldValue
            return 0    

    def setReward(self,reward):
        return

        if (not self.waitingReward):
            return

        self.waitingReward = False
        self.qtable += self.alpha * (reward-self.sbQhat) * self.sbPhi

class NashEqAgent(Agent):
    def __init__(self,id):
        super().__init__(id)
        json1_file = open('D:\\Emulerr\\CS\\year 4\\ai\\TOY_POKER_FINAL.txt')
        json1_str = json1_file.read()
        json1_file.close()
        self.data = json.loads(json1_str)
        
    def convertRank(self,rank):
        if rank == 14:
          rank = 'A'
        elif rank == 13:
          rank = 'K'
        elif rank == 12:
          rank = 'Q'
        elif rank == 11:
          rank = 'J'
        elif rank == 10:
          rank = 'T'
        else:
          rank = rank
        return str(rank)

    def evalAct(self,state):
        rank1, rank2,isSuited, isSB,ep = state[0][0].rank,state[0][1].rank,state[0][0].suit == state[0][1].suit, state[1], state[2]
        row = self.convertRank(rank2) + self.convertRank(rank1) + ('s' if isSuited else 'o') + ('p' if isSB else 'c')
        ep = int((ep / 0.05)-20)
        action = self.data[row][ep]

        #print("==============")
        #print("rank1", "rank2","isSuited", "isSB","ep")
        #print(rank1, rank2,isSuited, isSB,state[2])
        #print(row)
        action = Poker.ALLIN if (np.random.rand() < action) else Poker.FOLD
        #print("action:", action)
        #print("!!!!!!!!!!!!!!!!")
        return action

class RandomAgent(Agent):
    def evalAct(self,state):
        return random.randint(0,1)

class PlayerAgent(Agent):
    def evalAct(self,state):
        while (True):
            try:
                print ('your status: ' + str(state))
                return int(input("0 Fold, 1 All-in: "))
            except:
                logger.log(logger.WARNING,'Please choose 0 or 1')

def get_pretty_table(iterable, header):
    max_len = [len(x) for x in header]
    for row in iterable:
        row = [row] if type(row) not in (list, tuple) else row
        for index, col in enumerate(row):
            if max_len[index] < len(str(col)):
                max_len[index] = len(str(col))
    output = ''
    #output = '-' * (sum(max_len) + 1) + '\n'
    output += '\t' + ''.join([h + ' ' * (l - len(h)) + '\t' for h, l in zip(header, max_len)]) + '\n'
    #output += '-' * (sum(max_len) + 1) + '\n'
    for row in iterable:
        row = [row] if type(row) not in (list, tuple) else row
        output += '\t' + ''.join([str(c) + ' ' * (l - len(str(c))) + '\t' for c, l in zip(row, max_len)]) + '\n'
    #output += '-' * (sum(max_len) + 1) + '\n'
    return output

class PristineQAgent(Agent):
    def __init__(self,id):
        super().__init__(id)
        #self.qtable = np.zeros((2*2*13*13))
        self.qtable = np.load(filepath + self.getAgentClass() + '.npy')
        logger.log(logger.CRITICAL,self.printTable())

        self.alpha = 0.1
        self.waitingForReward = False
        self.epsilon = 0.1

        self.action = -1
        self.stateIndex = -1
        self.ep = 0

    #[rank1, rank2, suited, isSB]
    def getLinearIndex(self,indices):
        return np.ravel_multi_index([indices[0], indices[1], indices[2],indices[3]],[13,13,2,2])

    def printTable(self):
        table = self.getTable(self.qtable)
        headers =  list(map(str, [0] + [i for i in range(14,1,-1)]))
        for row in range(len(table)):
            table[row] = list(map(str, list(map(int, table[row]))))

        print(get_pretty_table(table,headers))
        #for r in table:
            #print(list(map(int, r)))


    def getTable(self,qtable):
        table = []
        isSuited = 0
        for r1 in range(12,-1,-1):
            table.append([r1+2])
            for r2 in range(12,-1,-1):
                if (r1 < r2):
                    id = self.getLinearIndex([r2,r1,isSuited,0])
                else:
                    id = self.getLinearIndex([r1,r2,isSuited,0])
                #print(r1,r2,isSuited,12-r1,id,qtable[id])
                if (r1 == r2):
                    isSuited = isSuited  ^ 1
                table[12 - r1].append(qtable[id])
            isSuited = isSuited ^ 1  
        return table
            
    def getstateIndex(self,state):
        rank1, rank2,isSuited, isSB = state[0][0].rank,state[0][1].rank,state[0][0].suit == state[0][1].suit, state[1]
        return self.getLinearIndex((rank2-2,rank1-2,int(isSuited),int(isSB)))

    def evalAct(self,state):
        self.ep = state[2]
        self.stateIndex = self.getstateIndex(state)

        #action = (self.ep <= self.qtable[self.stateIndex])
        #if (np.random.rand() < self.epsilon):
        #    action = not action

        action = (0 <= self.qtable[self.stateIndex])
        #if (np.random.rand() < self.epsilon):
        #    action = not action

        #logger.log(logger.CRITICAL,state,action)

        self.action = int(action) #
        self.waitingForReward = True

        return self.action

    def setReward(self,reward):
        if (not self.waitingForReward):
            return

        self.waitingForReward = False
        if (self.action == Poker.ALLIN):
            self.qtable[self.stateIndex] += self.alpha * reward
 
    def saveTable(self):
        return np.save(filepath + self.getAgentClass() ,self.qtable, allow_pickle=True, fix_imports=True)


class QAgent(Agent):
    def __init__(self,id):
        super().__init__(id)
        #self.qtable = np.array([np.zeros((2*2*13*13*4)),np.zeros((2*2*13*13*4))])
        self.qtable = np.load(filepath + self.getAgentClass() + '.npy')
        #logger.log(logger.CRITICAL,self.printTable())

        self.alpha = 0.05
        self.waitingForReward = False
        self.epsilon = 0.1

        self.action = -1
        self.stateIndex = -1
        self.ep = 0

    #[rank1, rank2, suited, isSB]
    def getLinearIndex(self,indices):
        return np.ravel_multi_index([indices[0], indices[1], indices[2],indices[3],indices[4]],[13,13,2,2,4])

    def printTable(self):
        table = self.getTable(self.qtable)
        headers =  list(map(str, [0] + [i for i in range(14,1,-1)]))
        for row in range(len(table)):
            table[row] = list(map(str, list(map(int, table[row]))))

        print(get_pretty_table(table,headers))
        #for r in table:
            #print(list(map(int, r)))


    def getTable(self,qtable):
        table = []
        isSuited = 0
        for r1 in range(12,-1,-1):
            table.append([r1+2])
            for r2 in range(12,-1,-1):
                if (r1 < r2):
                    id = self.getLinearIndex([r2,r1,isSuited,0])
                else:
                    id = self.getLinearIndex([r1,r2,isSuited,0])
                #print(r1,r2,isSuited,12-r1,id,qtable[id])
                if (r1 == r2):
                    isSuited = isSuited  ^ 1
                table[12 - r1].append(qtable[id])
            isSuited = isSuited ^ 1  
        return table
            
    def getstateIndex(self,state):
        rank1, rank2,isSuited, isSB,money = state[0][0].rank,state[0][1].rank,state[0][0].suit == state[0][1].suit, state[1],state[2]
        return self.getLinearIndex((rank2-2,rank1-2,int(isSuited),int(isSB),int(money/20.0)))

    def evalAct(self,state):
        self.state = state
        self.stateIndex = self.getstateIndex(state)

        #print (state)
        #print (self.qtable[0][self.stateIndex],self.qtable[1][self.stateIndex])
        self.action = (self.qtable[0][self.stateIndex] <= self.qtable[1][self.stateIndex])
        if (np.random.rand() < self.epsilon):
            self.action = not self.action
        self.action = int(self.action)
        self.waitingForReward = True
        return self.action

    def setReward(self,state,reward):
        if (not self.waitingForReward):
            return

        self.waitingForReward = False
        if (state[2] == 20.0):
            self.qtable[self.action][self.stateIndex] += self.alpha * 20
        elif (state[2] == 0):
            self.qtable[self.action][self.stateIndex] += self.alpha * -20
        else:
            nextstate = self.getstateIndex(state)
            self.qtable[self.action][self.stateIndex] += self.alpha * (0.1 * reward) *( 0.9 * max(self.qtable[0][nextstate],self.qtable[1][nextstate]))
        

    def saveTable(self):
        return np.save(filepath + self.getAgentClass() ,self.qtable, allow_pickle=True, fix_imports=True)



def main():
    win_count1 = 0
    win_count2 = 0
   
    game = Poker()
    agents = (QAgent(game.addPlayer()),RandomAgent(game.addPlayer()))
    for i in range(epochs):
        game.reset()
        game.deal()
        while not game.isGameover():
            if game.isRoundFinished():
                game.deal()

            playerIdTurn = game.getplayerIDTurn()            
            action = agents[playerIdTurn].evalAct(game.getPlayerState(playerIdTurn))
            game.setAction(action)

            if game.isRoundFinished() or game.isGameover():
                for agent in agents:
                    agent.setReward (game.getPlayerState(agent.getId()), game.getRoundDividends(agent.getId()))

        game.printStatus()
        winners = game.getWinnerIDs()
        if (winners[0] == agents[0].getId()):
            agents[0].wins[i] = 1
            agents[1].wins[i] = 0
        if (winners[0] == agents[1].getId()):
            agents[0].wins[i] = 0
            agents[1].wins[i] = 1


    logger.log(logger.WARNING,agents[0].wins)
    logger.log(logger.WARNING,agents[0].getAgentClass() + "(id:0) wins:",(sum(agents[0].wins) / epochs)*100.0,"%")
    logger.log(logger.WARNING,agents[1].getAgentClass() + "(id:1) wins:",(sum(agents[1].wins) / epochs) * 100.0,"%")

    for agent in agents:
        agent.saveTable()
    

if __name__ == '__main__':
	main()

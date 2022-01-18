Timelog:
1/12, 8
1/13, 4
1/14, 2
1/15, 1
1/16, 1
1/17, 2

Basic Rule-base Model 1 =  0.1598 (58% win) vs random
Basic Rule-base Model 2 =  0.1635 (58% win) vs random, 0.2917 (65% win) vs rule model 1
Tests:
 1: [64, 64],      5000 = -0.0036
 3: [32, 32],      5000 = -0.0741
 4: [128, 128],    5000 = -0.0183
 5: [64, 64, 64],  5000 = -0.0482
 6: [64],          5000 =  0.0252
 7: [128],         5000 =  0.0189
 8: [64],         25000 =  0.0353
 9: [64, 64],     25000 = -0.0408
10: [128],        25000 =  0.0038
11: [64],         25000 =  0.0517 # 0.1x learning rate
12: [64],         25000 =  0.0894 # 0.1x learning rate, 2x batch size and estimater update size
13: [64],         50000 =  0.0871 # 0.1x learning rate
14: [64],         25000 =  0.0252 # 0.1x discount factor
15: [64],        100000 =  0.1060 # 0.1x learning rate
16: [64],         25000 =  0.0994 # using books for payoff
17: [64],         50000 =  0.1203 # using books for payoff, 0.1x learning rate
18: [64],         50000 =  0.0883 # using books for payoff, 0.1x learning rate, 1,000,000 epsilon decay
19: [64],        250000 =  0.1410 # using books for payoff, 0.1x learning rate, 1,000,000 epsilon decay  
    ^ 57% win against random, 59% win against rules 1, 51% win against rules 2
20: [64],         50000 =  0.1192 # using books for payoff, 0.1x learning rate, 0.1x discount factor
21: [64],         50000 =  0.1348 # using books for payoff, 0.1x learning rate, 0.1x discount factor, 2x batch size
22: [64],        100000 =  0.1551 # using books for payoff, 0.1x learning rate, 0.1x discount factor, 2x batch size
    ^ 58% win against random, 59% win against rules 1, 50% win against rules 2
23: [64],        100000 =  0.1448 # using books for payoff, 0.1x learning rate, 0.1x discount factor, 4x batch size
24: [64],        100000 =  0.1527 # using books for payoff, 0.1x learning rate, 0.1x discount factor, 2x batch size, 1,000,000 epsilon decay 
25: [64, 64],    100000 =  0.1468 # using books for payoff, 0.1x learning rate, 0.1x discount factor, 2x batch size









My rule based model for 2-player Go Fish with 4-card books (not pairs) first guesses all the cards I know the opponent must have based on their guesses and otherwise randomly chooses a number from its hand to guess. This rule based model beats a random guessing model 58% of the time (in 50,000 evaluation matches). My best AI model can also beat the random model 58% of the time. However, my AI model beats the rule model 59% of the time! In other words, the AI model does even better against the rule model than the random model even though it wasn't trained against it! So I played a match against the AI to see its strategy. It seems to really try to limit the information it shares and often asks for mostly the same few cards. At one point it took two of my kings and then immediately asked for kings again. I don't think this was the best possible move (e.g. it could have re-asked for something else), but didn't reveal anything new. So I created a second rule based model ("rule model 2") following a similar strategy that first tries to ask for anything it knows will produce a full book, then will ask for the same thing repeatedly until it makes a book, otherwise it will make a random guess. This strategy also beats the random guesser 58% of the time (I suspect there is an upper bound of 58% wins against a random guesser, which kinda makes sense). But rule model 2 beats rule model 1 with a huge 65%. So clearly rule model 2 exploits the weakness of rule model 1. Rule model 2 vs my AI is a dead even 50%, and this kinda makes sense since they are kinda doing the same strategy. It still is amazing to me that the AI landed on this superior model-2-like strategy even though it performs just as well as the simpler model-1-like strategy against the random model it was trained on. 

The game state fed to the models includes the cards other players are known to have, but it does not include anything about the cards they are known NOT to have (e.g. if I have 3 Kings and 3 Queens, but I asked for Kings last round, there is more likely to be a Queen in my opponent's hand then a King). So instead of feeding the models with the known cards, I will feed it the probability of completing a book for each possible guess. The probabiliy for each guess goes up based on the asks the opponent has made and the probability goes down based on what has been asked of the opponent. The probability should be 100% if I have one card and another player is known to have the other 3, for example. (Note: An edge case in a 4-player version is the player should know if it can get a full book by asking from multiple people. For example, if the player has 2 Kings and another player is known to have 1 King, and another player is known to have 1 King, the probability of creating a King book via a guess from a single other player is not 100%, but asking from both back-to-back is 100%. I think I can get around this by overriding the probabilities for the other players and setting them to 100% in this scenario). Then I am going to create a final rule model 3 that leverages this information. The main challenge will be determining the right balance between going with the highest probability option and not revealing new information. I think a good option would be to set some threshold (e.g. 50%) that the probability has to be above before guessing and revealing new information. In other words, if the higest probability guess has a 45% chance of getting a book, but it would reveal new information, then instead go with the highest pobability guess that does not reveal new information. Alternatively I could try to determine the real time value of giving up some information. In other words, calculate the increase in probability the opponents will receive by making a guess and factor that in. The problem is that giving up information has an effect on more than just the next round; it effects an unknown number of future rounds. The other thing I want to do is to train the AI model against the random model, the rule models, and the best prior AI models so it doesn't overfit to beating the random player. I am curious if it can beat the theoretical rule model 3.
Timelog:
Date, Hours
1/12, 8
1/13, 4
1/14, 2
1/15, 1
1/16, 1
1/17, 3
1/18, 2.5
1/19, 6
1/20, 3
1/21, 2
1/22, 2
1/23, 1
Total: 35.5
1/28, 2.5
1/29, 2.5
1/31, 3.5
2/02, 3
2/03, 1

# 2 Player, knowledge of cards players must have, but no knowledge of cards players must NOT have
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

My rule based model for 2-player Go Fish with 4-card books (not pairs) first guesses all the cards I know the opponent must have based on their guesses and otherwise randomly chooses a number from its hand to guess. This rule based model beats a random guessing model 58% of the time (in 50,000 evaluation matches). My best AI model can also beat the random model 58% of the time. However, my AI model beats the rule model 59% of the time! In other words, the AI model does even better against the rule model than the random model even though it wasn't trained against it! So I played a match against the AI to see its strategy. It seems to really try to limit the information it shares and often asks for mostly the same few cards. At one point it took two of my kings and then immediately asked for kings again. I don't think this was the best possible move (e.g. it could have re-asked for something else), but it didn't reveal anything new. So I created a second rule based model ("rule model 2") following a similar strategy that first tries to ask for anything it knows will produce a full book, then will ask for the same thing repeatedly until it makes a book, otherwise it will make a random guess. This strategy also beats the random guesser 58% of the time (I suspect there is an upper bound of 58% wins against a random guesser, which kinda makes sense). But rule model 2 beats rule model 1 with a huge 65%. So clearly rule model 2 exploits the weakness of rule model 1. Rule model 2 vs my AI is a dead even 50%, and this kinda makes sense since they are kinda doing the same strategy. It still is amazing to me that the AI landed on this superior model-2-like strategy even though it performs just as well as the simpler model-1-like strategy against the random model it was trained on.

The game state fed to the models includes the cards other players are known to have, but it does not include anything about the cards they are known NOT to have (e.g. if I have 3 Kings and 3 Queens and my opponents know it, but I asked for Kings last round, there is more likely to be a Queen in my opponent's hand then a King). So instead of feeding the models with the known cards, I will feed it the probability of completing a book for each possible guess. The probability for each guess goes up based on the asks the opponent has made and the probability goes down based on what has been asked of the opponent. The probability should be 100% if I have one card and another player is known to have the other 3, for example. (Note: An edge case in a 4-player version is the player should know if it can get a full book by asking from multiple people. For example, if the player has 2 Kings and another player is known to have 1 King, and another player is known to have 1 King, the probability of creating a King book via a guess from a single other player is not 100%, but asking from both back-to-back is 100%. I think I can get around this by overriding the probabilities for the other players and setting them to 100% in this scenario). Then I am going to create a final rule model 3 that leverages this information. The main challenge will be determining the right balance between going with the highest probability option and not revealing new information. I think a good option would be to set some threshold (e.g. 50%) that the probability has to be above before guessing and revealing new information. In other words, if the highest probability guess has a 45% chance of getting a book, but it would reveal new information, then instead go with the highest probability guess that does not reveal new information. Alternatively I could try to determine the real time value of giving up some information. In other words, calculate the increase in probability the opponents will receive by making a guess and factor that in. The problem is that giving up information has an effect on more than just the next round; it effects an unknown number of future rounds. The other thing I want to do is to train the AI model against the random model, the rule models, and the best prior AI models so it doesn't overfit to beating the random player. I am curious if it can beat the theoretical rule model 3.

Then I will try training the AI in a 4 player game. Since there are more inputs and more outputs, I think training will be more difficult. But it is a good step towards Hearts and I think the learnings from hyperperameter tuning the 2 player game will be very applicable to 4-player too!

# 2 Player, expected value evaluation
Goal is to get average down to 0 and keep variance low
Test Average Variance
0:   0.4039  0.3274
1:   0.3922  0.3218
2:   0.1445  0.2460
3:   0.0413  0.2371
4:   0.0143  0.2347

0: Initial (basically using the info available to the previous AI)
1: Adds tracking of not possible ranks (ranks that a card in a player's hand can't possibly be) and uses logic and process of elimination to reveal cards based on the additional information.
2: Uses not possible ranks in probability of getting cards of the rank from a player
3: Accounts for the possibly drawing the desired card from the deck if the requested player doesn't have a card of the rank
4: Uses not possible ranks of a card to increase the probability for the remaining ranks on the card.

I completed the code that basically determines the expected number of cards you would end up with of that rank if you asked for that rank of another player (e.g. if you have two 2’s and you know another player has at least another 2, then the expected number of 2’s you’d end up with by asking for 2’s might be 3.5; the sum of your existing two 2’s and their guaranteed 2 and the possibility that one of their other cards is also a 2). I came up with a good way to evaluate the accuracy of this “expected cards” calculation too. I have two random guessing agents play 5000 games. After each guess, I calculate the error between the “expected cards” I calculated for the guess and the number of cards they actually ended up with. Then I calculate the mean and variance of this and use that to evaluate the accuracy. The closer the mean and variance are to 0, the better. Theoretically the mean should be able to get pretty close to 0, but there will always be some variance since you can only have a finite number of cards and there is luck involved. As a baseline, I evaluated calculating “expected cards” without taking any information into account about what cards the player must not have (i.e. using the same information my AI models have trained on to-date). I got an average of 0.4039 and variance of 0.3274. This means that on average you will get 0.4 extra cards than what you knew you would for sure get. I started to layering in different improvements and taking advantage of all additional information and deducing all I could think of. Now I get an average of 0.0143 and variance of 0.2347. The average has basically come to 0 (yay!) and the variance has improved by 28% though. This improvement is best understood visually (the more clustered around the centerline the better):
[Image of the two normal distributions]
(Red is baseline, Green is improved)

I created a new rule based AI that always guesses whichever rank has the highest “expected cards” value. As expected using this information improves the players performance against a random guesser with a huge 62% win rate (up from 58% with prior rule based AIs).

So my next steps are:
1. Profile and optimize the code. Games take longer to run now with all the extra calculations, so before training an AI on hundreds of thousands of games, I need to speed it up.
2. Train a new AI
3. Train a new AI vs 4 players
4. On to Hearts!

Basic Rule-base Model 2 = 0.2052 (60% win) vs random
Basic Rule-base Model 3 = 0.2478 (62% win) vs random

# Profiling
Executing 2-player, random vs random, 1000 games
0: 10.32 - Baseline
1:  9.99 - Optimized tracking of non-public cards in each player hand
2:  6.95 - Improve card hashing
3:  6.40 - Remove string formatting in non-debug mode
4:  6.18 - Don't sort player hands
5:  5.87 - Store player hand by rank instead of recomputing
Times are in ms per game. Achieved 43% improvement.

# 2 Player, model training with expected value data
Base settings:
* Discount Factor: 0.999
* Batch Size: 64
* Learning Rate: 0.000005

| Test | Network   | Episodes | Epsilon Decay | vs Random | vs Rules v3 | Opponent Pool                       | Info |
----------------------------------------------------------------------------------------------------------------------------
| 1    | [64]      |    50000 |         20000 |     0.167 |      -0.072 | Random                              | Baseline
| 2    | [64]      |    50000 |         20000 |     0.186 |      -0.057 | Random, RulesV1, RulesV3, TrainedV1 | Added opponent pool
| 3    | [128, 64] |   100000 |        500000 |     0.162 |      -0.066 | Random, RulesV1, RulesV3, TrainedV2 |
| 4    | [128]     |   100000 |        500000 |     0.177 |      -0.054 | Random, RulesV1, RulesV3, TrainedV2 |
| 5    | [64, 64]  |   100000 |        500000 |     0.177 |      -0.046 | Random, RulesV1, RulesV3, TrainedV2 |
| 6    | [64, 32]  |   100000 |        500000 |     0.165 |      -0.070 | Random, RulesV1, RulesV3, TrainedV2 |
| 7    | [64]      |   100000 |        500000 |     0.195 |      -0.024 | Random, RulesV1, RulesV3, TrainedV2 |
^Best (60% vs Random, 49% vs Rules v3)
| 8    | [64]      |   250000 |        500000 |     0.194 |      -0.050 | Random, RulesV1, RulesV3, TrainedV7 |
| 9    | [64]      |   250000 |       1000000 |     0.182 |      -0.063 | Random, RulesV1, RulesV3, TrainedV7 |
| 10   | [64]      |   250000 |        500000 |     0.182 |      -0.067 | Random, RulesV1, RulesV3, TrainedV7 | 0.0000005 Learning Rate
| 11   | [64]      |   250000 |        500000 |     0.191 |      -0.043 | Random, RulesV1, RulesV3, TrainedV7 | 0.9995 Discount factor
| 12   | [64]      |   250000 |        500000 |     0.191 |      -0.047 | RulesV3                             |
| 13   | [64]      |   100000 |        500000 |    -0.286 |      -0.484 | Random, RulesV1, RulesV3, TrainedV2 | Normalized inputs
| 14   | [64]      |   100000 |        500000 |     0.182 |      -0.056 | Random, RulesV1, RulesV3, TrainedV2 | Squared rewards

Whelp, I am a bit discouraged now. My best trained model is not as good as the Rule V3 model. My trained model has a 60% win rate vs a random opponent wheras the Rule V3 model has a 62% win rate. My trained model has a 49% win rate vs the Rule V3 model. This means my trained AI has not been able to find any suprior strategy and can't quite mimic the very basic strategy of Rule V3 model (which is to simply pick the action with the highest expected number of cards value from the game state). I have tried a range of different changes and tunings and can't think of anything else to try. So I am going to put this project on pause for now and come back to it after Mexico.


# 4 Player, model training with expected value data
Basic Rule-base Model 3 = 0.700 (84.9% win) vs random

Base settings:
* Discount Factor: 0.999
* Batch Size: 64
* Learning Rate: 0.000005
* Epsilon End: 0.1

| Test | Network   | Episodes | Epsilon Decay | vs Random | vs Rules v3 | Opponent Pool                       | Info |
----------------------------------------------------------------------------------------------------------------------------
| 1    | [64]      |    50000 |         20000 |     84.4% |        8.5% | Random                              | Baseline
| 2    | [128]     |    50000 |         20000 |     84.8% |        8.4% | Random                              | Baseline
| 3    | [64, 64]  |    50000 |         20000 |     83.7% |        8.5% | Random                              | Baseline
| 4    | [128]     |   250000 |         20000 |     85.4% |        9.9% | Random, RulesV1, RulesV3, TrainedV2 |
| 5    | [128]     |   250000 |        500000 |     85.3% |       10.0% | Random, RulesV1, RulesV3, TrainedV2 |
| 6    | [128]     |   250000 |        500000 |     84.3% |        9.9% | Random, RulesV1, RulesV3, TrainedV2 | 0.2 Epsilon End
| 7    | [128]     |   250000 |        500000 |     84.9% |       10.3% | Random, RulesV1, RulesV3, TrainedV2 | 0.05 Epsilon End


# 4 Player Hearts

| Test | Network    | Episodes | Epsilon Decay | Learning Rate | Decay | vs Random | Info
----------------------------------------------------------------------------------------------------------------------------
| PC 1 | [256, 256] |   100000 |        500000 |          0.01 | 0.999 |     15.9% |
| PC 2 | [256, 256] |   100000 |        500000 |         0.001 | 0.999 |     23.1% |
| PC 3 | [256, 256] |   100000 |        500000 |        0.0001 | 0.999 |     21.9% |
| PC 4 | [256, 256] |   100000 |        500000 |       0.00001 | 0.999 |     25.0% |
| PC 5 | [256, 256] |   100000 |        500000 |      0.000001 | 0.999 |     24.9% |
| PC 6 | [256, 256] |   100000 |        500000 |     0.0000001 | 0.999 |     22.3% |
| MAC1 | [512]      |   100000 |        100000 |      0.000005 | 0.999 |     15.3% |
| MAC2 | [512]      |   100000 |        500000 |      0.000005 | 0.9999|     20.7% |
| MAC3 | [512]      |   100000 |        500000 |      0.000005 | 0.995 |     20.6% |
| MAC4 | [1024]     |   100000 |        500000 |      0.000005 | 0.999 |     24.4% |

I have switched over to Hearts now. Programing the mechanics of the game were actually simpler than Go Fish especially without the complex "expected cards" logic. Unforetunately there are many more inputs into the neural network for Hearts than with Go Fish. For example, I only need 13 input values to represent the current hand in Go Fish, but need a full 52 for Hearts. Therefore, I have to train with a much larger neural network. With the larger network I decided to try doing training using my PC GPU. Interestingly, the training is much slower using the GPU. I think this is because the network is still relatively small, so the overhead of transferring input and outputs from CPU to GPU outweighs the benefit of the GPU. But all of my attempts at training so far have been futile. My best trained model can only achieve a 25% win rate in a 4 player game against random players, so it performs basically as well as random players do :( But I kinda expected this. The input space has increased from 87 values for 4-player Go Fish to 393 values for 4-player Hearts and decision making in Hearts is very situational (e.g. when leading a trick, the considerations are quite different than as the last player of a trick). So my next action is going to be to train a handful of more focused networks on specific tasks and situations. The framework I am using is not really setup for this type of multi-network setup so I will need to do some rejiggering of that code to get this going. I will also create a simple rule based Hearts player to get a better baseline for what the neural network should be able to achieve at minimum.



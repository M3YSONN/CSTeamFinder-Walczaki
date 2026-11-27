# Counter-Strike Team Selection

**Team:** Z6 · group L2 · **Repository:**  Artificial Intelligence  — laboratory · Collegium Da Vinci · 2026/2027

> 

## 1\. Problem *(rubryka A)*

> This is a problem faced by organizers of mixers, in-house events, or amateur tournaments who need to divide players into teams. Usually, they hold a draft or select team captains, who then choose their lineups themselves \- for example, by drafting in a snake format. This often leads to situations where teams are heavily unbalanced. Our system uses a genetic algorithm to select all teams simultaneously, taking into account roles, statistics, and positional coverage. It takes a database of players and algorithm parameters as input. It returns the team assignments along with a rating for each team and compares these results to those obtained using the snake draft method.

## 2\. Why AI, and why this technology?*(B · 7 pkt)*

A simple algorithm is not enough, because a precise procedure would be too costly. There are approximately 1.2 × 10⁶⁶ ways to divide 75 players into 15 groups of five; therefore, checking every single possibility \- even at a rate of a billion combinations per second \- would take about 10⁴⁹ years.

## 3\. Data *(B · 8 pkt)*

> Source: https\://www\.hltv.org/stats/players   
> Scale: 75 players, 7 maps, 35 positions, 525 player-position assignments  
> Format: SQL script with four tables joined by foreign keys

## 4\. Solution *(A · 10 pkt, B · 5 pkt)*

> Evaluation of an individual team: F(d) \= 0,4·R \+ 0,3·S \+ 0,2·P \+ 0,1·K, where F ∈ \[0, 1\]    
>   
> (R \- roles, S \- statistics, P \- positional coverage, K \- communication (percentage of players on a team who come from same country  
>   
> Process flow:  
> 

1. Data loading  
2. Preparation of evaluations  
3. Snake draft \- sorts players by rating and distributes them using the snake sort algorithm into up to 15 teams  
4. The genetic algorithm searches for the best distribution:  
- Individual: permutation of the 75 players’ numbers  
- Initial population: 150 random permutations  
- In each generation: evaluates each individual using a fitness function; the top 2 individuals are retained unchanged; performs tournament selection; crossover; mutation. The termination condition is 800 generations

## 5\. Evaluation *(B · 8 pkt)*

| Przypadek / zbiór | Punkt odniesienia | Nasz system |
| :---- | :---- | :---- |
| Evaluation function, fitness | Snake draft \- 0,39 | Genetic algorithm \- 0,71 |

## The system is nearly twice as good as the benchmark.

## 6\. Non-functional requirements *(A · 5 pkt)*

> The genetic algorithm divides 75 players into 15 teams in 12.9 seconds on an Intel Core i7-13700K processor. Before performing the calculations, the program checks the data and displays warnings if something is incorrect. Despite this, it continues to run, and missing values are replaced with 0\. The genetic algorithm is random; however, in 10 runs, the fitness score was consistent, ranging from 0.696 to 0.713.

## 7\. Limitations *(E · 4 pkt)*

> When the system makes a mistake \- a team may receive a high communication rating in cases where, for example, four players are from the same country and speak the same language, even though the fifth player, who is from a different country, is the team leader and is the one who has to do most of the communicating.  When the system fails or produces an incorrect result \- such as when there are fewer players in the database than the number of teams requires, or when a rating is missing \- the default value of 0 affects the team’s score. With more time, we would collect more data, introduce new variables, and develop a graphical user interface.

## 8\. Practical implementation *(E · 4 pkt)*

> FACEIT (CS2 MATCHMAKING PLATFORM) \- The platform’s match balance metric is based on “Team Rating,” which takes into account the skill level of the players on the team, whether the team consists of solo players or a full squad, the number of matches each player has played, and the skill spread within the team. This is very similar to our rating system: it’s not just the average that matters, but also the team composition and skill spread.

## 9\. Team *(D · 8 pkt)*

| Osoba | Za co odpowiadała |
| :---- | :---- |
| Andrii Piskun Tymur Popovych Konrad Wawrzyniak | Code, data collection Database, data collection Documentation, presentation, data collection, algorithm specifications |

## 10\. Launch *(C · 4 pkt)*

```
git clone https://github.com/M3YSONN/CSTeamFinder-Walczaki
cd DoborDruzynCS
python -c "import sqlite3; c=sqlite3.connect('cs2.db'); c.executescript(open('ctf_db_poprawiony.sql', encoding='utf-8').read()); c.commit()" 
python main.py --typ sqlite
```

## 11\. AI tools

> Claude \- code assistance, presentation tool.
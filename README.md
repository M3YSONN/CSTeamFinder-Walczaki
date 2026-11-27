
CS2 Team Selection – Genetic Algorithm
Artifical Intelligence 

The program splits professional Counter-Strike 2 players into balanced five-player teams using a genetic algorithm. It compares the result with a simple baseline: a snake draft by rating.

How to run
```
git clone https://github.com/M3YSONN/CSTeamFinder-Walczaki
cd DoborDruzynCS
python -c "import sqlite3; c=sqlite3.connect('cs2.db'); c.executescript(open('ctf_db_poprawiony.sql', encoding='utf-8').read()); c.commit()" 
python main.py --typ sqlite
```

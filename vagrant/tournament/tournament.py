#!/usr/bin/env python
# tournament.py -- implementation of a Swiss-system tournament

import bleach
import psycopg2
from random import randint


def connect():
    """Connect to the PostgreSQL database.  Returns a database connection."""
    try:
        db = psycopg2.connect("dbname=tournament")
        cursor = db.cursor()
        return db, cursor
    except:
        print("Error connecting to database.")


def deleteMatches():
    """Remove all the match records from the database."""
    db, cursor = connect()
    cursor.execute("truncate matches cascade;")
    db.commit()
    db.close()


def deletePlayers():
    """Remove all the player records from the database."""
    db, cursor = connect()
    # Use cascade to remove matches in which the players participated.
    cursor.execute("truncate players cascade;")
    db.commit()
    db.close()


def countPlayers():
    """Returns the number of players currently registered."""
    db, cursor = connect()
    cursor.execute("select count(*) from players;")
    result = cursor.fetchone()[0]
    db.close()
    # count(*) will return only one number, so fetchone() is appropriate.
    return result


def registerPlayer(name):
    """Adds a player to the tournament database.

    The database assigns a unique serial id number for the player.  (This
    should be handled by your SQL database schema, not in your Python code.)

    Args:
      name: the player's full name (need not be unique).
    """
    # Avoid script injection.
    name = bleach.clean(name)
    db, cursor = connect()
    # Avoid sql injection.
    cursor.execute("insert into players (name) values (%s)", (name, ))
    db.commit()
    db.close()


def playerStandings():
    """Returns a list of the players and their win records, sorted by wins.

    The first entry in the list should be the player in first place, or a
    player tied for first place if there is currently a tie.

    Returns:
      A list of tuples, each of which contains (id, name, wins, matches):
        id: the player's unique id (assigned by the database)
        name: the player's full name (as registered)
        wins: the number of matches the player has won
        matches: the number of matches the player has played
    """
    db, cursor = connect()
    cursor.execute("select * from wins_total;")
    results = cursor.fetchall()
    db.close()
    return results


def reportMatch(winner, loser):
    """Records the outcome of a single match between two players.

    Args:
      winner:  the id number of the player who won
      loser:  the id number of the player who lost
    """
    if (winner != loser):
        db, cursor = connect()
        # Avoid sql injection by passing arguments to the .execute() function
        # rather than using string interpolation or the like.
        cursor.execute("insert into matches (winner, loser) values (%s, %s)",
                       (winner, loser))
        db.commit()
        db.close()
    else:
        # Handle case of person playing him/her self.
        raise ValueError("Winner cannot be the same as loser")


# Note that this helper function can error out if there are more rounds than
# are necessary to determine a winner. A more robust implementation would
# require entry of all results before issuing a new swissPairings(), and would
# declare a winner once sufficient rounds were played to determine one.
def handleBye(standings):
    """Given input of the type returned by playerStandings(), adjusts the
    standings by selecting a bye player at random from among those who have not
    yet received a bye, crediting that player with a win, and returning a
    standings-type output with an even number of players."""
    db = connect()
    cursor = db.cursor()
    cursor.execute("select * from no_byes")
    noByeList = cursor.fetchall()
    # randint includes the top number
    luckyId = noByeList[randint(0, len(noByeList) - 1)][0]
    # Give a win by inserting dummy game with opponent 0.
    cursor.execute("insert into matches (winner, loser) values (%s, 0)",
                   (luckyId, ))
    cursor.execute("update players set had_bye = true where id = %s",
                   (luckyId, ))
    db.commit()
    db.close()
    index = [i[0] for i in standings].index(luckyId)
    standings.pop(index)
    return standings


def swissPairings():
    """Returns a list of pairs of players for the next round of a match.

    Assuming that there are an even number of players registered, each player
    appears exactly once in the pairings.  Each player is paired with another
    player with an equal or nearly-equal win record, that is, a player adjacent
    to him or her in the standings.

    Returns:
      A list of tuples, each of which contains (id1, name1, id2, name2)
        id1: the first player's unique id
        name1: the first player's name
        id2: the second player's unique id
        name2: the second player's name
    """

    # Raw results back from the view. raw[n][0] is id; raw[n][1] is name.
    raw = playerStandings()
    if len(raw) % 2 != 0:
        raw = handleBye(raw)

    # Partition by twos the results of the games. If we were going to do an
    # odd number of players, we could assign a bye at random or to the first or
    # last player in the sorted list, removing them from the list and running
    # this same code.
    results = []
    for i in range(0, len(raw), 2):
        results.append((raw[i][0], raw[i][1], raw[i + 1][0], raw[i + 1][1]))
    return results

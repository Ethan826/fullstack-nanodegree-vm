#!/usr/bin/env python
# tournament.py -- implementation of a Swiss-system tournament

import psycopg2
import bleach


def connect():
    """Connect to the PostgreSQL database.  Returns a database connection."""
    return psycopg2.connect("dbname=tournament")


def deleteMatches():
    """Remove all the match records from the database."""
    db = connect()
    cursor = db.cursor()
    cursor.execute("truncate matches cascade;")
    db.commit()
    db.close()


def deletePlayers():
    """Remove all the player records from the database."""
    db = connect()
    cursor = db.cursor()
    # Use cascade to remove matches in which the players participated.
    cursor.execute("truncate players cascade;")
    db.commit()
    db.close()


def countPlayers():
    """Returns the number of players currently registered."""
    db = connect()
    cursor = db.cursor()
    cursor.execute("select count(*) from players;")
    # count(*) will return only one number, so fetchone() is appropriate.
    return cursor.fetchone()[0]
    db.close()


def registerPlayer(name):
    """Adds a player to the tournament database.

    The database assigns a unique serial id number for the player.  (This
    should be handled by your SQL database schema, not in your Python code.)

    Args:
      name: the player's full name (need not be unique).
    """
    # Avoid script injection.
    name = bleach.clean(name)
    db = connect()
    cursor = db.cursor()
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
    # Two left joins to get winners and losers as aggregate values. Then a
    # subquery in order to get total games rather than losses.
    query = """select id, name, wins, wins + losses as total from
                   (select players.id,
                    players.name,
                    count(W.winner) as wins,
                    count(L.loser) as losses
                    from
                    players
                    left join matches W on W.winner = players.id
                    left join matches L on L.loser = players.id
                    group by players.id
                    order by wins desc) as sub;"""

    db = connect()
    cursor = db.cursor()
    cursor.execute(query)
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
        db = connect()
        cursor = db.cursor()
        # Avoid sql injection by passing arguments to the .execute() function
        # rather than using string interpolation or the like.
        cursor.execute("insert into matches (winner, loser) values (%s, %s)",
                       (winner, loser))
        db.commit()
        db.close()
    else:
        # Handle case of person playing him/her self.
        raise ValueError("Winner cannot be the same as loser")


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
    standings = playerStandings()

    # Prepend a winning percentage to each player. Then sort on that
    # percentage. Although this involves sorting outside of the database, it
    # would be quite complicated to implement an in-database recomputation of
    # winning percentages each time playerStandings() is run.
    sort = sorted(
        [[float(s[2]) / s[3], s[0], s[1]] for s in standings],
        reverse=True)

    # Now partition by twos the results of the games. If we were going to do an
    # odd number of players, we could assign a bye at random or to the first or
    # last player in the sorted list, removing them from the list and running
    # this same code.
    results = []
    for i in range(0, len(sort), 2):
        results.append((sort[i][1], sort[i][2], sort[i + 1][1], sort[i + 1][2]
                        ))
    return results

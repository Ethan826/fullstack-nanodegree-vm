rdb-fullstack
=============

Common code for the Relational Databases and Full Stack Fundamentals courses

To use the Tournament application, from the `./vagrant/tournament/` directory, issue the following commands

    $ psql
    vagrant=> \i tournament.sql

This will set up the database schema. Next

    $ python -i tournament.python

From the Python REPL, you can run the functions in the file.

To run the tests, issue

    $ python tournament_test.py

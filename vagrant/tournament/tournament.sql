-- Table definitions for the tournament project.

-- Reset (from here http://bit.ly/1XntaJI)
select pg_terminate_backend(pg_stat_activity.pid)
    from pg_stat_activity
    where pg_stat_activity.datname = 'tournament'
    and pid <> pg_backend_pid();

drop database tournament;

create database tournament;

\connect tournament;

create table players (
    id serial primary key,
    name text not null,
    had_bye boolean default false
);

create table matches (
    id serial primary key,
    winner int references players(id) on delete cascade,
    loser int references players(id) on delete cascade
    check (winner <> loser)
);

-- Used in the bye scenario
create view no_byes as
    select id
    from players
    where had_bye = false;

-- Set to true so fake player cannot be selected as the bye.
insert into players (id, name, had_bye) values (0, 'bye_opponent', true);

-- Two left joins to get both wins and losses
create view wins_losses as
    select players.id,
        players.name,
        count(W.winner) as wins,
        count(L.loser) as losses
        from
        players
        left join matches W on W.winner = players.id
        left join matches L on L.loser = players.id
        where players.id != 0
        group by players.id
        order by wins desc;

-- Convert to wins total rather than wins and losses
create view wins_total as
    select id, name, wins, wins + losses as total
    from wins_losses
    order by wins desc;

-- Potentially useful for alternative scoring schemes
create view win_percent as
    select id, name
    from wins_total
    order by cast(wins as decimal) / total desc;

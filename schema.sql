create table server_configs (
    server_id text primary key,
    prefix text,
    log_channel text
);

create type mod_action as enum ('kick', 'ban', 'timeout', 'warn');

create table mod_actions (
    id text not null,
    server_id text not null,
    moderator_id text not null,
    action mod_action not null,
    user_id text not null,
    reason text default null
);

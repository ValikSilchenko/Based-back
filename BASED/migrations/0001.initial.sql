create table "user"(
    "id" serial primary key,
    "name" varchar(256) not null,
    "created_timestamp" timestamp not null default (now() at time zone 'utc')
);
create table "task"(
    "id" serial primary key,
    "title" varchar(128),
    "description" varchar,
    "status" varchar(16) not null,
    "responsible_user_id" int not null references "user"(id),
    "deadline" date not null,
    "cross_deadline" date,
    "task_delay_caused_by" int,
    "time_for_completion" int not null,
    "actual_start_date" date,
    "actual_finish_date" date,
    "actual_completion_time" int,
    "is_archived" bool not null default false,
    "created_timestamp" timestamp not null default (now() at time zone 'utc')
);
create table "task_depends"(
    "task_id" int,
    "depends_task_id" int,
    "created_timestamp" timestamp not null default (now() at time zone 'utc')
);
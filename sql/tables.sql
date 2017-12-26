

--ALTER TABLE ONLY frontendcache
--    ADD CONSTRAINT pkey PRIMARY KEY (x, y, zoom);


 
CREATE  TABLE object(
        position        geometry(Geometry, 3857) not null,
        inertia         _inertia not null default (0,0),
        acceleration    real not null default 0,
        rotation        real not null default 0,
        name            text primary key default random(),
	controller	text unique,
        boosting        smallint not null default 0,
        hp              real not null default 100, -- identifies ordering for checkpoints
        ontrack         bool not null default False,
        last_checkpoint int,
        weight          real not null default 1,
              check (weight >= 1 and weight < 5),
        typ             entity not null default 'car',
        modification    timestamp with time zone default now()
        --z_level int not null default 0, --not in use right now
        --additional jsonb -- not in use right now
) with (fillfactor=10);

CREATE TABLE object_static(
	position	geometry not null,
	rotation	real not null default 0,
	epoch		bigserial,
	typ		text,
	creation	timestamp with time zone default now()
);

CREATE INDEX ON object(position);
CREATE INDEX ON object(controller) WHERE controller is not null;
CREATE INDEX ON object(acceleration);
CREATE INDEX on object(typ) where typ != 'track';

CREATE TABLE homebase(
	controller text primary key,
	position geometry(point, 3857 )
)


CREATE  TABLE checkpoints_players( player_name text, cp_name text references object(name),
       starttime timestamp with time zone default now()   );
CREATE  TABLE object_hist( like  object, insertstamp timestamp with time zone default now());                                                               

CREATE  TABLE event(
 id bigserial primary key,
 typ _typ not null,
 referee text references object(name) on delete cascade,
 source text,
 payload text,
 modification timestamp with time zone default now() 
);


CREATE TABLE images(
 id serial primary key,
 data bytea,
 name text unique);






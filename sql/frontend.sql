--drop table frontendcache;

CREATE TABLE frontendcache (
    x numeric NOT NULL,
    y numeric NOT NULL,
    zoom numeric NOT NULL,
    zlevel smallint not null default 0,
    data text
);


CREATE TABLE frontendcache_tracks (
    x numeric NOT NULL,
    y numeric NOT NULL,
    zoom numeric NOT NULL,
    trackmax bigint NOT NULL,
    data text
);




ALTER TABLE ONLY frontendcache
    ADD CONSTRAINT pkey PRIMARY KEY (x, y, zoom);

CREATE TABLE frontendimages(
        name text primary key,
        data bytea
);


--DROP   TABLE renderdata CASCADE;
CREATE TABLE renderdata(
	id serial,	

	key text,
	value text,

	type text,
	zlevel int,	
	color text,
	_width float
	);

COPY renderdata (id, key, value, type, zlevel, color, _width) FROM stdin;
1	boundary	postal_code	polygon	-100	color=(55 ,50+qid%55 ,55)	0
2	leisure	any	polygon	-20	color=(55 ,10+qid%55 ,55)	0
3	surface	any	polygon	-19	color=(55 ,10+qid%55 ,55)	0
4	wetland	any	polygon	-18	color=(0 ,10+qid%55 ,0)	0
5	sport	any	polygon	-17	color=(70,10+qid%55 ,0)	0
6	wood	any	polygon	-16	color=(0 ,10+qid%55 ,0)	0
7	natural	any	polygon	-15	color=(0 ,10+qid%55 ,0)	0
8	landuse	any	polygon	-14	color=(0 ,10+qid%55 ,0)	0
8	landuse	residential	polygon	-11	color=(10+qid%55 ,10+qid%55 ,10+qid%55)	0
8	landuse	garages	polygon	-10	color=(10+qid%55 ,10+qid%55 ,10+qid%55)	0
9	amenity	grassland	polygon	-13	color=(10+qid%55 ,10+qid%55 ,255)	0
9	amenity	parking	polygon	-12	color=(70+qid%55 ,70+qid%55 ,70+qid%55)	0
9	amenity	school	polygon	-12	color=(70+qid%55 ,70+qid%55 ,70+qid%55)	0
9	amenity	place_of_worship	polygon	-12	color=(70+qid%55 ,70+qid%55 ,70+qid%55)	0
9	amenity	public_building	polygon	-12	color=(70+qid%55 ,70+qid%55 ,70+qid%55)	0
11	building	any	polygon	99	color=(0 ,0 ,0)	4
11	building	any	polygon	100	color=(130+qid%55 ,110+qid%55 ,110+qid%55)	0
12	highway	primary	line	5	color=(0 ,0 ,0)	30
13	highway	primary	line	6	color=(130+qid%55 ,130+qid%55 ,130+qid%55)	28
14	highway	primary	line	7	color=(255 ,255 ,255)	1
15	highway	service	line	5	color=(0 ,0 ,0)	25
16	highway	service	line	6	color=(130+qid%55 ,130+qid%55 ,130+qid%55)	23
17	highway	service	line	7	color=(255 ,255 ,255)	1
18	highway	residential	line	5	color=(0 ,0 ,0)	20
19	highway	residential	line	6	color=(130+qid%55 ,130+qid%55 ,130+qid%55)	18
20	highway	residential	line	7	color=(255 ,255 ,255)	1
22	highway	any	line	5	color=(0 ,0 ,0)	20
22	highway	any	line	6	color=(155 ,155 ,155)	18
22	highway	any	line	7	color=(255 ,255 ,255)	1
21	footway	any	line	3	color=(255 ,0 ,255)	8
27	water	any	polygon	-1	color=(0 ,0 ,130)	0
28	waterway	any	polygon	2	color=(80 ,80 ,170)	40
21	barrier	any	line	10	color=(0 ,0 ,0)	4
\.

SELECT pg_catalog.setval('renderdata_id_seq', 1, true);

CREATE OR REPLACE VIEW all_render AS 
	SELECT * FROM all_osm ao 
		JOIN renderdata rd ON ao.tags-> rd.key = rd.value or (rd.value='any' and ao.tags-> rd.key is not null);



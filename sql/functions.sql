CREATE OR REPLACE FUNCTION floats_to_geo(x double precision, y double precision) RETURNS geometry AS $$
SELECT ST_SetSRID(ST_MakePoint(x, x),3857)
$$ language SQL; 

SELECT floats_to_geo (12, 13);




CREATE OR REPLACE FUNCTION applyphysics() RETURNS TRIGGER AS $example_table$
DECLARE
RC integer;
COLLIDER object;
inertia _inertia;
timediff float;
inertiafact real;
BEGIN
IF NEW.typ = 'pedestrian' THEN 
	inertiafact = 0.7;
ELSE
	inertiafact = 0.96;
END IF;
NEW.boosting = new.boosting-1;
NEW.acceleration=(CASE WHEN abs(new.acceleration) > 0.000001 THEN (CASE WHEN old.boosting > 0 THEN new.acceleration*0.5 ELSE new.acceleration*0.1 END) ELSE 0 END);
SELECT extract(epoch from age(old.modification,new.modification) ) into timediff; 
NEW.inertia=(
(CASE WHEN abs((new.inertia).x) > 0.00001 THEN inertiafact* ((0.99*(new.inertia).x) -(0.01* cos(radians(new.rotation)) / (abs(cos(radians(new.rotation)))+abs(sin(radians(new.rotation))))* (abs((new.inertia).x)+abs((new.inertia).y)))) ELSE 0 END),
(CASE WHEN abs((new.inertia).y) > 0.00001 THEN inertiafact* ((0.99*(new.inertia).y) +(0.01* sin(radians(new.rotation)) / (abs(cos(radians(new.rotation)))+abs(sin(radians(new.rotation))))* (abs((new.inertia).x)+abs((new.inertia).y)))) ELSE 0 END) );   


SELECT 1 INTO RC from planet_osm_line a where a.highway not in ('steps','rejected','proposed') and st_dwithin(a.way,NEW.position, 20) limit 1;
IF RC IS NULL THEN
    NEW.inertia = ((NEW.inertia).x*0.95, (NEW.inertia).y*0.95);
    NEW.ontrack=False;
	-- ADDTRACK?
ELSE
    NEW.ontrack=True;
END IF;

SELECT 1 INTO RC 
	from planet_osm_polygon p2 
	WHERE landuse is null 
		and "natural" is null 
		and boundary is null 
		and sport is null 
		and leisure is null 
		and area is null 
		and (amenity is null or amenity != 'parking') 
		and NEW.typ in ('bullet','car') 
		and  st_dwithin(p2.way, NEW.position,3*NEW.weight) 
		and building != 'roof';    
        IF RC IS NOT NULL THEN 
	NEW.hp = NEW.hp-(abs((NEW.inertia).x)+abs((NEW.inertia).y))*3;
        NEW.inertia = (0,0)::_inertia;
	NEW.position =st_translate(NEW.position, -(OLD.inertia).x*4, -(OLD.inertia).y*4);
	NEW.acceleration =0;
	IF NEW.hp < 0 THEN
	   NEW.typ = 'wreck';
	END IF;
	END IF;
RETURN NEW;
    END;
$example_table$ LANGUAGE plpgsql;



CREATE OR REPLACE FUNCTION applyphysics_post() RETURNS TRIGGER AS $example_table$
DECLARE
RC integer;
COLLIDER object;
COLLIDER_TMP object;
BEGIN

FOR COLLIDER IN 
SELECT p2.* FROM object p2
       WHERE st_dwithin(NEW.position, p2.position,4*(NEW.weight+p2.weight))
       	     and NEW.name != p2.name
	     and p2.typ in ('car','bullet','target')
	     and NEW.typ in ('car') --RETURNING * --INTO COLLIDER;
	     LOOP 
             COLLIDER_TMP = (collide_a_with_b(COLLIDER, NEW)::object) ; 
	     UPDATE object o SET position=COLLIDER_TMP.position
				,inertia=COLLIDER_TMP.inertia
				,modification=now() 
				WHERE name = COLLIDER.name;
	     END LOOP;

RETURN NEW;
    END;
$example_table$ LANGUAGE plpgsql;


CREATE TRIGGER applyphysics_t BEFORE UPDATE ON object FOR EACH ROW
WHEN (not ST_EQUALS(NEW.position,OLD.position))
EXECUTE PROCEDURE applyphysics();

CREATE TRIGGER applyphysics_t_post AFTER UPDATE ON object FOR EACH ROW
WHEN (not ST_EQUALS(NEW.position,OLD.position))
EXECUTE PROCEDURE applyphysics_post();


CREATE OR REPLACE FUNCTION mount(controllername text) returns void AS $$
DECLARE
 oldpos object;
 newpos object;
BEGIN
	SELECT * INTO oldpos FROM object p WHERE controller = controllername;
	if oldpos.name is null then
		raise notice 'controllername not found';
		return;
	END IF;

	IF oldpos.typ = 'pedestrian' THEN
		SELECT * INTO newpos FROM object p 
			WHERE name != oldpos.name 
			AND typ = 'car' 
			AND controller is null
			and  st_dwithin(p.position, oldpos.position, 6) 
			order by st_distance(p.position, oldpos.position) asc limit 1;
		RAISE notice 'lol %', oldpos.name;
		RAISE notice 'lal %', newpos.name;
		IF newpos.name is not null THEN
			raise notice 'updating %', newpos.name;
			DELETE FROM object WHERE controller = oldpos.controller;
			UPDATE object SET controller = oldpos.controller
				WHERE name = newpos.name;
		ELSE
			raise notice 'nobody in range'; 
			return;
		END IF;
	elsif oldpos.typ = 'car' THEN
		UPDATE object SET controller = null WHERE name = oldpos.name;
		newpos = oldpos;
		newpos.name = newpos.controller;
		newpos.typ = 'pedestrian';
		INSERT INTO object VALUES (newpos.*);
		--DELETE FROM object WHERE name = oldpos.name;
	END IF;
return;
END $$ LANGUAGE plpgsql;



CREATE OR REPLACE FUNCTION spawn(name text, typ entity default 'car') returns bool AS $$
BEGIN
     BEGIN
		INSERT INTO object(name, typ, position, rotation)
      			VALUES (name,typ,ST_SetSRID(ST_MakePoint(1485334+random()*40,6892139.01+random()*40),3857),0 );
             -- INSERT INTO event (typ, referee, payload)
             --           VALUES ('message',name, name||' joined!');	
     exception when unique_violation THEN return true;END;
	return true;
END
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION guided_spawn(name text, positionx numeric, positiony numeric) returns bool AS $$
BEGIN
     BEGIN
		INSERT INTO object(name, typ, position, rotation, controller)
      			VALUES (name,'car',ST_SetSRID(ST_MakePoint(positionx, positiony),3857),0, name );
             -- INSERT INTO event (typ, referee, payload)
             --           VALUES ('message',name, name||' joined!');	
     exception when unique_violation THEN return true;END;
	return true;
END
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION reset(n text) returns void AS $$
	UPDATE object 
		SET position = ST_SetSRID(ST_MakePoint(716422.9+random()*80,6656813.01+random()*80),3857), hp = 100, typ = 'car'
	WHERE name = n;
$$ LANGUAGE SQL;

CREATE OR REPLACE FUNCTION addtrack(p geometry, rotation float, weight float) returns bool AS $$
DECLARE
 rand float;
BEGIN
	--RETURN True; -- for now, lets ignore tracks
        INSERT INTO object (name, typ, position, rotation, weight)
                VALUES ('__track'||random()::text, 'track', p,rotation, weight);
        RETURN True;
END
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION turn(d float, n text) RETURNS VOID AS $$
DECLARE
pos geometry;
i float;
dir float;
BEGIN
UPDATE object  o SET rotation = o.rotation+(d/(1.0+abs((o.inertia).x)+abs((o.inertia).y))) WHERE controller = n RETURNING o.position, o.rotation, (abs((o.inertia).x)+abs((o.inertia).y)) INTO pos, dir, i;
IF i > 1 THEN PERFORM addtrack ( pos, dir, 1); END IF;
--RETURN;
END;
$$ LANGUAGE plpgsql;



CREATE OR REPLACE FUNCTION aligncars() RETURNS VOID AS $$
BEGIN
UPDATE object SET px= 716578+10*a.rnum , py = 6656688, vx = 0, vy = 0, i = 0, r = 90 FROM (SELECT name ,row_number() OVER (order by name) as rnum FROM object WHERE typ='car')a WHERE typ = 'car' and object.name = a.name ;
END;
$$ LANGUAGE PLPGSQL;



CREATE OR REPLACE FUNCTION cleanup() RETURNS int AS $$
        DECLARE
        pedcnt int;
        BEGIN
		    INSERT INTO event(typ, referee, payload) 
                      SELECT 'message',referee, referee||' left' FROM
                        (SELECT min(age(now(), modification) )  lastupdate, referee 
                         FROM event where typ = 'isalive' GROUP BY referee) a 
                      WHERE lastupdate > interval '5seconds';

                    DELETE FROM event WHERE  (age(now(), modification) > interval '5seconds' and typ != 'isalive')
				or (age(now(), modification) > interval '10seconds' and typ = 'isalive');	


                    DELETE FROM object WHERE typ = 'bullet' and age(now(), modification) > interval '5seconds';
                    --SELECT count(*) INTO pedcnt FROM object where typ = 'pedestrian';
                    --if pedcnt < 100 THEN
	            --        perform spawn_pedestrian(px-500*sin(radians(r)), py+500*cos(radians(r))) from object  where typ = 'car' ;
		    --END if;
                    DELETE FROM object WHERE typ in ('track', 'pedestrian') and name not in ( select p1.name from object p1 , object p2 where  p1.typ in ('pedestrian','track') and  p2.typ = 'car'  and abs(p1.px-p2.px)+ abs(p1.py-p2.py) <1000) ; 
--                    SELECT count(*) INTO pedcnt FROM object WHERE typ = 'track';
--                    IF pedcnt < 250 THEN
--                    DELETE FROM object WHERE typ = 'track' and age(now(), modification) > interval '120seconds'; 
--                    
--                    ELSIF pedcnt < 500 THEN
--                    DELETE FROM object WHERE typ = 'track' and age(now(), modification) > interval '10seconds'; 
--                    ELSE
--                    DELETE FROM object WHERE typ = 'track' and age(now(), modification) > interval '1seconds'; 
--                    END IF;

                    --DELETE FROM object WHERE typ='blood' and name not in ( select p1.name from deko_long p1 , objects_long p2 where  p1.typ='blood' and  p2.typ = 'car'  and abs(p1.px-p2.px)+ abs(p1.py-p2.py) <1000); 
               
                    --INSERT INTO object_hist SELECT * FROM object WHERE typ = 'car';
                    --DELETE FROM object_hist WHERE  age(now(), insertstamp) > interval '5seconds';
                RETURN NULL;
        END;
$$ LANGUAGE plpgsql;



SELECT spawn('DEMOCAR'||nr) FROM generate_series(1,5) nr;
--SELECT spawn('target0', 'target');

SELECT spawn('jsc');
update object set controller='jsc', typ='pedestrian' where name='jsc';


UPDATE object SET acceleration = 3 WHERE name = 'DEMOCAR1';

--SELECT generate_series(1,100000), addtrack(10, 10, 0, 1);
--UPDATE OBJECT SET typ='target', weightfactor = 4 WHERE name = 'target0';

vacuum analyze object;

UPDATE object o SET 
               inertia=
                (       ((o.inertia).x/5)*4+((o.inertia).x-cos(radians(rotation))*acceleration*0.4/weight)/5,
                        ((o.inertia).y/5)*4+((o.inertia).y+sin(radians(rotation))*acceleration*0.4/weight)/5  ),
               position=o.position+o.inertia* extract(epoch from age(now(),o.modification) ) ,
               modification = now()
               WHERE  
                    (abs((o.inertia).x)+abs((o.inertia).y)>0 or acceleration != 0) AND typ in ('car','pedestrian','bullet');

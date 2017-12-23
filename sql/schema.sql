DROP SCHEMA IF EXISTS RC CASCADE;
CREATE SCHEMA rc;

--public, as i may need it later for OSM data (it's quite helpfull to store those outside of the volatile schema

SET search_path TO rc, public;

CREATE TABLE meta( revision numeric, installed timestamp with time zone, name text);
INSERT INTO meta VALUES (0.01,now(), 'dev');

CREATE EXTENSION plpythonu;

CREATE EXTENSION unaccent;
CREATE or replace VIEW all_osm as SELECT * FROM planet_osm_polygon UNION ALL SELECT * FROM planet_osm_line ;



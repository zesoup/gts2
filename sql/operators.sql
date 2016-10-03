CREATE OR REPLACE FUNCTION pos_add_inert(p geometry,i _inertia) RETURNS geometry AS
'SELECT ST_Translate(p, i.x, i.y)' language SQL;

CREATE OR REPLACE FUNCTION inert_mult_time(i _inertia, fact double precision) RETURNS _inertia AS
'SELECT ((i.x*fact*80),(i.y*fact*80))::_inertia;' language SQL;

CREATE OR REPLACE FUNCTION collide_a_with_b( a object, b object ) RETURNS object AS $$
DECLARE
	j_a jsonb;
	j_b jsonb;
	output object;
	deltax double precision;
	deltay double precision;
BEGIN
 j_a=st_asgeojson(a.position);
 j_b=st_asgeojson(b.position);
 output =b;
deltax = (j_a->'coordinates'->>0)::double precision
                        -(j_b->'coordinates'->>0)::double precision;
deltay = (j_a->'coordinates'->>1)::double precision
                        -(j_b->'coordinates'->>1)::double precision;
deltax = deltax * (b.weight / a.weight);
deltay = deltay * (b.weight / a.weight);


 output.inertia=( (a.inertia).x*0.4 + (b.inertia).x*0.4+(deltax*0.001),
		  (a.inertia).y*0.4 + (b.inertia).y*0.4+(deltay*0.001));
 output.position=ST_SetSRID(ST_MakePoint( 
		(j_a->'coordinates'->>0)::double precision
			+deltax*0.02,
		(j_a->'coordinates'->>1)::double precision
			+deltay*0.02)
		, 900913);
RAISE LOG '% vs %', j_a, st_asgeojson(output.position);
 return output;
END $$ language plpgSQL;


CREATE OPERATOR + ( procedure = pos_add_inert, leftarg=geometry, rightarg=_inertia);
CREATE OPERATOR * ( procedure = inert_mult_time, leftarg=_inertia, rightarg=double precision);

SELECT st_asgeojson(ST_SetSRID(ST_MakePoint(12, 13),900913) + (1,1)::_inertia * extract(epoch from age('2016-03-09 10:34:19.350156','2016-03-09 10:34:18.350156') ));


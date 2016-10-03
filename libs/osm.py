#!/usr/bin/env python
# -*- coding: utf-8 -*-

import db

class OSM:
	def __init__(self):
		pass
	def stats(self):
		try:
			conn=db.pool.getconn()
			curs = conn.cursor()
			curs.execute("select name, round(st_area(way)), rank() over (order by st_area(way) desc ),st_astext(st_centroid(way)) center  from planet_osm_polygon where boundary = 'administrative' and name not ilike '%kreis%'  order by 2 desc limit 10;")
			top_citys=curs.fetchall()
			print "Biggest Areas:"
			for city in top_citys:
				print " %2s : %s" % (city[2], city[0])
			curs.execute("select sum(reltuples), pg_size_pretty(sum(pg_relation_size(oid))) from pg_class where relname ilike 'planet_osm_%'");
			tuples=curs.fetchone()
			print "OnDisk:  %dTuples(%s)" % (tuples[0],tuples[1])


			curs.close()
			db.pool.putconn(conn)
		except Exception as e:
			print e
		pass

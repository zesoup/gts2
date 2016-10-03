#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import libs.db
import sys
import time
import getpass
import json

parser = argparse.ArgumentParser()
parser.add_argument('-S', '--setup', action='store_true', default= False, 
                        help="Setup the Environment" )
parser.add_argument('-v', '--verbose', action='store_true', default=False,  
                        help="Print additional Logmessages" )

parser.add_argument('-V', '--version', action='store_true', default= False, 
                        help="Show game- and Schemaversion" )
parser.add_argument('-O', '--osmstats', action='store_true', default= False, 
                        help="Show Information about OSM" )
parser.add_argument('-F', '--forcespawn', action='store_true', default=False,  
                        help="Force a Respawn" )


parser.add_argument('-n', '--username', default=getpass.getuser(),
			help="Set a Username. Defaults to executing user")

args=parser.parse_args()
if 'help' in args:
	usage()
	sys.exit(0)

if args.version:
	from libs.version import VERSION
	VERSION().run()
	sys.exit(0)

if args.osmstats:
	from libs.osm import OSM
	OSM().stats()
	sys.exit(0)

print "Launching Game"
from libs import renderer
from libs import db
import pygame


game=renderer.game(args.username)
conn=db.pool.getconn()
cursor=conn.cursor()
cursor.execute(" SELECT * FROM object WHERE name = %s ", (args.username,)); 

if (args.forcespawn or cursor.rowcount < 1 ):
	print "Executing MapSelector"
	newspawnlocation = game.spawnselector(args.username)
	time.sleep(3)
	#print "You chose %s"% (newspawnlocation)

cursor.execute("SELECT o.name, p.name, st_asgeojson(o.position) from object o,  planet_osm_polygon p WHERE o.controller=%s AND  st_dwithin(p.way, o.position, 1) and boundary='administrative' ORDER by st_area(p.way) asc limit 1;", (args.username,))
user = cursor.fetchone()
try:
	game.userpos = json.loads(user[2])['coordinates']
	print "Your Account '%s' is located at %s near %s" % (user[0], game.userpos, user[1])
except:
	print "Please spawn first (-F)"
	renderer.panic=True
	sys.exit(1)
cursor.close()
conn.commit()
db.pool.putconn(conn)
game.initbg()
print "Entering MainLoop"
while True:
	game.getKeys()
	game.finishFrame()
	game.clock.tick(50)


#!/usr/bin/env python                                                                                       
# -*- coding: utf-8 -*-


import pygame
import db
import json
from random import random
import sys
import threading
import multiprocessing
import cairo


import rastermap
import time
import datetime

import cPickle

import psycopg2
from sprites import Sprite
from objectmanager import objectmanager
from objects import drawableobject

import collections

global panic
panic = False

querylog=collections.deque(maxlen=20)
querylog_sem=threading.Semaphore()
querycount = 0
def logQ(txt):
	#return txt
	global querycount
	querycount =querycount + 1
	querylog_sem.acquire()
	shortq = txt[:60]
	if len(txt) > 60:
		shortq+='..'
	querylog.append ("%s) %s"%(querycount, shortq))
	querylog_sem.release()
	return txt

class objectpuller( threading.Thread):
        def __init__(self,centerobject, objectman, username):
                threading.Thread.__init__(self)
                self.centerobject = centerobject
		self.objectman = objectman
		self.username=username
		conn = db.pool.getconn()
		curs = conn.cursor()
		self.hold=True
		pos=(0,0)
		print pos
		curs.close()
		db.pool.putconn( conn )
	def run(self):
		global panic
		age = 0
		while not panic:
			age = age + 1
			while not panic and self.hold:
				time.sleep(0.001)
			self.hold=True
			conn = db.pool.getconn()
			curs = conn.cursor()
			try:
				#curs.execute("SELECT st_asgeojson(position),rotation FROM object WHERE name = 'jsc'")
				curs.execute(logQ("SELECT name, st_asgeojson(position),rotation, typ, controller, hp, modification FROM object WHERE typ != 'track' "))

				objects = curs.fetchall()
				self.objectman.lock.acquire(True)	
				for r in objects:
					(name, p, rot, typ, controller,hp, modification) = r
					#print "ObjectOffseT: %s " %(time.time()-time.mktime( modification.timetuple() ) ) 
					pos = json.loads(p)['coordinates']
					if not name in self.objectman.objectlist or typ != self.objectman.objectlist[name].typ:
						print ("SPAWN %s"%(name,) )
						add = drawableobject(name, pos )
						add.SetSprite( Sprite('images/'+typ+'.png', (50,50), transparent=True ))
						add.position=pos
						add.typ = typ
						add.rotation=rot
						add.hp = hp
						add.controller = controller
						self.objectman.objectlist[name]=add
					self.objectman.objectlist[name].position=pos
					self.objectman.objectlist[name].controller=controller
					self.objectman.objectlist[name].rotation=rot
					self.objectman.objectlist[name].hp=hp
					self.objectman.objectlist[name].typ=typ
					self.objectman.objectlist[name].age = age
				dellist = []
				for x in self.objectman.objectlist:
					if self.objectman.objectlist[x].age != age:
						 dellist.append(x)
				for x in dellist:
					del(self.objectman.objectlist[x])
				self.objectman.lock.release()
			except Exception as e:
				print e
				print "Environmenter phase1"
				pos=(0,0)

			try:
				if age % 50 == 30:
					curs.execute(logQ("DELETE from object where name in (SELECT name FROM object WHERE typ = 'track' and age(now(), modification) > interval'4seconds' order by modification desc);"), )

				if age % 50 == 10:
					
					curs.execute(logQ("""SELECT unaccent(coalesce(name, ref))
						 FROM planet_osm_line a join ( SELECT position FROM object WHERE controller = %s) b
							on 1=1 
				            WHERE a.highway not in ('steps','rejected','proposed') 
			                    and st_dwithin(a.way, b.position, 20) 
                    				and (ref is not null or name is not null) 
 					           limit 1"""), (self.username,) )
					street = curs.fetchone()
					if street:
						self.objectman.currentstreet = street[0]

			except Exception as e:
				print e
				print "environmenter phase 2"
			curs.close()
			db.pool.putconn( conn )

class ticker( threading.Thread ):
	def __init__(self):
		threading.Thread.__init__(self)
		pass
	def run(self):
		global panic
		while not panic:
			time.sleep(0.018)
			conn = db.pool.getconn()
			cursor = conn.cursor()
                        try:
			    logQ("SELECT tick(%s))")##Still havent migrated the tick to a function.. Lets pretend for demonstrational purposes
			    cursor.execute("""UPDATE object o SET 
               inertia=
                (       ((o.inertia).x/10.0)*9+((o.inertia).x-cos(radians(rotation))*acceleration*0.4/weight)/10.0,
                        ((o.inertia).y/10.0)*9+((o.inertia).y+sin(radians(rotation))*acceleration*0.4/weight)/10.0  ),
               position=o.position+o.inertia* extract(epoch from age(now(),o.modification) ) ,
               modification = now()
               WHERE  
                    (abs((o.inertia).x)+abs((o.inertia).y)>0 or acceleration != 0) 
                        AND typ in ('pedestrian','car', 'bullet')
                        AND ( age(now(),modification)> interval '10 milliseconds')
                 ;""", )
                        except:
                            pass
                        try:
			    cursor.close()
			    conn.commit()
                        except:
                            pass
			db.pool.putconn(conn)
	

class environmenter(threading.Thread):
	def __init__(self, rm, centerobject='jsc'):
		threading.Thread.__init__(self)
		self.centerobject = centerobject
		self.rasterpool = rm
		#self.renderrequests = dict()
	def run(self):
		global panic
		while not panic:
			currentRequest = None
			conn=db.pool.getconn()
			conn.set_session( autocommit = True )	
                        #print("Environmenter pulled connection")
                        try:
				time.sleep(0.01)
				if not self.rasterpool._requestqueue:
					time.sleep(.05)
					self.rasterpool.cleanup()
                                        raise Exception("Nothing to do..")
					continue
				#print len(self.rasterpool._requestqueue)
				if 1:
					zoom = self.rasterpool.size
					pixpermap = self.rasterpool.pixpermap
					_pos=self.rasterpool.getRequest(self)
					currentRequest = _pos
					if _pos == None:
                                                raise Exception ("Nothing to do")
						continue
					#conn=db.pool.getconn()
					#conn.set_session( autocommit = True )
					curs = conn.cursor()
					curs.execute(logQ("SELECT x, y, zoom, data FROM frontendcache WHERE x = %s and y = %s and zoom=%s"),
							(_pos[0], _pos[1], zoom)
								)
					d = curs.fetchone()
					if d != None:
						#print len(data)
						x, y, _zoom, data = d
						#dbimg = pygame.image.fromstring( data.decode('hex'), pixpermap, 'RGBA' )
						dbimg = pygame.image.fromstring( data.decode('hex') , pixpermap, 'RGBA' )
						rasterimg = pygame.Surface( pixpermap, pygame.SRCALPHA, 32)
						rasterimg.blit( dbimg, (0,0) ) ## THIS STEP IS IMPORTANT. BUT I DO NOT KNOW WHY
						r= rastermap.raster(rasterimg,_pos)
						self.rasterpool.putraster(r)
						#self.rasterpool._inflightqueue.remove(_pos)
					else:
						curs.execute(logQ("SELECT renderbackend( %s, %s, %s, %s, %s, %s)"),(_pos[0], _pos[1], int(pixpermap[0]*1) , int(pixpermap[1]*1) , zoom*1., zoom*1.  ) )
						self.rasterpool._inflightqueue.remove(_pos)
 					#r = rastermap.raster(rasterimg, _pos)	
					#self.rasterpool.putraster(r)	
				#conn.commit()
				#curs.close()
				#db.pool.putconn( conn )
				#return;
			except Exception as e:
				#print "vvvvv"
				#print e
				#print "Environmenter ERROR"
                                #import traceback
                                #traceback.print_exc()
				#self.rasterpool.releaseRequest( currentRequest )
                                #time.sleep(0.02)
                                pass
                        #print("Environmenter gave connection")
                 	self.rasterpool.releaseRequest( currentRequest )
                        try:
                            conn.commit()
			    curs.close()
                        except:
                            pass
			db.pool.putconn(conn)
			time.sleep(0.02)

class game:
	def __init__(self, username,  size=(1200,800)):
		pygame.init()
		self.size = size
		self.screen = pygame.display.set_mode(size )
		pygame.display.set_caption("GrandTheftSchema2")
		pygame.mouse.set_visible(1)
		pygame.key.set_repeat(1, 1)

		self.renderitems=[]
		self.renderimages=[]
		self.renderlock = threading.Semaphore()
		self.clock = pygame.time.Clock()
		self.userpos = None
		self.username = username
		self.CACHEMODE = False
		self.font = pygame.font.Font("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)


		self.querybg = Sprite('images/querybg.png',(800,200), True)	
		self.forkme = Sprite('images/forkme.png',(298,298), True)
		self.GTS_OVERVIEW = Sprite('images/GTS_OVERVIEW.png',self.size, False)

                self._overviewmap = None
                self._overviewboundslower=None
                self._overviewboundsupper=None
                self._overviewsize=None

		self.lastactivity = time.time()


		self.kreis = Sprite('images/kreis.png',(20,20), True)	
		self.activelogo = Sprite('images/phant.png',(20,20), True)
		self.activelogo.xpos=0 
		#rasterm = rastermap.rastermap() 
		self.rastermap = rastermap.rastermap()

		self.envpool = []
		for x in range(0,multiprocessing.cpu_count()-1):
			a =  environmenter(self.rastermap)
			self.envpool.append( a )
			a.start()

		self.initBoundingBox()
		self.objectmanager = objectmanager()
		self.objectpuller = objectpuller(None,self.objectmanager, username )
		self.objectpuller.start()
		self.rastermap.setZoom(1)
		self.ticker=ticker()
		self.ticker.start()
		self.lastcontrolledobject = None
	def initbg(self):
		background = pygame.Surface(self.size, pygame.SRCALPHA, 32 )
		#background = pygame.Surface(self.size)
		background.fill((50,50,50,0))
		self.renderimages.append(background)

	def normalize(self, pos, offset, scale):
		return ( (pos[0]-offset[0])*scale[0], (pos[1]-offset[1])*scale[1]  )

	def renderenvironment(self):
		
		pass
	def putText(self,t,screen,pos, color=(255,255,255)  ):
		text = self.font.render(t, 3, color)
		textpos = text.get_rect()
		textpos.centerx = screen.get_rect().centerx
		screen.blit(text, pos )


	def prep(self):
		dx = self.bbupper[0] - self.bblower[0]
		dy = self.bbupper[1] - self.bblower[1]
		x = self.bblower[0]
		y = self.bblower[1]
		size = self.rastermap.size
		l = 0
		fieldsx =  dx/(self.rastermap.pixpermap[0]*size)
		fieldsy =  dy/(self.rastermap.pixpermap[1]*size)
		for _x in range(0, int(dx), self.rastermap.pixpermap[0]*size):
			print "LINE"
		
			for _y in range(0, int(dy), self.rastermap.pixpermap[1]*size):
				for readahead in range(1,8-len( self.rastermap._requestqueue ) ):
					self.rastermap.get( (_x+x, _y+y+readahead* self.rastermap.pixpermap[1]*size))
				s =  self.rastermap.get( (_x+x, _y+y), waitforimage=True).image
				#print len(self.rastermap._requestqueue)
				resx = int (self.size[0]/fieldsx )+1
				resy = int (self.size[1]/fieldsy )+1
				#print "%s, %s, %s, %s" %( resx, resy, dx,dy)
				self._map.blit(
					pygame.transform.scale(
								s ,( resx,resy ))
							, (_x/dx * self.size[0] , _y/dy*  self.size[1] ))
				l = l+1
				self.screen.blit( self._map,(0,0))
				self.LoadToScreen()
				pygame.display.flip()
		print "----"
		print l
		#time.sleep(99999)

	def initBoundingBox(self):
		conn=db.pool.getconn()
		curs = conn.cursor()
		curs.execute(logQ("select st_asgeojson(st_extent(way)) from planet_osm_polygon ;"));
		boundingbox = json.loads( curs.fetchone()[0] )['coordinates']
		smallest=boundingbox[0][0]
		biggest=boundingbox[0][2]
		self.bblower=smallest
		self.bbupper=biggest
		curs.close()
		conn.commit()
		db.pool.putconn( conn )

	def generateMap(self):
    		self.rastermap.setZoom(5)
                mapsize=(200,200)
                self._overviewsize=mapsize
		self._overviewmap = pygame.Surface(mapsize, pygame.SRCALPHA, 32 )
		self._overviewmap.fill((0,20,0,255))
		conn=db.pool.getconn()
		curs = conn.cursor()
		self.initBoundingBox()
		smallest = self.bblower
		biggest = self.bbupper
                self._overviewboundslower=smallest
                self._overviewboundsupper=biggest

		boundingsize=(biggest[0]-smallest[0], biggest[1]-smallest[1])
		scale= (mapsize[0]/boundingsize[0], mapsize[1]/boundingsize[1])

                curs.execute(logQ("""select unaccent(name), round(st_area(way)), st_asgeojson( way ), st_asgeojson( st_centroid(way) ),'polygon'  from (SELECT * FROM planet_osm_polygon where boundary = 'administrative' and name not ilike '%kreis%'  order by round(st_area(way)) desc limit 50 ) a
		UNION ALL
		SELECT unaccent(name), 0, st_asgeojson(way), '', 'line' FROM planet_osm_line WHERE highway is not null and highway in('primary','motorway_link',  'motorway')
"""))
		regions=curs.fetchall()
		names=dict()
		for region in regions:
			print "Worked on %s" %region[0]
			pts=[]
			typ = region[4]
			#print typ
			coords= json.loads(region[2])['coordinates']
			if typ != 'polygon':
				#print "NO POLY"
				for pt in coords:
					pts.append( ( (pt[0]-smallest[0])*scale[0],(pt[1]-smallest[1])*scale[1] ))
				pygame.draw.polygon(self._overviewmap , (0,0,0), pts,3)
				pygame.draw.polygon(self._overviewmap , (200,200,0), pts,2)

				continue
			for x in coords[0]:
				pts.append( ((x[0]-smallest[0])*scale[0],(x[1]-smallest[1])*scale[1]))
			center = json.loads( region[3])['coordinates']
			center = ((center[0]-smallest[0])*scale[0],(center[1]-smallest[1])*scale[1])
			pygame.draw.polygon(self._overviewmap , (20+random()*50,20+random()*50,20+random()*50), pts)
			pygame.draw.polygon(self._overviewmap , (200,200,200), pts,1)
			#self.putText(region[0], self._map, center)
			names[region[0]]= center
	
		#for cityname in names:
		#	self.putText( cityname, self._overviewmap, names[cityname] )  
		#randompos = ( 
                #         smallest[0]+(boundingsize[0]*0.25)+random()*0.5*boundingsize[0],
                #         smallest[1]+(boundingsize[1]*0.25)+random()*0.5*boundingsize[1])
		#crosspos = self.normalize( randompos, smallest, scale)
		#pygame.draw.lines(self._overviewmap, (255,0,0), True,[(crosspos[0]-7, crosspos[1]-7),(crosspos[0]+7, crosspos[1]-7), (crosspos[0]+7, crosspos[1]+7),(crosspos[0]-7, crosspos[1]+7) ] , 2)
		#self.putText( "you", self._map, crosspos, (0,0,255))	
		#self.screen.blit( self._map, (0,0))
		#curs.execute(logQ("DELETE FROM object WHERE controller = %s"), (name , ) )	
		#curs.execute(logQ("SELECT guided_spawn(%s, %s, %s)"), (name, randompos[0], randompos[1]) )
		conn.commit()
		curs.close()
		db.pool.putconn(conn)
		#pygame.display.flip()
		#time.sleep(20)
		#self.prep()
		return 1


	def spawnselector(self, name):
		self.rastermap.setZoom(5)
		self._map = pygame.Surface(self.size, pygame.SRCALPHA, 32 )
		self._map.fill((0,20,0,255))
		conn=db.pool.getconn()
		curs = conn.cursor()
		self.initBoundingBox()
		smallest = self.bblower
		biggest = self.bbupper
		boundingsize=(biggest[0]-smallest[0], biggest[1]-smallest[1])
		scale= (self.size[0]/boundingsize[0], self.size[1]/boundingsize[1])

                curs.execute(logQ("""select unaccent(name), round(st_area(way)), st_asgeojson( way ), st_asgeojson( st_centroid(way) ),'polygon'  from (SELECT * FROM planet_osm_polygon where boundary = 'administrative' and name not ilike '%kreis%'  order by round(st_area(way)) desc limit 50 ) a
		UNION ALL
		SELECT unaccent(name), 0, st_asgeojson(way), '', 'line' FROM planet_osm_line WHERE highway is not null and highway in('primary','motorway_link',  'motorway')
"""))
		regions=curs.fetchall()
		names=dict()
		for region in regions:
			print "Worked on %s" %region[0]
			pts=[]
			typ = region[4]
			#print typ
			coords= json.loads(region[2])['coordinates']
			if typ != 'polygon':
				#print "NO POLY"
				for pt in coords:
					pts.append( ( (pt[0]-smallest[0])*scale[0],(pt[1]-smallest[1])*scale[1] ))
				pygame.draw.polygon(self._map , (0,0,0), pts,3)
				pygame.draw.polygon(self._map , (200,200,0), pts,2)

				continue
			for x in coords[0]:
				pts.append( ((x[0]-smallest[0])*scale[0],(x[1]-smallest[1])*scale[1]))
			center = json.loads( region[3])['coordinates']
			center = ((center[0]-smallest[0])*scale[0],(center[1]-smallest[1])*scale[1])
			pygame.draw.polygon(self._map , (20+random()*50,20+random()*50,20+random()*50), pts)
			pygame.draw.polygon(self._map , (200,200,200), pts,1)
			#self.putText(region[0], self._map, center)
			names[region[0]]= center
	
		for cityname in names:
			self.putText( cityname, self._map, names[cityname] )  
		randompos = ( 
                         smallest[0]+(boundingsize[0]*0.25)+random()*0.5*boundingsize[0],
                         smallest[1]+(boundingsize[1]*0.25)+random()*0.5*boundingsize[1])
		crosspos = self.normalize( randompos, smallest, scale)
		pygame.draw.lines(self._map, (255,0,0), True,[(crosspos[0]-7, crosspos[1]-7),(crosspos[0]+7, crosspos[1]-7), (crosspos[0]+7, crosspos[1]+7),(crosspos[0]-7, crosspos[1]+7) ] , 2)
		self.putText( "you", self._map, crosspos, (0,0,255))	
		self.screen.blit( self._map, (0,0))
		curs.execute(logQ("DELETE FROM object WHERE controller = %s"), (name , ) )	
		curs.execute(logQ("SELECT guided_spawn(%s, %s, %s)"), (name, randompos[0], randompos[1]) )
		conn.commit()
		curs.close()
		db.pool.putconn(conn)
		pygame.display.flip()
		#time.sleep(20)
		#self.prep()
		return 1

	def getKeys(self):
		def singlepress():
			time.sleep (0.1)
			#some buttons are triggers and need to to understand
			
		global panic
		try:
			conn = db.pool.getconn()
			curs=conn.cursor()
			
			for event in pygame.event.get():
				self.lastactivity = time.time()
				#print event
				if pygame.key.get_pressed()[pygame.K_q]:
					panic = True
					sys.exit(0)
				if pygame.key.get_pressed()[pygame.K_e]:
					curs.execute(logQ("SELECT mount(%s);"),(self.username,))
					singlepress()
				if pygame.key.get_pressed()[pygame.K_r]:
					conn.commit()
					#curs.execute(" DELETE FROM  OBJECT WHERE controller is null;")
					curs.execute( logQ(" WITH del AS ( DELETE FROM OBJECT RETURNING * ) SELECT SPAWN(del.controller, 'pedestrian') FROM del WHERE controller is not null;") )
					#curs.execute(" SELECT SPAWN(object.controller, 'pedestrian') FROM object WHERE controller is not null;;", (self.username,) )
					curs.execute( logQ(" UPDATE OBJECT SET CONTROLLER = NAME "), (self.username,) )
					curs.execute( logQ(" SELECT spawn('democar'||id) FROM generate_series(1,5) id;"))
					conn.commit()
				if pygame.key.get_pressed()[pygame.K_t]:
					conn.commit()
					#curs.execute(" DELETE FROM  OBJECT WHERE controller is null;")
					curs.execute(" WITH del AS ( DELETE FROM OBJECT RETURNING * ) SELECT SPAWN(del.controller, 'pedestrian') FROM del WHERE controller is not null;" )
					#curs.execute(" SELECT SPAWN(object.controller, 'pedestrian') FROM object WHERE controller is not null;;", (self.username,) )
					curs.execute(" UPDATE OBJECT SET CONTROLLER = NAME WHERE NAME = %s;", (self.username,) )
					curs.execute(" SELECT spawn('democar'||id) FROM generate_series(1,5) id;")
					conn.commit()


                                if pygame.key.get_pressed()[pygame.K_p]:
					self.CACHEMODE=True			
					self.rastermap.setZoom(0.25)
				if pygame.key.get_pressed()[pygame.K_x]:
					self.rastermap.setZoom(50)		
				if pygame.key.get_pressed()[pygame.K_c]:
					self.rastermap.setZoom(20)	
				if pygame.key.get_pressed()[pygame.K_v]:
					self.rastermap.setZoom(10)	
				if pygame.key.get_pressed()[pygame.K_b]:
					self.rastermap.setZoom(5)
				if pygame.key.get_pressed()[pygame.K_n]:
					self.rastermap.setZoom(1)
				if pygame.key.get_pressed()[pygame.K_m]:
					self.rastermap.setZoom(0.25)
			if pygame.key.get_pressed()[pygame.K_RIGHT]:
					#self.userpos[0]=self.userpos[0]+100
					curs.execute(logQ("SELECT turn( -7.5, %s);"),(self.username, ) )
			if pygame.key.get_pressed()[pygame.K_LEFT]:
					pass
					curs.execute(logQ("SELECT turn( +7.5, %s);"),(self.username, ) )

					#self.userpos[0]=self.userpos[0]-100
			if pygame.key.get_pressed()[pygame.K_UP]:
					pass
					curs.execute(logQ("UPDATE object set acceleration = acceleration + 1 where controller = %s"),(self.username, ) )
			if pygame.key.get_pressed()[pygame.K_DOWN]:
					curs.execute(logQ("UPDATE object set acceleration = acceleration - 1 where controller = %s"),(self.username, ) )
					#self.userpos[1]=self.userpos[1]+100
			curs.close()
			conn.commit()
			db.pool.putconn(conn)

		except Exception as e:
			print e
			curs.close()
			conn.commit()
			db.pool.putconn(conn)


	def LoadToScreen(self):
		for x in range(0,len(self.rastermap._requestqueue)):
			self.screen.blit(self.activelogo.image,(0,20*x))
		for x in range(0,len(self.rastermap._inflightqueue)):
			self.screen.blit(self.activelogo.image,(20,20*x))

	def ToCenter(self, pos):
		zoom=		self.rastermap.size
		rendercenter=	self.userpos
		return( (pos[0]-rendercenter[0])/zoom+self.size[0]/2, 
			(pos[1]-rendercenter[1])/zoom+self.size[1]/2 )


	def finishFrame(self):
		
		#self.renderlock.acquire()
		zoom = self.rastermap.size
		try:  # Very quickly prototyped. things may fail alot due to the lack of proper handling
			try:
				if self.objectmanager.objectlist[self.lastcontrolledobject].controller == self.username:
					pass
				else:
					raise
			except:
				for obj in self.objectmanager.objectlist:
					if self.objectmanager.objectlist[obj].controller == self.username:
						self.lastcontrolledobject=obj
			self.userpos = self.objectmanager.objectlist[self.lastcontrolledobject].position						 
		except:
			print ("Could not focus on %s"%(self.username))
			print ("Skipping Frame")
			self.objectpuller.hold=False
			return

		rendercenter= self.userpos
		renderrect_lower = (rendercenter[0]-(self.size[0]/1.0)*zoom,rendercenter[1]-(self.size[1]/1.0)*zoom  )
		renderrect_upper = (rendercenter[0]+(self.size[0]/1.0)*zoom,rendercenter[1]+(self.size[1]/1.0)*zoom  )
		x = renderrect_lower[0]
		imgsize = (self.rastermap.pixpermap[0]*zoom,
				 self.rastermap.pixpermap[1]*zoom)
                loopcount = 0
		while x < renderrect_upper[0]:
			y=renderrect_lower[1]
			while y < renderrect_upper[1]:
				loopcount=loopcount+1
				m =  self.rastermap.get( (x, y) )
				if m != None:
					self.screen.blit (m.image,self.ToCenter(m.position))
				y = y+ imgsize[1]		
			x = x+imgsize[0]


		if zoom==20:
			self.CACHEMODE=False
		if self.CACHEMODE:
			zooms= dict()
			zooms[0.25]=0.5
			zooms[0.5] = 1
			zooms[1] = 5
			zooms[5] = 10
			zooms[10] = 20


			if not self.rastermap._requestqueue:
				self.rastermap.setZoom( zooms[zoom] )

		self.screen.blit( self.kreis.image, (self.screen.get_width()/2 - self.kreis.image.get_width()/2,self.screen.get_height()/2 - self.kreis.image.get_height()/2 ) )


		drawlist = self.objectmanager.objectlist
		try:
			self.objectmanager.lock.acquire(True)
			for drawable in drawlist:
				obj = drawlist[drawable]
				blitim = pygame.transform.rotate(obj.sprite.image, obj.rotation+180)
				blitim = pygame.transform.smoothscale( blitim , (int(blitim.get_width()/(4*zoom)),int(blitim.get_height()/(4*zoom) )))
				pos= self.ToCenter(obj.position)
				self.screen.blit( 
					blitim,
					(pos[0]-blitim.get_width()/2.0, pos[1]-blitim.get_height()/2.0)
					 )
				if obj.typ != 'track':
					self.putText('%s [%s]'%( drawable, int(obj.hp) ), self.screen, (pos[0]-10, pos[1]+20), (0,0,255))
			self.objectmanager.lock.release()
		except Exception as e:
			print e
			print "Could not draw objects. Possible concurrency issue"
			self.objectmanager.lock.release()
		self.LoadToScreen()
		try:
			self.putText('FPS %s'% ( int(self.clock.get_fps())),
					 self.screen, (100,25), (255,10, 10))

			self.putText('%s'% ( self.objectmanager.currentstreet,),
					 self.screen, (self.size[0]/2 - 100, self.size[1]/2 + 100), (255,0, 0))
		except:
			print "issue rendering FPS or Street"
		self.activelogo.xpos = (self.activelogo.xpos+2)%100

		for x in self.envpool:
			if not x.isAlive():
				x.join()
				self.envpool.remove(x)
				a =  environmenter(self.rastermap)
				self.envpool.append( a )
				a.start()
		#if time.time() - self.lastactivity > 20:
		#	self.screen.blit( self.GTS_OVERVIEW.image, (0,0) )
                try:
                    if self._overviewmap == None:
                        self.generateMap()
                    self.screen.blit( self._overviewmap,(10,10) )
                    nx = self.userpos[0] - self._overviewboundslower[0]
                    ny = self.userpos[1] - self._overviewboundslower[1]


                    facx = self._overviewboundsupper[0] - self._overviewboundslower[0]
                    facy = self._overviewboundsupper[1] - self._overviewboundslower[1]

                    nx = 10+(nx / facx)*200.
                    ny = 10+(ny / facy)*200.


                    crosspos=( nx, ny)
                    #print(crosspos)
		    pygame.draw.lines( self.screen, (255,0,0),
                                True,[(crosspos[0]-5, crosspos[1]-5),(crosspos[0]+5, crosspos[1]-5), (crosspos[0]+5, crosspos[1]+5),(crosspos[0]-5, crosspos[1]+5) ] , 2)
	
                except Exception as e:
                    print("Could not draw map")
                    print(e)
                try:
                    offset=0
                    for element in querylog:
                        #continue
                        offset+=15
		        self.putText('%s'% ( element ),
		    	    self.screen, (10,790-offset), (255,255, 255))
                except Exception as e:
                    print(e)
                    pass

		self.screen.blit( self.forkme.image, (self.size[0]-self.forkme.image.get_width(),0) )

		self.objectpuller.hold=False
		pygame.display.update()

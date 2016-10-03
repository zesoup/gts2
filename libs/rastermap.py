from sprites import Sprite
from threading import Semaphore
import time
class raster():
	def __init__(self, image, position):
		self.position=position
		self.image=image
		self.lru=0

class rastermap():
	def __init__(self, size=10, pool=100):
		self.size = size #realworld unit. 1 means 1pix for 1'unit'. 0.1 means 0.1'units' per pix
		self.pixpermap = (300,300)
		self.pool=pool
		self._contents = dict()
		self._totalgets = 0
		self._requestqueue= dict()
		self._inflightqueue=[]
		self.nasprite = Sprite(size=self.pixpermap, transparent=False)
		self.lock = Semaphore()

	def getRequest(self, caller):
		#return
		#self.lock.acquire()
		for key in self._requestqueue.keys():
			if key in self._inflightqueue:
				continue
			self._inflightqueue.append( key )
			self.lock.release()
			return key
		#self.lock.release()
	def releaseRequest(self, key):
		for _key in self._inflightqueue:
			if key == _key:
				self._inflightqueue.remove( key )
	def addZoom(self, zoom):
		self.setZoom( self.size + zoom)
	def setZoom(self, zoom):
		if zoom <=0:
			zoom = 0.25
		self.lock.acquire()
		self.size = zoom
		self._contents = dict()
		self._requestqueue = dict()
		self._inflightqueue = []
		self.lock.release()
	def cleanup(self):
		if len(self._requestqueue) == 0 and len(self._inflightqueue)==0:
			self._requestqueue = dict()
			self._inflightqueue = []

	def putraster(self, raster):
		raster.lru = 10
		#raster.position = (raster.position[0] - raster.position[0]%(self.size*self.pixpermap[0]), raster.position[1] - raster.position[1]%(self.size*self.pixpermap[1]) )
		#print "putting %s" %(raster.position,)
		#print "Poolsize: %s" %( len(self._contents))

		old = self.get( raster.position, False )
		if old:
			#self._contents.remove( old )
			self._contents[raster.position] = raster
			return
		#self.lock.acquire()
		if len(self._contents.keys()) > self.pool:
			self.evict()
		if len(self._contents.keys()) > self.pool:
			print "Cache is still oversized."
			print "Second round of evict!"
			self.evict()
		self.clock()
		self._contents[raster.position] = raster
		#self.lock.release()
		try:
			del self._requestqueue[raster.position]
			self._inflightqueue.remove(raster.position)	
		except Exception as e:
			print e
			print "COULD NOT REMOVE REQUEST!"
	def get(self, position, defaultIfNone=True, waitforimage=False):
		#self.lock.acquire()
		self._totalgets = self._totalgets+1
		position = (position[0] - position[0]%(self.size*self.pixpermap[0]), position[1] - position[1]%(self.size*self.pixpermap[1]) )
		#print "getting pos: %s" %(position,)
		#try:
		x = None
		while True:
			if position in self._contents.keys():
				x = self._contents[position]
				x.lru=10
				try:
					del self._requestqueue[position]
				except:
					#print "couldnt remove request i allready have"
					pass
				#self.lock.release()
				return x
			elif not waitforimage:
				self._requestqueue[position]=1
				#print "notwaiting"
				break
			time.sleep(0.01)
			self._requestqueue[position]=1
			self.clock()
		#self.lock.release()
		if defaultIfNone:
			return raster(self.nasprite.image, position)
		return None
		#return raster(self.nasprite.image, position)
	def clock(self):
		try:
			for x in self._contents.keys():
				self._contents[x].lru=self._contents[x].lru-1
		except:
			pass
	def evict(self):
		smallest=None
		for poolitem in self._contents.keys():
			if smallest == None or self._contents[poolitem].lru < smallest.lru :
				smallest=self._contents[poolitem]
		del self._contents[smallest.position]

if __name__ == '__main__':
	print "Testing Rastermap"
	attempts = 50*1000
	m = rastermap()
	while attempts > 0:
		attempts=attempts-1
		item=raster(None, (attempts%10,attempts) )
		m.putraster(item)
	#for x in m._contents:
	#	print x.lru

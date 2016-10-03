from threading import Semaphore

class objectmanager():
	def __init__(self):
		self.objectlist = dict()
		self.lock = Semaphore()


import sprites

class drawableobject():
	def __init__(self, _id, position):
		self._id = _id
		self.position=position
		self.size = 1
		self.rotation = 0
		self.sprite=None
	#Semaphores
	def access(self):
		pass
	def release(self):
		pass

	def SetSprite(self, sprite):
		self.sprite=sprite

	def asImage(self, absolute=True):
		return (self.position, self.rotation, self.size, self.image) 

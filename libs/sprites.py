import  pygame

spritecache = dict()


class Sprite(pygame.sprite.Sprite):
	def __init__(self, image='images/na.png', size=(100,100), transparent=False):
		super(Sprite, self).__init__()
		identifier = "%s %s %s" %(  image, size[0]*size[1] , transparent) 
		print identifier
		if identifier in spritecache:
			self.image = spritecache[identifier]
			return
		if not transparent:
			self.image = pygame.Surface( size, pygame.SRCALPHA, 32)
			self.image.fill((255,255,255,100))
			try:
				self.image.blit(pygame.transform.smoothscale(  pygame.image.load(image), size),(0,0))
			except:
				print "not found.."
				self.image.blit(pygame.transform.smoothscale(  pygame.image.load('images/na.png'), size),(0,0))
	
		else:
			try:
				self.image=pygame.transform.smoothscale( pygame.image.load(image), size)
			except:
				self.image=pygame.transform.smoothscale( pygame.image.load('images/na.png'), size)
	

		spritecache[identifier] = self.image

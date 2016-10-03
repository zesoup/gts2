import db
import psycopg2.extras

class VERSION:
	def __init__(self):
		self.VERSION = 0.01
		self.dbversion = None
	def run (self):
		print "Codeversion %s " % self.VERSION
		self.compareLocalAndDB()
	def compareLocalAndDB(self):
		self.getSchemaVersion()
		if str(self.VERSION) != str(self.dbversion):
			print "Version mismatch."
			return 1
		return 0
	def getSchemaVersion(self):
		try:
			conn = db.pool.getconn()
			cursor = conn.cursor( cursor_factory=psycopg2.extras.DictCursor )
			cursor.execute("SELECT revision, name, installed::date FROM meta ORDER BY revision desc limit 1")
			result= cursor.fetchone()
			print "DB-Revision %s(%s) deployed %s" %(result['revision'],result['name'] ,result['installed']) 
			self.dbversion=result['revision']
			cursor.close()
			db.pool.putconn(conn)
		except Exception as e:
			print "Could not read Table 'meta'"
			print ""
			print e
			pass
if __name__ == '__main__':
	v=VERSION()
	v.run()

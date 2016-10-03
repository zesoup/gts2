from libs import db
import os
import psycopg2
#import psycopg2.Binary
c = db.pool.getconn()
curs = c.cursor()

d = os.listdir('images')
for img in d:
	f = open( os.path.join('images', img) ,'rb')
	filedata = psycopg2.Binary( f.read() )
	f.close()
	curs.execute("INSERT INTO frontendimages(data,name) VALUES (%s,%s) ON CONFLICT (name) DO UPDATE SET data=EXCLUDED.data", (filedata,img) )



c.commit()

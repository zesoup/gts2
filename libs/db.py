import psycopg2
import psycopg2.extras
import psycopg2.pool

MINPOOL = 15
MAXPOOL = 30
APPNAME = 'GTS'

pool = psycopg2.pool.ThreadedConnectionPool( MINPOOL, MAXPOOL,'port=5432 user=gts password=gts host=127.0.0.1 application_name=%s dbname=gts ' % (APPNAME,) )


#conn = pool.getconn()

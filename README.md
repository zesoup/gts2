# GTS2
This game is designed as a PostgreSQL playgound and techdemo.
By utilizing PostGIS and Openstreetmap, the Database allows for quick geospatial queries for either buisness logic or rendering. Also Rendering is done by a postgresql backend.

The games logic is based on triggers and constraints. Hence here's little the application has to do besides forwarding commands like "accelerate".


![alt tag](https://github.com/zesoup/gts2/blob/master/images/GTS.png)


Currently based on Python2.7 the key requirements on the frontend are:

 * pygame
 * psycopg2
 * cairo

The Server requirements are:

 * postgresql >= 9.5
 * EXTENSION: postgis 2.2
 * EXTENSION: unaccent

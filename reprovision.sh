set -e
set -x

psql postgres -c "drop database gts";
psql postgres -c "create database gts";

psql gts -c "CREATE EXTENSION postgis; CREATE EXTENSION hstore;"

osm2pgsql -c data/duesseldorf-regbez-latest.osm.pbf --number-processes=8 -j --hstore-add-index  --database=gts -C 2500 --merc
#pg_restore --dbname gts data/osm.dump -j4 --verbose
pushd sql
psql gts < init.sql
popd


cd tvee
node_modules/.bin/gulp watch &
cd ..
redis-cli shutdown
redis-server /usr/local/etc/redis.conf &
rqscheduler &
python -m tvee

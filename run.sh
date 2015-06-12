#!/bin/bash


prepare-pubby () {
  set -e
  pushd /pubby-prep > /dev/null

  unzip -q pubby*.zip
  cd pubby*

  #enable Jetty service
  sed -i 's/NO_START=1/NO_START=0/' /etc/default/jetty8
  sed -i 's/#JETTY_HOST=.*$/JETTY_HOST="0.0.0.0"/' /etc/default/jetty8
  sed -i 's/#AUTHBIND=.*$/AUTHBIND=yes/' /etc/default/jetty8
  [ -z ${PORT+x} ] || sed -i "s/#JETTY_PORT=.*\$/JETTY_PORT=$PORT/" /etc/default/jetty8

  echo 'generating Pubby configuration according to template and environment variables:'
  env | grep -P '(STORE_SPARQL_ENDPOINT_URL)|(STORE_MAIN_GRAPH)|(PROJECT_NAME)|(PROJECT_HOMEPAGE)|(INDEX_RESOURCE)|(DATASET_BASE)|(WEB_BASE)|(PORT)'
python3 /pubby-prep/make-pubby-conf.py /pubby-prep/config.ttl.template webapp/WEB-INF/config.ttl
chmod a+r webapp/WEB-INF/config.ttl

  echo 'deploying configured pubby as root context webapp for Jetty' 
  rm -rf /var/lib/jetty8/webapps/root/
  cp -r webapp/ /var/lib/jetty8/webapps/root/

  popd > /dev/null
  set +o errexit
}


# allowing for clean shutdown of background jobs
cleanup () {
  echo "stopping jetty..."
  service jetty8 stop
  [[ -n $tailpid ]] && kill -TERM "$tailpid"

  exit 0
}

echo "preparing pubby web context"
prepare-pubby

trap 'cleanup' INT TERM

echo "starting jetty..."
# hiding output from start script for now, as it reports a failure although the server is starting o.k.
service jetty8 start > /dev/null

touch /var/log/jetty8/out.log
echo "starting to tail logs..."
tail -fn10000 /var/log/jetty8/*.log &
tailpid=$!

wait $tailpid

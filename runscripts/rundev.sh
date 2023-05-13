#!/bin/bash

source /reg/g/psdm/sw/dm/conda/etc/profile.d/conda.sh
conda activate /reg/g/psdm/sw/dm/conda/envs/psdm_ws_0_0_10

# We pick up installation-specific config from a file outside of this repo.
PRNT_DIR=`dirname $PWD`
G_PRNT_DIR=`dirname $PRNT_DIR`;
GG_PRNT_DIR=`dirname $G_PRNT_DIR`;
GGG_PRNT_DIR=`dirname $GG_PRNT_DIR`;
EXTERNAL_CONFIG_FILE="${GGG_PRNT_DIR}/appdata/psdm_mongo_ws/psdm_mongo_ws_config.sh"


if [[ -f "${EXTERNAL_CONFIG_FILE}" ]]
then
   echo "Sourcing deployment specific configuration from ${EXTERNAL_CONFIG_FILE}"
   source "${EXTERNAL_CONFIG_FILE}"
else
   echo "Did not find external deployment specific configuration - ${EXTERNAL_CONFIG_FILE}"
fi

# Assume that the current directory for the process is this directory.
export PYTHONPATH="modules/flask_authnz:${PYTHONPATH}"

export ACCESS_LOG_FORMAT='%(h)s %(l)s %({REMOTE_USER}i)s %(t)s "%(r)s" "%(q)s" %(s)s %(b)s %(D)s'
export LOG_LEVEL=${LOG_LEVEL:-"INFO"}

[ -z "$SERVER_IP_PORT" ] && export SERVER_IP_PORT="0.0.0.0:5000"

exec gunicorn start:app -b ${SERVER_IP_PORT} --reload \
       --log-level=${LOG_LEVEL} --capture-output --enable-stdio-inheritance \
       --worker-class eventlet --workers 4 --worker-connections 2048 --max-requests 100000 \
       --access-logfile - --access-logformat "${ACCESS_LOG_FORMAT}"

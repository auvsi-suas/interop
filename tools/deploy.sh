#!/usr/bin/env bash
# Deploys Docker containers to hub.

set -e
TOOLS=$(dirname ${BASH_SOURCE[0]})
source ${TOOLS}/common.sh


log "Tagging Docker images."
DATE=$(date '+%Y.%m')
docker tag auvsisuas/interop-client:latest auvsisuas/interop-client:${DATE}
docker tag auvsisuas/interop-server:latest auvsisuas/interop-server:${DATE}

log "Logging into Docker."
echo "$DOCKER_PASSWORD" | docker login -u="$DOCKER_USERNAME" --password-stdin

log "Pushing Docker images."
docker push auvsisuas/interop-server
docker push auvsisuas/interop-client

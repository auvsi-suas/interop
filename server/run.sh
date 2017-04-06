#!/bin/bash
# Runs the Interop Server in a container.

docker run -d --restart=unless-stopped --interactive --tty --publish 8000:80 --name interop-server auvsisuas/interop-server

# Poll server up to 2 min for healthiness before proceeding.
for i in {1..120};
do
    docker inspect -f "{{.State.Health.Status}}" interop-server | grep "^healthy$" && exit 0 || sleep 1;
done

exit 1

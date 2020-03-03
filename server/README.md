# Running mission creation scripts
```
$ docker-compose up
... new terminal ...
$ docker-compose run interop-server python3 /interop/scripts/create_mission.py -m /interop/scripts/sample_mission.json
```

# Interacting with the server via curl
```
$ curl http://localhost:8000/api/login -d @scripts/test_login.json -c cookies.txt
$ curl http://localhost:8000/api/missions/1 -b cookies.txt | tee mission.json
```
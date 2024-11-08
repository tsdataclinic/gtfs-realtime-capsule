# Common Errors
## Local development docker container
### You have to remove (or rename) that container to be able to reuse that name.
Symptoms:
```
$ make local-dev-run
docker run -d --name local-dev local-dev-image
docker: Error response from daemon: Conflict. The container name "/local-dev" is already in use by container "69a800be08538f6c45e9b747ac4447c55a2ea8cc4627f5b530b713c5deff49fe". You have to remove (or rename) that container to be able to reuse that name.
See 'docker run --help'.
make: *** [local-dev-run] Error 125
```
Explanations: <br>
You ran `make local-dev-run` twice which is wrong. <br>
If you wish to shell back into the local dev container, use `make local-dev-shell` instead. <br>
If you wish to restart the container:
```shell
make local-dev-restart
```
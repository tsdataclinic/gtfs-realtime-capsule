# How to start local development docker container
After [installing docker](https://docs.docker.com/engine/install/) on your system, [start the docker daemon](https://docs.docker.com/engine/daemon/start/) and then:
```shell
make local-dev-build
make local-dev-run
# you are now in shell in the docker container, feel free to do any development work!
# to see the source code dir:
ls local/src
```

If you exited the shell and want to shell back
```shell
make local-dev-shell
```

If you exited the shell and want to tear down local dev environment
```shell
make local-dev-down
```

Code changed locally in your computer or docker is not synced to each other.
To restart docker that contains your local changes in your computer, exit the docker container shell and then:
```shell
make local-dev-restart
# you are now in the shell in the docker container
```
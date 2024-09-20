# Local development environment setup via docker
After installing docker on your system:
```shell
make local-dev-build
make local-dev-run
# you are now in shell in the docker container
# if you want to shell back in after exiting:
make local-dev-shell
# if you want to tear down local dev env:
make local-dev-down
```

Code changed locally in your computer or docker is not synced to each other.
To restart docker that contains your local changes in your computer:
```shell
make local-dev-down
make local-dev-build
make local-dev-run
# you are now in shell in the docker container
```
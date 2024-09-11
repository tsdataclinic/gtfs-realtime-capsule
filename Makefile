all: install lint test

install:
	pip install --no-cache-dir -r requirements.txt
test:
	pytest .
lint:
	black .
	flake8 .
local-dev-build:
	docker build -t local-dev-image -f ./docker/dev/Dockerfile .
local-dev-run:
	docker run -d --name local-dev local-dev-image
	docker exec -it local-dev /bin/bash
local-dev-shell:
	docker exec -it local-dev /bin/bash
local-dev-down:
	docker stop local-dev
	docker rm local-dev

local-prod-build:
	docker build -t local-prod-image -f ./docker/prod/Dockerfile .
local-prod-run:
	docker run -d --name local-prod local-prod-image
	docker exec -it local-prod /bin/bash
local-prod-shell:
	docker exec -it local-prod /bin/bash
local-prod-down:
	docker stop local-prod
	docker rm local-prod
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

local-prod-generate-compose:
	python3 ./docker/prod/generate_compose.py $(FEEDS)
local-prod-generate-compose-all:
	python3 ./docker/prod/generate_compose.py '*'
local-prod-run:
	docker-compose -f docker-compose.yml up -d
	docker ps -a
local-prod-down:
	docker-compose -f docker-compose.yml down
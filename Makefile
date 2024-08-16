all: install lint test

install:
	pip install --no-cache-dir -r requirements.txt
test:
	pytest .
lint:
	black8 .
	flake8 .
local-dev-build:
	docker build -t local-dev-image .
local-dev-run:
	docker run -d --name local-dev local-dev-image
	docker exec -it local-dev /bin/bash
local-dev-shell:
	docker exec -it local-dev /bin/bash
local-dev-down:
	docker stop local-dev
	docker rm local-dev

build:
	DOCKER_BUILDKIT=1 docker build -t auth-service:latest .

build-dev:
	DOCKER_BUILDKIT=1 docker build -f Dockerfile.dev -t auth-service:dev .

run:
	docker run --rm -it \
	--name auth-service \
	-p 8123:8000 \
	auth-service:latest


up:
	docker-compose up --build -d

down:
	docker-compose down

exec:
	docker exec -it auth-service bash

test:
	pytest --cov-report=term-missing --cov=app tests/
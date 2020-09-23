.PHONY: build clean test

build:
	docker-compose build

clean:
	docker-compose down

test:
	bin/integrate

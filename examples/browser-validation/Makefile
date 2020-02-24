build:
	docker build --target development -t prio:dev ../..

run:
	docker-compose run app

test:
	docker-compose run bash -c "python3 generate.py --path test.batch.json | bash"

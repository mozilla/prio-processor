build:
	docker build -t prio-validate ../../

run:
	docker run -v `pwd`:/app/examples/browser-validation \
		-e AWS_ACCESS_KEY_ID \
		-e AWS_SECRET_ACCESS_KEY \
		-e PRIO_DATE \
		-e PRIO_PINGS \
		-e PRIO_PUBKEY_A \
		-e PRIO_PVTKEY_A \
		-e PRIO_PUBKEY_B \
		-e PRIO_PVTKEY_B \
		-it prio-validate \
			sh -c 'cd /app/examples/browser-validation && \
			pipenv lock && \
			pipenv sync && \
			pipenv run python main.py'

test:
	docker run \
		-v `pwd`:/app/examples/browser-validation \
		-it prio-validate \
			sh -c 'cd /app/examples/browser-validation && \
			pipenv lock && \
			pipenv sync && \
			pipenv run \
				bash -c "python generate.py --path test.batch.json | bash"'

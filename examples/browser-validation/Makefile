build:
	docker build -t prio-validate ../../

run:
	docker run -v `pwd`:/app/examples/browser-validation \
		-e AWS_ACCESS_KEY_ID \
		-e AWS_SECRET_ACCESS_KEY \
		-e PRIO_BUILD_ID \
		-e PRIO_PUBKEY_A \
		-e PRIO_PVTKEY_A \
		-e PRIO_PUBKEY_B \
		-e PRIO_PVTKEY_B \
		-it prio-validate \
			cd /app/examples/browser-validation && \
			pipenv lock && \
			pipenv sync && \
			pipenv run python main.py
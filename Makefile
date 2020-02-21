.PHONY: all shell

all:
	docker build --target development -t prio:dev .
	docker build --target production -t prio:latest .

shell:
	docker run -v $(shell pwd):/app -it prio:dev bash -c "make && bash"

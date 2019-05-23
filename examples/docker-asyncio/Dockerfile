FROM prio-dev:latest

# install wait-for for docker-compose services
RUN curl -o /usr/local/bin/wait-for-it https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh
RUN chmod +x /usr/local/bin/wait-for-it

RUN pip install pipenv

CMD bash

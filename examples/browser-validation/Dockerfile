FROM prio:dev

# install wait-for for docker-compose services
RUN curl -o /usr/local/bin/wait-for-it https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh
RUN chmod +x /usr/local/bin/wait-for-it

RUN pip3 install \
    s3fs \
    pyarrow \
    click \
    pandas \

CMD bash

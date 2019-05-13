FROM prio-dev:latest

RUN curl https://dl.minio.io/client/mc/release/linux-amd64/mc -o mc
RUN chmod +x mc
ENV PATH="/app/:${PATH}"

CMD bash
FROM debian:bookworm-slim AS base


FROM base AS build

RUN apt-get -y update && \
	apt-get -y install python3-poetry

COPY . /usr/src/vocata
WORKDIR /usr/src/vocata
RUN poetry build


FROM base AS runtime
ARG VOCATA_VERSION=0.2.0

RUN apt-get -y update && \
	apt-get -y install python3-pip python3-psycopg2 git

COPY --from=build /usr/src/vocata/dist/vocata-${VOCATA_VERSION}.tar.gz /tmp
RUN pip3 install --break-system-packages "/tmp/vocata-${VOCATA_VERSION}.tar.gz[server,cli]"


FROM runtime AS clean

RUN apt-get -y purge git && apt-get -y autoremove && apt-get -y clean
RUN rm -rf /tmp/* /root/*

ENV VOC_server__host=0.0.0.0
EXPOSE 8044
CMD ["/usr/local/bin/vocata"]

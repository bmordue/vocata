# SPDX-FileCopyrightText: © 2023 Dominik George <nik@naturalnet.de>
# SPDX-FileCopyrightText: © 2023 magicfelix <felix@felix-zauberer.de>
#
# SPDX-License-Identifier: LGPL-3.0-or-later

FROM debian:bookworm-slim AS base


FROM base AS build
ARG VOCATA_VERSION=0.2.1

RUN apt-get -y update && \
	apt-get -y install python3-poetry python3-pip python3-venv git

COPY . /usr/src/vocata
WORKDIR /usr/src/vocata

RUN poetry build && python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip3 install "/usr/src/vocata/dist/vocata-${VOCATA_VERSION}.tar.gz[server,postgresql,cli]"


FROM debian:bookworm-slim AS runtime

RUN apt-get -y update && apt-get -y install python3
COPY --from=build /opt/venv /opt/venv

ENV VOC_server__host=0.0.0.0
ENV PATH="/opt/venv/bin:$PATH"
EXPOSE 8044
CMD ["/opt/venv/bin/vocata"]

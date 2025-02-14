FROM python:3.9.15-slim

# install pip==21.3.1 for python 3.6
RUN apt-get update -yqq && \
    apt-get install -y python3-dev build-essential vim wget && \
    pip install -U pip==21.3.1

# install dbnd packages:
COPY ./dbnd-core/dist-python/dbnd.requirements.txt \
    ./dbnd-core/dist-python/dbnd-airflow-monitor.requirements.txt \
    ./dbnd-core/dist-python/dbnd-airflow-monitor[[]composer].requirements.txt \
    /dist-python/
RUN pip install -r /dist-python/dbnd.requirements.txt \
    && pip install -r /dist-python/dbnd-airflow-monitor.requirements.txt \
    && pip install -r /dist-python/dbnd-airflow-monitor[composer].requirements.txt

COPY ./dbnd-core/dist-python/databand-*.whl \
    ./dbnd-core/dist-python/dbnd-*.whl \
    ./dbnd-core/dist-python/dbnd_airflow_monitor-*.whl \
    /dist-python/

ENV DBND_VERSION=1.0.21.0

RUN pip install dbnd==$DBND_VERSION \
    dbnd_airflow_monitor==$DBND_VERSION \
    dbnd_airflow_monitor[composer]==$DBND_VERSION \
    --no-index \
    --find-links /dist-python/

ENV DBND_HOME=/dbnd
WORKDIR ${DBND_HOME}

ARG SOURCE_VERSION
ENV DBND__RUN_INFO__SOURCE_VERSION ${SOURCE_VERSION:-""}

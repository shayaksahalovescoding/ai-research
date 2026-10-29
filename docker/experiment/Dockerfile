FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN groupadd --gid 10001 researcher && useradd --uid 10001 --gid 10001 --create-home researcher
WORKDIR /work
COPY experiments/toy_ml/experiment.py /opt/research-experiment/experiment.py
RUN chmod 0555 /opt/research-experiment/experiment.py
USER researcher
ENTRYPOINT ["python", "/opt/research-experiment/experiment.py"]


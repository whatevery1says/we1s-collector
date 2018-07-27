FROM python:3.6

RUN useradd -u 1000 -g users -m -s /bin/sh jovyan

COPY --chown=jovyan:users requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir lxml
RUN pip install -r /app/requirements.txt

COPY --chown=jovyan:users . /app

ENV PATH="${PATH}:/app"

ENTRYPOINT ["tail", "-f", "/dev/null"]

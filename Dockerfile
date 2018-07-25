FROM python:3.6

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir lxml
RUN pip install -r /app/requirements.txt

COPY . /app

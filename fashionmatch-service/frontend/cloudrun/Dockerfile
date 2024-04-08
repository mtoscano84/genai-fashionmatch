FROM python:3.9

ARG GRADIO_SERVER_PORT=8080
ENV GRADIO_SERVER_PORT=${GRADIO_SERVER_PORT}

WORKDIR /workspace

ADD requirements.txt main.py config.ini /workspace/

RUN pip3 install -r /workspace/requirements.txt

CMD ["python3", "/workspace/main.py"]

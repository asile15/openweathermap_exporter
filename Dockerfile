FROM python:3.6-alpine

WORKDIR /

COPY openweathermap_exporter.py /

RUN pip install prometheus-client requests && \
    rm -rf ~/.cache ~/.pip

ENV SMETERD_EXPORTER_LISTEN_ADDR=0.0.0.0:8091

EXPOSE 8091

CMD ["/openweathermap_exporter.py"]

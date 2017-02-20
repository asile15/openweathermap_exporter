#!/usr/bin/env python
import logging
import requests
import os
import sys

from http.server import HTTPServer
from http.server import SimpleHTTPRequestHandler
from prometheus_client.core import CounterMetricFamily
from prometheus_client.core import GaugeMetricFamily
from prometheus_client.exposition import CONTENT_TYPE_LATEST
from prometheus_client.exposition import generate_latest
from urllib.parse import parse_qs, urlparse

__version__ = '0.1.0'
__listen_address_env_var__ = 'SMETERD_EXPORTER_LISTEN_ADDR'

logging.basicConfig(format='time="%(asctime)s", level="%(levelname)s", message="%(message)s"', level=10)
log = logging.getLogger(__name__)


class WeatherExporter(SimpleHTTPRequestHandler):
    def do_GET(self):
        params = parse_qs(urlparse(self.path).query)

        try:
            registry = WeatherCollector(params['appid'][0], params['location'][0])
            metrics = generate_latest(registry)
        except:
            self.send_error(500, 'error generating metric output')
            raise

        self.send_response(200)
        self.send_header("Content-type", CONTENT_TYPE_LATEST)
        self.end_headers()
        self.wfile.write(metrics)

    def log_message(self, format, *args):
        log.warning(format%args)


class WeatherCollector(object):
    def __init__(self, appid=None, location=None):
        self.appid = appid
        self.location = location

    def collect(self):
        weather = requests.get('http://api.openweathermap.org/data/2.5/weather', params={
            'id': self.appid,
            'appid': self.location,
        }).json()

        temp = GaugeMetricFamily('weather_temperature_kelvin', 'Temperature in degrees Kelvin', labels=["name", "type"])
        temp.add_metric([weather['name'], 'current'], weather['main']['temp'])
        temp.add_metric([weather['name'], 'min'], weather['main']['temp_min'])
        temp.add_metric([weather['name'], 'max'], weather['main']['temp_max'])

        yield temp

        yield CounterMetricFamily('weather_measurement_epoch', 'Time of the measurement', value=weather['dt'], )


def main():
    if len(sys.argv) == 2:
        host, port = sys.argv[1].split(':', 2)
    elif __listen_address_env_var__ in os.environ:
        host, port = os.environ[__listen_address_env_var__].split(':', 2)
    else:
        host = ''
        port = 8091

    server = HTTPServer((host, port), WeatherExporter)
    log.warning("Serving at port {}:{}".format(host, port))

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass

    server.server_close()
    log.warning('All done here')


if __name__ == '__main__':
    sys.exit(main())

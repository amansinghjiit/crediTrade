import logging
from gunicorn.glogging import Logger

loglevel = 'debug'
errorlog = '-'
accesslog = '-'
capture_output = True
worker_class = 'uvicorn.workers.UvicornWorker'
workers = 2
timeout = 120
graceful_timeout = 120
worker_connections = 500
preload_app = True

class CustomLogger(Logger):
    def setup(self, cfg):
        super().setup(cfg)
        self.error_log.setLevel(logging.DEBUG)
        self.access_log.setLevel(logging.INFO)
        self.error_log.propagate = False
        self.access_log.propagate = False

logger_class = CustomLogger

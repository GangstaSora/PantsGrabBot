import logging
from logging.handlers import TimedRotatingFileHandler
import sys


def setup(channel):
	application_logger = logging.getLogger('pantsgrabbot')
	application_logger.propagate = False
	db_logger = logging.getLogger('sqlalchemy')
	application_logger.setLevel(logging.DEBUG)
	db_logger.setLevel(logging.DEBUG)

	fh_debug = TimedRotatingFileHandler(f'logs/{channel}/debug.log', when='h', interval=1, backupCount=48)
	fh_debug.setLevel(logging.DEBUG)
	fh_info = TimedRotatingFileHandler(f'logs/{channel}/info.log', when='h', interval=1, backupCount=48)
	fh_info.setLevel(logging.INFO)


	formatter = logging.Formatter('%(asctime)s-%(name)s-%(levelname)s: %(message)s', datefmt="%m/%d/%Y %I:%M:%S %p %Z")
	fh_debug.setFormatter(formatter)
	fh_info.setFormatter(formatter)

	application_logger.addHandler(fh_debug)
	application_logger.addHandler(fh_info)
	db_logger.addHandler(fh_debug)
	db_logger.addHandler(fh_info)

	
	sys.stdout = StreamToLogger(application_logger, logging.INFO)
	sys.stderr = StreamToLogger(application_logger, logging.ERROR)

	return application_logger


class StreamToLogger(object):
   """
   Fake file-like stream object that redirects writes to a logger instance.
   """
   def __init__(self, logger, log_level=logging.INFO):
      self.logger = logger
      self.log_level = log_level
      self.linebuf = ''

   def write(self, buf):
      for line in buf.rstrip().splitlines():
         self.logger.log(self.log_level, line.rstrip())
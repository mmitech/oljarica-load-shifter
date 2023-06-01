import logging
from config import logging_level

logger = logging.getLogger(__name__)
logger.propagate = False 
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
log_handler = logging.StreamHandler()
log_handler.setFormatter(formatter)
logger.addHandler(log_handler)
logger.setLevel(logging_level)
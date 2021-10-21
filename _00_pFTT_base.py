from json import load
from sys import stdout
from logging import basicConfig,\
    INFO, DEBUG, WARNING, ERROR, CRITICAL,\
    Formatter,\
    StreamHandler, FileHandler,\
    getLogger

def configure_logger():
    class CustomFormatter(Formatter):
        grey = "\x1b[38;21m"
        yellow = "\x1b[33;21m"
        red = "\x1b[31;21m"
        bold_red = "\x1b[31;1m"
        reset = "\x1b[0m"
        format = '%(asctime)s,%(msecs)d %(levelname)-4s [%(filename)s:%(lineno)d -> %(name)s - %(funcName)s] ___ %(message)s'

        FORMATS = {
            DEBUG: grey + format + reset,
            INFO: grey + format + reset,
            WARNING: yellow + format + reset,
            ERROR: red + format + reset,
            CRITICAL: bold_red + format + reset
        }

        def format(self, record):
            log_fmt = self.FORMATS.get(record.levelno)
            formatter = Formatter(log_fmt)
            return formatter.format(record)

    ch = StreamHandler(stream=stdout)
    ch.setLevel(DEBUG)
    ch.setFormatter(CustomFormatter())
    fh = FileHandler("runtime_log.log", encoding='utf-8')
    fh.setLevel(DEBUG)
    fh.setFormatter(Formatter('%(asctime)s,%(msecs)d %(levelname)-4s [%(filename)s:%(lineno)d -> %(name)s - %(funcName)s] ___ %(message)s'))

    basicConfig(datefmt='%Y-%m-%d:%H:%M:%S',
                level=INFO,
                handlers=[fh,ch])

class baseOPS():

    _log: getLogger

    def __init__(self,
                 **kwargs):
        """
        kwargs:
            wd_path (str) used to override wd_path from the config
        """

        self.load_config()

        self.wd_path = self.config['wd_path']
        new_wd_path = kwargs.get('wd_path')
        if new_wd_path:
            self._log.info('WD override to {}'.format(new_wd_path))
            self.wd_path = new_wd_path
        
        super(baseOPS, self).__init__()

    def load_config(self):
        with open('config.json', 'r') as json_in_handle:
            self.config = load(json_in_handle)
        self._log.info('Config loaded succesfully.')

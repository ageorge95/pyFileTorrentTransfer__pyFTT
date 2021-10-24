from sys import stdout
from os import path
from logging import basicConfig,\
    INFO, DEBUG, WARNING, ERROR, CRITICAL,\
    Formatter,\
    StreamHandler, FileHandler

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

class states():
    TORRENT_CREATED = 'TORRENT_CREATED'
    TORRENT_ADDED_SENDER = 'TORRENT_ADDED_SENDER'
    TORRENT_ADDED_RECEIVER = 'TORRENT_ADDED_RECEIVER'
    TORRENT_DOWNLOADED = 'TORRENT_DOWNLOADED'
    TORRENT_REMOVED = 'TORRENT_REMOVED'

class create_state():

    def __init__(self,
                 root):

        self.root = root

    def mark(self,
             mark_str : str):
        with open(path.join(self.root, mark_str), 'w') as dummy:
            pass

    def torrent_created(self):
        self.mark(states.TORRENT_CREATED)

    def torrent_removed(self):
        self.mark(states.TORRENT_REMOVED)

    def torrent_added_sender(self):
        self.mark(states.TORRENT_ADDED_SENDER)

    def torrent_added_receiver(self):
        self.mark(states.TORRENT_ADDED_RECEIVER)

    def torrent_downloaded(self):
        self.mark(states.TORRENT_DOWNLOADED)
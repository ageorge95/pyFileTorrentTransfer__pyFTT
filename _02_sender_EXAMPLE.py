from _00_pFTT_base import configure_logger
from _01_sender import sender
from time import sleep

configure_logger()
test = sender(file_foler_path=r'')
test.create_torrent()

while True:
    test.check_downloaded()
    sleep(5)
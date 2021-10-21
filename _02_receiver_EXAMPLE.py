from _00_pFTT_base import configure_logger
from _01_receiver import receiver
from time import sleep

configure_logger()
test = receiver(folder_out_path = r'C:\propriu\temp')
while True:
    test.check_for_new_torrents()
    test.check_torrent_completion()
    sleep(5)
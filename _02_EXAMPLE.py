from _01_pyFTT import pyFTT
from _00_pFTT_base import configure_logger
from threading import Thread

configure_logger()

# sender code
do = pyFTT(wd_path=r'C:\Users\g4m3rx\OneDrive\pyFTT',
           sender_torrent_file_folder=r'C:\propriu\No-image-found.jpg')
do.create_torrent()
Thread(target=do.thread_monitor_sender).start()

# receiver code
do = pyFTT(wd_path=r'C:\Users\g4m3rx\OneDrive\pyFTT',
           receiver_torrent_save_folder=r'H:\\')
Thread(target=do.thread_monitor_receiver).start()
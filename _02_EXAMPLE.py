from _01_pyFTT import pyFTT
from _00_pFTT_base import configure_logger
from threading import Thread

configure_logger()

# sender code
do = pyFTT(working_directory=r'C:\Users\g4m3rx\OneDrive\pyFTT',
           file_or_folder_to_send=r'C:\propriu\No-image-found.jpg')
do.create_torrent()
Thread(target=do.thread_monitor_sender).start()

# receiver code
do = pyFTT(working_directory=r'C:\Users\g4m3rx\OneDrive\pyFTT',
           receiver_torrent_save_folder=r'H:\\')
Thread(target=do.thread_monitor_receiver).start()
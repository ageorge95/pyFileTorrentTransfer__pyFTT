from _00_pFTT_base import create_state,\
    states
from qbittorrentapi import Client,\
    LoginFailed
from logging import getLogger
from traceback import format_exc
from os import path,\
    mkdir,\
    listdir
from subprocess import check_output
from time import sleep

class pyFTT():
    def __init__(self,
                 wd_path: str,
                 sender_torrent_file_folder : str = None,
                 receiver_torrent_save_folder : str = None,
                 qbHost : str = 'localhost',
                 qbPort : int = 8085,
                 qbPassword : str = 'admin',
                 qbUsername : str = 'adminadmin'):

        self._log = getLogger()

        self.wd_path = wd_path
        self.sender_torrent_file_folder = sender_torrent_file_folder
        self.receiver_torrent_save_folder = receiver_torrent_save_folder
        self.qbHost = qbHost
        self.qbPort = qbPort
        self.qbPassword = qbPassword
        self.qbUsername = qbUsername

        if sender_torrent_file_folder and receiver_torrent_save_folder:
            self._log.error('The same instance cannot be the sender and the receiver !')
            exit()
        if not sender_torrent_file_folder and not receiver_torrent_save_folder:
            self._log.error('You need to provide at least 1 path, either sender_torrent_file_folder or receiver_torrent_save_folder')
            exit()

        self.init_qBitorrent()

    def init_qBitorrent(self):

        self.qb_client = Client(host='localhost',
                                port=8085,
                                username='admin',
                                password='adminadmin')

        try:
            self.qb_client.auth_log_in()
            self._log.info('Successfully logged on to qBitorrent')
        except LoginFailed:
            self._log.error('Failed to login to qBitorrent !\n{}'.format(format_exc(chain=False)))
            exit()

    def create_torrent(self):

        if not self.sender_torrent_file_folder:
            self._log.error('sender_torrent_file_folder was not provided !')
            exit()

        if not path.isdir(path.join(self.wd_path, path.basename(self.sender_torrent_file_folder))):
            mkdir(path.join(self.wd_path, path.basename(self.sender_torrent_file_folder)))

        if not path.isfile(path.join(self.wd_path, path.basename(self.sender_torrent_file_folder), path.basename(self.sender_torrent_file_folder) + '.torrent')):
            to_exec_str = 'py3createtorrent -t best5 -o "{output_path}" "{file_foler_path}"'
            exec_out = check_output(to_exec_str.format(file_foler_path = self.sender_torrent_file_folder,
                                                       output_path = path.join(self.wd_path, path.basename(self.sender_torrent_file_folder)))).decode('utf-8')
            self._log.info('Torrent creation: {}'.format(str(exec_out)))
        else:
            self._log.warning('.torrent file already exists !')

        create_state(path.join(self.wd_path, path.basename(self.sender_torrent_file_folder))).torrent_created()

        self.add_torrent_to_qBitorrent(wd_entry=path.basename(self.sender_torrent_file_folder))

    def add_torrent_to_qBitorrent(self,
                                  wd_entry):
        save_folder = None
        mark_state = None
        if self.sender_torrent_file_folder:
            save_folder = path.dirname(self.sender_torrent_file_folder)
            mark_state = create_state(path.join(self.wd_path, path.basename(self.sender_torrent_file_folder))).torrent_added_sender
        if self.receiver_torrent_save_folder:
            save_folder = self.receiver_torrent_save_folder
            mark_state = create_state(path.join(self.wd_path, wd_entry)).torrent_added_receiver

        while len(list(filter(lambda x:x.endswith('.torrent'), listdir(path.join(self.wd_path, wd_entry))))) == 0:
            sleep(5)
        torrent_file_name = list(filter(lambda x:x.endswith('.torrent'), listdir(path.join(self.wd_path, wd_entry))))[0]
        self.qb_client.torrents_add(torrent_files=path.join(self.wd_path, wd_entry, torrent_file_name),
                                    save_path=save_folder)
        self._log.info('New torrent added: {}'.format(wd_entry))

        mark_state()

    def thread_monitor_sender(self):
        while True:
            for entry in listdir(self.wd_path):
                if path.isfile(path.join(self.wd_path, entry, states.TORRENT_DOWNLOADED)):
                    if not path.isfile(path.join(self.wd_path, entry, states.TORRENT_REMOVED)):
                        for torrent in self.qb_client.torrents_info():
                            if torrent.name == entry:
                                self.qb_client.torrents_delete(delete_files=True,
                                                                torrent_hashes=torrent.hash)

                                create_state(path.join(self.wd_path, entry)).torrent_removed()

                                self._log.info('{} downloaded by receiver so it was removed.'.format(entry))
            sleep(5)

    def thread_monitor_receiver(self):
        while True:
            # check for new torrents
            for entry in listdir(self.wd_path):
                if not path.isfile(path.join(self.wd_path, entry, states.TORRENT_ADDED_RECEIVER)):
                    self._log.info('New torrent to be added: {}'.format(entry))
                    self.add_torrent_to_qBitorrent(wd_entry=entry)

            # check torrent completion
            entries = listdir(self.wd_path)
            for torrent in self.qb_client.torrents_info():
                if torrent.name in entries:
                    if not path.isfile(path.join(self.wd_path, torrent.name, states.TORRENT_DOWNLOADED)):
                        if torrent.state in ["uploading", 'stalledUP']:
                            self._log.info('{} completed. Marking as downloaded ...'.format(torrent.name))

                            create_state(path.join(self.wd_path, torrent.name)).torrent_downloaded()
            sleep(5)
from _00_pFTT_base import baseOPS
from os import listdir,\
    path
from logging import getLogger
from qbittorrentapi import Client,\
    LoginFailed
from traceback import format_exc
from sys import exit

class receiver(baseOPS):
    def __init__(self,
                 **kwargs):

        self._log = getLogger()

        super(receiver, self).__init__(**kwargs)

        self.folder_out_path = kwargs.get('folder_out_path')
        self.qbt_client = Client(host='localhost', port=8085, username='admin', password='adminadmin')

        try:
            self.qbt_client.auth_log_in()
            self._log.info('Successfully logged on in qBitorrent')
        except LoginFailed:
            self._log.error('Failed to login to qBitorrent !\n{}'.format(format_exc(chain=False)))
            exit()

    def add_torrent(self,
                    wd_entry):
        torrent_file_name = list(filter(lambda x:x.endswith('.torrent'), listdir(path.join(self.wd_path, wd_entry))))[0]
        self.qbt_client.torrents_add(torrent_files=path.join(self.wd_path, wd_entry, torrent_file_name),
                                     save_path=self.folder_out_path)
        self._log.info('New torrent added: {}'.format(wd_entry))
        # create a file to notify that the .torrent file was created
        with open(path.join(self.wd_path, wd_entry, 'TORRENT_ADDED'), 'w') as dummy:
            pass

    def check_for_new_torrents(self):
        for entry in listdir(self.wd_path):
            if not path.isfile(path.join(self.wd_path, entry, 'TORRENT_ADDED')):
                self._log.info('New torrent to be added: {}'.format(entry))
                self.add_torrent(wd_entry=entry)

    def check_torrent_completion(self):
        entries = listdir(self.wd_path)
        for torrent in self.qbt_client.torrents_info():
            if torrent.name in entries:
                if not path.isfile(path.join(self.wd_path, torrent.name, 'TORRENT_DOWNLOADED')):
                    if torrent.state in ["uploading", 'stalledUP']:
                        self._log.info('{} completed. Marking as downloaded ...'.format(torrent.name))
                        # create a file to notify that the .torrent file was created
                        with open(path.join(self.wd_path, torrent.name, 'TORRENT_DOWNLOADED'), 'w') as dummy:
                            pass



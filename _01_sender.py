from _00_pFTT_base import baseOPS
from subprocess import check_output
from os import path,\
    mkdir,\
    listdir
from logging import getLogger
from qbittorrentapi import Client,\
    LoginFailed
from traceback import format_exc

class sender(baseOPS):
    def __init__(self,
                 **kwargs):

        self._log = getLogger()
        self.file_foler_path = kwargs.get('file_foler_path')

        super(sender, self).__init__(**kwargs)

        self.folder_out_path = kwargs.get('folder_out_path')
        self.qbt_client = Client(host='localhost', port=8085, username='admin', password='adminadmin')

        try:
            self.qbt_client.auth_log_in()
            self._log.info('Successfully logged on in qBitorrent')
        except LoginFailed:
            self._log.error('Failed to login to qBitorrent !\n{}'.format(format_exc(chain=False)))
            exit()

    def create_torrent(self):
        if not path.isdir(path.join(self.wd_path, path.basename(self.file_foler_path))):
            mkdir(path.join(self.wd_path, path.basename(self.file_foler_path)))
        if not path.isfile(path.join(self.wd_path, path.basename(self.file_foler_path), path.basename(self.file_foler_path) + '.torrent')):
            exec_out = check_output('py3createtorrent -t best5 -o "{output_path}" "{file_foler_path}"'.format(file_foler_path = self.file_foler_path,
                                                                                                              output_path = path.join(self.wd_path, path.basename(self.file_foler_path)))).decode('utf-8')
            self._log.info('Torrent creation: {}'.format(str(exec_out)))
        else:
            self._log.warning('.torrent file already exists !')

        # create a file to notify that the .torrent file was created
        with open(path.join(self.wd_path, path.basename(self.file_foler_path), 'TORRENT_CREATED'), 'w') as dummy:
            pass

    def check_downloaded(self):
        for entry in listdir(self.wd_path):
            if path.isfile(path.join(self.wd_path, entry, 'TORRENT_DOWNLOADED')):
                if not path.isfile(path.join(self.wd_path, entry, 'TORRENT_REMOVED')):
                    for torrent in self.qbt_client.torrents_info():
                        if torrent.name == entry:
                            self.qbt_client.torrents_delete(delete_files=True,
                                                            torrent_hashes=torrent.hash)
                            # create a file to notify that the .torrent file was created
                            with open(path.join(self.wd_path, entry, 'TORRENT_REMOVED'), 'w') as dummy:
                                pass
                            self._log.info('{} downloaded by receiver so it was removed.'.format(entry))
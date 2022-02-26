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
                 working_directory: str,
                 file_or_folder_to_send : str = None,
                 receiver_torrent_save_folder : str = None,
                 qbHost : str = 'localhost',
                 qbPort : int = 8085,
                 qbPassword : str = 'admin',
                 qbUsername : str = 'adminadmin'):

        self._log = getLogger()

        self.working_directory = working_directory
        self.file_or_folder_to_send = file_or_folder_to_send
        self.receiver_torrent_save_folder = receiver_torrent_save_folder
        self.qbHost = qbHost
        self.qbPort = qbPort
        self.qbPassword = qbPassword
        self.qbUsername = qbUsername

        if file_or_folder_to_send and receiver_torrent_save_folder:
            self._log.error('The same instance cannot be the sender and the receiver !')
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

        if not self.file_or_folder_to_send:
            self._log.error('file_or_folder_to_send was not provided !')
            exit()

        # create a directory entry for the current file_or_folder_to_send
        if not path.isdir(
                path.join(
                    self.working_directory,
                    path.basename(self.file_or_folder_to_send)
                )
        ):
            mkdir(
                path.join(
                    self.working_directory,
                    path.basename(self.file_or_folder_to_send)
                )
            )

        # create the .torrent file if missing
        if not path.isfile(
                path.join(
                    self.working_directory,
                    path.basename(self.file_or_folder_to_send),
                    path.basename(self.file_or_folder_to_send) + '.torrent'
                )
        ):
            to_exec_str = f"py3createtorrent" \
                          f" -t best5" \
                          f" -o { path.join(self.working_directory, path.basename(self.file_or_folder_to_send)) }" \
                          f" { self.file_or_folder_to_send }"
            exec_out = check_output(to_exec_str).decode('utf-8')
            self._log.info('Torrent creation: {}'.format(str(exec_out)))
        else:
            self._log.warning('.torrent file already exists !')

        create_state(
            path.join(
                self.working_directory,
                path.basename(self.file_or_folder_to_send)
            )
        ).torrent_created()

        self.add_torrent_to_qBitorrent(wd_entry=path.basename(self.file_or_folder_to_send))

    def add_torrent_to_qBitorrent(self,
                                  wd_entry):
        save_folder = None
        mark_state = None
        if self.file_or_folder_to_send:
            save_folder = path.dirname(self.file_or_folder_to_send)
            mark_state = create_state(path.join(self.working_directory, path.basename(self.file_or_folder_to_send))).torrent_added_sender
        if self.receiver_torrent_save_folder:
            save_folder = self.receiver_torrent_save_folder
            mark_state = create_state(path.join(self.working_directory, wd_entry)).torrent_added_receiver

        while len(list(filter(lambda x:x.endswith('.torrent'), listdir(path.join(self.working_directory, wd_entry))))) == 0:
            sleep(5)
        torrent_file_name = list(filter(lambda x:x.endswith('.torrent'), listdir(path.join(self.working_directory, wd_entry))))[0]
        self.qb_client.torrents_add(torrent_files=path.join(self.working_directory, wd_entry, torrent_file_name),
                                    save_path=save_folder)
        self._log.info('New torrent added: {}'.format(wd_entry))

        mark_state()

    def thread_monitor_sender(self):
        while True:
            for entry in listdir(self.working_directory):
                # check if the torrent has been downloaded
                if path.isfile(
                        path.join(
                            self.working_directory,
                            entry,
                            states.TORRENT_DOWNLOADED
                        )
                ):
                    # check if the torrent has NOT been removed
                    if not path.isfile(
                            path.join(
                                self.working_directory,
                                entry,
                                states.TORRENT_REMOVED
                            )
                    ):
                        for torrent in self.qb_client.torrents_info():
                            if torrent.name == entry:
                                self.qb_client.torrents_delete(delete_files=True,
                                                               torrent_hashes=torrent.hash)

                                # mark the torrent as being removed
                                create_state(path.join(self.working_directory, entry)).torrent_removed()

                                self._log.info('{} downloaded by receiver so it was removed.'.format(entry))
            sleep(5)

    def thread_monitor_receiver(self):
        while True:
            # check for new torrents
            for entry in listdir(self.working_directory):
                # check if the torrent has NOT been loaded into qbittorrent
                if not path.isfile(
                        path.join(
                            self.working_directory,
                            entry,
                            states.TORRENT_ADDED_RECEIVER
                        )
                ):
                    self._log.info('New torrent to be added: {}'.format(entry))
                    self.add_torrent_to_qBitorrent(wd_entry=entry)

            # check torrent completion
            entries = listdir(self.working_directory)
            for torrent in self.qb_client.torrents_info():
                if torrent.name in entries:
                    if not path.isfile(
                            path.join(
                                self.working_directory,
                                torrent.name,
                                states.TORRENT_DOWNLOADED
                            )
                    ):
                        if torrent.state in ["uploading", 'stalledUP']:
                            self._log.info('{} completed. Marking as downloaded ...'.format(torrent.name))

                            create_state(path.join(self.working_directory, torrent.name)).torrent_downloaded()
            sleep(5)
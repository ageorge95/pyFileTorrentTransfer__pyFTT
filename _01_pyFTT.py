from _00_pFTT_base import create_state,\
    states,\
    get_state
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
                 machine_type: str,
                 qbHost : str = 'localhost',
                 qbPort : int = 8085,
                 qbPassword : str = 'admin',
                 qbUsername : str = 'adminadmin'):
        '''

        :param working_directory:
        :param machine_type: sender or receiver
        :param qbHost:
        :param qbPort:
        :param qbPassword:
        :param qbUsername:
        '''

        self._log = getLogger()

        self.working_directory = working_directory
        self.machine_type = machine_type
        self.qbHost = qbHost
        self.qbPort = qbPort
        self.qbPassword = qbPassword
        self.qbUsername = qbUsername

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

    def get_qbClient(self):
        return self.qb_client

    def create_torrent(self,
                       file_or_folder_path_to_send):

        # create a directory entry for the current file_or_folder_to_send
        if not path.isdir(
                path.join(
                    self.working_directory,
                    path.basename(file_or_folder_path_to_send)
                )
        ):
            mkdir(
                path.join(
                    self.working_directory,
                    path.basename(file_or_folder_path_to_send)
                )
            )

        # create the .torrent file if missing
        if not path.isfile(
                path.join(
                    self.working_directory,
                    path.basename(file_or_folder_path_to_send),
                    path.basename(file_or_folder_path_to_send) + '.torrent'
                )
        ):
            to_exec_str = f"py3createtorrent" \
                          f" -t best5" \
                          f" -o { path.join(self.working_directory, path.basename(file_or_folder_path_to_send)) }" \
                          f" { file_or_folder_path_to_send }"
            exec_out = check_output(to_exec_str).decode('utf-8')
            self._log.info('Torrent creation: {}'.format(str(exec_out)))
        else:
            self._log.warning('.torrent file already exists !')

        create_state(
            path.join(
                self.working_directory,
                path.basename(file_or_folder_path_to_send)
            )
        ).torrent_created()

    def _add_sender_torrent(self,
                            file_or_folder_path_to_send):

        wd_entry = path.basename(file_or_folder_path_to_send)
        save_folder = path.dirname(file_or_folder_path_to_send)
        create_state(path.join(self.working_directory,
                              path.basename(file_or_folder_path_to_send))
                     ).torrent_added_sender()

        self._add_torrent_to_qbitorrent(save_folder,
                                        wd_entry)

    def _add_receiver_torrent(self,
                              wd_entry,
                              save_folder):
        # check if the torrent has NOT been loaded into qbittorrent
        if not get_state(self.working_directory,
                    wd_entry).verify(states.TORRENT_ADDED_RECEIVER):

            self._log.info('New torrent to be added: {}'.format(wd_entry))

            create_state(path.join(self.working_directory,
                                                wd_entry)
                         ).torrent_added_receiver()

            self._add_torrent_to_qbitorrent(save_folder,
                                            wd_entry)

    def _add_torrent_to_qbitorrent(self,
                                   save_folder,
                                   wd_entry):

        while len(list(filter(lambda x:x.endswith('.torrent'), listdir(path.join(self.working_directory, wd_entry))))) == 0:
            sleep(5)
        torrent_file_name = list(filter(lambda x:x.endswith('.torrent'), listdir(path.join(self.working_directory, wd_entry))))[0]
        self.qb_client.torrents_add(torrent_files=path.join(self.working_directory, wd_entry, torrent_file_name),
                                    save_path=save_folder)
        self._log.info('New torrent added: {}'.format(wd_entry))


    def check_sender(self):
        for entry in listdir(self.working_directory):
            # check if the torrent has been downloaded
            if get_state(self.working_directory,
                        entry).verify(states.TORRENT_DOWNLOADED):

                # check if the torrent has NOT been removed
                if not get_state(self.working_directory,
                        entry).verify(states.TORRENT_REMOVED):

                    for torrent in self.qb_client.torrents_info():
                        if torrent.name == entry:
                            self.qb_client.torrents_delete(delete_files=True,
                                                           torrent_hashes=torrent.hash)

                            # mark the torrent as being removed
                            create_state(path.join(self.working_directory, entry)).torrent_removed()

                            self._log.info('{} downloaded by receiver so it was removed.'.format(entry))

    def check_receiver(self,
                       save_folder):

        entries = listdir(self.working_directory)

        # check for new torrents
        for entry in entries:
            # check if the torrent has NOT been loaded into qbittorrent
            if not get_state(self.working_directory,
                        entry).verify(states.TORRENT_ADDED_RECEIVER):

                self._log.info('New torrent to be added: {}'.format(entry))
                self._add_receiver_torrent(wd_entry=entry,
                                           save_folder = save_folder)

        # check torrent completion
        for torrent in self.qb_client.torrents_info():
            if torrent.name in entries:

                if not get_state(self.working_directory,
                        torrent.name).verify(states.TORRENT_DOWNLOADED):
                    if torrent.state in ["uploading", 'stalledUP']:
                        self._log.info('{} completed. Marking as downloaded ...'.format(torrent.name))

                        create_state(path.join(self.working_directory, torrent.name)).torrent_downloaded()

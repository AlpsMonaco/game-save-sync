from concurrent import futures
import hashlib
import os
import sys
import threading
import time
import zipfile
from PySide6.QtWidgets import (
    QWidget,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QApplication,
    QLabel,
    QLineEdit,
    QFileDialog,
    QTextEdit,
    QInputDialog,
    QMenuBar,
)
from PySide6.QtCore import QObject, Signal
import grpc
from PySide6.QtGui import QMoveEvent, QAction

from compress import compress_file, decompress
from i18n import Text, get_i18n_text
from rpc_service import DEFAULT_GRPC_PORT, GrpcClient, RPCService, path_convention
from config import Config
import rpc_service_pb2_grpc


class Signal(QObject):
    print_to_console = Signal(str)
    debug = Signal(str)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self._debug_mode = True
        self._grpc_client = None
        self.config = Config()
        self._text: Text = get_i18n_text(self.config.lang)
        self.initUI()

    def print(self, text):
        if self._debug_mode:
            return
        self.signal.print_to_console.emit(
            f'{time.strftime("[%Y-%m-%d %H:%M:%S]",time.localtime())} {text}'
        )

    def i18n(self):
        self.ip_label.setText(self._text.ip_label)
        self.ip_edit_button.setText(self._text.ip_edit_button)
        self.filepath_title_label.setText(self._text.filepath_title_label)
        self.select_file_button.setText(self._text.select_file_button)
        self.select_directory_button.setText(self._text.select_directory_button)
        self.sync_button.setText(self._text.sync_button)
        self.close_button.setText(self._text.close_button)
        self.setWindowTitle(f"{self._text.title}")

    def switch_cn_en(self):
        if self.config.lang == "cn":
            self.config.lang = "en"
        else:
            self.config.lang = "cn"
        self.config.save()
        self._text = get_i18n_text(self.config.lang)
        self.i18n()

    def _debug_method(self):
        last = ""
        while True:
            time.sleep(1)
            style = self.console.toPlainText()
            if style != "":
                if last != style:
                    last = style
                    self.signal.debug.emit(last)

    def start_debug_thread(self):
        t = threading.Thread(target=self._debug_method, daemon=True)
        t.start()

    def set_menu(self, qvbox_layout: QVBoxLayout):
        self.menu_bar = QMenuBar(self)
        # file_menu = self.menu_bar.addMenu("File")
        # action = QAction("Settings", self)
        # file_menu.addAction(action)
        # qvbox_layout.setMenuBar(self.menu_bar)

    def initUI(self):
        qvbox_layout = QVBoxLayout()
        self.set_menu(qvbox_layout)
        hbox_layout_01 = QHBoxLayout()
        self.ip_label = QLabel()
        self.ip_label.setMinimumWidth(35)
        self.ip_edit = QLineEdit(self.config.ip)
        self.ip_edit.setReadOnly(True)
        self.ip_edit_button = QPushButton()
        self.ip_edit_button.clicked.connect(self.show_ip_edit_dialog)
        self.i18n_switch_button = QPushButton("中/EN")
        self.i18n_switch_button.clicked.connect(self.switch_cn_en)
        hbox_layout_01.addWidget(self.ip_label, 0)
        hbox_layout_01.addWidget(self.ip_edit, 0)
        hbox_layout_01.addWidget(self.ip_edit_button, 0)
        hbox_layout_01.addStretch(1)
        hbox_layout_01.addWidget(self.i18n_switch_button, 0)
        qvbox_layout.addLayout(hbox_layout_01)

        hbox_layout_02 = QHBoxLayout()
        self.filepath_title_label = QLabel()
        self.filepath_title_label.setMinimumWidth(35)
        self.filepath_line_edit = QLineEdit(self.config.filepath)
        self.select_file_button = QPushButton()
        self.select_file_button.clicked.connect(self.show_file_select_dialog)
        self.select_directory_button = QPushButton()
        self.select_directory_button.clicked.connect(self.show_directory_select_dialog)
        hbox_layout_02.addWidget(self.filepath_title_label, 0)
        hbox_layout_02.addWidget(self.filepath_line_edit, 1)
        hbox_layout_02.addWidget(self.select_file_button, 0)
        hbox_layout_02.addWidget(self.select_directory_button, 0)
        qvbox_layout.addLayout(hbox_layout_02)

        self.console = QTextEdit()
        self.console.setAcceptRichText(False)
        if not self._debug_mode:
            self.console.setReadOnly(True)
        qvbox_layout.addWidget(self.console)

        hbox_layout_04 = QHBoxLayout()
        hbox_layout_04.addStretch(1)
        self.sync_button = QPushButton()
        self.sync_button.clicked.connect(self.start_sync)
        self.close_button = QPushButton()
        self.close_button.clicked.connect(self.close)
        hbox_layout_04.addWidget(self.sync_button)
        hbox_layout_04.addWidget(self.close_button)
        hbox_layout_04.addStretch(1)
        qvbox_layout.addLayout(hbox_layout_04)

        self.signal = Signal()
        self.signal.print_to_console.connect(self.console.append)
        self.signal.debug.connect(self.menu_bar.setStyleSheet)

        self.setLayout(qvbox_layout)
        self.setGeometry(300, 300, 500, 400)
        if self.config.x is not None and self.config.y is not None:
            self.move(self.config.x, self.config.y)
        self.i18n()
        self.show()
        self.start_grpc_thread()
        if self._debug_method:
            self.start_debug_thread()

    def moveEvent(self, ev: QMoveEvent):
        self.config.x = ev.pos().x()
        self.config.y = ev.pos().y()
        self.config.save()

    def start_grpc_thread(self):
        try:
            self.grpc_server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
            rpc_service_pb2_grpc.add_RpcServicer_to_server(
                RPCService(
                    get_filepath=self.filepath_line_edit.text, logger=self.print
                ),
                self.grpc_server,
            )
            self.grpc_server.add_insecure_port("[::]:" + str(self.config.listen_port))
            self.grpc_server.start()
        except Exception as e:
            self.print(e)
            self.print(f"{self._text.unable_to_start_grpc_server}")

    def show_file_select_dialog(self):
        filepath = QFileDialog.getOpenFileName(
            self,
            self._text.dialog_select_file,
            (
                os.path.dirname(self.filepath_line_edit.text())
                if self.filepath_line_edit.text() != ""
                else "."
            ),
        )
        if filepath[0] != "":
            self.filepath_line_edit.setText(filepath[0])
            self.config.filepath = filepath[0]
            self.config.save()

    def show_directory_select_dialog(self):
        dir_path = QFileDialog.getExistingDirectory(
            self,
            self._text.dialog_select_directorty,
            (
                os.path.dirname(self.filepath_line_edit.text())
                if self.filepath_line_edit.text() != ""
                else "."
            ),
        )
        if dir_path != "":
            self.filepath_line_edit.setText(dir_path)
            self.config.filepath = dir_path
            self.config.save()

    def show_ip_edit_dialog(self):
        input_dialog = QInputDialog(self)
        input_dialog.setInputMode(QInputDialog.TextInput)
        input_dialog.setWindowTitle(self._text.ip_edit_dialog_title)
        input_dialog.setLabelText(
            self._text.ip_edit_dialog_label,
        )
        input_dialog.setTextValue(self.config.ip)
        line_edit = input_dialog.findChild(QLineEdit)
        line_edit.setPlaceholderText(f"192.168.x.x[:{DEFAULT_GRPC_PORT}]")
        ret = input_dialog.exec()
        text = input_dialog.textValue()
        if ret == 1:
            self.ip_edit.setText(text)
            self.config.ip = text
            self.config.save()

    def compress_file(self, filepath: str):
        zip_filepath = "temp.zip"
        self.print(f"{self._text.compressing}{os.path.basename(filepath)}")
        compress_file(filepath, zip_filepath)
        self.print(f"{self._text.compress_done}")
        return zip_filepath

    def sync_directory(self):
        with GrpcClient.get_channel(self.config.ip) as channel:
            directory_path = self.filepath_line_edit.text()
            response = GrpcClient.get_remote_files_status(
                channel, os.path.basename(directory_path)
            )
            remote_files_dict = {}
            receive_list = []
            send_list = []
            for file_info in response.files:
                remote_filepath = path_convention(file_info.filename)
                remote_files_dict[remote_filepath] = file_info
                if not os.path.exists(os.path.join(directory_path, remote_filepath)):
                    receive_list.append(remote_filepath)
            for path, _, filenames in os.walk(directory_path):
                for filename in filenames:
                    local_filepath = os.path.join(path, filename)
                    relative_path = local_filepath[len(directory_path) + 1 :]
                    if relative_path not in remote_files_dict:
                        send_list.append(relative_path)
                        continue
                    remote_file = remote_files_dict[relative_path]
                    md5 = None
                    try:
                        with open(local_filepath, "rb") as fp:
                            data = fp.read()
                            md5 = hashlib.md5(data).hexdigest()
                        if remote_file.md5 != md5:
                            local_file_timestamp = int(os.path.getmtime(local_filepath))
                            if local_file_timestamp > remote_file.timestamp:
                                send_list.append(relative_path)
                            else:
                                receive_list.append(relative_path)

                    except Exception as e:
                        self.print(str(e))

            if len(send_list) > 0:
                self.print(f"{self._text.sending_file_to_remote}")
                with zipfile.ZipFile("temp.zip", "w", zipfile.ZIP_DEFLATED) as zip:
                    for relative_path in send_list:
                        local_filepath = os.path.join(directory_path, relative_path)
                        zip_filepath = local_filepath[len(directory_path) + 1 :]
                        zip.write(local_filepath, zip_filepath)
                GrpcClient.upload_directory_archive(channel)
                self.print(f"{self._text.send_success}")
            if len(receive_list) > 0:
                self.print(f"{self._text.pulling_from_remote}")
                with open("temp.zip", "wb") as fp:
                    response = GrpcClient.download_files(channel, receive_list)
                    for i in response:
                        fp.write(i.data)
                decompress("temp.zip", directory_path)
                self.print(f"{self._text.pull_success}")

            self.print(f"{self._text.sync_success}")

    def start_sync(self):
        self.sync_button.setDisabled(True)

        def sync_method():
            self.print(f"{self._text.syncing}")
            try:
                local_filepath = self.filepath_line_edit.text()
                if os.path.isdir(local_filepath):
                    return self.sync_directory()
                local_file_md5 = ""
                local_file_basename = os.path.basename(local_filepath)
                local_file_mtime = 0
                if os.path.exists(local_filepath):
                    with open(local_filepath, "rb") as fp:
                        data = fp.read()
                        local_file_md5 = hashlib.md5(data).hexdigest()
                        local_file_mtime = os.path.getmtime(local_filepath)
                with GrpcClient.get_channel(self.config.ip) as channel:
                    response = GrpcClient.get_remote_file_status(channel)
                    if local_file_basename != response.filename:
                        self.print(f"{self._text.err_mismatch_file_name}")
                        return
                    if response.md5 == local_file_md5:
                        self.print(f"{self._text.same_hash_skip}")
                        return
                    if local_file_mtime > response.timestamp:
                        zip_filepath = self.compress_file(local_filepath)
                        self.print(f"{self._text.uploading_file}")
                        GrpcClient.upload_file(channel, zip_filepath)
                        self.print(f"{self._text.upload_file_success}")
                    else:
                        self.print(f"{self._text.downloading_file}")
                        zip_filepath = "temp.zip"
                        with open(zip_filepath, "wb") as fp:
                            response = GrpcClient.download_file(channel)
                            for i in response:
                                fp.write(i.data)
                        self.print(f"{self._text.download_file_success}")
                        self.print(f"{self._text.decompressing}")
                        decompress(zip_filepath, os.path.dirname(local_filepath))
                        self.print(f"{self._text.decompress_success}")
                self.print(f"{self._text.sync_success}")

            except Exception as e:
                self.print(f"{self._text.fail}")
                self.print(str(e))
            finally:
                self.sync_button.setDisabled(False)

        threading.Thread(target=sync_method, daemon=True).start()


def main():
    app = QApplication(sys.argv)
    main_window = MainWindow()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

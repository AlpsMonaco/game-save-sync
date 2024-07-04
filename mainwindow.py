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
)
from PySide6.QtCore import QObject, Signal
import grpc
from PySide6.QtGui import QMoveEvent

from compress import compress_file, decompress
from rpc_service import GrpcClient, RPCService
from config import Config
import rpc_service_pb2_grpc


class Signal(QObject):
    print_to_console = Signal(str)



class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self._grpc_client = None

    def print(self, text):
        self.signal.print_to_console.emit(
            f'{time.strftime("[%Y-%m-%d %H:%M:%S]",time.localtime())} {text}'
        )

    def initUI(self):
        qvbox_layout = QVBoxLayout()
        self.config = Config()

        hbox_layout_01 = QHBoxLayout()
        self.ip_label = QLabel("远程地址:")
        self.ip_label.setMinimumWidth(35)
        self.ip_edit = QLineEdit(self.config.ip)
        # self.ip_edit.setStyleSheet("QLineEdit { padding-left: 0px; margin-left:14px}")
        self.ip_edit.setReadOnly(True)
        self.ip_edit_button = QPushButton("修改")
        self.ip_edit_button.clicked.connect(self.show_ip_edit_dialog)
        hbox_layout_01.addWidget(self.ip_label, 0)
        hbox_layout_01.addWidget(self.ip_edit, 0)
        hbox_layout_01.addWidget(self.ip_edit_button, 0)
        hbox_layout_01.addStretch(1)
        qvbox_layout.addLayout(hbox_layout_01)

        hbox_layout_02 = QHBoxLayout()
        self.filepath_title_label = QLabel("目标:")
        self.filepath_title_label.setMinimumWidth(35)
        self.filepath_line_edit = QLineEdit(self.config.filepath)
        self.select_file_button = QPushButton("选择文件")
        self.select_file_button.clicked.connect(self.show_file_select_dialog)
        self.select_directory_button = QPushButton("选择文件夹")
        self.select_directory_button.clicked.connect(self.show_directory_select_dialog)
        hbox_layout_02.addWidget(self.filepath_title_label, 0)
        hbox_layout_02.addWidget(self.filepath_line_edit, 1)
        hbox_layout_02.addWidget(self.select_file_button, 0)
        hbox_layout_02.addWidget(self.select_directory_button, 0)
        qvbox_layout.addLayout(hbox_layout_02)

        self.console = QTextEdit()
        self.console.setReadOnly(True)
        qvbox_layout.addWidget(self.console)

        hbox_layout_04 = QHBoxLayout()
        hbox_layout_04.addStretch(1)
        self.sync_button = QPushButton("同步")
        self.sync_button.clicked.connect(self.start_sync)
        self.close_button = QPushButton("关闭")
        self.close_button.clicked.connect(self.close)
        hbox_layout_04.addWidget(self.sync_button)
        hbox_layout_04.addWidget(self.close_button)
        hbox_layout_04.addStretch(1)
        qvbox_layout.addLayout(hbox_layout_04)

        self.signal = Signal()
        self.signal.print_to_console.connect(self.console.append)

        self.setLayout(qvbox_layout)
        self.setGeometry(300, 300, 500, 400)
        self.setWindowTitle("Game Save Sync")
        if self.config.x is not None and self.config.y is not None:
            self.move(self.config.x, self.config.y)
        self.show()
        self.start_grpc_thread()

    def moveEvent(self, ev: QMoveEvent):
        self.config.x = ev.pos().x()
        self.config.y = ev.pos().y()
        self.config.save()

    def start_grpc_thread(self):
        self.grpc_server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        rpc_service_pb2_grpc.add_RpcServicer_to_server(
            RPCService(get_filepath=self.filepath_line_edit.text, logger=self.print),
            self.grpc_server,
        )
        self.grpc_server.add_insecure_port("[::]:" + str(self.config.listen_port))
        self.grpc_server.start()

    def show_file_select_dialog(self):
        filepath = QFileDialog.getOpenFileName(
            self,
            "选择文件",
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
            "选择文件夹",
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
        input_dialog = QInputDialog()
        text, ok = input_dialog.getText(
            self,
            "修改地址",
            "请输入地址:",
            text=self.config.ip,
        )
        if ok:
            self.ip_edit.setText(text)
            self.config.ip = text
            self.config.save()

    def compress_file(self, filepath: str):
        zip_filepath = "temp.zip"
        self.print(f"正在压缩{os.path.basename(filepath)}")
        compress_file(filepath, zip_filepath)
        self.print(f"压缩完成")
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
                            if local_file_timestamp > remote_file.md5:
                                send_list.append(relative_path)
                            else:
                                receive_list.append(relative_path)

                    except Exception as e:
                        self.print(str(e))

            if len(send_list) > 0:
                self.print("正在发送文件到远端")
                with zipfile.ZipFile("temp.zip", "w", zipfile.ZIP_DEFLATED) as zip:
                    for relative_path in send_list:
                        local_filepath = os.path.join(directory_path, relative_path)
                        zip_filepath = local_filepath[len(directory_path) + 1 :]
                        zip.write(local_filepath, zip_filepath)
                GrpcClient.upload_directory_archive(channel)
                self.print("发送成功")
            if len(receive_list) > 0:
                self.print("正在从远端拉取文件")
                with open("temp.zip", "wb") as fp:
                    for i in GrpcClient.download_files():
                        fp.write(i.data)
                decompress("temp.zip", directory_path)
                self.print("拉取成功")

            self.print("同步成功")

    def start_sync(self):
        self.sync_button.setDisabled(True)

        def sync_method():
            self.print("开始同步")
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
                        self.print("错误：文件名不一致")
                        return
                    if response.md5 == local_file_md5:
                        self.print("文件一致，跳过")
                        return
                    if local_file_mtime > response.timestamp:
                        zip_filepath = self.compress_file(local_filepath)
                        self.print("正在上传文件")
                        GrpcClient.upload_file(channel, zip_filepath)
                        self.print("上传文件成功")
                    else:
                        self.print("正在下载文件")
                        zip_filepath = "temp.zip"
                        with open(zip_filepath, "wb") as fp:
                            response = GrpcClient.download_file(channel)
                            for i in response:
                                fp.write(i.data)
                        self.print("下载文件成功")
                        self.print("正在解压")
                        decompress(zip_filepath, os.path.dirname(local_filepath))
                        self.print("解压成功")
                self.print("同步成功")

            except Exception as e:
                self.print("失败")
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

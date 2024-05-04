from concurrent import futures
import hashlib
import os
import sys
import threading
import time
from PyQt6.QtWidgets import (
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
from PyQt6.QtCore import QObject, pyqtSignal
import grpc

from rpc_service import GRPC_PORT, GrpcClient, GrpcServer, RPCService
from config import Config
import rpc_service_pb2_grpc


class Signal(QObject):
    print_to_console = pyqtSignal(str)


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
        self.ip_label = QLabel("ip:")
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
        self.filepath_title_label = QLabel("文件:")
        self.filepath_title_label.setMinimumWidth(35)
        self.filepath_line_edit = QLineEdit(self.config.filepath)
        self.select_file_button = QPushButton("选择文件")
        self.select_file_button.clicked.connect(self.show_file_select_dialog)
        hbox_layout_02.addWidget(self.filepath_title_label, 0)
        hbox_layout_02.addWidget(self.filepath_line_edit, 1)
        hbox_layout_02.addWidget(self.select_file_button, 0)
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
        self.show()
        self.start_grpc_thread()

    def start_grpc_thread(self):
        self.grpc_server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        rpc_service_pb2_grpc.add_RpcServicer_to_server(
            RPCService(get_filepath=self.filepath_line_edit.text),
            self.grpc_server,
        )
        self.grpc_server.add_insecure_port("[::]:" + str(GRPC_PORT))
        self.grpc_server.start()

    def show_file_select_dialog(self):
        filepath = QFileDialog.getOpenFileName(
            self,
            "选择文件",
        )
        if filepath[0] != "":
            self.filepath_line_edit.setText(filepath[0])
            self.config.filepath = filepath[0]
            self.config.save()

    def show_ip_edit_dialog(self):
        input_dialog = QInputDialog()
        text, ok = input_dialog.getText(
            self, "修改ip", "请输入ip:", text=self.config.ip
        )
        if ok:
            self.ip_edit.setText(text)
            self.config.ip = text
            self.config.save()

    def start_sync(self):
        self.sync_button.setDisabled(True)

        def sync_method():
            self.print("开始同步")
            try:
                local_filepath = self.filepath_line_edit.text()
                with open(local_filepath, "rb") as fp:
                    data = fp.read()
                    local_file_md5 = hashlib.md5(data).hexdigest()
                local_file_basename = os.path.basename(local_filepath)
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
                        self.print("正在上传文件")
                        GrpcClient.upload_file(channel, data)
                        self.print("上传文件成功")
                    else:
                        self.print("正在下载文件")
                        response = GrpcClient.download_file(channel)
                        self.print("下载文件成功")
                        self.print("写入文件")
                        with open(local_filepath, "wb") as fp:
                            fp.write(response.data)
                        self.print("写入文件成功")
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

from concurrent import futures
import hashlib
import logging
import os
import time
import sys
import zipfile

import grpc
from compress import compress_file, decompress
import rpc_service_pb2
import rpc_service_pb2_grpc
from threading import Thread

DEFAULT_GRPC_PORT = 6465


def path_convention(path: str):
    path = path.replace("\\", "/")
    return os.path.join(*(path.split("/")))


class RPCService(rpc_service_pb2_grpc.RpcServicer):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__()
        self._get_filepath = kwargs["get_filepath"]
        self._logger = kwargs["logger"]

    def Ping(self, request, context):
        print(request)
        return rpc_service_pb2.PingReply(msg="pong")

    def Binary(self, request, context):
        print(request)
        return rpc_service_pb2.BinaryReply(msg="ok")

    def FileStatus(self, request, context):
        filepath = self._get_filepath()
        if not os.path.exists(filepath):
            return rpc_service_pb2.FileStatusReply(
                md5="", timestamp=0, filename=os.path.basename(filepath)
            )
        if os.path.isdir(filepath):
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("not a file")
        file_timestamp = int(os.path.getmtime(filepath))
        with open(filepath, "rb") as fp:
            data = fp.read()
            md5 = hashlib.md5(data).hexdigest()
        return rpc_service_pb2.FileStatusReply(
            md5=md5, timestamp=file_timestamp, filename=os.path.basename(filepath)
        )

    def UploadFile(self, it, context):
        filepath = self._get_filepath()
        self._logger(f"正在接收文件{os.path.basename(filepath)}")
        zip_filepath = "temp.zip"
        with open(zip_filepath, "wb") as fd:
            for i in it:
                fd.write(i.data)
        self._logger(f"接收文件成功")
        self._logger(f"正在解压")
        decompress(zip_filepath, os.path.dirname(filepath))
        self._logger(f"解压成功")
        return rpc_service_pb2.UploadFileReply(status=True)

    def DownloadFile(self, request, context):
        filepath = self._get_filepath()
        self._logger(f"正在压缩{os.path.basename(filepath)}")
        zip_filepath = "temp.zip"
        compress_file(filepath, zip_filepath)
        self._logger(f"压缩成功")
        self._logger(f"发送文件{os.path.basename(filepath)}")
        with open(zip_filepath, "rb") as fd:
            while True:
                data = fd.read(BUF_SIZE)
                if len(data) <= 0:
                    self._logger(f"发送文件成功")
                    return
                yield rpc_service_pb2.DownloadFileReply(data=data)

    def DownloadDirectory(self, request, context):
        self._logger("正在发送文件到远端")
        directory_path = self._get_filepath()
        with zipfile.ZipFile("temp.zip", "w", zipfile.ZIP_DEFLATED) as zip:
            for file in request.files:
                file = path_convention(file)
                local_filepath = os.path.join(directory_path, file)
                zip_filepath = local_filepath[len(directory_path) + 1 :]
                zip.write(local_filepath, zip_filepath)
        with open("temp.zip", "rb") as fd:
            while True:
                data = fd.read(BUF_SIZE)
                if len(data) <= 0:
                    self._logger(f"发送文件成功")
                    return
                yield rpc_service_pb2.DownloadDirectoryReply(data=data)

    def ReceiveDirectory(self, request, context):
        dir_path = self._get_filepath()
        self._logger(f"同步文件到{dir_path}中")
        zip_filepath = "temp.zip"
        with open(zip_filepath, "wb") as fd:
            for i in request:
                fd.write(i.data)
        self._logger("正在解压")
        decompress("temp.zip", dir_path)
        self._logger("解压成功")
        self._logger("同步成功")
        return rpc_service_pb2.ReceiveDirectoryReply()

    def DirectoryStatus(self, request, context):
        directory_path = self._get_filepath()
        if os.path.basename(directory_path) != request.directory_name:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("not a directory")
            return rpc_service_pb2.DirectoryStatusReply()
        result = []
        for path, _, filenames in os.walk(directory_path):
            for filename in filenames:
                local_filepath = os.path.join(path, filename)
                relative_path = local_filepath[len(directory_path) + 1 :]
                md5 = None
                try:
                    with open(local_filepath, "rb") as fp:
                        data = fp.read()
                        md5 = hashlib.md5(data).hexdigest()
                    file_timestamp = int(os.path.getmtime(local_filepath))
                except Exception as e:
                    print(e)
                    continue
                result.append(
                    rpc_service_pb2.FileStatusReply(
                        md5=md5,
                        timestamp=file_timestamp,
                        filename=relative_path,
                    )
                )
        return rpc_service_pb2.DirectoryStatusReply(files=result)


BUF_SIZE = 1024 * 1024 * 2


class GrpcClient:
    @staticmethod
    def get_channel(addr: str):
        ip = addr
        port = DEFAULT_GRPC_PORT
        i = addr.find(":")
        if i != -1:
            ip = addr[:i]
            port = int(addr[i + 1 :])
        return grpc.insecure_channel(f"{ip}:{port}")

    @staticmethod
    def get_remote_file_status(channel: grpc.Channel):
        stub = rpc_service_pb2_grpc.RpcStub(channel)
        return stub.FileStatus(rpc_service_pb2.FileStatusRequest())

    @staticmethod
    def upload_file(channel: grpc.Channel, filepath: str):
        def wrapper():
            with open(filepath, "rb") as fd:
                while True:
                    data = fd.read(BUF_SIZE)
                    if len(data) <= 0:
                        return
                    yield rpc_service_pb2.UploadFileRequest(data=data)

        stub = rpc_service_pb2_grpc.RpcStub(channel)
        response = stub.UploadFile(wrapper())
        return response

    @staticmethod
    def download_file(channel: grpc.Channel):
        stub = rpc_service_pb2_grpc.RpcStub(channel)
        return stub.DownloadFile(rpc_service_pb2.DownloadFileRequest())

    @staticmethod
    def get_remote_files_status(channel: grpc.Channel, directory_name: str):
        stub = rpc_service_pb2_grpc.RpcStub(channel)
        return stub.DirectoryStatus(
            rpc_service_pb2.DirectoryStatusRequest(directory_name=directory_name)
        )

    @staticmethod
    def upload_directory_archive(channel: grpc.Channel, archive_path: str = "temp.zip"):
        def wrapper():
            with open(archive_path, "rb") as fd:
                while True:
                    data = fd.read(BUF_SIZE)
                    if len(data) <= 0:
                        return
                    yield rpc_service_pb2.ReceiveDirectoryRequest(data=data)

        stub = rpc_service_pb2_grpc.RpcStub(channel)
        response = stub.ReceiveDirectory(wrapper())
        return response

    @staticmethod
    def download_files(channel: grpc.Channel, files):
        stub = rpc_service_pb2_grpc.RpcStub(channel)
        return stub.DownloadDirectory(
            rpc_service_pb2.DownloadDirectoryRequest(files=files)
        )


def serve():
    def wrapper():
        return "config.json"


def client_test():
    with grpc.insecure_channel("localhost:50051") as channel:
        stub = rpc_service_pb2_grpc.RpcServicer(channel)
        while True:
            time.sleep(3)
            response = stub.FileStatus(rpc_service_pb2.FileStatusRequest())
            print(response)
            # b = "hello".encode()
            # for i in range(0, len(b)):
            #     response = stub.Binary(rpc_service_pb2.BinaryRequest(b=b[i : i + 1]))
            #     print(response)
            break


def test():
    logging.basicConfig()
    t = Thread(target=client_test)
    t.start()
    serve()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("need file path")
        sys.exit(1)

    grpc_server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    service = rpc_service_pb2_grpc.add_RpcServicer_to_server(
        RPCService(get_filepath=lambda: sys.argv[1], logger=print),
        grpc_server,
    )
    grpc_server.add_insecure_port("[::]:" + str(DEFAULT_GRPC_PORT))
    grpc_server.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt as e:
        print("shutting down grpc server")
        grpc_server.stop(1)
        grpc_server.wait_for_termination()
        print("grpc server is shut down")

from concurrent import futures
import hashlib
import logging
import os
import time

import grpc
import rpc_service_pb2
import rpc_service_pb2_grpc
from threading import Thread

GRPC_PORT = 6465


class RPCService(rpc_service_pb2_grpc.RpcServicer):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__()
        self._get_filepath = kwargs["get_filepath"]

    def Ping(self, request, context):
        print(request)
        return rpc_service_pb2.PingReply(msg="pong")

    def Binary(self, request, context):
        print(request)
        return rpc_service_pb2.BinaryReply(msg="ok")

    def FileStatus(self, request, context):
        filepath = self._get_filepath()
        file_timestamp = int(os.path.getmtime(filepath))
        with open(filepath, "rb") as fp:
            data = fp.read()
            md5 = hashlib.md5(data).hexdigest()
        return rpc_service_pb2.FileStatusReply(
            md5=md5, timestamp=file_timestamp, filename=os.path.basename(filepath)
        )

    def UploadFile(self, request, context):
        filepath = self._get_filepath()
        with open(filepath, "wb") as fd:
            fd.write(request.data)
            return rpc_service_pb2.UploadFileReply(status=True)

    def DownloadFile(self, request, context):
        filepath = self._get_filepath()
        with open(filepath, "rb") as fd:
            data = fd.read()
            return rpc_service_pb2.DownloadFileReply(data=data)


class GrpcClient:
    @staticmethod
    def get_channel(ip: str):
        return grpc.insecure_channel(f"{ip}:{GRPC_PORT}")

    @staticmethod
    def get_remote_file_status(channel: grpc.Channel):
        stub = rpc_service_pb2_grpc.RpcStub(channel)
        return stub.FileStatus(rpc_service_pb2.FileStatusRequest())

    @staticmethod
    def upload_file(channel: grpc.Channel, data: bytes):
        stub = rpc_service_pb2_grpc.RpcStub(channel)
        return stub.UploadFile(rpc_service_pb2.UploadFileRequest(data=data))

    @staticmethod
    def download_file(channel: grpc.Channel, data: bytes):
        stub = rpc_service_pb2_grpc.RpcStub(channel)
        return stub.DownloadFile(rpc_service_pb2.DownloadFileRequest())


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
    test()

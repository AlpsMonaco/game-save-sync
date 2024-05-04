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


class GrpcServer:
    def __init__(self, *args, **kwargs) -> None:
        self._func_map = kwargs
        if "logger" in self._func_map:
            self._logger = self._func_map["logger"]
        else:
            self._logger = print

    def serve(self):
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        rpc_service_pb2_grpc.add_RpcServicer_to_server(
            RPCService(file_status_getter=self._func_map["file_status_getter"]),
            self.server,
        )
        self.server.add_insecure_port("[::]:" + str(GRPC_PORT))
        self.server.start()
        self._logger(f"grpc服务器启动,正在监听{GRPC_PORT}端口")
        self.server.wait_for_termination()


class GrpcClient:
    @staticmethod
    def get_channel(ip: str):
        return grpc.insecure_channel(f"{ip}:{GRPC_PORT}")

    @staticmethod
    def get_remote_file_status(channel: grpc.Channel):
        stub = rpc_service_pb2_grpc.RpcStub(channel)
        response = stub.FileStatus(rpc_service_pb2.FileStatusRequest())
        return response


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

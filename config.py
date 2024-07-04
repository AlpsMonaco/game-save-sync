import json

from rpc_service import DEFAULT_GRPC_PORT


class Config:
    def __init__(self) -> None:
        self.ip = ""
        self.filepath = ""
        self.listen_port = DEFAULT_GRPC_PORT
        self.x = None
        self.y = None

        try:
            with open("config.json") as fd:
                d = json.loads(fd.read())
                self.ip = d["ip"]
                self.filepath = d["filepath"]
                try:
                    self.listen_port = int(d["listen_port"])
                except Exception as e:
                    print(e)
                try:
                    self.x = int(d["x"])
                except Exception as e:
                    print(e)
                try:
                    self.y = int(d["y"])
                except Exception as e:
                    print(e)

        except Exception as e:
            print(e)

    def save(self):
        try:
            with open("config.json", "w") as fd:
                fd.write(
                    json.dumps(
                        {
                            "ip": self.ip,
                            "filepath": self.filepath,
                            "listen_port": self.listen_port,
                            "x": self.x,
                            "y": self.y,
                        }
                    )
                )
        except Exception as e:
            print(e)


if __name__ == "__main__":
    config = Config()
    config.save()

import json

from rpc_service import DEFAULT_GRPC_PORT
import locale


class Config:
    def __init__(self) -> None:
        self.ip = ""
        self.filepath = ""
        self.listen_port = DEFAULT_GRPC_PORT
        self.x = None
        self.y = None
        self.lang = None

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
                try:
                    self.lang = d["lang"]
                except Exception as e:
                    print(e)
                    self._try_get_lang()

        except Exception as e:
            self._try_get_lang()

    def _try_get_lang(self):
        language, _ = locale.getdefaultlocale()
        if language.lower().find("cn"):
            self.lang = "cn"
        else:
            self.lang = "en"

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
                            "lang": self.lang,
                        }
                    )
                )
        except Exception as e:
            print(e)


if __name__ == "__main__":
    config = Config()
    config.save()

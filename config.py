import json


class Config:
    def __init__(self) -> None:
        self.ip = ""
        self.filepath = ""

        try:
            with open("config.json") as fd:
                d = json.loads(fd.read())
                self.ip = d["ip"]
                self.filepath = d["filepath"]
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
                        }
                    )
                )
        except Exception as e:
            print(e)


if __name__ == "__main__":
    config = Config()
    config.save()

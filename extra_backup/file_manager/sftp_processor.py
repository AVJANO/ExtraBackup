class SFTPProcessor:
    username = None
    password = None
    address = None
    port = 445

    def __init__(self, username: str, password: str, address: str, port: int):
        self.username = username
        self.password = password
        self.address = address
        self.port = port

    def connect(self):
        pass

    def upload(self, filename: str):
        pass

    def download(self, filename: str):
        pass

    def list(self) -> list:
        pass

    def quit(self):
        pass
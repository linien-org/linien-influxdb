import signal

from time import sleep
from influxdb import InfluxDBClient


class Pusher:
    def __init__(self, pipe, cfg):
        self.cfg = cfg
        self.pipe = pipe
        self.queue = []

    def connect(self):
        self.idb = InfluxDBClient(
            host=self.cfg.influxdb_host,
            port=self.cfg.influxdb_port,
            username=self.cfg.influxdb_user,
            password=self.cfg.influxdb_password,
            database=self.cfg.influxdb_database
        )

    def run(self):
        while True:
            if self.pipe.poll():
                # FIXME: limit queue size
                self.add_to_queue(self.pipe.recv())

            if self.queue:
                self.send()

            # let the parent process know that we're still alive
            self.pipe.send(True)
            sleep(.1)

    def add_to_queue(self, data):
        self.queue.append(data)
        self.queue = self.queue[-1 * self.cfg.max_queue_length:]

    def send(self):
        self.idb.write_points(self.queue)
        self.queue = []



def push_data(pipe, cfg):
    # ignore sigint in worker
    signal.signal(signal.SIGINT, signal.SIG_IGN)

    pusher = Pusher(pipe, cfg)
    while True:
        try:
            pusher.connect()
            pusher.run()
        except:
            if cfg.debug:
                from traceback import print_exc
                print_exc()

            sleep(1)

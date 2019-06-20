import signal

from time import sleep
from influxdb import InfluxDBClient


class Pusher:
    def __init__(self, pipe, cfg):
        self.cfg = cfg
        self.pipe = pipe
        self.queue = []

        self.counter = 0

    def connect(self):
        self.idb = InfluxDBClient(
            host=self.cfg.influxdb_host,
            port=self.cfg.influxdb_port,
            username=self.cfg.influxdb_user,
            password=self.cfg.influxdb_password,
            database=self.cfg.influxdb_database
        )
        # this forces a check whether the database really exists
        self.check_connection()

    def run(self):
        while True:
            self.populate_queue()

            if self.queue:
                self.send()
            else:
                self.check_connection()

            # let the parent process know that we're still alive
            self.pipe.send(self.counter)
            sleep(self.cfg.echo_status_interval)

    def populate_queue(self):
        while self.pipe.poll():
            data = self.pipe.recv()

            if data['fields']:
                self.queue.append(data)
                self.queue = self.queue[-1 * self.cfg.max_queue_length:]

    def send(self):
        self.idb.write_points(self.queue)
        self.counter += len(self.queue)
        self.queue = []

    def check_connection(self):
        self.idb.query(
            'SELECT * FROM "%s" LIMIT 1' % (self.cfg.influxdb_database.replace('"', ''))
        )
        # FIXME: when a new version of influxdb is released,
        # including https://github.com/influxdata/influxdb-python/pull/678
        # update this to
        # self.idb.query(
        #     'SELECT * FROM $db LIMIT 1',
        #     bind_params={'db': self.cfg.influxdb_database}
        # )



def push_data(pipe, cfg):
    # ignore sigint in worker
    signal.signal(signal.SIGINT, signal.SIG_IGN)

    pusher = Pusher(pipe, cfg)

    iteration = -1

    while True:
        iteration += 1
        connected = False

        try:
            # read messages of the pipe and write them into our own queue such
            # that we have control over how many items are cached.
            pusher.populate_queue()

            pusher.connect()
            connected = True
            pusher.run()
        except:
            if cfg.debug or (iteration == 0 and not connected):
                from traceback import print_exc
                print_exc()

            sleep(1)

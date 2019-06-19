import os
import click

from time import time, sleep
from plumbum import colors
from datetime import datetime
from multiprocessing import Process, Pipe

import default_config
from pull import pull_data
from push import push_data

PRINT_INTERVAL = 1


class Runner:
    def __init__(self, cfg):
        self.cfg = cfg

        self.pull, pull_child_conn = Pipe()
        self.push, push_child_conn = Pipe()

        self.pull_process = Process(target=pull_data, args=(pull_child_conn, cfg))
        self.push_process = Process(target=push_data, args=(push_child_conn, cfg))

        self.pull_process.start()
        self.push_process.start()

        self.pull_data_time = 0
        self.push_data_time = 0
        self.push_data = None
        self.last_print_time = 0

    def run(self):
        try:
            while True:
                self.get_child_data()
                self.print_status()

                sleep(.05)
        except KeyboardInterrupt:
            self.pull_process.terminate()
            self.push_process.terminate()

    def get_child_data(self):
        if self.pull.poll():
            self.pull_data = self.pull.recv()
            self.pull_data_time = time()
            self.push.send(self.pull_data)

        if self.push.poll():
            self.push_data = self.push.recv()
            self.push_data_time = time()

    def print_status(self):
        interval = self.cfg.echo_status_interval

        if time() - self.last_print_time > interval:
            self.last_print_time = time()

            pull_live = False
            push_live = False

            if time() - self.pull_data_time < interval:
                pull_live = True
            if time() - self.push_data_time < interval:
                push_live = True

            status = lambda connected: (colors.Red | 'Disconnected') if not connected else (colors.Green | 'Connected')

            print(
                '   '.join((
                    datetime.now().strftime('%H:%M:%S'),
                    'Lock: ' + status(pull_live),
                    'InfluxDB: ' + status(push_live),
                    '       '
                )),
                end="\r"
            )


@click.command()
@click.argument('config')
def run(config):
    assert config.endswith('.py'), 'config file is not a python file'
    config = config.rstrip('.py')

    os.chdir(
        os.path.abspath(os.path.join(*os.path.split(config)[:-1]))
    )

    cfg = __import__(config)

    for attr in dir(default_config):
        if not attr.startswith('_'):
            if not hasattr(cfg, attr):
                setattr(cfg, attr, getattr(default_config, attr))

    runner = Runner(cfg)
    runner.run()


if __name__ == '__main__':
    run()
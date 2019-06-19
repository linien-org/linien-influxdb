import rpyc
import signal
import numpy as np
from time import sleep, time
from datetime import datetime

from linien.communication.client import BaseClient


class Puller:
    def __init__(self, pipe, cfg):
        self.cfg = cfg
        self.pipe = pipe

    def run(self):
        while True:
            try:
                self.connect()

                for data in self.pull():
                    self.pipe.send(data)
            except:
                if self.cfg.debug:
                    from traceback import print_exc
                    print_exc()

                sleep(1)

    def connect(self):
        # FIXME: check remote version
        self.connection = BaseClient(self.cfg.linien_host, self.cfg.linien_port)
        self.dp = DataPreparation(self.connection, self.cfg.data_fields)

    def pull(self):
        params = self.connection.parameters

        while True:
            start_time = time()
            yield {
                'measurement': self.cfg.influxdb_measurement,
                'tags': self.cfg.influxdb_tags,
                'time': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
                'fields': self.dp.load_data()
            }
            sleep(
                self.cfg.echo_status_interval
                - (time() - start_time)
            )


class DataPreparation:
    required_parameters = {
        'control_signal': ('to_plot',),
        'error_signal': ('to_plot',),
        'control_signal_std': ('to_plot',),
        'error_signal_std': ('to_plot',),
        'p': ('p',),
        'i': ('i',),
        'd': ('d',),
        'modulation_amplitude': ('modulation_amplitude',),
        'modulation_frequency': ('modulation_frequency,'),
        'demodulation_phase': ('demodulation_phase',),
        'demodulation_multiplier': ('demodulation_multiplier',),
    }

    def __init__(self, connection, data_fields):
        self.connection = connection
        self.data_fields = data_fields

    def load_data(self):
        params = self.load_parameters()
        return self.prepare_data(params)

    def load_parameters(self):
        param_keys = set()

        for field in self.data_fields:
            param_keys.update(set(self.required_parameters[field]))

        # FIXME: retrieve params all at the same time
        params = {}

        for key in param_keys:
            params[key] = getattr(self.connection.parameters, key).value

        return params

    def prepare_data(self, params):
        data = {}

        for field in self.data_fields:
            def default_cb(params, field=field):
                return params[field]

            cb = getattr(self, 'get_%s' % field, default_cb)
            cb(params)

        return data

    def get_control_signal(self, params):
        return np.mean(params['control_signal'])

    def get_error_signal(self, params):
        return np.mean(params['error_signal'])

    def get_control_signal_std(self, params):
        return np.std(params['control_signal'])

    def get_error_signal_std(self, params):
        return np.std(params['error_signal'])

def pull_data(pipe, cfg):
    # ignore sigint in worker
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    puller = Puller(pipe, cfg)
    puller.run()

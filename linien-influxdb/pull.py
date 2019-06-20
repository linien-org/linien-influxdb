import rpyc
import signal
import pickle
import numpy as np
from time import sleep, time
from datetime import datetime

from linien.communication.client import BaseClient


class Puller:
    def __init__(self, pipe, cfg):
        self.cfg = cfg
        self.pipe = pipe

    def run(self):
        iteration = -1

        while True:
            iteration += 1
            connected = False

            try:
                self.connect()
                connected = True

                for data in self.pull():
                    self.pipe.send(data)
            except:
                if self.cfg.debug or (iteration == 0 and not connected):
                    from traceback import print_exc
                    print_exc()

                sleep(1)

    def connect(self):
        # FIXME: check remote version
        self.connection = BaseClient(self.cfg.linien_host, self.cfg.linien_port, False)
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

            while True:
                time_until_next_logging = self.cfg.logging_interval - (time() - start_time)
                if time_until_next_logging > self.cfg.echo_status_interval:
                    sleep(self.cfg.echo_status_interval)
                    # check whether our connection is still there
                    self.check_connection()
                    # tell the master that we're still there
                    yield None
                else:
                    sleep(time_until_next_logging)
                    break

    def check_connection(self):
        self.connection.parameters.p.value


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
        'modulation_frequency': ('modulation_frequency',),
        'demodulation_phase': ('demodulation_phase',),
        'demodulation_multiplier': ('demodulation_multiplier',),
        'lock': ('lock',)
    }

    def __init__(self, connection, data_fields):
        self.connection = connection
        self.data_fields = data_fields

    def load_data(self):
        params = self.load_parameters()
        return self.prepare_data(params)

    def load_parameters(self):
        param_keys = set(['lock'])

        for field in self.data_fields:
            new = self.required_parameters[field]
            assert isinstance(new, (tuple, list)), 'invalid required parameter for %s' % field
            param_keys.update(set(new))

        # FIXME: retrieve params all at the same time
        params = {}

        for key in param_keys:
            params[key] = getattr(self.connection.parameters, key).value

        if 'to_plot' in params:
            to_plot = pickle.loads(params['to_plot'])
            if to_plot is not None:
                params['error_signal'], params['control_signal'] = to_plot

        return params

    def prepare_data(self, params):
        data = {}

        for field in self.data_fields:
            if not params['lock'] and field != 'lock':
                continue

            def default_cb(params, field=field):
                return params[field]

            cb = getattr(self, 'get_%s' % field, default_cb)
            data[field] = cb(params)

        return data

    def get_control_signal(self, params):
        return np.mean(params.get('control_signal', 0))

    def get_error_signal(self, params):
        return np.mean(params.get('error_signal', 0))

    def get_control_signal_std(self, params):
        return np.std(params.get('control_signal', 0))

    def get_error_signal_std(self, params):
        return np.std(params.get('error_signal', 0))

def pull_data(pipe, cfg):
    # ignore sigint in worker
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    puller = Puller(pipe, cfg)
    puller.run()

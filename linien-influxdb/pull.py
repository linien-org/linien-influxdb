import rpyc
import signal
import pickle
import numpy as np
from time import sleep, time
from datetime import datetime

from linien.communication.client import BaseClient
from linien.common import MHz, Vpp

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
        self.dp = DataPreparation(self.connection, self.cfg.data_fields, 
                                    lock_status_as_int=self.cfg.lock_status_as_int)

    def pull(self):

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
        'demodulation_phase_a': ('demodulation_phase_a',),
        'demodulation_multiplier_a': ('demodulation_multiplier_a',),
        'demodulation_phase_b' : ('demodulation_phase_b',),
        'demodulation_multiplier_b': ('demodulation_multiplier_b',),
        'lock': ('lock',)
    }

    def __init__(self, connection, data_fields, lock_status_as_int=False):
        self.connection = connection
        self.data_fields = data_fields
        self.lock_status_as_int = lock_status_as_int

    def load_data(self):
        params = self.load_parameters()
        return self.prepare_data(params)

    def load_parameters(self):
        param_keys = set(['lock'])

        for field in self.data_fields:
            # get parameter keys for the server, param_keys contains 'to_plot' 
            # once at most due to using set()
            new = self.required_parameters[field]
            assert isinstance(new, (tuple, list)), 'invalid required parameter for %s' % field
            param_keys.update(set(new))

        # FIXME: retrieve params all at the same time
        params = {}

        for key in param_keys:
            if key == 'to_plot':
                # special treatment for input and output signals
                to_plot = pickle.loads(self.connection.parameters.to_plot.value)
                for signal_key in ['control_signal', 'error_signal']:
                    # FIXME: should only calculate values in data_fields
                    params[signal_key] = np.mean(to_plot.get(signal_key, 0))
                    params[signal_key+'_std'] = np.std(to_plot.get(signal_key, 0))
            else:
                params[key] = getattr(self.connection.parameters, key).value

        return params

    def prepare_data(self, params):
        data = {}
        # only use additional data_fields if locked
        for field in self.data_fields:
            if not params['lock'] and field != 'lock':
                continue
            if 'signal' in field:
                # Convert to mV
                data[field] = params[field] / Vpp / 2 
            elif field == 'modulation_frequency':
                # convert to Mhz
                data[field] = params[field] / MHz
            else:
                data[field] = params[field]
        if self.lock_status_as_int:
            data['lock'] = int(data['lock'])
        return data

def pull_data(pipe, cfg):
    # ignore sigint in worker
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    puller = Puller(pipe, cfg)
    puller.run()

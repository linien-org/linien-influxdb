linien_host = 'localhost'
linien_port = 18862

influxdb_host = 'localhost'
influxdb_port = 8086
influxdb_user = None
influxdb_password = None
# FIXME: set to None
influxdb_database = 'test'
influxdb_measurement = 'linien'
influxdb_tags = {}

data_fields = (
    'control_signal', 'error_signal', 'control_signal_std', 'error_signal_std',
    'p', 'i', 'd', 'modulation_amplitude', 'modulation_frequency',
    'demodulation_phase', 'demodulation_multiplier'
)

echo_status_interval = 1 # in seconds
max_queue_length = 10000

debug = False
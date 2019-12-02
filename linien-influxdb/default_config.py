logging_interval = 1 # in seconds

# On which host is the linien server running? Should point to a RedPitaya
linien_host = 'localhost'
# On which port does the server run?
linien_port = 18862

# influxdb configuration parameters
influxdb_host = 'localhost'
influxdb_port = 8086
influxdb_user = None # optional
influxdb_password = None # optional
influxdb_database = None
influxdb_measurement = 'linien'
influxdb_tags = {}
influxdb_ssl = False
influxdb_verify_ssl = True

# which fields should be logged?
# notice that all parameters are only logged when the lock is turned on (not in
# ramping mode)
data_fields = (
    'lock',                 # is the laser locked?

    # the following parameters are only logged if the laser is locked
    #'control_signal',       # the mean value of the control signal
    #'error_signal',         # the mean value of the control signal
    #'control_signal_std',   # the standard deviation of the control signal
    #'error_signal_std',     # the standard deviation of the error signal
    'p', 'i', 'd',          # the PID parameters,
    'modulation_amplitude', # amplitude of modulation frequency for spectroscopy
    'modulation_frequency', # frequency of modulation for spectroscopy
    'demodulation_phase_a',   # demodulation phase for spectroscopy
    'demodulation_multiplier_a', # demodulation frequency multiplier for spectroscopy
    'demodulation_phase_b',   # demodulation phase for spectroscopy
    'demodulation_multiplier_b', # demodulation frequency multiplier for spectroscopy
)

echo_status_interval = 1 # in seconds
# if the influxdb server is down, how many values should be cached?
max_queue_length = 1000

debug = False
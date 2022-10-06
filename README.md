Logs the status of a [linien](https://github.com/linien-org/linien) spectroscopy lock server to influxdb.

# Installation

``` bash
sudo pip install linien-influxdb
```

Note that `linien-influxdb` is currently only compatible with influxdb2.
# Usage

`linien-influxdb` is a command line tool that uses an ini-file for configuration:

```bash
    linien-influxdb config.ini
```

To get help, use

```bash
    linien-influxdb --help
```

An example configuration file, can be found [here](https://github.com/linien-org/linien-influxdb/blob/master/linien_influxdb/example_config.ini):

```ini
[influx2]
url=http://localhost:8086
org=my-org
token=my-token
timeout=6000
verify_ssl=False
bucket=my-bucket
measurement=linien-status

[linien]
host=rp-f0xxxxx.local
username=root
password=root
interval=10 # log interval in seconds
parameters=lock, modulation_amplitude, modulation_frequency, p, i, d, monitor_signal_mean, error_signal_mean, error_signal_std, control_signal_mean
```

For more parameters, have a look at [`parameters.py`](https://github.com/linien-org/linien/blob/master/linien/server/parameters.py) of Linien.
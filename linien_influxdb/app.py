from configparser import ConfigParser
from time import sleep

import click
from influxdb_client import InfluxDBClient, Point
from linien.client.connection import LinienClient, MHz, Vpp


class LinienConnection:
    def __init__(self, host, username="root", password="root"):
        self.client = LinienClient(
            {"host": host, "username": username, "password": password}
        )

    def get_parameters(self, parameters):

        # get the `signal_stats` parameter only once and only if required
        stats_suffices = ["_min", "_max", "_mean", "_std"]
        if any(
            [
                any([stats_suffix in param for stats_suffix in stats_suffices])
                for param in parameters
            ]
        ):
            signal_stats = self.client.parameters.signal_stats.value

        data = {}
        for param in parameters:
            if any(stats_suffix in param for stats_suffix in stats_suffices):
                try:
                    data[param] = signal_stats[param]
                except KeyError:
                    # the keys of `signal_stats` change depending on `lock` state.
                    # continue with next parameter to avoid failed conversion to
                    # volts in the next step
                    continue
            else:
                data[param] = getattr(self.client.parameters, param).value
            if param == "modulation_amplitude":
                data[param] = data[param] / Vpp  # convert to V
            elif param == "modulation_frequency":
                data[param] = data[param] / MHz
            # at last, convert to volts if required
            if "signal" in param:
                data[param] = data[param] / (2 * Vpp)
            if "slow_mean" == param:
                # range of slow is 0 -- 1.3 V
                data[param] = data[param] / (2 * Vpp) * 0.9 + 0.9

        return data


@click.command()
@click.version_option()
@click.option(
    "--config",
    "config_file",
    type=click.Path(exists=True),
    help="Configuration file path.",
    required=True,
)
def main(config_file):
    config = ConfigParser(
        converters={"list": lambda x: [i.strip() for i in x.split(",")]}
    )
    config.read(config_file)

    bucket = config["influx2"]["bucket"]
    interval = config["linien"].getfloat("interval")
    measurement = config["linien"]["measurement"]
    parameters = config["linien"].getlist("parameters")
    host = config["linien"]["host"]
    username = config["linien"]["username"]
    password = config["linien"]["password"]

    if len(parameters) == 1 and parameters[0] == "":
        raise ValueError(
            "No parameters requested. Add at least one parameter in the .ini file."
        )

    connection = LinienConnection(host, username, password)

    with InfluxDBClient.from_config_file(config_file) as client:
        write_api = client.write_api()

        while True:
            point = Point(measurement)
            parameters = connection.get_parameters(parameters=parameters)
            print(parameters)
            for key, value in parameters.items():
                point.field(key, value)
            write_api.write(bucket=bucket, record=point)
            sleep(interval)


if __name__ == "__main__":
    main()

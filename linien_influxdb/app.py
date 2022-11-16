from configparser import ConfigParser
from time import sleep
from typing import Any, Dict, List

import click
from influxdb_client import InfluxDBClient, Point
from linien.client.connection import LinienClient, MHz, Vpp


class LinienConnection:
    def __init__(self, host: str, username: str = "root", password: str = "root"):
        self.client = LinienClient(
            {"host": host, "username": username, "password": password}
        )

    def get_parameters(self, parameters: List[str]) -> Dict[str, Any]:

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
@click.argument("config", type=click.Path(exists=True))
@click.option(
    "--print-only",
    default=False,
    is_flag=True,
    help="Do not write the logged data to influxdb.",
)
def main(config: str, print_only: bool):
    """Logs Linien parameters according to the configuration in CONFIG ini file."""
    config_parser = ConfigParser(
        converters={"list": lambda x: [i.strip() for i in x.split(",")]}
    )
    config_parser.read(config)

    if not print_only:
        bucket = config_parser["influx2"]["bucket"]
        measurement = config_parser["influx2"]["measurement"]
    interval = config_parser["linien"].getfloat("interval")
    requested_parameters = config_parser["linien"].getlist("parameters")
    host = config_parser["linien"]["host"]
    username = config_parser["linien"]["username"]
    password = config_parser["linien"]["password"]

    if len(requested_parameters) == 1 and requested_parameters[0] == "":
        raise ValueError(
            "No parameters requested. Add at least one parameter in the .ini file."
        )

    connection = LinienConnection(host, username, password)

    if not print_only:
        with InfluxDBClient.from_config_file(config) as client:
            write_api = client.write_api()
            while True:
                point = Point(measurement)
                parameters = connection.get_parameters(parameters=requested_parameters)
                print(parameters)
                for key, value in requested_parameters.items():
                    point.field(key, value)
                write_api.write(bucket=bucket, record=point)
                sleep(interval)
    else:
        while True:
            parameters = connection.get_parameters(parameters=requested_parameters)
            print(parameters)
            sleep(interval)


if __name__ == "__main__":
    main()

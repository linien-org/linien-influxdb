Logs the status of a `linien <https://github.com/hermitdemschoenenleben/linien>`_
spectroscopy lock server to influxdb.

============
Installation
============

..  code-block:: bash

    sudo pip3 install linien-influxdb

============
Usage
============
First, you have to create a `config.py` file with the basic configuration:


..  code-block:: python

    # On which host is the linien server running? Should point to a RedPitaya
    linien_host = 'localhost'

    # influxdb configuration parameters
    influxdb_host = 'localhost'
    influxdb_port = 8086
    influxdb_user = None # optional
    influxdb_password = None # optional
    influxdb_database = 'my_database_name'
    influxdb_measurement = 'linien'

    logging_interval = 1 # in seconds

For a complete list of parameters, refer to
`default_config.py <https://github.com/hermitdemschoenenleben/linien-influxdb/blob/master/linien-influxdb/default_config.py>`_.

Then you can start the application (in the directory of `config.py`):

..  code-block:: bash

    linien-influxdb config.py
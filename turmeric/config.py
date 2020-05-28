import json
import logging

DEFAULT_CONFIG_FILE = 'config.json'

def load_config(config=DEFAULT_CONFIG_FILE):
    _load_config_file(config)

def _load_config_file(filename):
    logging.info(f'Loading config file {filename}')
    try:
        with open(filename, 'r') as f:
            config = json.load(f)

        import turmeric.options
        for k, desc in config.items():
            print(f"Setting {k} to {desc['value']}")
            setattr(turmeric.options,k,desc['value'])
    except FileNotFoundError as e:
        logging.error(f"Config file {filename} not found")

options = {}

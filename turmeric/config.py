import json
import logging
import turmeric.settings

DEFAULT_CONFIG_FILE = 'config.json'

def load_config(configfile=DEFAULT_CONFIG_FILE,configdict=None):
    if configdict is not None:
        _write_options(configdict)
    else:
        _load_config_file(configfile)

def write_config(configdict, configfile=DEFAULT_CONFIG_FILE):
    with open(configfile,'w') as f:
        json.dump(configdict, f, sort_keys=True)

def _write_options(configdict):
    for k, desc in configdict.items():
        setattr(turmeric.settings,k,desc['value'])


def _load_config_file(filename):
    logging.info(f'Loading config file {filename}')
    try:
        with open(filename, 'r') as f:
            config = json.load(f)

        _write_options(config)
        setattr(turmeric.settings,'config_filename',{'value' : filename, 'type':'str', 'description' : 'The name of the current config file'})
    except FileNotFoundError as e:
        logging.error(f"Config file {filename} not found")

#!/usr/bin/env python3

"""
Flask server to provide a simple interface to the Mines Maker society's custom vending machine.
Requires Python 3.6 or newer.

Command-line options
====================
Currently, no command line options are accepted.

Configuration
=============
The behavior of the server can be configured using three YAML files:
 * config.yaml: Controls server settings (bind address, port, etc.). Further documented in settings.py
 * items.yaml: Controls inventory manifest for the vending machine. Further documented in items.py
 * users.yaml: Controls users and user permissions. Further documented in users.py
"""

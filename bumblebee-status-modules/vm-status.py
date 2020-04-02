# pylint: disable=C0111,R0903
# -*- coding: utf-8 -*-

"""Displays the price of a cryptocurrency.

Requires the following python packages:
    * requests

Parameters:
    * getcrypto.interval: Interval in seconds for updating the price, default is 120, less than that will probably get your IP banned.
    * getcrypto.getbtc: 0 for not getting price of BTC, 1 for getting it (default).
    * getcrypto.geteth: 0 for not getting price of ETH, 1 for getting it (default).
    * getcrypto.getltc: 0 for not getting price of LTC, 1 for getting it (default).
    * getcrypto.getcur: Set the currency to display the price in, usd is the default.
"""

import subprocess
import time
import bumblebee.util
import bumblebee.input
import bumblebee.output
import bumblebee.engine
from requests.exceptions import RequestException

class Module(bumblebee.engine.Module):
    def __init__(self, engine, config):
        super(Module, self).__init__(engine, config,
            bumblebee.output.Widget(full_text=self.make)
        )
        self.text = ""
        self._nextcheck = 0
        self._interval = int(self.parameter("interval", "3"))
        engine.input.register_callback(self, button=bumblebee.input.LEFT_MOUSE,
                                       cmd=self.click)

    def make(self, widget):
        return self.text.strip()

    def click(self, e=None):
      try:
        subprocess.call('vm-switch')
        self.text = subprocess.check_output('vm-status').strip().decode('utf-8')
      except:
        self.text = 'unknown'

    def update(self, widgets):
      if self._nextcheck < int(time.time()):
        self._nextcheck = int(time.time()) + self._interval
        try:
          self.text = subprocess.check_output('vm-status').strip().decode('utf-8')
        except:
          self.text = 'unknown'

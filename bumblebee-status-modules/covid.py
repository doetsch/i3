# pylint: disable=C0111,R0903
# -*- coding: utf-8 -*-

"""
  Displays covid stats
"""

import requests
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
        self._interval = int(self.parameter("interval", "300"))
        self._country = self.parameter("country", "Germany")

        engine.input.register_callback(self, button=bumblebee.input.LEFT_MOUSE,
            cmd="xdg-open https://www.worldometers.info/coronavirus/")

    def make(self, widget):
        return self.text.strip()

    def update(self, widgets):
      if self._nextcheck < int(time.time()):
        self._nextcheck = int(time.time()) + self._interval
        try:
          data = requests.get('https://www.worldometers.info/coronavirus/').text
          idy = data.find('href="country/' + self._country.lower())
          idy = data.find('</td>', idy)

          idy = data.find('</td>', idy + 1)
          idx = idy
          while data[idx] != '>' and idx >= 0:
            idx -= 1
          total_cases = data[idx+1:idy].strip()

          idy = data.find('</td>', idy + 1)
          idx = idy
          while data[idx] != '>' and idx >= 0:
            idx -= 1
          new_cases = data[idx+1:idy].strip()

          idy = data.find('</td>', idy + 1)
          idx = idy
          while data[idx] != '>' and idx >= 0:
            idx -= 1
          total_deaths = data[idx+1:idy].strip()

          idy = data.find('</td>', idy + 1)
          idx = idy
          while data[idx] != '>' and idx >= 0:
            idx -= 1
          new_deaths = data[idx+1:idy].strip()
          self.text = " ".join([total_cases, '|', new_cases, '|', total_deaths, '|', new_deaths])
        except:
          self.text = 'unknown'

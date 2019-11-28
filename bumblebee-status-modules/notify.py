# -*- coding: utf-8 -*-

"""i3 notification widget

Requires the following python packages:
    * python-i3

Parameters:
"""

import requests
import time
import bumblebee.util
import bumblebee.input
import bumblebee.output
import bumblebee.engine
import i3
import subprocess

class Module(bumblebee.engine.Module):
    def __init__(self, engine, config):
        super(Module, self).__init__(engine, config,
            bumblebee.output.Widget(full_text=self.make)
        )
        i3.Subscription(self.i3sub, 'workspace')
        engine.input.register_callback(self, button=bumblebee.input.LEFT_MOUSE, cmd="i3-msg '[class=\"Signal\"] focus'")
        engine.input.register_callback(self, button=bumblebee.input.RIGHT_MOUSE, cmd="update-manager")
        self.text = ""
        self._nextcheck = 0
        self.signal = False
        self.update(None)

    def i3sub(self, event, data, subscription):
      if event['change'] == 'urgent':
        for node in event['current']['floating_nodes'][0]['nodes']:
          if node['name'] == 'Signal':
            if node['urgent']:
              self.signal = True
            else:
              self.signal = False

    def make(self, widget):
      return self.text.strip()

    def state(self, widget):
      if self.signal:
        return ["warning"]
      return ["default"]

    def update(self, widgets):
      if self._nextcheck < int(time.time()):
        self._nextcheck = int(time.time()) + 300
        upd, sec = map(int,subprocess.Popen("/usr/lib/update-notifier/apt_check.py 2>&1",
                                            shell=True, stdout=subprocess.PIPE).stdout.read().split(';'))
        self.text = '◯'
        if upd > 0:
          self.text = u"\u25CF"
        if sec > 0:
          self.text = u"\U0001F534"






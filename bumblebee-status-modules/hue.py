# pylint: disable=C0111,R0903
# -*- coding: utf-8 -*-

"""Hue light control and notification

Requires the following python packages:
    * phue

Parameters:
    * hue.bridge: IP of Hue bridge.
    * hue.group: Name of group to control.
    * hue.action: action to execute when icon is right-clicked (default: luminance).

    * hue.interval: Polling interval in seconds (default: 5).
    * hue.sensor: Name of Sensor to read.
"""

import requests
import time
import bumblebee.util
import bumblebee.input
import bumblebee.output
import bumblebee.engine
from phue import Bridge, Group
from _thread import start_new_thread
from threading import Lock
import datetime
import json
import random
import gzip
from os import listdir
from rgbxy import Converter

import openrazer.client as rclient

class Module(bumblebee.engine.Module):
    def __init__(self, engine, config):
        super(Module, self).__init__(engine, config,
            bumblebee.output.Widget(full_text=self.make)
        )
        while True:
          try:
            self.bridge = Bridge(self.parameter("bridge", ""))
            self.bridge.connect()
            for group_id, group in self.bridge.get_group().items():
              if group['name'] == self.parameter("group", ""):
                break
            break
          except:
            self.text = "error: could not connect to bridge at: " + self.parameter("bridge", "")
            time.sleep(1)

        if group['name'] != self.parameter("group", ""):
          self.text = "error: unknown group: " + self.parameter("group", "")
          return

        self.group = Group(self.bridge, int(group_id))
        self.scene_ids = set([l.light_id for l in self.group.lights])
        self.scene_idx = len(self.bridge.scenes)
        self.brightness = 0
        self.base_brightness = self.group.brightness
        self.modify_brightness = True

        self._nextcheck = 0
        self._tempcheck = 0
        self._statecheck = 0
        self.lock = Lock()
        self.lock.acquire()
        start_new_thread(self.play, ())
        start_new_thread(self.razer, ())
        self.on = self.group.on
        self._interval = int(self.parameter("interval", "1"))

        engine.input.register_callback(self, button=bumblebee.input.LEFT_MOUSE,
                                       cmd=self.click)
        engine.input.register_callback(self, button=bumblebee.input.MIDDLE_MOUSE,
                                       cmd=self.middle)
        engine.input.register_callback(self, button=bumblebee.input.RIGHT_MOUSE,
                                       cmd=self.rightclick)
                                       #cmd=self.parameter("action", "luminance"))
        engine.input.register_callback(self, button=bumblebee.input.WHEEL_UP,
                                       cmd=self.increase_brightness)
        engine.input.register_callback(self, button=bumblebee.input.WHEEL_DOWN,
                                       cmd=self.decrease_brightness)

        self.text = "%d%%" % (100 * self.brightness / 255)
        self.middle()

    def rightclick(self, e=None):
      lights = self.bridge.get_light_objects('name')
      if self.parameter("plug", "") in lights:
        lights[self.parameter("plug", "")].on = not lights[self.parameter("plug", "")].on

    def click(self, e=None):
      self.group.on = self.on = not self.group.on
      self._statecheck = int(time.time()) + 1

    def play(self):
      dir = self.parameter('rec', '.')
      keys = ['night','morning','day','evening']
      models = {k: [] for k in keys}
      for k in models:
        for f in listdir(dir + '/' + k):
          if f.endswith('.gz'):
            models[k].append(json.loads(gzip.open(dir + '/' + k + '/' + f).read()))
      speed = 0.1
      key = ''
      lights = self.bridge.get_light_objects('name')
      while True:
        self.lock.acquire()
        now = datetime.datetime.now()
        if now.hour < 5:
          hour = 0
        elif now.hour < 10:
          hour = 1
        elif now.hour < 18:
          hour = 2
        else:
          hour = 3
        if keys[hour] != key:
          key = keys[hour]
          seed = now.year * 10000 + now.month * 100 + now.day
          var = int(seed % len(models[key]))
          t = int(seed % len(models[key][var]))
          while models[key][var][t][1] < 2:
            t = (t + 1) % len(models[key][var])
        x = models[key][var][t]
        t = (t + 1) % len(models[key][var])

        try:
          for l in x[0]:
            if x[0][l][2] > 0:
              lights[l].transitiontime = max(int(10 * x[0][l][2] / speed), 1)
              lights[l].xy = x[0][l][0]
              lights[l].brightness = min(max(int(x[0][l][1]) + self.brightness,0),255)
              if l == 'Desk Go':
                for d in ['TV left', 'TV right']:
                  lights[d].transitiontime = max(int(10 * x[0][l][2] / speed), 1)
                  lights[d].xy = x[0][l][0]
                  lights[d].brightness = min(max(int(x[0][l][1]) + self.brightness,0),255)
              #if l == 'Desk Center':
              #  #hex = self.rgbxy.xy_to_hex(x[0][l][0][0],x[0][l][0][1],bri=min(max(int(x[0][l][1]) + self.brightness,0),255)/255.)
              #  #rgb = tuple(int(hex[i:i+2], 16) for i in (0, 2, 4))
              #  r, g, b = self.rgbxy.color.get_rgb_from_xy_and_brightness(x[0][l][0][0],x[0][l][0][1],min(max(int(x[0][l][1]) + self.brightness,0),255)/255.)
              #  #r, g, b = self.rgbxy.color.get_rgb_from_xy(x[0][l][0][0],x[0][l][0][1])
              #  self.razer = rclient.DeviceManager()
              #  for device in self.razer.devices:
              #    if device.name == 'Razer Huntsman Elite':
              #      device.fx.static(r, g, b)
            self.group.brightness = min(max(self.base_brightness + self.brightness,0),255)
        except:
          self.text = "play error"
        self.lock.release()
        time.sleep(x[1] / speed)

    def razer(self):
      rgbxy = Converter()
      manager = rclient.DeviceManager()
      for device in manager.devices:
        if device.name == 'Razer Huntsman Elite':
          break
      src = self.bridge.get_light_objects('name')['Desk Center']
      while True:
        src = self.bridge.get_light_objects('name')['Desk Center']
        manager = rclient.DeviceManager()
        for device in manager.devices:
          if device.name == 'Razer Huntsman Elite':
            break
        r, g, b = rgbxy.color.get_rgb_from_xy_and_brightness(src.xy[0], src.xy[1], src.brightness)
        device.fx.static(r, g, b)
        time.sleep(3)

    def middle(self, e=None):
      if self.scene_idx == len(self.bridge.scenes):
        self.group.on = not self.group.on
        time.sleep(1.0)
        self.group.on = not self.group.on
        self.lock.release()
      else:
        if self.scene_idx == 0:
          self.lock.acquire()
        self.bridge.activate_scene(self.group.group_id, self.bridge.scenes[self.scene_idx].scene_id)
      self.scene_idx = (self.scene_idx + 1) % (len(self.bridge.scenes) + 1)
      while self.scene_idx < len(self.bridge.scenes):
        if any([l in self.scene_ids for l in self.bridge.scenes[self.scene_idx].lights]):
          break
        self.scene_idx = (self.scene_idx + 1) % (len(self.bridge.scenes) + 1)

    def increase_brightness(self, e=None):
      if self.brightness >= 255: return
      self.brightness += 5
      self.text = "%d%%" % (100 * self.brightness / 255)
      self._nextcheck = int(time.time()) + self._interval
      self._tempcheck = int(time.time()) + self._interval + 3
      self.modify_brightness = True

    def decrease_brightness(self, e=None):
      if self.brightness <= -255: return
      self.brightness -= 5
      self.text = "%d%%" % (100 * self.brightness / 255)
      self._nextcheck = int(time.time()) + self._interval
      self._tempcheck = int(time.time()) + self._interval + 3
      self.modify_brightness = True

    def make(self, widget):
      return self.text.strip()

    def state(self, widget):
      if self._statecheck < int(time.time()):
        self._statecheck = int(time.time()) + 1
        try:
          self.on = self.group.on
        except:
          self.text = "state error"
      if not self.on:
        return ["warning"]
      return ["default"]

    def update(self, widgets):
      if self._nextcheck < int(time.time()) and self.modify_brightness:
        self._nextcheck = int(time.time()) + self._interval
        try:
          self.group.brightness = min(max(self.base_brightness + self.brightness,0),255)
          self._tempcheck = int(time.time()) - 1
          self.modify_brightness = False
        except:
          self.text = "brightness error"
      if self._tempcheck < int(time.time()):
        self._tempcheck = int(time.time()) + 5
        try:
          if self.parameter("sensor", ""):
            api = self.bridge.get_api()['sensors']
            sensors = {}
            for s in api:
              if api[s].get('productname', '') == 'Hue motion sensor' and api[s]['name'] == self.parameter("sensor", ""):
                sensors = {
                  'motion': api[str(int(s) + 0)]['state'],
                  'light': api[str(int(s) + 1)]['state'],
                  'temperature': api[str(int(s) + 2)]['state']
                }
                break
            self.text = "%.1f°" % (float(sensors['temperature']['temperature'])/100,)
        except:
          self.text = "sensor error"

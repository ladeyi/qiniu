#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import ConfigParser

config = ConfigParser.ConfigParser()
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
config.read(os.path.join(BASE_DIR, 'app.conf'))


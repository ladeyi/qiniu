#!/usr/bin/python
# -*- coding: utf-8 -*-
import qiniu
from qiniu import CdnManager
import time
import os
from config import config

def print_result(result):
    if result[0] is not None:
        print(result[0])


access_key = config.get("qiniu_key", "access_key")
secret_key = config.get("qiniu_key", "secret_key")
charset = config.get("charset", "charset_name")

auth = qiniu.Auth(access_key=access_key, secret_key=secret_key)
cdn_manager = CdnManager(auth)
scriptdir = os.path.realpath(os.path.dirname(__file__))
urltext = os.path.join(scriptdir, "url.txt")

urls = []

with open(urltext) as f:
    for line in f.readlines():
        urls.append(line.decode(charset))

print('刷新url')
refresh_dir_result = cdn_manager.refresh_urls(urls)
print_result(refresh_dir_result)


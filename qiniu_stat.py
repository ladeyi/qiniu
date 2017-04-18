#!/usr/bin/env python
# -*- coding: utf-8 -*-

from qiniu import Auth
from qiniu import BucketManager
from config import config
import sys


access_key = config.get("qiniu_key", "access_key")
secret_key = config.get("qiniu_key", "secret_key")
bucket_name = config.get("bucket", "bucket_name")

#初始化Auth状态
q = Auth(access_key, secret_key)

#初始化BucketManager
bucket = BucketManager(q)

#你要测试的空间， 并且这个key在你空间中存在

key = sys.argv[1]

#获取文件的状态信息
ret, info = bucket.stat(bucket_name, key)
print ret
assert 'hash' in ret

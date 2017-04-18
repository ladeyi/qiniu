#!/usr/bin/env python
# -*- coding: utf-8 -*-

from qiniu import Auth, put_file, etag, urlsafe_base64_encode
import qiniu.config
from config import config
import re
import logging
import ConfigParser
import os


class Upload:
   def __init__(self, localfile):
       if not localfile:
           localfile = []
       if not isinstance(localfile, list):
           self.localfile = [localfile]
       else:
           self.localfile = localfile
       self.access_key = config.get("qiniu_key", "access_key")
       self.secret_key = config.get("qiniu_key", "secret_key")
       self.bucket = config.get("bucket", "bucket_name")
       self.local_root = config.get("data_path", "local_root") 
       self.q = Auth(self.access_key, self.secret_key)
       self.log_path = config.get("log", "log_path")
       logging.basicConfig(level=logging.INFO,filename=self.log_path)


   def get_remotefile(self):
       """
       获取去掉根目录之后的文件路径列表
       """
       root_path = [x for x in self.local_root.split("/") if x != ""]
       remotefile = {}
       for f in self.localfile:
           file_path = [x for x in f.split("/") if x != ""]
           remote_path_list = file_path[len(root_path):]
           remote_path = "/".join(remote_path_list)
           remotefile[remote_path] = f
       return remotefile

   def upload_files(self):
       """
       上传文件
       """
       remotefile = self.get_remotefile()
       for key in remotefile:
           token = self.q.upload_token(self.bucket, key, 3600)
           ret, info = put_file(token, key, remotefile[key])
           try:
               assert ret['key'] == key
               assert ret['hash'] == etag(remotefile[key])
               logging.info("%s upload success" % remotefile[key])
           except Exception as e:
               print e
               logging.error("%s upload failed: %s" % (remotefile[key], e))


#!/usr/bin/env python
# -*- coding: utf-8 -*-

import qiniu
from qiniu import Auth, etag, BucketManager
import os
import re
import urllib2
import sys
from config import config



access_key = config.get("qiniu_key", "access_key")
secret_key = config.get("qiniu_key", "secret_key")
bucket_name = config.get("bucket", "bucket_name")
bucket_domain = config.get("domain", "bucket_domain")
basedir = config.get("data_path", "local_root")
charset = config.get("charset", "charset_name")



q = Auth(access_key, secret_key)
bucket = BucketManager(q)
filename=__file__
ignore_paths=[filename,"{0}c".format(filename)]
ignore_names=[".DS_Store",".git",".gitignore"]



def list_all(bucket_name, bucket=None, prefix="", limit=100):
    rlist=[]
    if bucket is None:
        bucket = BucketManager(q)
    marker = None
    eof = False
    while eof is False:
        ret, eof, info = bucket.list(bucket_name, prefix=prefix, marker=marker, limit=limit)
        marker = ret.get('marker', None)
        for item in ret['items']:
            rlist.append(item["key"])
    if eof is not True:
        pass
    return rlist

def get_files(basedir="",fix="",rlist=None,ignore_paths=[],ignore_names=[]):
    if rlist is None:
        rlist=[]
    for subfile in os.listdir(basedir):
        temp_path=os.path.join(basedir,subfile)
        tp=os.path.join(fix,subfile)
        if tp in ignore_names:
            continue
        if tp in ignore_paths:
            continue
        if os.path.isfile(temp_path):
            rlist.append(tp)
        elif os.path.isdir(temp_path):
            get_files(temp_path,tp,rlist,ignore_paths,ignore_names)
    return rlist

def diff_file(rlist, llist, basedir=""):
    diff_list = []
    rlist = [r.encode(charset) if isinstance(r,unicode) else r for r in rlist]
    ops=qiniu.build_batch_stat(bucket_name,rlist)
    rets,infos = bucket.batch(ops)

    for i in xrange(len(rlist)):
        r = rlist[i]
        if r not in llist:
            diff_list.append(r)
        else:
            local_f = os.path.join(basedir,r)
            local_hash=etag(local_f)
            ret=rets[i]["data"]
            remote_hash=ret.get("hash",None)
            if local_hash != remote_hash:
                diff_list.append(r)
    return diff_list


def down_file(key,basedir="",is_private=1,expires=3600):
    if isinstance(key,unicode):
        key=key.encode(charset)
    url = 'http://%s/%s' % (bucket_domain, key)
    if is_private:
        url=q.private_download_url(url, expires=expires)
    c=urllib2.urlopen(url)
    fpath=key.replace("/",os.sep)
    savepath=os.path.join(basedir,fpath)
    dir_=os.path.dirname(savepath)
    if not os.path.isdir(dir_):
        os.makedirs(dir_)
    elif os.path.isfile(savepath):
        os.remove(savepath)
    f = file(savepath, 'wb')
    f.write(c.read())
    f.close()

def down_all(prefix=""):
    import traceback
    rlist = list_all(bucket_name,bucket,prefix=prefix)
    llist = get_files(basedir=basedir)
    list_diff = diff_file(rlist, llist, basedir=basedir)
    for key in list_diff:
        try:
            down_file(key,basedir=basedir)
            print "down:\t"+key
        except:
            print "error down:\t"+key
            print traceback.format_exc()
    print "down end"

def main():
    #if len(sys.argv)>1:
    #    if sys.argv[1]=="down":
    prefix=len(sys.argv)>1 and sys.argv[1] or ""
    down_all(prefix=prefix)

if __name__=="__main__":
    main()


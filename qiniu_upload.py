#!/usr/bin/env python
#-*- coding:utf-8 -*-

import qiniu
from qiniu import Auth, etag, CdnManager, BucketManager
import os
import re
from config import config


scriptdir = os.path.realpath(os.path.dirname(__file__))
urltext = os.path.join(scriptdir, "url.txt")

access_key = config.get("qiniu_key", "access_key")
secret_key = config.get("qiniu_key", "secret_key")
bucket_name = config.get("bucket", "bucket_name")
bucket_domain = config.get("domain", "bucket_domain")
basedir = config.get("data_path", "local_root")
charset = config.get("charset", "charset_name")


q = Auth(access_key, secret_key)
bucket = BucketManager(q)
cdn_manager = CdnManager(q)
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
        #print "error"
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

def get_valid_key_files(subdir=""):
    basedir=subdir or basedir
    files = get_files(basedir=basedir,ignore_paths=ignore_paths,ignore_names=ignore_names)
    return map(lambda f:(f.replace("\\","/"),f),files)


def sync():
    qn_keys=list_all(bucket_name,bucket)
    qn_set=set(qn_keys)
    l_key_files=get_valid_key_files(basedir)
    k2f={}
    update_keys=[]
    u_count=500
    u_index=0
    for k,f in l_key_files:
        k2f[k]=f
        str_k=k
        if isinstance(k,str):
            k=k.decode(charset)
        if k in qn_set:
            update_keys.append(str_k)
            u_index+=1
            if u_index > u_count:
                u_index-=u_count
                update_file(k2f,update_keys)
                update_keys=[]
        else:
            # upload
            upload_file(str_k,os.path.join(basedir,f))
    if update_keys:
        update_file(k2f,update_keys)
    print "sync end"

def update_file(k2f,ulist):
    ops=qiniu.build_batch_stat(bucket_name,ulist)
    rets,infos = bucket.batch(ops)
    for i in xrange(len(ulist)):
        k=ulist[i]
        f=k2f.get(k)
        ret=rets[i]["data"]
        remote_hash=ret.get("hash",None)
        local_f = os.path.join(basedir,f)
        local_hash=etag(local_f)
        if local_hash != remote_hash:
            print "update_file: %s" % f
            upload_file(k,os.path.join(basedir,f),flag=True)

def upload_file(key,localfile,flag=False):
    print "upload_file: %s" % key
    u_key = unicode(key, charset)
    u_localfile = unicode(localfile, charset)
    token = q.upload_token(bucket_name, key)
    #mime_type = get_mime_type(localfile)
    #params = {'x:a': 'a'}
    #progress_handler = lambda progress, total: progress
    #ret, info = qiniu.put_file(token, key, localfile, params, mime_type, progress_handler=progress_handler)
    ret, info = qiniu.put_file(token, u_key, u_localfile)
    print "upload result: ", ret
    if flag:
        print type(u_key)
        refresh(bucket_domain, u_key)
        with open(urltext, "a+") as ff:
            ff.write(os.path.join(bucket_domain, key))
    
    
def print_result(result):
    if result[0] is not None:
        print("refresh result: ", result[0])
    

def refresh(domain, key):
    urls = [os.path.join(domain, key)]
    refresh_url_result = cdn_manager.refresh_urls(urls)
    print_result(refresh_url_result)

    

def get_mime_type(path):
    mime_type = "text/plain"
    return mime_type

def main():
    ff = open(urltext, "w")
    ff.close()
    sync()

if __name__=="__main__":
    main()

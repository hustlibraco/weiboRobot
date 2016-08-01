#coding=utf-8
#!/usr/bin/env python
import codecs
import sys
UTF8Writer = codecs.getwriter('utf8')
sys.stdout = UTF8Writer(sys.stdout)

import time
import requests
requests.packages.urllib3.disable_warnings()

import threading
import pymongo
import ConfigParser
conf = ConfigParser.ConfigParser()
conf.read('config.ini')

from flask import Flask, render_template
from weibo import Client

app = Flask(__name__)

def _datetime(x=None):
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(x))

mongo = pymongo.MongoClient(conf.get('mongo', 'host'), int(conf.get('mongo', 'port')))

class MyClient(Client):
    def __init__(self, api_key, api_secret, redirect_uri, token=None,
                 username=None, password=None):
        super(MyClient, self).__init__(api_key, api_secret, redirect_uri, token, username, password)
        self.weibos = mongo.sinaweibo.weibos
    
    def run(self):
        '''定时抓取'''
        while 1:
            try:
                comments = self.get('comments/mentions')['comments']
            except Exception, e:
                print e
                break
            for comment in comments:
                # if comment['user']['name'] != WHOCANAT:
                #     # 忽略陌生人的@
                #     continue
                status = comment['status']
                origin = status['retweeted_status'] if 'retweeted_status' in status else status
                if self.weibos.find_one({'id':origin['id']}):
                    # 忽略重复的@
                    continue
                print u'new weibo: {0}, time: {1}, @ by {2}'.format(
                    origin['id'], _datetime(), comment['user']['name'])
                w = {
                    'id': origin['id'],
                    'text': origin['text'], 
                    'author': origin['user']['name'], 
                    'addtime':self._format(status['created_at']), 
                    'at_time': self._format(comment['created_at']), 
                    'at_by': comment['user']['name']
                }
                if origin.get('pic_urls'):
                	w['pics'] = [i['thumbnail_pic'] for i in origin['pic_urls']]
                self.weibos.insert_one(w)
            time.sleep(3600)
    
    def _format(self, t):
        return time.mktime(time.strptime(t, '%a %b %d %H:%M:%S +0800 %Y'))

@app.route('/')
def index():
    weibos = mongo.sinaweibo.weibos.find().sort('at_time', pymongo.DESCENDING)
    return render_template('weibo.html', weibos=weibos)

@app.context_processor
def utility_processor():
    _globals = {
        'datetime': _datetime
    }
    return _globals

if __name__ == '__main__':
    api_key = conf.get('weibo', 'api_key')
    api_secret = conf.get('weibo', 'api_secret')
    redirect_uri = conf.get('weibo', 'redirect_uri')
    username = conf.get('weibo', 'username')
    password = conf.get('weibo', 'password')
    c = MyClient(api_key, api_secret, redirect_uri, username=username, password=password)
    t = threading.Thread(target=c.run, args=())
    t.setDaemon(True)
    t.start()
    app.run()

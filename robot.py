#coding=utf-8
#!/usr/bin/env python
import time
import requests
import threading
from flask import Flask, render_template
from weibo import Client
from config import *

requests.packages.urllib3.disable_warnings()
app = Flask(__name__)

WEIBOS = []

class MyClient(Client):
    def __init__(self, api_key, api_secret, redirect_uri, token=None,
                 username=None, password=None):
        super(MyClient, self).__init__(api_key, api_secret, redirect_uri, token, username, password)
        self.weibos = set()
    
    def run(self, target):
        '''定时抓取'''
        while 1:
            comments = self.get('comments/mentions')['comments']
            for comment in comments:
                # if comment['user']['name'] != WHOCANAT:
                #     # 忽略陌生人的@
                #     continue
                status = comment['status']
                origin = status['retweeted_status'] if 'retweeted_status' in status else status
                if origin['id'] in self.weibos:
                    # 忽略重复的@
                    continue
                self.weibos.add(origin['id'])
                w = {'text': origin['text'], 'author': origin['user']['name'], 'addtime': self._format(comment['created_at'])}
                if len(target) > 0 and w['addtime'] > target[0]['addtime']:
                    target.insert(0, w)
                else:
                    target.append(w)
            time.sleep(60)
    
    def _format(self, t):
        return time.mktime(time.strptime(t, '%a %b %d %H:%M:%S +0800 %Y'))

@app.route('/')
def index():
    return render_template('weibo.html', weibos=WEIBOS)

@app.context_processor
def utility_processor():
    _globals = {
        'datetime': lambda x: time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(x))
    }
    return _globals

if __name__ == '__main__':
    c = MyClient(API_KEY, API_SECRET, REDIRECT_URI, username=USERNAME, password=PASSWORD)
    t = threading.Thread(target=c.run, args=(WEIBOS,))
    t.setDaemon(True)
    t.start()
    app.run()

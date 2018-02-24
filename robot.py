# coding=utf-8
# !/usr/bin/env python
import os
import logging
import time
import threading
import ConfigParser
import pymongo
import requests
from flask import Flask, render_template

import base62
from weibo import Client

requests.packages.urllib3.disable_warnings()
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(name)s:%(lineno)d:%(levelname)s: %(message)s")
conf = ConfigParser.ConfigParser()
conf.read(os.path.abspath(os.path.dirname(__file__)) + '/config.ini')

app = Flask(__name__)
N = 10**7  # ~ 64 ** 4


def _datetime(x=None):
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(x))


def weibo_url(uid, mid):
    s = ''
    while mid:
        s = base62.encode(mid % N) + s
        mid /= N
    return u'http://weibo.com/{0}/{1}'.format(uid, s)


mongo = pymongo.MongoClient(
    conf.get('mongo', 'host'), int(conf.get('mongo', 'port')))


class MyClient(Client):
    def __init__(self,
                 api_key,
                 api_secret,
                 redirect_uri,
                 token=None,
                 username=None,
                 password=None):
        super(MyClient, self).__init__(api_key, api_secret, redirect_uri,
                                       token, username, password)
        self.weibos = mongo.sinaweibo.weibos
        self._picurl = 'http://ww1.sinaimg.cn/thumbnail/{0}.jpg'

    def run(self):
        '''定时抓取'''
        times = 1
        while 1:
            try:
                comments = self.get('comments/mentions')['comments']
            except Exception, e:
                logging.error(e, exc_info=True)
            else:
                logging.info('scrapy %s times.' % times)
                times += 1
                for comment in comments:
                    # if comment['user']['name'] != WHOCANAT:
                    #     # 忽略陌生人的@
                    #     continue
                    status = comment['status']
                    origin = status[
                        'retweeted_status'] if 'retweeted_status' in status else status

                    if origin.get('deleted') == '1':
                        # 微博被删除
                        continue
                    if self.weibos.find_one({'id': origin['id']}):
                        # 微博已保存
                        continue
                    logging.info(u'new weibo: {0}, time: {1}, @ by {2}'.format(
                        origin['id'], _datetime(), comment['user']['name']))
                    w = {
                        'id': origin['id'],
                        'text': origin['text'],
                        'author': origin['user']['name'],
                        'addtime': self._format(status['created_at']),
                        'at_time': self._format(comment['created_at']),
                        'at_by': comment['user']['name'],
                        'url': weibo_url(origin['user']['id'],
                                         int(origin['mid'])),
                    }
                    if origin.get('pic_ids'):
                        w['pics'] = [
                            self._picurl.format(i) for i in origin['pic_ids']
                        ]
                    self.weibos.insert_one(w)
            time.sleep(3600)

    def _format(self, t):
        return time.mktime(time.strptime(t, '%a %b %d %H:%M:%S +0800 %Y'))


@app.route('/')
def index():
    # 客户端跳转
    # return redirect(url_for('show', page=1))

    # 相当于服务器内部跳转
    return show(1)


@app.route('/page/<page>')
def show(page):
    pagenum = 20
    page = int(page)
    weibo_count = mongo.sinaweibo.weibos.count()
    skip = (page - 1) * pagenum
    np = page + 1 if (page * pagenum < weibo_count) else False
    lp = page - 1 if (page - 1 > 0) else False
    weibos = mongo.sinaweibo.weibos.find().sort(
        'at_time', pymongo.DESCENDING).skip(skip).limit(pagenum)
    return render_template('weibo.html', weibos=weibos, next=np, last=lp)


@app.context_processor
def utility_processor():
    _globals = {'datetime': _datetime}
    return _globals


if __name__ == '__main__':
    api_key = conf.get('weibo', 'api_key')
    api_secret = conf.get('weibo', 'api_secret')
    redirect_uri = conf.get('weibo', 'redirect_uri')
    username = conf.get('weibo', 'username')
    password = conf.get('weibo', 'password')
    c = MyClient(
        api_key,
        api_secret,
        redirect_uri,
        username=username,
        password=password)
    t = threading.Thread(target=c.run, args=())
    t.setDaemon(True)
    t.start()
    app.run()

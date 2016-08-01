# weiboRobot
一个自动保存微博并展示的小工具

## 安装依赖

1. 安装mongodb
2. 安装python模块，`pip install request, flask, pymongo` 
3. 在`weiboRobot`目录下新建配置文件`config.ini`, 内容如下
```ini
[weibo]
api_key = your_api_key
api_secret = your_api_secret
redirect_uri = your_redirect_uri
username = username
password = username
whocanat = whocanat  

[mongo]
host = 127.0.0.1
port = 27017
```

api_key和api_secret需要去[微博开放平台](http://open.weibo.com/)申请。

## 运行
```
python robot.py
```

## 使用方法

在你想保存的微博的评论中@配置文件中的用户名即可。最慢一个小时生效。

因为应用未审核，所以接口调用频率有限制，一个小时调用一次是目前比较理想的频率。

## 鸣谢

[比官方更好更好用的Python版新浪微博SDK](https://github.com/lxyu/weibo)

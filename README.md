TVee
----

抓取 http://www.yayaxz.com 上的资源，定时抓取并发送到 Aria2 RPC，或者生成RSS

安装
====

* 安装 python
* 安装依赖 `pip install -r tvee/requirements.txt && pip install supervisor`
* 安装前端依赖 `cd tvee && bower install`
* 启动 `supervisord -c production/supervisord.conf`
* http://localhost:8000

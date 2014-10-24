TVee
----

定时抓取下载链接并发送到 Aria2 RPC，或者生成RSS，目前只支持 http://www.yayaxz.com 上的资源，适合部署到 NAS 上自动下载剧集

安装
====

* 安装 python
* 安装依赖 `pip install -r tvee/requirements.txt && pip install supervisor`
* 安装前端依赖 `cd tvee && bower install` 该步骤依赖比较复杂，你可以在本地安装好以后再服务到 NAS
* 配置 `cp config.sample.conf config.conf && vi config.conf`
* 初始化 `python -m tvee init`
* 启动 `supervisord -c production/supervisord.conf`
* http://localhost:8000
* 点击 设置 设定 迅雷用户名和密码、Aria2 RPC Path 和 下载目录

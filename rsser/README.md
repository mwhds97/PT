# 使用手册

### 简介

这个小东西是配合 [Deluge](https://github.com/deluge-torrent/deluge)（1.3.x 以上版本）或 [qBittorrent](https://github.com/qbittorrent/qBittorrent) （4.1.x 以上版本）玩一些 PT 站用的

目前支持的站点：

- [x] CHDBits
- [x] HDSky
- [x] M-Team（建议关闭 2FA）
- [x] OpenCD
- [x] OurBits（Cookies 有效期一个月）
- [x] SSD
- [x] TTG
- [x] U2

---

### 依赖

```text
python >= 3.7.0
beautifulsoup4 >= 4.9.0
feedparser >= 6.0.0
lxml >= 4.6.0
PyYAML >= 5.4.0
requests >= 2.25.0
```

依赖库可用以下命令安装：

`pip3 install -r requirements.txt`

---

### 配置

`config.yaml` [配置示例](https://github.com/mwhds97/PT/blob/master/rsser/config.yaml)

```yaml
torrent_pool_size: 1000
#保留信息的种子数量
#若纳入过计划的种子总数超过该值，最早的种子信息将被删除
#找不到种子信息的任务无法被处理
sort_by: #种子信息排序的关键字，可用以下六种，值表示升序或降序排序
  size: true #按体积降序排序
  publish_time: true #按发布时间降序排序
  seeder: false #按做种人数升序排序
  leecher: true #按下载人数降序排序
  snatch: false #按完成人数升序排序
  site: false #按站点的优先级（priority）升序排序
#顺序决定优先级
#若无需排序请设置为 {}
snippets: {}
#可复用的配置片段，用法参见配置示例
#若无需使用该功能请设置为 {}
clients: #客户端列表（字典）
  客户端1:
    snippets: []
    #引用的配置片段列表，顺序决定优先级
    #若无需引用请设置为 []
    type: deluge #客户端的类型
    host: '...'
    #Deluge daemon 地址
    #必须包含端口，不可含有协议头
    user: '...' #Deluge daemon 用户名
    pass: '...' #Deluge daemon 密码
    timeout: 15 #与客户端通信超时的阈值（单位：秒）
    reconnect_interval: 10 #重新连接客户端的时间间隔（单位：秒）
    run_interval: 30 #执行任务处理（包括添加、移除种子）流程的时间间隔（单位：秒）
    space: 1024 #总空间大小（单位：GB），任务的总体积不会超过该值
    task_count_max: 10
    #同时进行的最大任务数量
    #所有状态的任务都会被计入
  客户端2:
    snippets: []
    #引用的配置片段列表，顺序决定优先级
    #若无需引用请设置为 []
    type: qbittorrent
    #客户端的类型
    #若要使用 qBittorrent，请在 Web UI 设置中取消勾选“启用跨站请求伪造（CSRF）保护”
    host: 'http://...'
    #qBittorrent Web UI 地址
    #必须包含端口和协议头
    user: '...' #qBittorrent Web UI 用户名
    pass: '...' #qBittorrent Web UI 密码
    headers: {}
    #用于访问 qBittorrent Web UI 的 request headers
    #如果 Web UI 设置中的“启用 Host header 属性验证”被勾选，且 Web UI 的本地监听端口和远程访问端口不一致（常见于 NAT 环境）
    #，该值必须包含 'Host': '设定域名（若为 * 可取任意值）:本地监听端口（Web UI）'
    timeout: 15 #与客户端通信超时的阈值（单位：秒）
    reconnect_interval: 10 #重新连接客户端的时间间隔（单位：秒）
    run_interval: 30 #执行任务处理（包括添加、移除种子）流程的时间间隔（单位：秒）
    space: 1024 #总空间大小（单位：GB），任务的总体积不会超过该值
    task_count_max: 10
    #同时进行的最大任务数量
    #所有状态的任务都会被计入
  ...
sites: #站点列表（字典）
  站点1: #必须和 sites 目录下的 py 文件名一致
    snippets: []
    #引用的配置片段列表，顺序决定优先级
    #若无需引用请设置为 []
    rss: '...'
    #站点的 RSS 地址，要求包含体积信息
    #多数站点传入 isize=1 即可
    rss_timeout: 15 #获取站点 RSS 信息的超时阈值（单位：秒）
    web: #站点的种子页面地址列表
    - '...'
    #建议每个页面都按发布时间降序排列种子
    #多数站点传入 sort=4&type=desc 即可
    web_timeout: 15 #获取站点种子页面信息的超时阈值（单位：秒）
    cookies: {} #用于访问站点的 cookies
    user_agent: '...' #用于访问站点的 user-agent
    proxies: {} #代理设置，例如 {'http': 'http://127.0.0.1:7890', 'https': 'http://127.0.0.1:7890'}
    fetch_interval: 300 #获取种子信息的时间间隔（单位：秒）
    retry_interval: 30 #获取种子信息失败时重试的时间间隔（单位：秒）
    priority: 1
    #用于种子信息排序的站点优先级
    #该值越小，站点优先级越高
    timezone: +8 #站点的时区，一般设置为 +8 即可
  ...
projects: #任务计划列表（字典）
  计划1:
    snippets: []
    #引用的配置片段列表，顺序决定优先级
    #若无需引用请设置为 []
    client: 客户端1 #执行任务的客户端
    path: '...' #任务的下载路径，不需要转义
    sites: #用于种子筛选，不属于以下任一站点的种子不会被纳入计划
    - 站点1
    regexp: #用于种子筛选，标题不匹配以下任一正则表达式的种子不会被纳入计划
    - '.*'
    size: #用于种子筛选，体积不在以下任一范围（单位：GB）内的种子不会被纳入计划
    - [0, 100]
    publish_within: 660
    #发布时间在该值（单位：秒）之前的种子不会被添加至客户端
    #考虑到程序延迟，建议略大于期望值
    seeder: [0, 5] #做种人数不在该范围内的种子不会被添加至客户端
    leecher: [0, 5000] #下载人数不在该范围内的种子不会被添加至客户端
    snatch: [0, 5] #完成人数不在该范围内的种子不会被添加至客户端
    free_only: true #若该值为 true，非免费的种子不会被添加至客户端
    free_time_min: 21000
    #若 free_only 的值为 true，免费时长小于该值（单位：秒）的种子不会被添加至客户端
    #考虑到程序延迟，建议略小于期望值
    free_end_escape: true
    #若该值为 true，下载中的免费到期的种子将被移除
    #是否规避 H&R 将由 ignore_hr_leeching 的值决定
    escape_trigger_time: 60
    #若 free_end_escape 的值为 true，检测到种子的免费剩余时长小于该值（单位：秒）时触发移除操作
    #该值应不小于对应客户端 run_interval 的值
    hr_time_max: 432000 #H&R 要求做种时间超过该值（单位：秒）的种子不会被添加至客户端
    hr_seed_delay: 1800 #满足 H&R 要求后继续做种的时间（单位：秒），防止因未及时汇报等问题触发 H&R
    hr_seed_ratio: null #若站点的 H&R 规则允许达到一定分享率后停止做种，可将该值设定为对应分享率
    ignore_hr_seeding: false #若该值为 true，做种中的种子的 H&R 要求将被忽略
    ignore_hr_leeching: true #若该值为 true，下载中的种子的 H&R 要求将被忽略
    retry_count_max: 2 #添加任务失败时重试的最大次数
    extra_options: {}
    #任务的其他设置（例如限速、分类等），参见 Deluge 源代码和 qBittorrent API 文档
    #若使用 qBittorrent，请用 'true' 'false' 替代布尔值
    remove_conditions: #满足以下任一条件的种子将被移除
    - info: '活动时长超过限制'
      exp: 'active_time >= 259200'
      period: B
    - info: '做种时长达到要求'
      exp: 'seeding_time >= size / 1073741824 * 1.0 * 60'
      period: S
    - info: '做种和下载人数未达要求'
      exp: 'seeder > 10 and leecher < 20'
      period: S
    #可用字段：size active_time seeding_time seeder leecher progress ratio uploaded downloaded upload_speed download_speed eta
    #时间单位：秒，体积单位：B，速率单位：B/s，进度范围：0-1（qBittorrent）或 0-100（Deluge）
    #period 为条件的适用阶段，L 表示下载阶段，S 表示做种阶段，B 表示所有阶段
    #若无需删种请设置为 []
  ...
```

---

### 使用

直接运行 `rsser.py` 即可

按 `Ctrl + C` 结束

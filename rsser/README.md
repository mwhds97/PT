# 使用手册

### 简介

这个小东西是配合 [Deluge](https://github.com/deluge-torrent/deluge) [qBittorrent](https://github.com/qbittorrent/qBittorrent) 玩一些 PT 站用的

---

### 依赖

python >= 3.7

依赖库可用以下命令安装：

`pip3 install -r requirements.txt`

---

### 配置

`config.yaml`

```yaml
client: 'deluge' #客户端类型，可设定为 'deluge' 或 'qbittorrent'
#若要使用 qBittorrent，请在 Web UI 设置中取消勾选“启用跨站请求伪造（CSRF）保护”
host: '127.0.0.1:58846' #Deluge daemon 或者 qBittorrent Web UI 地址
#qBittorrent Web UI 地址必须包含协议头，Deluge daemon 地址不可含有协议头
user: 'localclient' #Deluge daemon 或者 qBittorrent Web UI 用户名
pass: 'deluge' #Deluge daemon 或者 qBittorrent Web UI 密码
headers: {} #用于访问 qBittorrent Web UI 的 request headers
#如果 Web UI 设置中的“启用 Host header 属性验证”被勾选，则该值必须包含 'Host': '设定域名（若为 * 则可取任意值）:本地监听端口（Web UI）'
timeout: 15 #连接客户端超时的阈值（单位：秒）
reconnect_interval: 10 #重新连接客户端的时间间隔（单位：秒）
space: 1024 #总空间大小（单位：GB），任务的总体积不会超过该值
task_count_max: 10 #同时进行的最大任务数量（所有状态的任务都会被计入）
run_interval: 30 #任务操作（包括添加、移除种子等）的时间间隔（单位：秒）
torrent_pool_size: 1000 #保留信息的种子数量，若获取过的种子总数超过该值，最早获取的种子信息将被删除（找不到种子信息的任务将无法操作）
order_by_site: false #若该值为 true，种子信息将按下方 sites 设定的站点顺序排列
sites: #指定要执行任务的站点，不执行的站点不要出现在这里
- '站点1'
- '站点2'
- '站点n'
站点1:
  rss: 'https://站点1.com/torrentrss.php?rows=50&isize=1&linktype=dl&passkey=' #站点的 RSS 地址，要求包含大小信息，即 isize=1
  rss_timeout: 15 #获取站点 RSS 信息的超时阈值（单位：秒）
  web: 'https://u2.dmhy.org/torrents.php?sort=4&type=desc' #站点的种子页面地址，建议按发布时间降序排列
  web_timeout: 15 #获取站点种子页面信息的超时阈值（单位：秒）
  cookies: {} #用于访问站点的 cookies
  user_agent: '' #用于访问站点的 user-agent
  proxies: {} #代理设置，例如 {'http': 'http://127.0.0.1:7890', 'https': 'http://127.0.0.1:7890'}
  fetch_interval: 300 #获取种子信息的时间间隔（单位：秒）
  retry_interval: 30 #获取种子失败时重试的时间间隔（单位：秒）
  retry_count_max: 2 #添加任务失败时重试的最大次数
  regexp: '(-|@)(站点1)' #用于根据标题筛选种子的正则表达式
  publish_within: 660 #发布时间在该值（单位：秒）之前的种子将被忽略（考虑到程序延迟，建议略大于期望值）
  free_only: true #若该值为 true，则非免费的种子将被忽略，下载中的免费到期的种子（包括带有 H&R 要求的）将被移除
  free_time_min: 21000 #仅当 free_only 的值为 true 时有效，免费时长小于该值（单位：秒）的种子将被忽略（考虑到程序延迟，建议略小于期望值）
  exclude_hr: false #若该值为 true，则带有 H&R 要求的种子将被忽略
  ignore_hr: false #若该值为 true，则种子的 H&R 要求将被忽略
  size: [10, 100] #体积超过该范围（单位：GB）的种子将被忽略
  path: '' #种子的保存路径，不需要转义
  extra_options: {} #任务的其他设置（例如限速、分类等），参见 Deluge 源代码和 qBittorrent API 文档
  #若使用 qBittorrent，请用 'true' 'false' 替代布尔值
  seed_by_size: true #若该值为 true，则做种时间将和种子体积成正比，否则做种时间将为固定值
  seed_time_size_ratio: 1.0 #仅当 seed_by_size 的值为 true 时有效，做种时间（单位：分）= 该值 * 种子体积（单位：GB）
  seed_time_fixed: 3600 #仅当 seed_by_size 的值为 false 时有效，做种时间（单位：秒）= 该值（单位：秒）
  seed_delay_hr: 1800 #满足 H&R 要求后继续做种的时间（单位：秒），防止因未及时汇报或服务器问题被站点记为 H&R
  seed_ratio_hr: null #若站点的 H&R 规则允许达到一定分享率后停止做种，则可将该值设定为对应分享率
  life: 259200 #活动时间超过该值的任务（无 H&R 要求）将被删除
站点2:
  ...
站点n:
  ...
```

---

### 使用

直接运行 `rsser.py` 即可

按 `Ctrl + C` 结束

# 使用手册

## 简介

这个东西是配合 [Deluge](https://github.com/deluge-torrent/deluge) 玩一些 PT 站用的

---

## 依赖

python >= 3.7.9

依赖库可用以下命令安装：

`pip3 install -r requirements.txt`

---

## 配置

`config.yaml`

```yaml
host: '127.0.0.1:58846' #Deluge daemon 地址，默认端口为 58846
user: 'localclient'
pass: 'deluge'
space: 1024 #总空间大小（单位：GB），任务的总体积不会超过该值
task_count_max: 10 #同时进行的最大任务数量（所有状态的任务都会被计入）
run_interval: 30 #任务操作（包括添加、移除种子等）的间隔（单位：秒）
torrent_pool_size: 1000 #保留信息的种子数量，若获取过的种子总数超过该值，最早获取的种子信息将被删除（找不到种子信息的任务将无法操作）
order_by_site: false #若该值为 true，种子信息将按下方 sites 设定的站点顺序排列
sites: #指定要执行任务的站点
- '站点1'
- '站点2'
- '站点n'
站点1:
  rss: 'https://站点1.com/torrentrss.php?rows=50&isize=1&linktype=dl&passkey=' #站点的 RSS 地址，要求包含大小信息，即 isize=1
  regexp: '(-|@)(CHD|OneHD)' #用于根据标题筛选种子的正则表达式
  cookies: {}
  user_agent: 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.135 Safari/537.36'
  proxies: {} #代理设置，例如 {'http': 'http://127.0.0.1:7890', 'https': 'http://127.0.0.1:7890'}
  fetch_interval: 300 #获取种子信息的间隔（单位：秒）
  retry_interval: 30 #获取种子失败时重试的间隔（单位：秒）
  publish_within: 660 #发布时间在该值（单位：秒）之前的种子将被忽略（考虑到程序延迟，建议略大于期望值）
  free_only: true #若该值为 true，则非免费的种子将被忽略，下载中的免费到期的种子（包括带有 H&R 要求的）将被移除
  free_time_min: 21000 #仅当 free_only 的值为 true 时有效，免费时长小于该值（单位：秒）的种子将被忽略（考虑到程序延迟，建议略小于期望值）
  exclude_hr: false #若该值为 true，则带有 H&R 要求的种子将被忽略
  ignore_hr: false #若该值为 true，则种子的 H&R 要求将被忽略
  size: [10, 100] #体积超过该范围（单位：GB）的种子将被忽略
  path: '' #种子的保存路径，不需要转义
  extra_options: {} #任务的其他设置（例如限速等），参见 Deluge 源代码
  seed_by_size: true #若该值为 true，则做种时间将和种子体积成正比，否则做种时间将为固定值
  seed_time_size_ratio: 1.0 #仅当 seed_by_size 的值为 true 时有效，做种时间（单位：分）= 该值 * 种子体积（单位：GB）
  seed_time_fixed: 3600 #仅当 seed_by_size 的值为 false 时有效，做种时间（单位：秒）= 该值（单位：秒）
  seed_delay_hr: 1800 #满足 H&R 要求后继续做种的时间（单位：秒），防止因未及时汇报或服务器问题被站点记为 H&R
  seed_ratio_hr: null #若站点的 H&R 规则允许达到一定分享率后停止做种，则可将该值设定为对应分享率
  life: 259200 #活动时间超过该值的任务（无 H&R 要求）将被删除
站点2:
  同上
站点n:
  同上
```

---

## 使用

直接运行 `main.py` 即可

按 `Ctrl + C` 退出

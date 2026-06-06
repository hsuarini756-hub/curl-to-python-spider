# Curl一键转防封控Python爬虫生成器
一个零配置、开箱即用的curl命令转Python爬虫工具，自动生成具备顶级防封控能力的生产级爬虫代码。

## ✨ 核心特性
- 🚀 **一键转换**：直接粘贴浏览器复制的curl命令，自动生成完整可运行的Python代码
- 🔒 **顶级防封**：优先使用curl_cffi实现TLS指纹随机（Chrome/Edge/Firefox指纹轮换），未安装依赖时自动降级原生requests
- 🛡️ **内置防封控套件**：
  - 随机User-Agent池
  - 区间随机延时(0.3~2.2s)
  - 失败自动重试3次
  - 代理IP一键配置
  - 会话池复用
  - 自动区分params/data/cookie参数
- 📁 **三文件极简架构**：无需复杂配置，上手即用

## 📦 快速开始
### 1. 安装依赖
```bash
pip install curl-cffi requests
# 国内源加速
pip install curl-cffi requests -i https://pypi.tuna.tsinghua.edu.cn/simple
2. 使用方法
打开curls.txt，在第 6 行往后粘贴你从浏览器复制的 curl 命令（一行一个）
运行curl_parse.py
生成的完整爬虫代码会自动写入result_spider.txt
复制result_spider.txt中的代码到任意 Python 文件中直接运行即可
Q: 出现 "curl_cffi not installed" 警告怎么办？
A: 这是正常现象，工具会自动降级使用原生 requests。如果需要 TLS 指纹防封能力，请执行上面的依赖安装命令。
Q: 如何配置代理？
A: 打开生成的result_spider.txt，找到PROXIES配置项，取消注释并填写你的代理地址即可。
Q: 支持哪些请求方式？
A: 支持 GET、POST、PUT、DELETE 等所有 HTTP 请求方式，自动解析 JSON、表单、URL 参数和 Cookie。
⚠️ 免责声明
本工具仅用于学习和研究目的，请勿用于任何非法用途。使用本工具产生的一切后果由使用者自行承担。

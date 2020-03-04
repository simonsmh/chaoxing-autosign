# 超星学习通自动签到
[![Require: Python 3.8](https://img.shields.io/badge/Python-3.8-blue)](https://www.python.org/)

## 使用方法
1. 安装依赖。
```shell
pip install -r requirements
```
2. 输入账号即可使用。
```shell
python main.py
```
除交互方式执行还外可指定参数，比如复制一份`sample.json`为`config.json`，需要在文件中修改为自己的学号和密码，支持以数组方式添加多账号。
```shell
python main.py config.json
```
1. 保持良好的网络连接，程序将默认每5分钟执行一次。

## License

[![License: GPL v3](https://img.shields.io/badge/License-GPL%20v3-blue)](https://www.gnu.org/licenses/gpl-3.0)

## Credit

Copyright © 2020 Simon Shi <simonsmh@gmail.com>

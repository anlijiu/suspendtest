#!/bin/bash

PYTHONPATH=src uv run python -m suspendtest validate-config --config config.ini


# 1) 先校验配置
# PYTHONPATH=src uv run python -m suspendtest validate-config --config config.ini
#
# 2) 跑 1 次休眠唤醒
# PYTHONPATH=src uv run python -m suspendtest run-once --config config.ini
#
# 3) 跑 N 次循环 〈例如 10000 次)
# PYTHONPATH=src uv run python -m suspendtest loop --config config.ini --cycles 10000
#
# 指定报告文件
# PYTHONPATH=src uv run python -m suspendtest loop --config config.ini --cycles 10 --report result_custom.md
#
# 覆盖超时 (秒)
# PYTHONPATH=src uv run python -m suspendtest loop --config config.ini --cycles 16 --sleep-timeout 66 --wake-timeout 60
#
# 如果你已经把项目作为脚本入口安装好了，也可以用短命令:
# uv run suspendtest validate-config --config config.ini
# uv run suspendtest run-once --config config.int
# uh run suspendtest loop --config config.ini --cycles 10000
# (当前默认就是 zLgcan 配置。)

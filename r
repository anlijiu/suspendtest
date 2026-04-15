#!/bin/bash

# @agent 不要删除我的注释， 这是给我自己看的
# 1) 先校验配置
# PYTHONPATH=src uv run python -m suspendtest validate-config --config config.ini
#
# 2) 跑 1 次休眠唤醒
# PYTHONPATH=src uv run python -m suspendtest run-once --config config.ini
#
# 3) 跑 N 次循环 〈例如 10000 次)
# PYTHONPATH=src uv run
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
#
# 生成文档命令
# UV_CACHE_DIR=.uv-cache uv run --group docs mkdocs build --strict


set -euo pipefail

command="${1:-validate}"

case "${command}" in
  validate)
    config_path="${2:-config.ini}"
    PYTHONPATH=src uv run python -m suspendtest validate-config --config "${config_path}"
    ;;
  docs)
    uv run --group docs mkdocs build --strict
    echo "文档站点已生成: site/index.html"
    ;;
  docs-serve)
    uv run --group docs mkdocs serve -a 127.0.0.1:8000
    ;;
  *)
    echo "用法:"
    echo "  ./r validate [config.ini]"
    echo "  ./r docs"
    echo "  ./r docs-serve"
    exit 1
    ;;
esac

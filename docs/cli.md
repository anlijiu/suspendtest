# CLI 使用说明

命令入口由 `src/cli/main.py` 提供，主命令为 `suspendtest`。

## 命令概览

```bash
suspendtest run-once [OPTIONS]
suspendtest loop --cycles <N> [OPTIONS]
suspendtest validate-config [OPTIONS]
```

## 通用参数（run-once / loop）

- `--config PATH`：配置文件路径，默认 `config.ini`
- `--sleep-method [can_uds]`：休眠方式
- `--wake-method [can_uds]`：唤醒方式
- `--disable-serial-detector`：禁用串口检测器
- `--disable-adb-detector`：禁用 ADB 检测器
- `--sleep-timeout FLOAT`：覆盖休眠超时（秒）
- `--wake-timeout FLOAT`：覆盖唤醒超时（秒）
- `--report PATH`：自定义报告输出路径

## run-once

执行一轮休眠/唤醒流程。

```bash
uv run suspendtest run-once --config config.ini
```

## loop

执行多轮循环流程。

```bash
uv run suspendtest loop --cycles 1000 --config config.ini
```

## validate-config

仅校验配置，不执行休眠/唤醒流程。

```bash
uv run suspendtest validate-config --config config.ini
```

## 错误输出行为

当出现 `SuspendTestError`（及其子类）时，CLI 会：

1. 输出 `错误: ...`
2. 若异常包含 `hint`，额外输出 `建议: ...`
3. 以 `click.Abort` 终止命令


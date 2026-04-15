# 快速开始

## 1. 安装依赖

在仓库根目录执行：

```bash
uv sync --all-extras --all-groups
```

## 2. 准备配置

默认读取根目录 `config.ini`。如果你使用自定义配置，可通过 `--config` 指定路径。

建议先校验配置：

```bash
uv run suspendtest validate-config --config config.ini
```

如果校验通过，会输出 `配置校验通过。` 以及关键配置摘要。

## 3. 运行一轮测试

```bash
uv run suspendtest run-once --config config.ini
```

成功后会输出报告路径，例如：

```text
测试完成，报告已生成: result_2026_04_15.md
```

## 4. 运行多轮循环测试

```bash
uv run suspendtest loop --cycles 100 --config config.ini
```

## 5. 常用覆盖参数

- `--sleep-timeout`：覆盖休眠检测超时（秒）
- `--wake-timeout`：覆盖唤醒检测超时（秒）
- `--disable-serial-detector`：禁用串口检测器
- `--disable-adb-detector`：禁用 ADB 检测器
- `--report`：指定报告输出路径

> 注意：串口和 ADB 检测器不能同时禁用，否则配置校验会失败。

## 6. 最小可用流程

1. 配好 `config.ini`
2. 执行 `validate-config`
3. 执行 `run-once` 验证链路
4. 执行 `loop --cycles N` 做稳定性测试

## 7. 一键生成可浏览文档站点

在仓库根目录执行：

```bash
./r docs
```

生成后可直接打开 `site/index.html` 浏览。

如果需要本地预览服务：

```bash
./r docs-serve
```

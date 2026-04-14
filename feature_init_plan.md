# feature_init_plan

## Summary

初始化 `suspendtest` MVP：提供可运行 CLI、`config.ini` 配置加载、基于 **zlgcan** 的 CAN UDS 休眠/唤醒命令发送、MCU 串口与 SOC ADB 双检测、循环执行与 Markdown 报告输出。

## Implementation Changes

- 建立 `src/suspendtest/core` 领域层：
  - 强类型配置/结果模型
  - 统一异常
  - 休眠/唤醒/检测器/报告接口
  - 配置解析校验服务
  - 单轮编排服务、循环服务、报告服务
- 实现 `can_uds` 休眠与唤醒方法（CAN 设备优先走 zlgcan），并保留后续多方法扩展点。
- 实现 `SerialMcuSleepDetector`（串口静默判定）与 `AdbSocSleepDetector`（ADB 连通判定）。
- 建立 `src/suspendtest/cli` 胶水层命令：
  - `run-once`
  - `loop --cycles N`
  - `validate-config`
- 默认报告命名：`result_YYYY_MM_DD.md`。

## Test Plan

- 配置加载与校验：默认配置、缺失字段、非法值。
- 单轮编排：命令成功路径、检测失败路径、命令失败路径。
- 报告输出：文件命名与关键字段覆盖。
- CLI：`validate-config`、`loop` 基础执行路径。

## Assumptions

- 一期仅实现 `can_uds` 方法，但接口已可扩展。
- 串口与 ADB 检测一期同时支持，默认都启用。
- 仅支持标准 CAN 单帧（8 字节以内）。

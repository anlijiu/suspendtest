# 架构与扩展点

## 目录分层

- `src/cli/`：CLI 胶水层，参数解析与错误处理
- `src/core/`：核心域逻辑（配置、接口、状态机、方法、检测器、服务）
- `src/core/services/`：单轮编排、循环执行、报告输出
- `src/core/methods/`：休眠/唤醒方法实现（当前为 CAN UDS）
- `src/core/detectors/`：状态检测器实现（串口 MCU、ADB SOC）

## 执行链路

```text
CLI(run-once/loop)
  -> ConfigService.load + validate
  -> _build_services()
      -> CanUdsCommandService
      -> CanUdsSleepMethod / CanUdsWakeMethod
      -> SerialMcuSleepDetector (optional)
      -> AdbSocSleepDetector (optional)
      -> SuspendTestService
      -> CycleRunnerService
      -> ReportService
  -> 输出 Markdown 报告
```

## 核心对象

- `SuspendCycleRequest`：循环请求（轮次、sleep/wake 超时）
- `CycleResult`：单轮结果（命令结果、检测结果、phase history、错误）
- `RunReport`：整次运行汇总
- `CycleStateMachine`：记录每轮阶段迁移轨迹

## 状态机阶段

`CyclePhase` 当前包含：

- `idle`
- `sending_sleep`
- `waiting_sleep`
- `sleeping`
- `sending_wake`
- `waiting_wake`
- `awake`
- `finished`
- `failed`

## 可扩展点

### 1) 新增休眠/唤醒方法

实现 `SleepMethod` / `WakeMethod` 接口，并在 CLI 的服务构建阶段注入新实现。

### 2) 新增状态检测器

实现 `StateDetector` 接口：

- `subsystem`
- `wait_for_sleep(timeout_seconds)`
- `wait_for_wake(timeout_seconds)`

将检测器对象加入 `SuspendTestService` 的 detectors 列表即可参与流程。

### 3) 新增报告格式

可新增 `ReportRenderer` 实现（当前 `ReportService` 负责 Markdown）。

## 设计取向

- 用 dataclass 建模，降低隐式字典传参
- 核心模块可注入依赖（串口工厂、subprocess runner、CAN bus 工厂），便于单元测试
- CLI 与核心解耦，后续可以在不破坏核心逻辑的前提下接入 GUI


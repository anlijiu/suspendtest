# suspendtest 文档

`suspendtest` 是一个面向车机场景的休眠/唤醒循环测试工具。

当前版本通过 **CAN UDS** 发送休眠/唤醒命令，并通过以下检测器判断状态变化：

- MCU：串口静默/恢复数据检测
- SOC：ADB 可达性检测

## 文档目录

- [快速开始](./quickstart.md)
- [CLI 使用说明](./cli.md)
- [配置文件说明（config.ini）](./configuration.md)
- [架构与扩展点](./architecture.md)
- [报告格式说明](./report.md)
- [API 参考](./api/index.md)

## 适用场景

- 单轮休眠/唤醒验证（`run-once`）
- 多轮稳定性与压力验证（`loop --cycles N`）
- 配置静态校验（`validate-config`）

## 当前实现边界

- 休眠方式：`can_uds`
- 唤醒方式：`can_uds`
- 报告格式：Markdown
- 报告默认文件名：`result_YYYY_MM_DD.md`


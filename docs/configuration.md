# 配置文件说明（config.ini）

配置由 `ConfigService` 从 INI 文件加载，并转换为强类型 `SuspendTestConfig`。

## 示例

```ini
[can]
interface = zlgcan
channel = 0
bitrate = 500000
device_type = ZCAN_USBCANFD_200U
device_index = 0
libpath = library/
resistance = true
physical_id = 0x773
response_id = 0x7B3
functional_id = 0x7DF

[sleep.can_uds]
request_id = 0x773
request_data = 10 01

[wake.can_uds]
request_id = 0x773
request_data = 11 01

[detect.serial]
enabled = true
port = /dev/ttyUSB0
baudrate = 115200
silence_seconds = 0.5
poll_interval_seconds = 0.05

[detect.adb]
enabled = true
adb_path = adb
device_serial =
poll_interval_seconds = 0.5
command_timeout_seconds = 3.0

[timeouts]
sleep_timeout_seconds = 30
wake_timeout_seconds = 30
```

## 各 section 字段

### [can]

| 字段 | 默认值 | 说明 |
| --- | --- | --- |
| interface | `zlgcan` | python-can 接口名 |
| channel | `0` | 通道号 |
| bitrate | `500000` | 波特率 |
| device_type | `ZCAN_USBCANFD_200U` | zlgcan 设备类型枚举名 |
| device_index | `0` | 设备索引 |
| libpath | `library/` | zlgcan 动态库目录 |
| resistance | `true` | 终端电阻（zlgcan） |
| physical_id | `0x773` | 物理请求 ID |
| response_id | `0x7B3` | 响应 ID |
| functional_id | `0x7DF` | 功能请求 ID |

### [sleep.can_uds] / [wake.can_uds]

| 字段 | 默认值 | 说明 |
| --- | --- | --- |
| request_id | 默认继承 `can.physical_id` | 报文 ID |
| request_data | 无默认，必填 | 报文数据（空格或逗号分隔） |

### [detect.serial]

| 字段 | 默认值 | 说明 |
| --- | --- | --- |
| enabled | `true` | 是否启用串口检测 |
| port | `/dev/ttyUSB0` | 串口设备 |
| baudrate | `115200` | 波特率 |
| silence_seconds | `0.5` | 判定休眠所需静默时长 |
| poll_interval_seconds | `0.05` | 轮询间隔 |

### [detect.adb]

| 字段 | 默认值 | 说明 |
| --- | --- | --- |
| enabled | `true` | 是否启用 ADB 检测 |
| adb_path | `adb` | adb 可执行文件 |
| device_serial | 空 | 设备序列号（多设备场景建议配置） |
| poll_interval_seconds | `0.5` | 轮询间隔 |
| command_timeout_seconds | `3.0` | 单次 adb 命令超时 |

### [timeouts]

| 字段 | 默认值 | 说明 |
| --- | --- | --- |
| sleep_timeout_seconds | `30.0` | 休眠检测超时 |
| wake_timeout_seconds | `30.0` | 唤醒检测超时 |

## 校验规则（重要）

`ConfigService.validate()` 会执行如下约束：

1. `detect.serial.enabled` 与 `detect.adb.enabled` 不能同时为 `false`
2. CAN ID（sleep/wake request_id、physical_id、response_id、functional_id）必须在 `0x000 ~ 0x7FF`
3. `request_data` 不能为空，且长度不能超过 8 字节（当前仅支持标准 CAN 单帧）
4. `sleep_timeout_seconds` / `wake_timeout_seconds` 必须 > 0
5. `can.channel` 与 `can.device_index` 不能小于 0

## CLI 覆盖配置

`run-once` / `loop` 执行时可通过以下参数临时覆盖配置值：

- `--disable-serial-detector`
- `--disable-adb-detector`
- `--sleep-timeout`
- `--wake-timeout`

覆盖后仍会重新执行配置校验。


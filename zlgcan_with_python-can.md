## zlgcan + python-can 示例

```python
import can
import zlgcan

with can.Bus(
    interface="zlgcan",
    channel=0,
    device_type=zlgcan.ZCANDeviceType.ZCAN_USBCANFD_200U,
    device_index=0,
    libpath="library/",
    # 单通道示例：配置 1 个通道即可
    configs=[{"bitrate": 500000, "resistance": 1}],
) as bus:
    bus.send(
        can.Message(
            arbitration_id=0x123,
            is_extended_id=False,
            channel=0,
            data=[0x01, 0x02, 0x03],
            dlc=3,
        ),
        tx_mode=zlgcan.ZCanTxMode.SELF_SR,
    )

    msg = bus.recv()
    print(msg)
```

> 多通道时，将 `configs` 扩展为多个配置项，并在发送 `Message` 时设置对应 `channel`。

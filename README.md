# 校园 MAC 地址采集工具

Windows 工具会优先读取有默认网关的物理网卡 MAC 地址；筛选命令失败时，会自动降级显示全部物理网卡，再降级显示全部网卡，最后再尝试 `getmac`，避免结果为空。同时自动读取电脑品牌、型号和电脑名称。

界面支持复制 MAC、复制电脑名称、复制品牌、复制型号，以及一键复制全部信息，并可生成清晰的 TXT 文件。

## 生成 Windows EXE

macOS 上不能直接用 PyInstaller 生成 Windows EXE，需要在 Windows 环境构建。最方便的方式是将项目上传 GitHub，打开 Actions，运行 `Build Windows EXE` 工作流，下载 Artifact `MAC地址采集工具-windows`。

也可以在 Windows 电脑中双击 `build_windows.bat`。脚本会自动尝试 `py` 和 `python` 命令。

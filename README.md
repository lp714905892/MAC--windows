# 校园 MAC 地址采集工具

这是一个面向 Windows 的小工具。老师双击运行后，可以填写姓名和学校/部门，点击“生成 TXT 文件”，在保存对话框中确认位置（默认打开桌面），即可得到一份清晰的 MAC 地址记录。

## 直接在 Windows 构建 EXE

1. 安装 Python 3.9 或更高版本（安装时勾选“Add Python to PATH”）。如果电脑提示“没有该命令”，通常表示 Python 未安装或没有加入 PATH。
2. 将本目录复制到 Windows 电脑。
3. 双击 `build_windows.bat`，脚本会自动安装 PyInstaller 并构建。
4. 生成的文件位于 `dist\MAC地址采集工具.exe`，可复制给老师使用，无需安装 Python。

> 注意：PyInstaller 需要在目标系统上构建。macOS 上运行 PyInstaller 只能得到 macOS 程序，不能直接生成可在 Windows 打开的 `.exe`。如果你现在使用的是 Mac，请使用下面的 GitHub Actions，或在 Windows 虚拟机中执行 `build_windows.bat`。

构建脚本会自动尝试 `py` 和 `python` 两种命令，因此不要求必须存在 `py`。也可以在命令提示符中手动构建：

```bat
python -m pip install --upgrade pyinstaller
python -m PyInstaller --noconfirm --clean --onefile --windowed --name MAC地址采集工具 mac_collector.py
```

如果 `python` 也提示不是命令，请重新安装 Python，并勾选安装器中的 **Add python.exe to PATH**；安装后要重新打开命令提示符窗口。

## 在 Mac 上生成 Windows EXE（无需安装 Windows）

项目已附带 `.github/workflows/build-windows.yml`。将整个项目上传到 GitHub 后：

1. 打开仓库的 **Actions** 页面。
2. 选择 **Build Windows EXE**。
3. 点击 **Run workflow**。
4. 任务完成后下载名为 `MAC地址采集工具-windows` 的 Artifact，里面就是 Windows EXE。

如果不使用 GitHub，也可以在 Parallels、UTM 等 Windows 虚拟机中运行 `build_windows.bat`，效果相同。

## 使用说明

- 姓名和学校/部门为可选项；填写后方便后续汇总。
- 程序只读取存在 IPv4 或 IPv6 默认网关且标记为物理设备的网卡 MAC 地址，虚拟网卡会被排除。
- 程序会自动读取 Windows 电脑的品牌和型号，并显示在界面和 TXT 文件中。
- “复制 MAC”可将地址复制到剪贴板，便于临时粘贴到表格或聊天工具。
- 文件使用 UTF-8 with BOM 编码，可直接用 Windows 记事本或 Word 打开。

## 安全与隐私

程序只读取本机网络适配器地址和电脑名称，不联网、不上传数据。生成的文件由使用者自行保存和传递。

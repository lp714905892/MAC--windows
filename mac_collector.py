"""校园教师 MAC 地址采集工具。

双击运行后填写姓名（可选），点击按钮即可在桌面生成一份清晰的 TXT 文件。
程序只使用 Python 标准库，适合用 PyInstaller 打包为 Windows EXE。
"""

from __future__ import annotations

import datetime as _dt
import os
import re
import socket
import subprocess
import sys
import tkinter as tk
import uuid
from pathlib import Path
from tkinter import filedialog, messagebox, ttk


MAC_PATTERN = re.compile(r"(?i)(?:[0-9a-f]{2}[-:]){5}[0-9a-f]{2}")


def _normalise_mac(value: str) -> str:
    """统一输出为大写、短横线分隔的 MAC 地址。"""
    compact = re.sub(r"[^0-9a-fA-F]", "", value)
    if len(compact) != 12:
        return ""
    return "-".join(compact[i : i + 2] for i in range(0, 12, 2)).upper()


def _extract_macs(source: str) -> list[str]:
    addresses: list[str] = []
    for match in MAC_PATTERN.findall(source):
        mac = _normalise_mac(match)
        if mac and mac not in addresses and mac != "00-00-00-00-00-00":
            addresses.append(mac)
    return addresses


def get_mac_addresses() -> list[str]:
    """只读取存在默认网关的物理网卡 MAC 地址，排除虚拟网卡。"""
    addresses: list[str] = []

    # 通过默认网关筛选接口，再读取其 MAC，避免把虚拟网卡混入结果。
    if sys.platform.startswith("win"):
        try:
            completed = subprocess.run(
                [
                    "powershell.exe",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-Command",
                    (
                        "$configs = Get-NetIPConfiguration | "
                        "Where-Object { $_.IPv4DefaultGateway -ne $null -or $_.IPv6DefaultGateway -ne $null }; "
                        "foreach ($config in $configs) { "
                        "$adapter = Get-NetAdapter -Physical -InterfaceIndex $config.InterfaceIndex "
                        "-ErrorAction SilentlyContinue; "
                        "if ($adapter.MacAddress) { $adapter.MacAddress } }"
                    ),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="ignore",
                timeout=5,
                check=False,
            )
            addresses = _extract_macs(completed.stdout)
        except (OSError, subprocess.SubprocessError):
            pass

    # 非 Windows 环境仅用于开发测试，使用系统主网卡地址兜底。
    if not addresses and not sys.platform.startswith("win"):
        node = uuid.getnode()
        raw = f"{node:012x}"
        mac = _normalise_mac(raw)
        if mac and mac != "00-00-00-00-00-00":
            addresses.append(mac)

    return addresses


def get_device_info() -> tuple[str, str]:
    """读取 Windows 电脑品牌和型号；读取失败时返回明确的未知值。"""
    unknown = ("未知品牌", "未知型号")
    if not sys.platform.startswith("win"):
        return unknown

    try:
        completed = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                (
                    "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; "
                    "Get-CimInstance -ClassName Win32_ComputerSystem | "
                    "ForEach-Object { '{0}`t{1}' -f $_.Manufacturer, $_.Model }"
                ),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            timeout=5,
            check=False,
        )
        line = next((item.strip() for item in completed.stdout.splitlines() if item.strip()), "")
        if "\t" in line:
            manufacturer, model = (part.strip() for part in line.split("\t", 1))
            return manufacturer or unknown[0], model or unknown[1]
    except (OSError, subprocess.SubprocessError):
        pass
    return unknown


def _safe_filename_part(value: str, fallback: str) -> str:
    value = re.sub(r"[<>:\"/\\|?*\x00-\x1f]", "_", value.strip())
    return value or fallback


def desktop_path() -> Path:
    """返回 Windows 桌面目录；找不到时回退到用户目录。"""
    home = Path.home()
    for name in ("Desktop", "桌面"):
        candidate = home / name
        if candidate.exists():
            return candidate
    return home


class MacCollectorApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("校园 MAC 地址采集工具")
        self.root.minsize(560, 430)
        self.root.resizable(False, False)

        self.mac_addresses = get_mac_addresses()
        self.manufacturer, self.model = get_device_info()
        self.name_var = tk.StringVar()
        self.school_var = tk.StringVar()
        self.mac_var = tk.StringVar(value=self._mac_display())
        self.status_var = tk.StringVar(value="请确认信息后点击“生成 TXT 文件”。")

        self._build_ui()

    def _mac_display(self) -> str:
        if not self.mac_addresses:
            return "未读取到 MAC 地址"
        return "\n".join(self.mac_addresses)

    def _build_ui(self) -> None:
        outer = ttk.Frame(self.root, padding=24)
        outer.pack(fill="both", expand=True)

        ttk.Label(
            outer,
            text="校园 MAC 地址采集工具",
            font=("Microsoft YaHei UI", 18, "bold"),
        ).pack(anchor="w")
        ttk.Label(
            outer,
            text="每位老师运行一次，结果会保存为一份易读的 TXT 文件。",
            foreground="#555555",
        ).pack(anchor="w", pady=(5, 20))

        form = ttk.Frame(outer)
        form.pack(fill="x")
        form.columnconfigure(1, weight=1)

        ttk.Label(form, text="教师姓名（可选）：").grid(row=0, column=0, sticky="w", pady=7)
        name_entry = ttk.Entry(form, textvariable=self.name_var, width=42)
        name_entry.grid(row=0, column=1, sticky="ew", pady=7)

        ttk.Label(form, text="学校/部门（可选）：").grid(row=1, column=0, sticky="w", pady=7)
        ttk.Entry(form, textvariable=self.school_var, width=42).grid(
            row=1, column=1, sticky="ew", pady=7
        )

        ttk.Label(form, text="有网关的 MAC 地址：").grid(row=2, column=0, sticky="nw", pady=7)
        self.mac_box = tk.Text(
            form,
            width=40,
            height=max(2, min(5, len(self.mac_addresses) or 2)),
            state="normal",
            font=("Consolas", 11),
            relief="solid",
            borderwidth=1,
            padx=8,
            pady=7,
        )
        self.mac_box.insert("1.0", self.mac_var.get())
        self.mac_box.configure(state="disabled")
        self.mac_box.grid(row=2, column=1, sticky="ew", pady=7)

        ttk.Label(form, text="电脑名称：").grid(row=3, column=0, sticky="w", pady=7)
        ttk.Label(form, text=socket.gethostname()).grid(row=3, column=1, sticky="w", pady=7)

        ttk.Label(form, text="电脑品牌：").grid(row=4, column=0, sticky="w", pady=7)
        ttk.Label(form, text=self.manufacturer).grid(row=4, column=1, sticky="w", pady=7)

        ttk.Label(form, text="电脑型号：").grid(row=5, column=0, sticky="w", pady=7)
        ttk.Label(form, text=self.model).grid(row=5, column=1, sticky="w", pady=7)

        ttk.Separator(outer).pack(fill="x", pady=(20, 14))
        ttk.Label(outer, textvariable=self.status_var, foreground="#555555").pack(anchor="w")

        buttons = ttk.Frame(outer)
        buttons.pack(fill="x", pady=(18, 0))
        ttk.Button(buttons, text="重新检测", command=self.refresh).pack(side="left")
        ttk.Button(buttons, text="复制 MAC", command=self.copy_mac).pack(side="left", padx=(8, 0))
        ttk.Button(buttons, text="生成 TXT 文件", command=self.save_txt).pack(side="right")
        name_entry.focus_set()

    def refresh(self) -> None:
        self.mac_addresses = get_mac_addresses()
        self.mac_var.set(self._mac_display())
        self.status_var.set("已重新检测本机网络适配器。")
        self.mac_box.configure(state="normal")
        self.mac_box.delete("1.0", "end")
        self.mac_box.insert("1.0", self.mac_var.get())
        self.mac_box.configure(state="disabled")

    def copy_mac(self) -> None:
        if not self.mac_addresses:
            messagebox.showwarning("无法复制", "没有检测到可用的 MAC 地址。")
            return
        self.root.clipboard_clear()
        self.root.clipboard_append("\n".join(self.mac_addresses))
        self.status_var.set("MAC 地址已复制到剪贴板。")

    def save_txt(self) -> None:
        if not self.mac_addresses:
            messagebox.showerror(
                "无法生成文件",
                "没有检测到带默认网关的网卡，请先连接网络后重试。",
            )
            return

        now = _dt.datetime.now()
        teacher = _safe_filename_part(self.name_var.get(), "未填写姓名")
        filename = f"MAC采集_{teacher}_{now:%Y%m%d_%H%M%S}.txt"
        default_path = desktop_path() / filename
        path = filedialog.asksaveasfilename(
            title="保存 MAC 地址采集结果",
            initialdir=str(default_path.parent),
            initialfile=filename,
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")],
        )
        if not path:
            return

        lines = [
            "校园 MAC 地址采集结果",
            "=" * 28,
            f"教师姓名：{self.name_var.get().strip() or '未填写'}",
            f"学校/部门：{self.school_var.get().strip() or '未填写'}",
            f"电脑名称：{socket.gethostname()}",
            f"电脑品牌：{self.manufacturer}",
            f"电脑型号：{self.model}",
            f"采集时间：{now:%Y-%m-%d %H:%M:%S}",
            "",
            "MAC 地址：",
        ]
        lines.extend(f"  {index}. {mac}" for index, mac in enumerate(self.mac_addresses, 1))
        lines.extend(["", "说明：本文件由校园 MAC 地址采集工具生成。"])

        try:
            Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8-sig")
        except OSError as exc:
            messagebox.showerror("保存失败", f"无法写入文件：\n{exc}")
            return

        self.status_var.set(f"已生成：{Path(path).name}")
        if messagebox.askyesno("生成成功", f"文件已保存到：\n{path}\n\n是否立即打开？"):
            try:
                os.startfile(path)  # type: ignore[attr-defined]
            except (AttributeError, OSError):
                pass


def main() -> None:
    root = tk.Tk()
    try:
        ttk.Style(root).theme_use("vista")
    except tk.TclError:
        pass
    MacCollectorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

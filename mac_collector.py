"""校园教师 MAC 地址采集工具。"""

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
    compact = re.sub(r"[^0-9a-fA-F]", "", value)
    if len(compact) != 12:
        return ""
    return "-".join(compact[i : i + 2] for i in range(0, 12, 2)).upper()


def _extract_macs(source: str) -> list[str]:
    result: list[str] = []
    for match in MAC_PATTERN.findall(source):
        mac = _normalise_mac(match)
        if mac and mac not in result and mac != "00-00-00-00-00-00":
            result.append(mac)
    return result


def _powershell(command: str) -> str:
    completed = subprocess.run(
        ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore",
        timeout=8,
        check=False,
    )
    return completed.stdout


def get_mac_addresses() -> list[str]:
    """优先返回有默认网关的物理网卡；筛选失败时逐级降级，保证尽量有结果。"""
    if sys.platform.startswith("win"):
        commands = [
            # 首选：有 IPv4/IPv6 默认网关，并且是物理网卡。
            (
                "$c=Get-NetIPConfiguration | Where-Object { $_.IPv4DefaultGateway -ne $null -or $_.IPv6DefaultGateway -ne $null }; "
                "foreach($x in $c){ Get-NetAdapter -Physical -InterfaceIndex $x.InterfaceIndex -ErrorAction SilentlyContinue | Select-Object -ExpandProperty MacAddress }"
            ),
            # 某些旧版 Windows 的 Get-NetIPConfiguration 不可用时，至少显示全部物理网卡。
            "Get-NetAdapter -Physical -ErrorAction SilentlyContinue | Select-Object -ExpandProperty MacAddress",
            # 如果物理网卡标记异常，继续显示全部适配器，避免结果为空。
            "Get-NetAdapter -ErrorAction SilentlyContinue | Select-Object -ExpandProperty MacAddress",
            # 最后使用 Windows 自带 getmac，兼容精简系统或 PowerShell 组件异常。
            "getmac.exe /fo csv /nh",
        ]
        for command in commands:
            try:
                addresses = _extract_macs(_powershell(command))
                if addresses:
                    return addresses
            except (OSError, subprocess.SubprocessError):
                continue
        try:
            completed = subprocess.run(
                ["getmac.exe", "/fo", "csv", "/nh"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="ignore",
                timeout=8,
                check=False,
            )
            addresses = _extract_macs(f"{completed.stdout}\n{completed.stderr}")
            if addresses:
                return addresses
        except (OSError, subprocess.SubprocessError):
            pass
        return []

    # 非 Windows 环境仅用于开发测试。
    mac = _normalise_mac(f"{uuid.getnode():012x}")
    return [mac] if mac and mac != "00-00-00-00-00-00" else []


def get_device_info() -> tuple[str, str]:
    """读取 Windows 电脑品牌和型号；读取失败时返回未知值。"""
    unknown = ("未知品牌", "未知型号")
    if not sys.platform.startswith("win"):
        return unknown
    try:
        output = _powershell(
            "[Console]::OutputEncoding=[System.Text.Encoding]::UTF8; "
            "Get-CimInstance Win32_ComputerSystem | ForEach-Object { Write-Output $_.Manufacturer; Write-Output $_.Model }"
        )
        values = [line.strip() for line in output.splitlines() if line.strip()]
        if len(values) >= 2:
            return values[0] or unknown[0], values[1] or unknown[1]
    except (OSError, subprocess.SubprocessError):
        pass
    return unknown


def desktop_path() -> Path:
    home = Path.home()
    for name in ("Desktop", "桌面"):
        if (home / name).exists():
            return home / name
    return home


def _safe_filename_part(value: str, fallback: str) -> str:
    value = re.sub(r"[<>:\"/\\|?*\x00-\x1f]", "_", value.strip())
    return value or fallback


class MacCollectorApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("校园 MAC 地址采集工具")
        self.root.resizable(False, False)
        self.mac_addresses = get_mac_addresses()
        self.manufacturer, self.model = get_device_info()
        self.name_var = tk.StringVar()
        self.school_var = tk.StringVar()
        self.status_var = tk.StringVar(value="请确认信息后点击“生成 TXT 文件”。")
        self._build_ui()

    def _mac_display(self) -> str:
        return "\n".join(self.mac_addresses) if self.mac_addresses else "未读取到 MAC 地址"

    def _build_ui(self) -> None:
        outer = ttk.Frame(self.root, padding=24)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text="校园 MAC 地址采集工具", font=("Microsoft YaHei UI", 18, "bold")).pack(anchor="w")
        ttk.Label(outer, text="优先显示有网关的物理网卡；筛选失败时自动显示全部物理网卡。", foreground="#555555").pack(anchor="w", pady=(5, 18))

        form = ttk.Frame(outer)
        form.pack(fill="x")
        form.columnconfigure(1, weight=1)
        ttk.Label(form, text="教师姓名（可选）：").grid(row=0, column=0, sticky="w", pady=6)
        name_entry = ttk.Entry(form, textvariable=self.name_var, width=42)
        name_entry.grid(row=0, column=1, sticky="ew", pady=6)
        ttk.Label(form, text="学校/部门（可选）：").grid(row=1, column=0, sticky="w", pady=6)
        ttk.Entry(form, textvariable=self.school_var, width=42).grid(row=1, column=1, sticky="ew", pady=6)
        ttk.Label(form, text="MAC 地址：").grid(row=2, column=0, sticky="nw", pady=6)
        self.mac_box = tk.Text(form, width=40, height=max(2, min(5, len(self.mac_addresses) or 2)), state="disabled", font=("Consolas", 11), relief="solid", borderwidth=1, padx=8, pady=7)
        self._update_mac_box()
        self.mac_box.grid(row=2, column=1, sticky="ew", pady=6)
        ttk.Label(form, text="电脑名称：").grid(row=3, column=0, sticky="w", pady=6)
        ttk.Label(form, text=socket.gethostname()).grid(row=3, column=1, sticky="w", pady=6)
        ttk.Label(form, text="电脑品牌：").grid(row=4, column=0, sticky="w", pady=6)
        ttk.Label(form, text=self.manufacturer).grid(row=4, column=1, sticky="w", pady=6)
        ttk.Label(form, text="电脑型号：").grid(row=5, column=0, sticky="w", pady=6)
        ttk.Label(form, text=self.model).grid(row=5, column=1, sticky="w", pady=6)

        ttk.Separator(outer).pack(fill="x", pady=(16, 12))
        ttk.Label(outer, textvariable=self.status_var, foreground="#555555").pack(anchor="w")
        buttons = ttk.Frame(outer)
        buttons.pack(fill="x", pady=(16, 0))
        ttk.Button(buttons, text="重新检测", command=self.refresh).pack(side="left")
        ttk.Button(buttons, text="复制 MAC", command=self.copy_mac).pack(side="left", padx=(8, 0))
        ttk.Button(buttons, text="复制全部信息", command=self.copy_all).pack(side="left", padx=(8, 0))

        copy_buttons = ttk.Frame(outer)
        copy_buttons.pack(fill="x", pady=(8, 0))
        ttk.Button(copy_buttons, text="复制电脑名称", command=self.copy_computer_name).pack(side="left")
        ttk.Button(copy_buttons, text="复制品牌", command=self.copy_manufacturer).pack(side="left", padx=(8, 0))
        ttk.Button(copy_buttons, text="复制型号", command=self.copy_model).pack(side="left", padx=(8, 0))
        ttk.Button(copy_buttons, text="生成 TXT 文件", command=self.save_txt).pack(side="right")
        name_entry.focus_set()

    def _update_mac_box(self) -> None:
        self.mac_box.configure(state="normal")
        self.mac_box.delete("1.0", "end")
        self.mac_box.insert("1.0", self._mac_display())
        self.mac_box.configure(state="disabled")

    def refresh(self) -> None:
        self.mac_addresses = get_mac_addresses()
        self.manufacturer, self.model = get_device_info()
        self._update_mac_box()
        self.status_var.set("已重新检测网卡和电脑信息。")

    def _all_info_text(self) -> str:
        mac_text = "、".join(self.mac_addresses) if self.mac_addresses else "未读取到"
        return "\n".join([
            "校园 MAC 地址采集结果",
            f"教师姓名：{self.name_var.get().strip() or '未填写'}",
            f"学校/部门：{self.school_var.get().strip() or '未填写'}",
            f"电脑名称：{socket.gethostname()}",
            f"电脑品牌：{self.manufacturer}",
            f"电脑型号：{self.model}",
            f"MAC 地址：{mac_text}",
        ])

    def copy_mac(self) -> None:
        if not self.mac_addresses:
            messagebox.showwarning("无法复制", "没有读取到 MAC 地址。")
            return
        self.root.clipboard_clear()
        self.root.clipboard_append("\n".join(self.mac_addresses))
        self.status_var.set("MAC 地址已复制到剪贴板。")

    def copy_all(self) -> None:
        self._copy_text(self._all_info_text(), "品牌、型号、电脑名和 MAC 地址已复制到剪贴板。")

    def _copy_text(self, value: str, status: str) -> None:
        self.root.clipboard_clear()
        self.root.clipboard_append(value)
        self.root.update()  # 确保程序关闭前剪贴板内容已交给 Windows。
        self.status_var.set(status)

    def copy_computer_name(self) -> None:
        self._copy_text(socket.gethostname(), "电脑名称已复制到剪贴板。")

    def copy_manufacturer(self) -> None:
        self._copy_text(self.manufacturer, "电脑品牌已复制到剪贴板。")

    def copy_model(self) -> None:
        self._copy_text(self.model, "电脑型号已复制到剪贴板。")

    def save_txt(self) -> None:
        if not self.mac_addresses:
            messagebox.showerror("无法生成文件", "没有读取到 MAC 地址，请先检查网络后重试。")
            return
        now = _dt.datetime.now()
        teacher = _safe_filename_part(self.name_var.get(), "未填写姓名")
        filename = f"MAC采集_{teacher}_{now:%Y%m%d_%H%M%S}.txt"
        path = filedialog.asksaveasfilename(title="保存 MAC 地址采集结果", initialdir=str(desktop_path()), initialfile=filename, defaultextension=".txt", filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")])
        if not path:
            return
        lines = [self._all_info_text(), "", "采集时间：" + now.strftime("%Y-%m-%d %H:%M:%S"), "", "说明：本文件由校园 MAC 地址采集工具生成。"]
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

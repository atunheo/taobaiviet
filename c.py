#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox
import re

def clean_final_repo_name(title: str) -> str:
    """Xử lý tiêu đề để ra 'Tên repo cuối cùng'"""
    if not title:
        return ""
    name = title.strip()

    # Bỏ dấu # ở đầu
    name = re.sub(r"^#+\s*", "", name)

    # Bỏ phần sau dấu '-' cuối cùng
    if "-" in name:
        name = name.rsplit("-", 1)[0].strip()

    return name

def export_repos_to_excel(base_dir):
    """Chuyển từ thư mục baiviet → file Excel (repo.xlsx)"""

    if not os.path.exists(base_dir):
        messagebox.showerror("Lỗi", f"Không tìm thấy thư mục: {base_dir}")
        return False

    data = []
    for repo_dir in os.listdir(base_dir):
        repo_path = os.path.join(base_dir, repo_dir)
        if not os.path.isdir(repo_path):
            continue

        readme_path = os.path.join(repo_path, "README.md")
        if not os.path.exists(readme_path):
            continue

        with open(readme_path, "r", encoding="utf-8") as f:
            content = f.read().strip()

        # Lấy tiêu đề = dòng đầu tiên
        lines = content.splitlines()
        title = lines[0].strip() if lines else ""
        body = "\n".join(lines[1:]).strip() if len(lines) > 1 else ""

        final_name = clean_final_repo_name(title)

        data.append({
            "Tên repo": repo_dir,
            "Tiêu đề": title,
            "Nội dung": body,
            "Tên repo cuối cùng": final_name
        })

    if not data:
        messagebox.showwarning("Cảnh báo", "Không có dữ liệu để xuất ra Excel")
        return False

    excel_path = os.path.join(base_dir, "repocuoicung.xlsx")
    df = pd.DataFrame(data, columns=["Tên repo", "Tiêu đề", "Nội dung", "Tên repo cuối cùng"])
    df.to_excel(excel_path, index=False)

    messagebox.showinfo("Hoàn tất", f"Đã xuất {len(data)} repo sang file Excel:\n{excel_path}")
    return True


if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()  # Ẩn cửa sổ chính

    folder_selected = filedialog.askdirectory(title="Chọn thư mục chứa các repo (baiviet)")
    if folder_selected:
        export_repos_to_excel(folder_selected)
    else:
        messagebox.showinfo("Thông báo", "Bạn chưa chọn thư mục nào.")

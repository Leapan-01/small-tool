import os
import hashlib
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from collections import defaultdict
import threading
import sys
import ctypes
from ctypes import wintypes

# 调用 Windows API 的 SHFileOperation
FO_DELETE = 0x0003
FOF_ALLOWUNDO = 0x0040
FOF_NOCONFIRMATION = 0x0010

class SHFILEOPSTRUCT(ctypes.Structure):
    _fields_ = [
        ("hwnd", wintypes.HWND),
        ("wFunc", ctypes.c_uint),
        ("pFrom", wintypes.LPCWSTR),
        ("pTo", wintypes.LPCWSTR),
        ("fFlags", ctypes.c_uint),
        ("fAnyOperationsAborted", wintypes.BOOL),
        ("hNameMappings", wintypes.LPVOID),
        ("lpszProgressTitle", wintypes.LPCWSTR),
    ]

def move_to_recycle_bin(file_path):
    """将文件移到回收站"""
    file_operation = SHFILEOPSTRUCT()
    file_operation.wFunc = FO_DELETE
    file_operation.pFrom = file_path + '\0'
    file_operation.fFlags = FOF_ALLOWUNDO | FOF_NOCONFIRMATION

    result = ctypes.windll.shell32.SHFileOperationW(ctypes.byref(file_operation))
    if result != 0:
        raise Exception(f"Failed to delete file {file_path}. Error code: {result}")

def resource_path(relative_path):
    """获取资源文件的路径"""
    if hasattr(sys, '_MEIPASS'):  # 打包后的临时目录
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

class DuplicateFileFinder:
    def __init__(self):
        self.files_dict = defaultdict(list)  # 存储文件的哈希值和文件路径
        self.files_to_delete = []

    def scan_directory(self, directory, progress_callback=None):
        """扫描指定目录中的文件"""
        total_files = sum([len(files) for _, _, files in os.walk(directory)])  # 计算总文件数
        scanned_files = 0
        self.files_dict.clear()  # 清空之前的文件记录，防止错误重复
        self.files_to_delete.clear()  # 清空重复文件记录
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                file_hash = self.get_file_hash(file_path, root)
                if file_hash:
                    self.files_dict[file_hash].append(file_path)
                
                # 更新进度条
                scanned_files += 1
                if progress_callback:
                    progress_callback(scanned_files, total_files)
    
    def get_file_hash(self, file_path, root_path):
        """计算文件的哈希值，并考虑文件路径"""
        hash_md5 = hashlib.md5()
        try:
            # 结合文件内容和文件所在路径计算哈希值
            hash_md5.update(root_path.encode('utf-8'))  # 加入文件夹路径
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)  # 加入文件内容
            return hash_md5.hexdigest()
        except Exception as e:
            print(f"无法计算文件 {file_path} 的哈希值：{e}")
            return None

    def find_duplicates(self):
        """查找所有重复文件"""
        self.files_to_delete = []
        for file_hash, paths in self.files_dict.items():
            if len(paths) > 1:
                self.files_to_delete.append(paths)

    def delete_file(self, file_path, progress_callback=None):
        """将文件移动到回收站"""
        try:
            move_to_recycle_bin(file_path)
            print(f"文件已移动到回收站：{file_path}")
        except Exception as e:
            print(f"无法删除文件 {file_path}：{e}")
            return False
        if progress_callback:
            progress_callback(file_path)  # 更新删除进度
        return True

class DuplicateFileApp:
    def __init__(self, root):
        self.root = root
        self.root.title("NoRedo")
        self.root.geometry("800x700")
        self.root.configure(bg="#f4f4f4")  # 设置背景色

        self.finder = DuplicateFileFinder()

        # 设置窗口图标
        self.root.iconbitmap(resource_path('icon.ico'))

        # 设置按钮样式
        style = ttk.Style()
        style.configure("TButton", padding=10, relief="flat", background="#4CAF50", foreground="black", borderwidth=2)
        style.map("TButton", background=[('active', '#45a049')])

        # 设置进度条样式
        style.configure("TProgressbar", thickness=30, background="#4CAF50")

        # UI布局
        self.create_widgets()

    def create_widgets(self):
        """创建界面控件"""
        # 使用ttk.Button
        self.scan_button = ttk.Button(self.root, text="选择文件夹", command=self.scan_folder, style="TButton")
        self.scan_button.pack(pady=20)

        # 文件列表框
        self.file_listbox = tk.Listbox(self.root, width=100, height=20)
        self.file_listbox.pack(padx=10, pady=10)

        # 删除按钮
        self.delete_button = ttk.Button(self.root, text="删除选中的文件", command=self.delete_selected, style="TButton")
        self.delete_button.pack(pady=10)

        # 进度条
        self.progress_label = tk.Label(self.root, text="扫描进度：", bg="#f4f4f4")
        self.progress_label.pack(pady=5)
        
        self.progressbar = ttk.Progressbar(self.root, orient="horizontal", length=600, mode="determinate", style="TProgressbar")
        self.progressbar.pack(pady=10)

        # 关于按钮
        self.about_button = ttk.Button(self.root, text="关于", command=self.show_about, style="TButton")
        self.about_button.pack(pady=10)

        # 确保点击关闭时退出程序
        self.root.protocol("WM_DELETE_WINDOW", self.on_exit)

    def on_exit(self):
        """点击关闭按钮时退出程序"""
        self.root.quit()
        self.root.destroy()

    def scan_folder(self):
        """选择文件夹并扫描重复文件"""
        folder = filedialog.askdirectory(title="选择文件夹")
        if folder:
            # 清空之前的文件列表
            self.file_listbox.delete(0, tk.END)

            # 禁用按钮，避免重复操作
            self.scan_button.config(state=tk.DISABLED)
            self.root.after(100, self.start_scan, folder)

    def start_scan(self, folder):
        """开始扫描文件"""
        def scan():
            # 更新进度条
            def update_progress(scanned_files, total_files):
                self.progressbar["value"] = (scanned_files / total_files) * 100
                self.progressbar.update()

            self.finder.scan_directory(folder, progress_callback=update_progress)
            self.finder.find_duplicates()
            self.show_duplicates()
            self.scan_button.config(state=tk.NORMAL)

        threading.Thread(target=scan, daemon=True).start()

    def show_duplicates(self):
        """显示重复文件"""
        self.file_listbox.delete(0, tk.END)  # 清空当前显示的文件
        for group in self.finder.files_to_delete:
            self.file_listbox.insert(tk.END, "重复文件组：")
            for file_path in group:
                self.file_listbox.insert(tk.END, f"  {file_path}")
            self.file_listbox.insert(tk.END, "----------------------------------")

    def delete_selected(self):
        """删除选中的文件"""
        selected_indices = self.file_listbox.curselection()
        if not selected_indices:
            messagebox.showinfo("提示", "请选择要删除的文件。")
            return

        confirm = messagebox.askyesno("确认删除", "确定要删除选中的文件吗？")
        if not confirm:
            return

        def update_deletion_progress(file_path):
            self.progressbar["value"] += 100 / len(selected_indices)
            self.progressbar.update()

        for index in selected_indices:
            file_path = self.file_listbox.get(index).strip()
            if file_path.startswith("重复文件组") or file_path.startswith("-"):
                continue
            if self.finder.delete_file(file_path, progress_callback=update_deletion_progress):
                self.file_listbox.delete(index)

        messagebox.showinfo("完成", "选中的文件已删除。")
        self.show_duplicates()

    def show_about(self):
        """显示关于页面"""
        about_window = tk.Toplevel(self.root)
        about_window.title("关于")
        about_window.geometry("500x400")
        about_window.configure(bg="#ffffff")

        # 设置关于窗口图标
        about_window.iconbitmap(resource_path('icon.ico'))

        about_text = (
            "作者：Leapan\n"
            "更新网址：\nhttps://github.com/Leapan-01/NoRedo\n\n"
            "博客网址：\nhttps://www.lp-gardenwalk.top\n\n"
            "Bug反馈：lp-gardenwalk@outlook.com\n\n"
            "版本号：V1.1.0"
        )

        label = tk.Label(about_window, text=about_text, justify="left", bg="#ffffff")
        label.pack(padx=20, pady=20)

        close_button = ttk.Button(about_window, text="关闭", command=about_window.destroy, style="TButton")
        close_button.pack(pady=5)

def main():
    root = tk.Tk()
    app = DuplicateFileApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()

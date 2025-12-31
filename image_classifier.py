#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片分类工具
- 浏览当前目录下的图片
- 将图片移动到分类文件夹
- 支持键盘快捷键
"""

import os
import shutil
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk


class ImageClassifier:
    def __init__(self, root):
        self.root = root
        self.root.title("图片分类工具")
        self.root.geometry("1200x800")
        
        # 当前工作目录
        self.work_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 图片列表和当前索引
        self.image_files = []
        self.current_index = 0
        
        # 分类文件夹列表
        self.folders = []
        
        # 撤销栈：存储 (原路径, 目标路径) 元组
        self.undo_stack = []
        
        # 当前显示的图片对象（防止被垃圾回收）
        self.current_photo = None
        
        # 初始化界面
        self.setup_ui()
        
        # 加载数据
        self.load_images()
        self.load_folders()
        
        # 绑定键盘事件
        self.bind_keys()
        
        # 显示第一张图片
        self.show_current_image()
    
    def setup_ui(self):
        """设置界面布局"""
        # 主容器
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 左侧：图片显示区域
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 图片标签
        self.image_label = ttk.Label(left_frame, anchor=tk.CENTER)
        self.image_label.pack(fill=tk.BOTH, expand=True)
        
        # 右侧：控制面板
        right_frame = ttk.Frame(main_frame, width=350)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        right_frame.pack_propagate(False)
        
        # 分类文件夹标题
        folder_title = ttk.Label(right_frame, text="分类文件夹 (小键盘 1-9 快速分类)", font=("", 12, "bold"))
        folder_title.pack(pady=(0, 10))
        
        # 文件夹列表框
        list_frame = ttk.Frame(right_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # 添加垂直滚动条
        y_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL)
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 添加水平滚动条（用于长文件名）
        x_scrollbar = ttk.Scrollbar(list_frame, orient=tk.HORIZONTAL)
        x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.folder_listbox = tk.Listbox(list_frame, font=("", 14), 
                                          yscrollcommand=y_scrollbar.set,
                                          xscrollcommand=x_scrollbar.set,
                                          selectmode=tk.SINGLE)
        self.folder_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        y_scrollbar.config(command=self.folder_listbox.yview)
        x_scrollbar.config(command=self.folder_listbox.xview)
        
        # 新建文件夹区域
        new_folder_frame = ttk.Frame(right_frame)
        new_folder_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(new_folder_frame, text="新建文件夹:").pack(anchor=tk.W)
        
        input_frame = ttk.Frame(new_folder_frame)
        input_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.new_folder_entry = ttk.Entry(input_frame)
        self.new_folder_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        create_btn = ttk.Button(input_frame, text="创建", command=self.create_folder)
        create_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        # 操作按钮
        btn_frame = ttk.Frame(right_frame)
        btn_frame.pack(fill=tk.X, pady=(15, 0))
        
        move_btn = ttk.Button(btn_frame, text="移动到选中文件夹", command=self.move_to_selected)
        move_btn.pack(fill=tk.X, pady=(0, 5))
        
        undo_btn = ttk.Button(btn_frame, text="撤销 (Ctrl+Z)", command=self.undo_move)
        undo_btn.pack(fill=tk.X)
        
        # 底部：导航栏
        nav_frame = ttk.Frame(self.root, padding="10")
        nav_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        # 上一张按钮
        self.prev_btn = ttk.Button(nav_frame, text="↑ 上一张", command=self.prev_image)
        self.prev_btn.pack(side=tk.LEFT)
        
        # 进度信息
        self.info_label = ttk.Label(nav_frame, text="", font=("", 11))
        self.info_label.pack(side=tk.LEFT, expand=True)
        
        # 下一张按钮
        self.next_btn = ttk.Button(nav_frame, text="下一张 ↓", command=self.next_image)
        self.next_btn.pack(side=tk.RIGHT)
    
    def bind_keys(self):
        """绑定键盘快捷键"""
        # 上下键翻页
        self.root.bind("<Up>", lambda e: self.prev_image())
        self.root.bind("<Down>", lambda e: self.next_image())
        
        # 小键盘数字键 1-9 用于快速分类
        for i in range(1, 10):
            self.root.bind(f"<KP_{i}>", lambda e, idx=i: self.quick_move(idx))
        
        # Ctrl+Z 撤销
        self.root.bind("<Control-z>", lambda e: self.undo_move())
        self.root.bind("<Command-z>", lambda e: self.undo_move())  # macOS
        
        # 回车键创建文件夹
        self.new_folder_entry.bind("<Return>", lambda e: self.create_folder())
    
    def load_images(self):
        """加载当前目录下的所有图片"""
        self.image_files = []
        
        for f in os.listdir(self.work_dir):
            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                self.image_files.append(f)
        
        # 按文件名排序
        self.image_files.sort()
        self.current_index = 0
    
    def load_folders(self):
        """加载当前目录下的所有子文件夹，按创建时间排序"""
        self.folders = []
        folder_with_time = []
        
        for f in os.listdir(self.work_dir):
            full_path = os.path.join(self.work_dir, f)
            if os.path.isdir(full_path) and not f.startswith('.'):
                # 获取文件夹创建时间（macOS 使用 st_birthtime）
                try:
                    create_time = os.stat(full_path).st_birthtime
                except AttributeError:
                    # 其他系统使用 st_ctime 作为备选
                    create_time = os.stat(full_path).st_ctime
                folder_with_time.append((f, create_time))
        
        # 按创建时间排序（最早创建的在前）
        folder_with_time.sort(key=lambda x: x[1])
        self.folders = [f[0] for f in folder_with_time]
        self.update_folder_listbox()
    
    def update_folder_listbox(self):
        """更新文件夹列表显示"""
        self.folder_listbox.delete(0, tk.END)
        
        for i, folder in enumerate(self.folders):
            # 前9个显示快捷键编号
            if i < 9:
                display_text = f"[{i+1}] {folder}"
            else:
                display_text = f"    {folder}"
            self.folder_listbox.insert(tk.END, display_text)
    
    def show_current_image(self):
        """显示当前图片"""
        if not self.image_files:
            self.image_label.config(image="", text="没有找到图片文件")
            self.info_label.config(text="共 0 张图片")
            return
        
        # 获取当前图片路径
        image_path = os.path.join(self.work_dir, self.image_files[self.current_index])
        
        try:
            # 加载图片
            img = Image.open(image_path)
            
            # 获取显示区域大小
            self.root.update_idletasks()
            max_width = self.image_label.winfo_width() - 20
            max_height = self.image_label.winfo_height() - 20
            
            # 如果窗口还没准备好，使用默认值
            if max_width < 100:
                max_width = 800
            if max_height < 100:
                max_height = 600
            
            # 计算缩放比例
            ratio = min(max_width / img.width, max_height / img.height)
            if ratio < 1:
                new_size = (int(img.width * ratio), int(img.height * ratio))
                img = img.resize(new_size, Image.Resampling.LANCZOS)
            
            # 转换为 Tkinter 可用的格式
            self.current_photo = ImageTk.PhotoImage(img)
            self.image_label.config(image=self.current_photo, text="")
            
        except Exception as e:
            self.image_label.config(image="", text=f"无法加载图片: {e}")
        
        # 更新进度信息
        current_file = self.image_files[self.current_index]
        self.info_label.config(
            text=f"图片 {self.current_index + 1} / {len(self.image_files)}    |    {current_file}"
        )
    
    def prev_image(self):
        """显示上一张图片"""
        if self.image_files and self.current_index > 0:
            self.current_index -= 1
            self.show_current_image()
    
    def next_image(self):
        """显示下一张图片"""
        if self.image_files and self.current_index < len(self.image_files) - 1:
            self.current_index += 1
            self.show_current_image()
    
    def create_folder(self):
        """创建新的分类文件夹"""
        folder_name = self.new_folder_entry.get().strip()
        
        if not folder_name:
            messagebox.showwarning("提示", "请输入文件夹名称")
            return
        
        folder_path = os.path.join(self.work_dir, folder_name)
        
        if os.path.exists(folder_path):
            messagebox.showwarning("提示", f"文件夹 '{folder_name}' 已存在")
            return
        
        try:
            os.makedirs(folder_path)
            self.new_folder_entry.delete(0, tk.END)
            self.load_folders()
            messagebox.showinfo("成功", f"已创建文件夹: {folder_name}")
        except Exception as e:
            messagebox.showerror("错误", f"创建文件夹失败: {e}")
    
    def move_to_selected(self):
        """将当前图片移动到选中的文件夹"""
        selection = self.folder_listbox.curselection()
        
        if not selection:
            messagebox.showwarning("提示", "请先选择一个目标文件夹")
            return
        
        folder_index = selection[0]
        self.move_image_to_folder(folder_index)
    
    def quick_move(self, number):
        """快捷键移动：按数字键1-9快速移动到对应文件夹"""
        folder_index = number - 1
        
        if folder_index < len(self.folders):
            self.move_image_to_folder(folder_index)
    
    def move_image_to_folder(self, folder_index):
        """将当前图片移动到指定文件夹"""
        if not self.image_files:
            return
        
        if folder_index >= len(self.folders):
            return
        
        # 源文件路径
        src_file = self.image_files[self.current_index]
        src_path = os.path.join(self.work_dir, src_file)
        
        # 目标文件夹和路径
        target_folder = self.folders[folder_index]
        dst_path = os.path.join(self.work_dir, target_folder, src_file)
        
        # 检查目标是否已存在
        if os.path.exists(dst_path):
            result = messagebox.askyesnocancel(
                "文件已存在",
                f"文件 '{src_file}' 在文件夹 '{target_folder}' 中已存在。\n\n"
                "是 - 覆盖\n"
                "否 - 跳过\n"
                "取消 - 取消操作"
            )
            
            if result is None:  # 取消
                return
            elif result is False:  # 跳过
                self.go_to_next_or_finish()
                return
            # result is True: 覆盖，继续执行
        
        try:
            # 移动文件
            shutil.move(src_path, dst_path)
            
            # 记录到撤销栈
            self.undo_stack.append((dst_path, src_path))
            
            # 从列表中移除已移动的图片
            del self.image_files[self.current_index]
            
            # 调整索引
            if self.current_index >= len(self.image_files):
                self.current_index = len(self.image_files) - 1
            
            # 检查是否还有图片
            self.go_to_next_or_finish()
            
        except Exception as e:
            messagebox.showerror("错误", f"移动文件失败: {e}")
    
    def go_to_next_or_finish(self):
        """移动到下一张或显示完成"""
        if not self.image_files:
            self.image_label.config(image="", text="🎉 所有图片已分类完成！")
            self.info_label.config(text="共 0 张图片")
            messagebox.showinfo("完成", "所有图片已分类完成！")
        else:
            self.show_current_image()
    
    def undo_move(self):
        """撤销上一次移动操作"""
        if not self.undo_stack:
            messagebox.showinfo("提示", "没有可撤销的操作")
            return
        
        # 获取上一次操作
        current_path, original_path = self.undo_stack.pop()
        
        try:
            # 移回原位置
            shutil.move(current_path, original_path)
            
            # 重新加载图片列表
            old_index = self.current_index
            self.load_images()
            
            # 尝试定位到恢复的图片
            restored_file = os.path.basename(original_path)
            if restored_file in self.image_files:
                self.current_index = self.image_files.index(restored_file)
            else:
                self.current_index = min(old_index, len(self.image_files) - 1)
            
            self.show_current_image()
            messagebox.showinfo("成功", f"已撤销: {restored_file}")
            
        except Exception as e:
            messagebox.showerror("错误", f"撤销失败: {e}")


def main():
    root = tk.Tk()
    app = ImageClassifier(root)
    root.mainloop()


if __name__ == "__main__":
    main()


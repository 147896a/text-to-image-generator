#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
文字转图像生成器 - 主程序
使用 Tkinter GUI 和 Stability AI API
"""

import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog
from PIL import Image, ImageTk
import requests
import os
from datetime import datetime
import threading
import json
import base64
from config import (
    STABILITY_API_KEY,
    STABILITY_API_URL,
    IMAGE_WIDTH,
    IMAGE_HEIGHT,
    STEPS,
    SCALE,
    OUTPUT_DIR
)


class TextToImageGenerator:
    """文字转图像生成器主类"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("文字转图像生成器 (Text to Image Generator)")
        self.root.geometry("1000x700")
        self.root.resizable(True, True)
        
        # 创建输出目录
        if not os.path.exists(OUTPUT_DIR):
            os.makedirs(OUTPUT_DIR)
        
        # 状态变量
        self.is_generating = False
        self.current_image = None
        self.current_image_path = None
        
        # 创建 GUI
        self.setup_ui()
    
    def setup_ui(self):
        """设置用户界面"""
        
        # ===== 顶部：API Key 配置 =====
        top_frame = tk.Frame(self.root, bg="#f0f0f0", pady=10)
        top_frame.pack(fill=tk.X, padx=10)
        
        tk.Label(top_frame, text="🔑 API Key:", bg="#f0f0f0", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        self.api_key_var = tk.StringVar(value=STABILITY_API_KEY if STABILITY_API_KEY != "YOUR_API_KEY_HERE" else "")
        self.api_key_entry = tk.Entry(top_frame, textvariable=self.api_key_var, width=40, show="*")
        self.api_key_entry.pack(side=tk.LEFT, padx=5)
        
        tk.Button(top_frame, text="保存 API Key", command=self.save_api_key, bg="#4CAF50", fg="white", padx=10).pack(side=tk.LEFT, padx=5)
        
        tk.Label(top_frame, text="💡 获取 API Key: https://platform.stabilityai.com/", 
                 bg="#f0f0f0", fg="#666", font=("Arial", 9)).pack(side=tk.LEFT, padx=5)
        
        # ===== 左侧：输入区域 =====
        left_frame = tk.Frame(self.root)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 输入框标题
        tk.Label(left_frame, text="📝 输入图像描述", font=("Arial", 12, "bold")).pack(anchor="w")
        
        # 输入文本框
        self.input_text = scrolledtext.ScrolledText(
            left_frame, 
            height=8, 
            width=40,
            font=("Arial", 10),
            wrap=tk.WORD,
            relief=tk.SOLID,
            borderwidth=1
        )
        self.input_text.pack(fill=tk.BOTH, expand=True, pady=(5, 10))
        self.input_text.insert(1.0, "例如：一只可爱的小猫，坐在阳光下，高质量，细节清晰")
        
        # 参数调整区域
        param_frame = tk.LabelFrame(left_frame, text="⚙️ 生成参数", font=("Arial", 10, "bold"), padx=10, pady=10)
        param_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 宽度和高度
        size_frame = tk.Frame(param_frame)
        size_frame.pack(fill=tk.X, pady=5)
        tk.Label(size_frame, text="图像尺寸:").pack(side=tk.LEFT)
        self.size_var = tk.StringVar(value="512x512")
        size_combo = tk.OptionMenu(
            size_frame, 
            self.size_var, 
            "512x512", "640x640", "768x768", "512x768", "768x512"
        )
        size_combo.pack(side=tk.LEFT, padx=5)
        
        # 生成步数
        steps_frame = tk.Frame(param_frame)
        steps_frame.pack(fill=tk.X, pady=5)
        tk.Label(steps_frame, text="生成步数 (10-50):").pack(side=tk.LEFT)
        self.steps_var = tk.IntVar(value=STEPS)
        steps_scale = tk.Scale(
            steps_frame, 
            from_=10, 
            to=50, 
            orient=tk.HORIZONTAL,
            variable=self.steps_var
        )
        steps_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.steps_label = tk.Label(steps_frame, text=str(STEPS))
        self.steps_label.pack(side=tk.LEFT)
        self.steps_var.trace("w", lambda *args: self.steps_label.config(text=str(self.steps_var.get())))
        
        # 引导尺度
        scale_frame = tk.Frame(param_frame)
        scale_frame.pack(fill=tk.X, pady=5)
        tk.Label(scale_frame, text="引导尺度 (0-20):").pack(side=tk.LEFT)
        self.scale_var = tk.DoubleVar(value=SCALE)
        scale_scale = tk.Scale(
            scale_frame, 
            from_=0, 
            to=20, 
            orient=tk.HORIZONTAL,
            resolution=0.5,
            variable=self.scale_var
        )
        scale_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.scale_label = tk.Label(scale_frame, text=str(SCALE))
        self.scale_label.pack(side=tk.LEFT)
        self.scale_var.trace("w", lambda *args: self.scale_label.config(text=f"{self.scale_var.get():.1f}"))
        
        # 生成按钮
        button_frame = tk.Frame(left_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.generate_btn = tk.Button(
            button_frame,
            text="🎨 生成图像",
            command=self.generate_image,
            font=("Arial", 12, "bold"),
            bg="#2196F3",
            fg="white",
            padx=20,
            pady=10,
            relief=tk.RAISED,
            activebackground="#1976D2"
        )
        self.generate_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        self.stop_btn = tk.Button(
            button_frame,
            text="⏹️ 停止",
            command=self.stop_generation,
            font=("Arial", 12, "bold"),
            bg="#f44336",
            fg="white",
            padx=20,
            pady=10,
            relief=tk.RAISED,
            activebackground="#da190b",
            state=tk.DISABLED
        )
        self.stop_btn.pack(side=tk.LEFT, padx=(5, 0))
        
        # 状态标签
        self.status_label = tk.Label(left_frame, text="准备就绪 ✓", fg="green", font=("Arial", 10))
        self.status_label.pack(anchor="w", pady=(0, 10))
        
        # ===== 右侧：图像展示区域 =====
        right_frame = tk.Frame(self.root)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        tk.Label(right_frame, text="🖼️ 生成的图像", font=("Arial", 12, "bold")).pack(anchor="w")
        
        # 图像显示区域
        self.image_label = tk.Label(
            right_frame,
            bg="#e0e0e0",
            width=50,
            height=25,
            relief=tk.SUNKEN,
            borderwidth=2
        )
        self.image_label.pack(fill=tk.BOTH, expand=True, pady=(5, 10))
        
        # 图像信息
        self.info_label = tk.Label(
            right_frame,
            text="点击'生成图像'按钮开始...",
            fg="#666",
            font=("Arial", 9),
            wraplength=300,
            justify=tk.LEFT
        )
        self.info_label.pack(anchor="w", pady=(0, 10))
        
        # 保存按钮
        save_frame = tk.Frame(right_frame)
        save_frame.pack(fill=tk.X)
        
        self.save_btn = tk.Button(
            save_frame,
            text="💾 另存为...",
            command=self.save_image,
            font=("Arial", 10, "bold"),
            bg="#FF9800",
            fg="white",
            padx=15,
            pady=8,
            state=tk.DISABLED
        )
        self.save_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        self.open_folder_btn = tk.Button(
            save_frame,
            text="📁 打开输出文件夹",
            command=self.open_output_folder,
            font=("Arial", 10, "bold"),
            bg="#9C27B0",
            fg="white",
            padx=15,
            pady=8
        )
        self.open_folder_btn.pack(side=tk.LEFT, padx=(5, 0))
    
    def save_api_key(self):
        """保存 API Key"""
        api_key = self.api_key_var.get().strip()
        if not api_key:
            messagebox.showerror("错误", "API Key 不能为空！")
            return
        
        # 更新全局变量
        global STABILITY_API_KEY
        STABILITY_API_KEY = api_key
        
        # 更新 config.py 文件
        try:
            with open("config.py", "r", encoding="utf-8") as f:
                content = f.read()
            
            # 替换 API Key
            content = content.replace(
                f'STABILITY_API_KEY = "{STABILITY_API_KEY}"',
                f'STABILITY_API_KEY = "{api_key}"'
            )
            
            with open("config.py", "w", encoding="utf-8") as f:
                f.write(content)
            
            messagebox.showinfo("成功", "API Key 已保存！")
            self.status_label.config(text="API Key 已保存 ✓", fg="green")
        except Exception as e:
            messagebox.showerror("错误", f"保存失败：{str(e)}")
    
    def generate_image(self):
        """生成图像（在新线程中运行）"""
        
        # 验证 API Key
        api_key = self.api_key_var.get().strip()
        if not api_key or api_key == "YOUR_API_KEY_HERE":
            messagebox.showerror("错误", "请先输入有效的 API Key！")
            return
        
        # 获取输入文本
        prompt = self.input_text.get(1.0, tk.END).strip()
        if not prompt:
            messagebox.showerror("错误", "请输入图像描述！")
            return
        
        # 禁用按钮
        self.is_generating = True
        self.generate_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_label.config(text="⏳ 正在生成图像，请稍候...", fg="orange")
        
        # 在新线程中执行生成任务
        thread = threading.Thread(target=self._generate_image_thread, args=(api_key, prompt))
        thread.daemon = True
        thread.start()
    
    def _generate_image_thread(self, api_key, prompt):
        """在线程中执行图像生成"""
        try:
            # 解析图像尺寸
            size = self.size_var.get()
            width, height = map(int, size.split("x"))
            
            # 获取参数
            steps = self.steps_var.get()
            scale = self.scale_var.get()
            
            # 请求头
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            # 请求数据
            payload = {
                "text_prompts": [
                    {
                        "text": prompt,
                        "weight": 1
                    }
                ],
                "height": height,
                "width": width,
                "steps": steps,
                "cfg_scale": scale,
                "samples": 1,
                "seed": 0
            }
            
            # 发送请求
            self.status_label.config(text="📡 正在调用 API...", fg="blue")
            self.root.update()
            
            response = requests.post(
                STABILITY_API_URL,
                headers=headers,
                json=payload,
                timeout=60
            )
            
            # 检查响应
            if response.status_code != 200:
                error_msg = response.json().get("message", response.text)
                raise Exception(f"API 错误 {response.status_code}: {error_msg}")
            
            # 获取图像数据
            data = response.json()
            image_data = data["artifacts"][0]["base64"]
            
            # 转换为图像
            image_bytes = base64.b64decode(image_data)
            self.current_image = Image.open(__import__("io").BytesIO(image_bytes))
            
            # 保存到文件
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"generated_{timestamp}.png"
            self.current_image_path = os.path.join(OUTPUT_DIR, filename)
            self.current_image.save(self.current_image_path)
            
            # 显示图像
            self.display_image(self.current_image)
            
            # 更新信息
            info_text = f"✓ 生成成功！\n图像尺寸: {width}x{height}\n保存路径: {filename}\n提示词: {prompt[:50]}..."
            self.info_label.config(text=info_text, fg="green")
            
            # 启用保存按钮
            self.save_btn.config(state=tk.NORMAL)
            
            self.status_label.config(text="✓ 生成完成！", fg="green")
        
        except Exception as e:
            error_msg = str(e)
            self.status_label.config(text=f"✗ 错误：{error_msg}", fg="red")
            self.info_label.config(text=f"错误详情：{error_msg}", fg="red")
            messagebox.showerror("生成失败", error_msg)
        
        finally:
            # 恢复按钮状态
            self.is_generating = False
            self.generate_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
    
    def stop_generation(self):
        """停止生成"""
        self.is_generating = False
        self.status_label.config(text="已停止", fg="red")
        self.generate_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
    
    def display_image(self, image):
        """在 GUI 中显示图像"""
        # 调整大小以适应显示区域
        display_image = image.copy()
        display_image.thumbnail((400, 400), Image.Resampling.LANCZOS)
        
        # 转换为 PhotoImage
        photo = ImageTk.PhotoImage(display_image)
        
        # 更新标签
        self.image_label.config(image=photo)
        self.image_label.image = photo  # 保留引用
    
    def save_image(self):
        """另存为图像"""
        if not self.current_image:
            messagebox.showwarning("警告", "没有可保存的图像！")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG 文件", "*.png"), ("JPEG 文件", "*.jpg"), ("所有文件", "*.*")],
            initialdir=OUTPUT_DIR
        )
        
        if file_path:
            try:
                self.current_image.save(file_path)
                messagebox.showinfo("成功", f"图像已保存到：\n{file_path}")
            except Exception as e:
                messagebox.showerror("错误", f"保存失败：{str(e)}")
    
    def open_output_folder(self):
        """打开输出文件夹"""
        import subprocess
        import sys
        
        folder_path = os.path.abspath(OUTPUT_DIR)
        
        try:
            if sys.platform == "win32":
                os.startfile(folder_path)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", folder_path])
            else:
                subprocess.Popen(["xdg-open", folder_path])
        except Exception as e:
            messagebox.showerror("错误", f"无法打开文件夹：{str(e)}")


def main():
    """主函数"""
    root = tk.Tk()
    app = TextToImageGenerator(root)
    root.mainloop()


if __name__ == "__main__":
    main()

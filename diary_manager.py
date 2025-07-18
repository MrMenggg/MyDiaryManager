import os
import sys
import yaml
import tkinter as tk
from tkinter import filedialog, messagebox
from utils.file_utils import create_diary_entry


CONFIG_PATH = "config.yaml"

def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                if not isinstance(data, dict):
                    # 配置文件格式不对，返回默认
                    return {
                        'base_path': '',
                        'filename_format': '%Y%m%d.md',
                        'use_template': False,
                        'template_path': ''
                    }
                # 确保所有字段都有默认值
                data.setdefault('base_path', '')
                data.setdefault('filename_format', '%Y%m%d.md')
                data.setdefault('use_template', False)
                data.setdefault('template_path', '')
                return data
        except Exception as e:
            print(f"读取配置文件出错: {e}")
            return {
                'base_path': '',
                'filename_format': '%Y%m%d.md',
                'use_template': False,
                'template_path': ''
            }
    else:
        # 配置文件不存在，返回默认配置
        return {
            'base_path': '',
            'filename_format': '%Y%m%d.md',
            'use_template': False,
            'template_path': ''
        }

def save_config(config):
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, allow_unicode=True)

def select_directory(entry_widget):
    path = filedialog.askdirectory()
    if path:
        entry_widget.delete(0, tk.END)
        entry_widget.insert(0, path)

def select_file(entry_widget):
    path = filedialog.askopenfilename(filetypes=[("Markdown files", "*.md"), ("All files", "*.*")])
    if path:
        entry_widget.delete(0, tk.END)
        entry_widget.insert(0, path)

def run_creation(config):
    base_path = config.get('base_path', '')
    filename_format = config.get('filename_format', '%Y%m%d.md')
    use_template = config.get('use_template', False)
    template_path = config.get('template_path', '')

    if not base_path:
        return "根目录不能为空"
    result = create_diary_entry(base_path, filename_format, use_template, template_path)
    return result

def gui_main():
    config = load_config()

    root = tk.Tk()
    root.title("日记管理工具")

    # 根目录
    tk.Label(root, text="📁 根目录:").grid(row=0, column=0, sticky="e")
    entry_path = tk.Entry(root, width=40)
    entry_path.grid(row=0, column=1)
    entry_path.insert(0, str(config.get('base_path', '')))
    tk.Button(root, text="浏览", command=lambda: select_directory(entry_path)).grid(row=0, column=2)

    # 命名格式
    tk.Label(root, text="📝 文件命名格式:").grid(row=1, column=0, sticky="e")

    # 预设格式选项
    format_options = ['%Y%m%d.md', '%Y-%m-%d 日记.md', 'diary_%Y%m%d.md']
    var_format = tk.StringVar(value=config.get('filename_format', '%Y%m%d.md'))
    combo_format = tk.OptionMenu(root, var_format, *format_options)
    combo_format.grid(row=1, column=1, sticky='w')

    # 自定义格式输入
    tk.Label(root, text="自定义格式:").grid(row=2, column=0, sticky="e")
    entry_custom_format = tk.Entry(root, width=40)
    entry_custom_format.grid(row=2, column=1, columnspan=2, sticky="we")
    entry_custom_format.insert(0, '')

    def update_format(*args):
        val = var_format.get()
        if val in format_options:
            entry_custom_format.delete(0, tk.END)
        else:
            entry_custom_format.delete(0, tk.END)
            entry_custom_format.insert(0, val)

    var_format.trace('w', update_format)

    # 是否使用模板
    var_template = tk.BooleanVar(value=config.get('use_template', False))
    check_template = tk.Checkbutton(root, text="使用模板", variable=var_template)
    check_template.grid(row=3, column=1, sticky="w")

    # 模板路径
    tk.Label(root, text="📄 模板路径:").grid(row=4, column=0, sticky="e")
    entry_template = tk.Entry(root, width=40)
    entry_template.grid(row=4, column=1)
    entry_template.insert(0, str(config.get('template_path', '')))
    tk.Button(root, text="浏览", command=lambda: select_file(entry_template)).grid(row=4, column=2)

    # 创建按钮
    def on_create():
        filename_format = entry_custom_format.get().strip()
        if not filename_format:
            filename_format = var_format.get()

        new_config = {
            'base_path': entry_path.get(),
            'filename_format': filename_format,
            'use_template': var_template.get(),
            'template_path': entry_template.get(),
        }
        save_config(new_config)
        res = run_creation(new_config)
        messagebox.showinfo("结果", res)

    btn_create = tk.Button(root, text="✅ 创建今日文件", command=on_create, bg="#aef", height=2)
    btn_create.grid(row=5, column=0, columnspan=3, pady=10)

    root.mainloop()

def cli_main():
    config = load_config()
    result = run_creation(config)
    print(result)

if __name__ == "__main__":
    if '--nogui' in sys.argv:
        cli_main()
    else:
        gui_main()

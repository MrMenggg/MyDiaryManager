from datetime import datetime
import os
import shutil


def create_diary_entry(base_path, filename_format=None, use_template=False, template_path=None):
    today = datetime.today()

    if not filename_format:
        filename_format = "%Y%m%d.md"

    filename = sanitize_filename(today.strftime(filename_format))

    year = today.strftime("%Y")
    year_month = today.strftime("%Y%m")

    year_dir = os.path.join(base_path, year)
    month_dir = os.path.join(year_dir, year_month)
    os.makedirs(month_dir, exist_ok=True)

    target_file = os.path.join(month_dir, filename)

    if os.path.exists(target_file):
        return f"📄 文件已存在: {target_file}"

    if use_template and template_path and os.path.exists(template_path):
        with open(template_path, "r", encoding="utf-8") as f:
            content = f.read()
        today_str = datetime.today().strftime("%Y%m%d")
        content = content.replace("{{date}}", today_str)
        with open(target_file, "w", encoding="utf-8") as f:
            f.write(content)

    else:
        with open(target_file, "w", encoding="utf-8") as f:
            f.write("")

    return f"✅ 成功创建: {target_file}"

def sanitize_filename(name):
    return name.replace("/", "-").replace("\\", "-").strip()

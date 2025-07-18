# auto_create_diary.py
import os
import yaml
from diary_manager import run_creation

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.yaml")

if not os.path.exists(CONFIG_PATH):
    print("❌ 配置文件 config.yaml 不存在，请先运行前端配置一次。")
    input("按任意键退出...")
    exit()

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

result = run_creation(config)

print(result)
input("按回车退出...")

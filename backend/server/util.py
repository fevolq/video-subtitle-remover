import hashlib
import os
from datetime import datetime


def hash256(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def mkdir(path):
    """创建文件夹"""
    path = os.path.realpath(path)
    if not os.path.exists(path):
        os.makedirs(path)


def get_current_date():
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    return date_str

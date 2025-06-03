#!/usr/bin/env python3
import mysql.connector
import requests
import sys
from typing import List, Dict
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def login_user() -> bool:
    """注册单个用户"""
    try:
        # 这里需要根据实际的注册API端点进行修改
        api_url = "http://know.bjzntd.com/v1/user/login"  # 替换为实际的注册API地址
        payload = {
            "email": "admin@bjzntd.com",
            "password": "Pg9WHt9UdxhoUiFVs8uZjWdQP9e66iAKFElOUV43Q4iWl4mfEPHgbVhrAc+GyAwGxPd8uPB97nb4jRaFp/V8Pr6zD1hpvJrk1gxi9/Na0m9rGaVZV04M8wSXnZhIfMgtr0wclSieneCvxeiA2WAalynFOMAVV+37H8lL/pkvIjyHrIyDZwY2Q4XzNa9NZBBl1UNoyw1eTbFKI5hWqwFNynUNJRkwVkezrfI5TdW5S71XziM9U8vckiDHU2iLwvHS73/l7L+YdrEKtNu98LJAWqxD4YxtgJKB6288l4LkjD9G6KFQZCYOnI1sgG0ZyikObv3SnDXNwZyx/brxPc5TWQ=="
        }
        response = requests.post(api_url, json=payload)
        
        if response.status_code == 200:
            # cookies使用;分割
            cookies = response.headers['Set-Cookie'].split(';')[0]
            return response.headers['Authorization'],cookies
        else:
            logging.error(f"用户登录失败: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        logging.error(f"登录请求失败: {e}")
        return False

def main():
    """主函数"""
    Authorization,cookie = login_user()
    print(Authorization,cookie)


if __name__ == "__main__":
    main()

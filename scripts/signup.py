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

# 数据库配置
DB_CONFIG = {
    'host': '192.168.8.88',
    'port': 5455,
    'user': 'root',
    'password': 'infini_rag_flow',
    'database': 'rag_flow'
}

def connect_to_database() -> mysql.connector.MySQLConnection:
    """连接到MySQL数据库"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        logging.info("成功连接到数据库")
        return connection
    except mysql.connector.Error as err:
        logging.error(f"数据库连接失败: {err}")
        sys.exit(1)

def get_users_from_db(connection: mysql.connector.MySQLConnection) -> List[Dict]:
    """从数据库获取用户信息"""
    users = []
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT email, nickname FROM user")
        users = cursor.fetchall()
        cursor.close()
        logging.info(f"成功获取 {len(users)} 个用户信息")
        return users
    except mysql.connector.Error as err:
        logging.error(f"获取用户信息失败: {err}")
        return []

def register_user(email: str, nickname: str, password: str = "123456") -> bool:
    """注册单个用户"""
    try:
        # 这里需要根据实际的注册API端点进行修改
        api_url = "http://192.168.8.88:8080/api/v1/auths/signup"  # 替换为实际的注册API地址
        payload = {
            "email": email,
            "name": nickname,
            "password": password
        }
        response = requests.post(api_url, json=payload)
        
        if response.status_code == 200:
            logging.info(f"用户 {email} 注册成功")
            return True
        else:
            logging.error(f"用户 {email} 注册失败: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        logging.error(f"注册请求失败: {e}")
        return False

def main():
    """主函数"""
    connection = connect_to_database()
    if not connection:
        return

    users = get_users_from_db(connection)
    
    success_count = 0
    fail_count = 0
    
    for user in users:
        if register_user(user['email'], user['nickname']):
            success_count += 1
        else:
            fail_count += 1
    
    logging.info(f"注册完成。成功: {success_count}, 失败: {fail_count}")
    connection.close()

if __name__ == "__main__":
    main()

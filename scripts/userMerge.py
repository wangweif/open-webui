import pymysql
import sqlite3

# 配置你的数据库信息
MYSQL_CONFIG = {
    "host": "127.0.0.1",
    "user": "root",
    "password": "infini_rag_flow",
    "database": "rag_flow",
    "port": 5455
}

SQLITE_PATH = "../backend/data/webui.db"  # SQLite 文件路径
MYSQL_TABLE = "user"        # MySQL 用户表名
SQLITE_TABLE = "user"      # SQLite 用户表名


def fetch_mysql_users():
    conn = pymysql.connect(**MYSQL_CONFIG)
    cursor = conn.cursor()
    cursor.execute(f"SELECT email, id, tenant_id, team_id FROM {MYSQL_TABLE}")
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    return users


def update_sqlite_users(users):
    conn = sqlite3.connect(SQLITE_PATH)
    cursor = conn.cursor()

    updated_count = 0
    for email, ragflow_user_id, tenant_id, team_id in users:
        cursor.execute(
            f"""
            UPDATE {SQLITE_TABLE}
            SET ragflow_user_id = ?, tenant_id = ?, team_id = ?
            WHERE email = ?
            """,
            (ragflow_user_id, tenant_id, team_id, email)
        )
        if cursor.rowcount > 0:
            updated_count += 1

    conn.commit()
    cursor.close()
    conn.close()
    print(f"✅ 更新完成，共更新了 {updated_count} 条记录。")


def main():
    print("🔄 从 MySQL 获取用户数据...")
    users = fetch_mysql_users()
    print(f"🔍 获取到 {len(users)} 条记录，开始更新 SQLite...")
    update_sqlite_users(users)


if __name__ == "__main__":
    main()

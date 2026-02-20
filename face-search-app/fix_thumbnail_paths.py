"""
修复人像库缩略图路径问题

问题：
1. 数据库中存储的缩略图文件名与实际文件名不匹配
2. 路径使用了Windows反斜杠

解决方案：
1. 删除所有现有的缩略图文件
2. 清空数据库中的所有人像记录
3. 用户需要重新保存人像
"""

import sqlite3
import os
import shutil

print("=" * 80)
print("修复人像库缩略图路径")
print("=" * 80)

# 1. 连接数据库
db_path = 'backend/cache/face_library.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 查询当前人像数量
cursor.execute('SELECT COUNT(*) FROM library_faces')
count = cursor.fetchone()[0]
print(f"\n当前数据库中有 {count} 个人像记录")

# 2. 清空数据库
print("\n正在清空数据库...")
cursor.execute('DELETE FROM library_faces')
conn.commit()
print("✅ 数据库已清空")

# 3. 清空缩略图目录
thumbnails_dir = 'backend/cache/thumbnails'
if os.path.exists(thumbnails_dir):
    files = os.listdir(thumbnails_dir)
    print(f"\n正在删除 {len(files)} 个缩略图文件...")
    for filename in files:
        file_path = os.path.join(thumbnails_dir, filename)
        try:
            os.remove(file_path)
        except Exception as e:
            print(f"  ⚠️  无法删除 {filename}: {e}")
    print("✅ 缩略图文件已清空")

# 4. 验证
cursor.execute('SELECT COUNT(*) FROM library_faces')
new_count = cursor.fetchone()[0]
remaining_files = len(os.listdir(thumbnails_dir)) if os.path.exists(thumbnails_dir) else 0

print("\n" + "=" * 80)
print("修复完成！")
print(f"数据库记录: {count} → {new_count}")
print(f"缩略图文件: {len(files) if 'files' in locals() else 0} → {remaining_files}")
print("\n⚠️  注意：所有历史人像已被清除，用户需要重新保存人像到库。")
print("=" * 80)

conn.close()

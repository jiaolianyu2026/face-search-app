"""
检查人像库缩略图问题
"""

import sqlite3
import os

# 连接数据库
conn = sqlite3.connect('backend/cache/face_library.db')
cursor = conn.cursor()

# 查询所有人像
cursor.execute('SELECT id, name, thumbnail_path FROM library_faces')
rows = cursor.fetchall()

print(f"数据库中共有 {len(rows)} 个人像")
print("=" * 80)

# 检查缩略图文件
missing_count = 0
for i, (face_id, name, thumbnail_path) in enumerate(rows[:10], 1):
    print(f"\n{i}. 人像: {name} (ID: {face_id[:8]}...)")
    print(f"   数据库路径: {thumbnail_path}")
    
    # 检查文件是否存在
    if os.path.exists(thumbnail_path):
        print(f"   ✅ 文件存在")
    else:
        print(f"   ❌ 文件不存在")
        missing_count += 1
        
        # 尝试查找可能的文件名
        thumbnail_filename = os.path.basename(thumbnail_path)
        possible_path = f"backend/cache/thumbnails/{thumbnail_filename}"
        if os.path.exists(possible_path):
            print(f"   💡 找到可能的文件: {possible_path}")

print("\n" + "=" * 80)
print(f"缺失的缩略图: {missing_count}/{min(10, len(rows))}")

# 列出实际存在的缩略图文件
print("\n实际存在的缩略图文件:")
thumbnails_dir = "backend/cache/thumbnails"
if os.path.exists(thumbnails_dir):
    files = os.listdir(thumbnails_dir)
    print(f"共 {len(files)} 个文件")
    for f in files[:5]:
        print(f"  - {f}")
    if len(files) > 5:
        print(f"  ... 还有 {len(files) - 5} 个文件")

conn.close()

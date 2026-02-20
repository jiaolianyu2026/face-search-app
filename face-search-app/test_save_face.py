"""
检查人像库缩略图状态
用于验证路径格式修复是否成功
"""

import os
import sqlite3

def check_current_state():
    """检查当前状态"""
    
    print("=" * 80)
    print("检查人像库缩略图状态")
    print("=" * 80)
    
    # 1. 检查数据库
    print("\n1. 检查数据库...")
    db_path = 'backend/cache/face_library.db'
    
    if not os.path.exists(db_path):
        print(f"   ❌ 数据库文件不存在: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM library_faces')
    count = cursor.fetchone()[0]
    print(f"   数据库中有 {count} 个人像记录")
    
    if count == 0:
        print("\n   ℹ️  数据库为空")
        print("   请通过前端上传图片并保存人像，然后再次运行此脚本")
        conn.close()
        return
    
    # 2. 检查所有记录的路径格式
    print(f"\n2. 检查路径格式（共 {count} 条记录）...")
    cursor.execute('SELECT id, name, thumbnail_path FROM library_faces ORDER BY created_at DESC')
    rows = cursor.fetchall()
    
    backslash_count = 0
    forward_slash_count = 0
    missing_file_count = 0
    
    for i, (face_id, name, thumbnail_path) in enumerate(rows, 1):
        print(f"\n   [{i}] {name}")
        print(f"       ID: {face_id[:8]}...")
        print(f"       路径: {thumbnail_path}")
        
        # 检查路径分隔符
        if '\\' in thumbnail_path:
            print(f"       ⚠️  使用反斜杠（Windows风格）")
            backslash_count += 1
        else:
            print(f"       ✅ 使用正斜杠（跨平台兼容）")
            forward_slash_count += 1
        
        # 检查文件是否存在
        if os.path.exists(thumbnail_path):
            file_size = os.path.getsize(thumbnail_path)
            print(f"       ✅ 文件存在 ({file_size} bytes)")
        else:
            print(f"       ❌ 文件不存在")
            missing_file_count += 1
            
            # 尝试查找可能的文件
            thumbnail_filename = os.path.basename(thumbnail_path)
            possible_paths = [
                f"backend/cache/thumbnails/{thumbnail_filename}",
                f"backend\\cache\\thumbnails\\{thumbnail_filename}"
            ]
            
            for possible_path in possible_paths:
                if os.path.exists(possible_path):
                    print(f"       💡 找到可能的文件: {possible_path}")
                    break
    
    conn.close()
    
    # 3. 统计摘要
    print("\n" + "=" * 80)
    print("统计摘要")
    print("=" * 80)
    print(f"总记录数: {count}")
    print(f"使用正斜杠: {forward_slash_count} ✅")
    print(f"使用反斜杠: {backslash_count} ⚠️")
    print(f"文件缺失: {missing_file_count} {'❌' if missing_file_count > 0 else '✅'}")
    
    # 4. 检查缩略图目录
    print("\n" + "=" * 80)
    print("缩略图目录状态")
    print("=" * 80)
    thumbnails_dir = "backend/cache/thumbnails"
    
    if not os.path.exists(thumbnails_dir):
        print(f"❌ 缩略图目录不存在: {thumbnails_dir}")
        return
    
    files = os.listdir(thumbnails_dir)
    print(f"目录中有 {len(files)} 个文件")
    
    if len(files) != count:
        print(f"⚠️  文件数量与数据库记录不匹配（数据库: {count}, 文件: {len(files)}）")
    else:
        print(f"✅ 文件数量与数据库记录匹配")
    
    # 5. 最终结论
    print("\n" + "=" * 80)
    print("验证结论")
    print("=" * 80)
    
    if forward_slash_count == count and missing_file_count == 0:
        print("✅ 所有检查通过！")
        print("   - 所有路径使用正斜杠格式")
        print("   - 所有缩略图文件存在")
        print("   - 修复成功！")
    elif backslash_count > 0:
        print("⚠️  发现使用反斜杠的路径")
        print("   这些可能是修复前保存的旧数据")
        print("   建议：删除这些记录并重新保存")
    elif missing_file_count > 0:
        print("❌ 发现缺失的缩略图文件")
        print("   可能的原因：")
        print("   1. 文件被意外删除")
        print("   2. 路径格式不匹配")
        print("   建议：删除这些记录并重新保存")
    else:
        print("✅ 路径格式正确，但请检查其他问题")
    
    print("=" * 80)

if __name__ == '__main__':
    check_current_state()

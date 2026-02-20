#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复所有未闭合的字符串"""

import re

# 读取文件
with open('tests/test_image_export_properties.py', 'r', encoding='utf-8', errors='replace') as f:
    lines = f.readlines()

# 修复未闭合的字符串
fixed_lines = []
for i, line in enumerate(lines):
    # 检查是否有未闭合的字符串
    if '"' in line and not line.rstrip().endswith('"') and not line.rstrip().endswith('"""'):
        # 检查是否是多行字符串的一部分
        if '"""' not in line and "'''" not in line:
            # 如果行以 f" 或 " 开始但没有闭合引号
            if (line.strip().startswith('f"') or line.strip().startswith('"')) and line.count('"') % 2 == 1:
                # 添加闭合引号
                line = line.rstrip() + '"\n'
                print(f"修复第 {i+1} 行: {line.strip()}")
    fixed_lines.append(line)

# 写回文件
with open('tests/test_image_export_properties.py', 'w', encoding='utf-8') as f:
    f.writelines(fixed_lines)

print("所有字符串已修复")

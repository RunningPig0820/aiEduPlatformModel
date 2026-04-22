#!/usr/bin/env python3
"""
修正教材 JSON 文件中章节嵌套错误的问题

问题：某些章节被错误地嵌套在其他章节的 sections 中
特征：section_name 以"数字."开头，如"3.1-5的认识和加减法"

修正策略：
1. 扫描所有章节的 sections
2. 识别以"数字."开头的 section_name（表示是独立章节）
3. 将其提取为独立章节
4. 使用 section_name 去掉编号部分作为章节名
5. 重新编排章节顺序
"""

import json
import os
import re
import shutil
from pathlib import Path


def extract_chapter_number(section_name: str) -> tuple[int, str]:
    """
    从 section_name 中提取章节编号和名称
    例如: "3.1-5的认识和加减法" -> (3, "1-5的认识和加减法")
    """
    match = re.match(r'^(\d+)\.(.+)$', section_name)
    if match:
        return int(match.group(1)), match.group(2)
    return None, section_name


def fix_textbook_json(filepath: str) -> bool:
    """
    修正单个教材 JSON 文件的章节结构
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    original_chapters = data.get('chapters', [])
    fixed_chapters = []
    extracted_count = 0

    for chapter in original_chapters:
        chapter_name = chapter.get('chapter_name', '')
        chapter_order = chapter.get('chapter_order', 0)
        sections = chapter.get('sections', [])

        # 检查是否有被错误嵌套的章节
        normal_sections = []
        extracted_chapters = []

        for section in sections:
            section_name = section.get('section_name', '')
            num, name = extract_chapter_number(section_name)

            if num is not None:
                # 这是一个被错误嵌套的章节，提取出来
                extracted_chapters.append({
                    'chapter_order': num,
                    'chapter_name': name,
                    'sections': [],
                    'extracted_knowledge_points': section.get('knowledge_points', [])
                })
                extracted_count += 1
            else:
                normal_sections.append(section)

        # 保留原章节（只包含正常 sections）
        if chapter_name != '总复习' or normal_sections:
            fixed_chapters.append({
                'chapter_order': chapter_order,
                'chapter_name': chapter_name,
                'sections': normal_sections
            })

        # 添加提取出的章节
        for ext_ch in extracted_chapters:
            fixed_chapters.append({
                'chapter_order': ext_ch['chapter_order'],
                'chapter_name': ext_ch['chapter_name'],
                'sections': [{
                    'section_order': 1,
                    'section_name': ext_ch['chapter_name'],
                    'knowledge_points': ext_ch['extracted_knowledge_points']
                }]
            })

    if extracted_count == 0:
        print(f"  {filepath}: 无需修正")
        return False

    # 按章节编号重新排序
    fixed_chapters.sort(key=lambda x: x['chapter_order'])

    # 重新分配章节编号（从1开始连续）
    for i, ch in enumerate(fixed_chapters, 1):
        ch['chapter_order'] = i

    # 更新数据
    data['chapters'] = fixed_chapters

    # 备份原文件
    backup_path = filepath + '.bak'
    shutil.copy(filepath, backup_path)

    # 写入修正后的数据
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"  {filepath}: 修正完成")
    print(f"    - 原章节数: {len(original_chapters)}")
    print(f"    - 提取嵌套章节: {extracted_count}")
    print(f"    - 修正后章节数: {len(fixed_chapters)}")
    print(f"    - 备份: {backup_path}")

    return True


def main():
    """修正所有教材 JSON 文件"""
    print("=== 教材 JSON 章节结构修正 ===\n")

    # 小学目录
    primary_dir = Path('edukg/data/textbook/math/renjiao/primary')
    fixed_files = []

    for grade_num in range(1, 7):
        grade_dir = primary_dir / f'grade{grade_num}'
        if not grade_dir.exists():
            continue

        for sem in ['shang', 'xia']:
            filepath = grade_dir / f'{sem}.json'
            if filepath.exists():
                if fix_textbook_json(str(filepath)):
                    fixed_files.append(str(filepath))

    # 初中目录
    middle_dir = Path('edukg/data/textbook/math/renjiao/middle')
    for grade_num in range(7, 10):
        grade_dir = middle_dir / f'grade{grade_num}'
        if not grade_dir.exists():
            continue

        for sem in ['shang', 'xia']:
            filepath = grade_dir / f'{sem}.json'
            if filepath.exists():
                if fix_textbook_json(str(filepath)):
                    fixed_files.append(str(filepath))

    # 高中目录
    high_dir = Path('edukg/data/textbook/math/renjiao/high')
    for bixiu in ['bixiu1', 'bixiu2', 'bixiu3']:
        filepath = high_dir / bixiu / 'textbook.json'
        if filepath.exists():
            if fix_textbook_json(str(filepath)):
                fixed_files.append(str(filepath))

    print(f"\n=== 修正完成 ===")
    print(f"共修正 {len(fixed_files)} 个文件")


if __name__ == '__main__':
    main()
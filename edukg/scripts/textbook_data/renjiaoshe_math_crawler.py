"""
人教版数学教材爬虫

从教师之家网站 (https://www.renjiaoshe.com/renjiaoshuxue/) 爬取人教版数学教材目录。

功能:
- 从入口页面解析小学、初中、高中三个学段的教材链接
- 提取章节目录和知识点列表
- 输出 JSON 和 TTL 格式数据
"""

import os
import json
import time
import logging
import re
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field, asdict
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ==================== 数据模型 ====================

@dataclass
class KnowledgePoint:
    """知识点"""
    name: str


@dataclass
class Section:
    """教材小节"""
    section_order: int
    section_name: str
    knowledge_points: List[str] = field(default_factory=list)


@dataclass
class Chapter:
    """教材章节"""
    chapter_order: int
    chapter_name: str
    sections: List[Section] = field(default_factory=list)


@dataclass
class Textbook:
    """教材数据"""
    subject: str = "math"
    textbook: str = "renjiao"
    stage: str = ""  # primary, middle, high
    grade: str = ""  # 一年级, 七年级, etc.
    semester: str = ""  # 上册, 下册
    publisher: str = "人民教育出版社"
    edition: str = "人教版"
    isbn: str = ""
    source_url: str = ""
    crawled_at: str = ""
    chapters: List[Chapter] = field(default_factory=list)


# ==================== 常量配置 ====================

ENTRY_URL = "https://www.renjiaoshe.com/renjiaoshuxue/"
BASE_URL = "https://www.renjiaoshe.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

REQUEST_TIMEOUT = 30
MAX_RETRIES = 3
RETRY_DELAY = 2


# ==================== 请求函数 ====================

def fetch_page(url: str, retry_count: int = 0) -> Optional[str]:
    """
    下载页面内容，支持重试机制

    Args:
        url: 页面 URL
        retry_count: 当前重试次数

    Returns:
        页面 HTML 内容，失败返回 None
    """
    try:
        logger.info(f"Fetching: {url} (retry: {retry_count})")
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()

        # 处理编码 - 教师之家使用 GB18030/GBK 编码
        # 优先使用 apparent_encoding，其次是 GBK
        content = response.content
        try:
            # 先尝试 apparent_encoding (通常为 GB18030)
            encoding = response.apparent_encoding or 'GB18030'
            content = content.decode(encoding, errors='ignore')
        except:
            # 备用：直接使用 GBK
            content = content.decode('gbk', errors='ignore')

        logger.info(f"Success: {url} ({len(content)} bytes, encoding: {encoding})")
        return content

    except requests.RequestException as e:
        logger.error(f"Failed: {url} - {e}")
        if retry_count < MAX_RETRIES:
            time.sleep(RETRY_DELAY)
            return fetch_page(url, retry_count + 1)
        return None


# ==================== 入口页面解析 ====================

def parse_entry_page(html: str) -> Dict[str, List[Dict]]:
    """
    解析入口页面，提取小学、初中、高中教材链接

    Args:
        html: 入口页面 HTML

    Returns:
        学段教材链接字典 {stage: [{name, url}, ...]}
    """
    soup = BeautifulSoup(html, 'lxml')
    result = {
        "primary": [],
        "middle": [],
        "high": []
    }

    # 查找教材目录区块
    # 通常包含标题如 "小学数学"、"初中数学"、"高中数学"
    content_divs = soup.find_all('div', class_='content') or \
                   soup.find_all('div', class_='book-list') or \
                   soup.find_all('div', class_='catalog')

    for div in content_divs:
        # 查找标题识别学段
        title_tag = div.find(['h2', 'h3', 'h4', 'strong']) or \
                    div.find_previous(['h2', 'h3', 'h4', 'strong'])

        if title_tag:
            title = title_tag.get_text(strip=True)
            stage = identify_stage(title)
            if stage:
                links = div.find_all('a')
                for link in links:
                    href = link.get('href', '')
                    name = link.get_text(strip=True)
                    if href and name:
                        full_url = href if href.startswith('http') else f"{BASE_URL}{href}"
                        result[stage].append({
                            "name": name,
                            "url": full_url
                        })

    # 如果上述方法失败，尝试直接查找所有链接
    if not any(result.values()):
        logger.warning("Primary parsing method failed, using fallback")
        result = fallback_parse_entry(soup)

    log_entry_result(result)
    return result


def identify_stage(title: str) -> Optional[str]:
    """根据标题识别学段"""
    title_lower = title.lower()

    # 先检查学段关键词
    if '小学' in title or 'primary' in title_lower:
        return 'primary'
    if '初中' in title or 'middle' in title_lower:
        return 'middle'
    if '高中' in title or 'high' in title_lower or '必修' in title or '选修' in title:
        return 'high'

    # 根据年级编号判断（一年级-六年级 = 小学，七年级-九年级 = 初中）
    grade_map = {
        '一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6,
        '七': 7, '八': 8, '九': 9
    }
    for char, num in grade_map.items():
        if char + '年级' in title:
            if num <= 6:
                return 'primary'
            else:
                return 'middle'

    return None


def fallback_parse_entry(soup: BeautifulSoup) -> Dict[str, List[Dict]]:
    """备用解析方法 - 直接查找所有教材链接"""
    result = {
        "primary": [],
        "middle": [],
        "high": []
    }

    # 查找所有包含 jiaocai 的链接（教材链接）
    all_links = soup.find_all('a')
    seen_urls = set()

    for link in all_links:
        href = link.get('href', '')
        name = link.get_text(strip=True)

        # 只处理教材链接
        if 'jiaocai' in href and '.html' in href:
            full_url = href if href.startswith('http') else f"{BASE_URL}{href}"

            # 避免重复链接
            if full_url in seen_urls:
                continue
            seen_urls.add(full_url)

            # 根据链接文本识别学段
            stage = identify_stage(name)
            if stage and name:
                result[stage].append({
                    "name": name,
                    "url": full_url
                })

    # 去重（同一链接可能有多个文本）
    for stage in result:
        unique = []
        seen = set()
        for item in result[stage]:
            if item['url'] not in seen:
                seen.add(item['url'])
                unique.append(item)
        result[stage] = unique

    return result


def log_entry_result(result: Dict[str, List[Dict]]):
    """记录入口页面解析结果"""
    for stage, links in result.items():
        logger.info(f"Found {stage}: {len(links)} textbooks")


# ==================== 教材页面解析 ====================

def parse_textbook_page(html: str, url: str, stage: str) -> Optional[Textbook]:
    """
    解析教材页面，提取章节目录和知识点

    Args:
        html: 教材页面 HTML
        url: 页面 URL
        stage: 学段

    Returns:
        Textbook 数据对象，失败返回 None
    """
    soup = BeautifulSoup(html, 'lxml')

    # 提取年级和学期信息
    grade, semester = extract_grade_semester(soup, url, stage)

    # 提取章节目录
    chapters = extract_chapters(soup)

    if not chapters:
        logger.warning(f"No chapters found for {url}")
        return None

    textbook = Textbook(
        stage=stage,
        grade=grade,
        semester=semester,
        source_url=url,
        crawled_at=datetime.now().isoformat(),
        chapters=chapters
    )

    logger.info(f"Parsed textbook: {grade}{semester} - {len(chapters)} chapters")
    return textbook


def extract_grade_semester(soup: BeautifulSoup, url: str, stage: str) -> Tuple[str, str]:
    """从页面或 URL 提取年级和学期信息"""
    grade = ""
    semester = ""

    # 从页面标题提取
    title = soup.find('title')
    if title:
        title_text = title.get_text(strip=True)
        grade, semester = parse_grade_semester_from_text(title_text, stage)

    # 如果标题解析失败，从 URL 提取
    if not grade:
        grade, semester = parse_grade_semester_from_url(url, stage)

    # 默认值
    if not grade:
        grade = "未知年级"
    if not semester:
        semester = "未知学期"

    return grade.strip(), semester.strip()


def parse_grade_semester_from_text(text: str, stage: str) -> Tuple[str, str]:
    """从文本解析年级和学期"""
    grade = ""
    semester = ""

    if stage == 'high':
        # 高中教材格式: "人教A版高中数学必修 第一册" 或 "选择性必修 第一册"
        if '选择性必修' in text:
            match = re.search(r'选择性必修\s*第?(一|二|三)册', text)
            if match:
                volume_map = {'一': '第一册', '二': '第二册', '三': '第三册'}
                grade = f"选择性必修{volume_map.get(match.group(1), match.group(1))}"
        elif '必修' in text:
            match = re.search(r'必修\s*第?(一|二|三|四|五)册', text)
            if match:
                volume_map = {'一': '第一册', '二': '第二册', '三': '第三册', '四': '第四册', '五': '第五册'}
                grade = f"必修{volume_map.get(match.group(1), match.group(1))}"
        elif '选修' in text:
            match = re.search(r'选修\s*[\d\-]+', text)
            if match:
                grade = match.group(0)
    else:
        # 小学/初中年级关键词映射
        grade_keywords = {
            'primary': ['一', '二', '三', '四', '五', '六'],
            'middle': ['七', '八', '九'],
        }

        keywords = grade_keywords.get(stage, [])

        for kw in keywords:
            if kw + '年级' in text or kw in text:
                grade = kw + "年级"
                break

        # 学期关键词
        if '上册' in text:
            semester = "上册"
        elif '下册' in text:
            semester = "下册"

    return grade.strip(), semester.strip()


def parse_grade_semester_from_url(url: str, stage: str) -> Tuple[str, str]:
    """从 URL 解析年级和学期"""
    grade = ""
    semester = ""

    # URL ID 映射 (根据已知规则)
    # 小学: ID 19-30, 初中: ID 31-36
    if '.html' in url:
        try:
            id_part = url.split('/')[-1].replace('.html', '')
            id_num = int(id_part)

            if 19 <= id_num <= 30:
                stage = 'primary'
                grade_num = (id_num - 19) // 2 + 1
                semester_num = (id_num - 19) % 2
                grade = f"{grade_num}年级"
                semester = "上册" if semester_num == 0 else "下册"
            elif 31 <= id_num <= 36:
                stage = 'middle'
                grade_num = (id_num - 31) // 2 + 7
                semester_num = (id_num - 31) % 2
                grade = f"{grade_num}年级"
                semester = "上册" if semester_num == 0 else "下册"
        except (ValueError, IndexError):
            pass

    return grade.strip(), semester.strip()


def extract_chapters(soup: BeautifulSoup) -> List[Chapter]:
    """提取章节目录 - 专门针对教师之家页面结构"""
    chapters = []

    # 查找课文目录列表 (kewen-ul 是教师之家特有的目录列表 class)
    kewen_ul = soup.find('ul', class_='kewen-ul')
    if kewen_ul:
        chapters = parse_kewen_ul(kewen_ul)
        if chapters:
            return chapters

    # 查找章节列表容器 (备用方法)
    chapter_list = soup.find('ul', class_='catalog-list') or \
                   soup.find('ul', class_='chapter-list') or \
                   soup.find('div', class_='chapter') or \
                   soup.find('div', class_='catalog')

    if not chapter_list:
        # 备用方法：查找所有 li 元素
        chapter_list = soup.find('ul')

    if chapter_list:
        chapter_items = chapter_list.find_all('li', recursive=False)
        for idx, item in enumerate(chapter_items, 1):
            chapter = parse_chapter_item(item, idx)
            if chapter:
                chapters.append(chapter)

    return chapters


def parse_kewen_ul(kewen_ul) -> List[Chapter]:
    """解析教师之家的 kewen-ul 目录结构

    目录结构有两种：

    1. 小学教材 (两级结构):
       - 1.准备课 (章节)
       - 数一数 (小节)
       - 比多少 (小节)

    2. 初中/高中教材 (三级结构):
       - 第一章 有理数 (一级章节)
       - 1.1 正数和负数 (二级小节)
       - 正数和负数的概念 (三级知识点)
    """
    chapters = []
    current_chapter = None
    current_section = None
    chapter_order = 0
    section_order = 0

    li_items = kewen_ul.find_all('li')
    for li in li_items:
        text = li.get_text(strip=True)
        if not text:
            continue

        # 判断层级
        is_chapter = check_is_chapter(text)
        is_subsection = check_is_subsection(text)

        if is_chapter:
            # 保存上一个章节
            if current_chapter:
                chapters.append(current_chapter)

            # 开始新章节
            chapter_order += 1
            section_order = 0
            current_section = None
            chapter_name = extract_chapter_name(text)

            current_chapter = Chapter(
                chapter_order=chapter_order,
                chapter_name=chapter_name,
                sections=[]
            )
        elif is_subsection:
            # 二级小节
            if current_chapter:
                section_order += 1
                current_section = Section(
                    section_order=section_order,
                    section_name=text,
                    knowledge_points=[]
                )
                current_chapter.sections.append(current_section)
        else:
            # 三级知识点或普通小节
            if current_section:
                # 添加到当前二级小节的知识点
                current_section.knowledge_points.append(text)
            elif current_chapter:
                # 没有二级小节，直接作为一级小节
                section_order += 1
                current_chapter.sections.append(Section(
                    section_order=section_order,
                    section_name=text,
                    knowledge_points=[]
                ))

    # 保存最后一个章节
    if current_chapter:
        chapters.append(current_chapter)

    return chapters


def check_is_chapter(text: str) -> bool:
    """检查是否为一级章节标题

    一级章节特征:
    1. "第N章" 格式 (中文数字或阿拉伯数字)
    2. "N." 或 "N、" 或 "N　" (数字开头+分隔符)
       - 但要排除 "N.N" 格式 (如 1.1, 2.3) 这是二级小节
    """
    # 1. "第N章" 格式
    if re.match(r'^第[一二三四五六七八九十\d]+章', text):
        return True

    # 2. "N." 或 "N、" 或 "N　" (数字+分隔符)
    # 但要排除 "N.N" 这种二级小节格式 (数字+点+数字)
    match = re.match(r'^(\d+)([.、\s　])(.+)$', text)
    if match:
        # 检查分隔符后面是否以数字开头 (如 "1.1", "2.3")
        rest = match.group(3)
        if not re.match(r'^\d+', rest):
            return True

    return False


def check_is_subsection(text: str) -> bool:
    """检查是否为二级小节标题 (N.N 格式)

    例如: "1.1 正数和负数", "2.3 有理数的加减法"
    """
    return bool(re.match(r'^\d+\.\d+\s*', text))


def extract_chapter_name(text: str) -> str:
    """从章节标题中提取章节名称

    输入: "1.准备课" 或 "第一章 有理数" 或 "1　数据收集整理"
    输出: "准备课" 或 "有理数" 或 "数据收集整理"
    """
    # 1. "第N章" 格式
    match = re.match(r'^第[一二三四五六七八九十\d]+章\s*(.+)$', text)
    if match:
        return match.group(1).strip()

    # 2. "N." 或 "N、" 或 "N　" 格式
    match = re.match(r'^\d+[.、\s　](.+)$', text)
    if match:
        return match.group(1).strip()

    return text


def parse_chapter_item(item, order: int) -> Optional[Chapter]:
    """解析单个章节项"""
    # 章节名称
    chapter_name = ""

    # 查找章节标题
    title_tag = item.find(['span', 'a', 'strong'])
    if title_tag:
        chapter_name = title_tag.get_text(strip=True)

    # 如果是 class="cut nourl" 的 li，通常是章节名
    if 'cut' in item.get('class', []) or 'nourl' in item.get('class', []):
        chapter_name = item.get_text(strip=True)

    if not chapter_name:
        chapter_name = item.get_text(strip=True)[:50]  # 截取前 50 字符

    # 提取小节
    sections = extract_sections(item, order)

    # 提取知识点（从小节或章节文本中）
    knowledge_points = extract_knowledge_points(item)

    return Chapter(
        chapter_order=order,
        chapter_name=chapter_name,
        sections=sections
    )


def extract_sections(item, chapter_order: int) -> List[Section]:
    """提取小节列表"""
    sections = []

    # 查找小节列表
    sub_list = item.find('ul') or item.find('div', class_='section-list')
    if sub_list:
        sub_items = sub_list.find_all('li')
        for idx, sub_item in enumerate(sub_items, 1):
            section_name = ""
            link = sub_item.find('a')
            if link:
                section_name = link.get_text(strip=True)
            else:
                section_name = sub_item.get_text(strip=True)

            if section_name:
                kps = extract_knowledge_points(sub_item)
                sections.append(Section(
                    section_order=idx,
                    section_name=section_name,
                    knowledge_points=kps
                ))

    return sections


def extract_knowledge_points(item) -> List[str]:
    """提取知识点列表"""
    knowledge_points = []

    # 查找知识点标签
    kp_tags = item.find_all('span', class_='kp') or \
              item.find_all('span', class_='knowledge') or \
              item.find_all('a', class_='kp-link')

    for tag in kp_tags:
        kp_name = tag.get_text(strip=True)
        if kp_name:
            knowledge_points.append(kp_name)

    # 如果没有专门的标签，尝试从文本中提取
    if not knowledge_points:
        text = item.get_text(strip=True)
        # 简单的关键词提取（可根据实际页面结构调整）
        # 例如：文本中包含"数数"、"一一对应"等

    return knowledge_points


# ==================== 数据输出 ====================

def save_textbook_json(textbook: Textbook, output_dir: Path):
    """保存单个教材 JSON 文件"""
    # 构建保存路径
    stage_dir = output_dir / textbook.stage

    # 年级目录名
    if textbook.stage == 'primary':
        grade_dir_name = f"grade{extract_grade_number(textbook.grade)}"
    elif textbook.stage == 'middle':
        grade_dir_name = f"grade{extract_grade_number(textbook.grade)}"
    else:
        grade_dir_name = normalize_high_grade(textbook.grade)

    grade_dir = stage_dir / grade_dir_name
    grade_dir.mkdir(parents=True, exist_ok=True)

    # 文件名
    semester_name = textbook.semester.replace('册', '')
    semester_pinyin = {'上': 'shang', '下': 'xia'}
    filename = f"{semester_pinyin.get(semester_name, semester_name)}.json" if textbook.stage != 'high' else "textbook.json"
    filepath = grade_dir / filename

    # 保存
    data = asdict(textbook)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    logger.info(f"Saved: {filepath}")
    return filepath


def extract_grade_number(grade: str) -> int:
    """从年级字符串提取数字"""
    grade_map = {
        '一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6,
        '七': 7, '八': 8, '九': 9
    }
    for char, num in grade_map.items():
        if char in grade:
            return num
    return 1


def normalize_high_grade(grade: str) -> str:
    """规范化高中年级目录名"""
    if '必修' in grade:
        if '第一' in grade or '一' in grade:
            return 'bixiu1'
        elif '第二' in grade or '二' in grade:
            return 'bixiu2'
        elif '第三' in grade or '三' in grade:
            return 'bixiu3'
        else:
            return 'bixiu'
    elif '选修' in grade:
        return 'xuanxiu'
    return 'high'


def save_stage_combined_json(textbooks: List[Textbook], stage: str, output_dir: Path):
    """保存学段合并 JSON 文件"""
    stage_dir = output_dir / stage
    filename = f"{stage}_textbook.json"
    filepath = stage_dir / filename

    combined_data = [asdict(tb) for tb in textbooks]
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(combined_data, f, ensure_ascii=False, indent=2)

    logger.info(f"Saved combined: {filepath}")
    return filepath


def save_ttl(all_textbooks: List[Textbook], output_dir: Path):
    """保存 TTL 格式文件"""
    filepath = output_dir / "k12_math_textbook.ttl"

    ttl_content = generate_ttl_content(all_textbooks)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(ttl_content)

    logger.info(f"Saved TTL: {filepath}")
    return filepath


def generate_ttl_content(textbooks: List[Textbook]) -> str:
    """生成 TTL 内容"""
    lines = [
        "@prefix ns1: <http://edukg.org/knowledge/3.0/ontology/data_property/main#> .",
        "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .",
        "@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .",
        "@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .",
        "",
    ]

    counter = 1
    for tb in textbooks:
        book_name = f"{tb.grade}{tb.semester}"

        for chapter in tb.chapters:
            for section in chapter.sections:
                for kp in section.knowledge_points:
                    uri = f"http://edukg.org/knowledge/3.0/instance/math#textbook-{tb.stage}-{counter:05d}"
                    mark = f"{chapter.chapter_order}.{section.section_order}"

                    temp_data = {
                        "book": book_name,
                        "chapter": chapter.chapter_name,
                        "section": section.section_name,
                        "mark": mark
                    }
                    temp_json = json.dumps(temp_data, ensure_ascii=False)

                    lines.append(f"<{uri}>")
                    lines.append(f"    a <http://edukg.org/knowledge/3.0/ontology/class/main#KnowledgePoint> ;")
                    lines.append(f"    rdfs:label \"{kp}\" ;")
                    lines.append(f"    ns1:temp '{temp_json}' .")
                    lines.append("")
                    counter += 1

    return "\n".join(lines)


# ==================== 进度记录 ====================

def load_progress(progress_file: Path) -> set:
    """加载已爬取的 URL 进度"""
    if progress_file.exists():
        with open(progress_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return set(data.get('completed_urls', []))
    return set()


def save_progress(progress_file: Path, completed_urls: set, failed_urls: List[Dict]):
    """保存爬取进度"""
    data = {
        'completed_urls': list(completed_urls),
        'failed_urls': failed_urls,
        'last_updated': datetime.now().isoformat()
    }
    with open(progress_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ==================== 主爬虫函数 ====================

def crawl_renjiaoshe_math(output_dir: Path, resume: bool = True):
    """
    爬取人教版数学教材目录

    Args:
        output_dir: 数据输出目录
        resume: 是否支持断点续爬
    """
    logger.info("=" * 50)
    logger.info("Starting Renjiaoshe Math Crawler")
    logger.info(f"Output directory: {output_dir}")
    logger.info("=" * 50)

    # 进度文件
    progress_file = output_dir / "progress.json"
    completed_urls = set()
    failed_urls = []
    all_textbooks = []

    if resume:
        completed_urls = load_progress(progress_file)
        logger.info(f"Resuming: {len(completed_urls)} URLs already completed")

    # 1. 获取入口页面
    logger.info("Step 1: Fetching entry page...")
    entry_html = fetch_page(ENTRY_URL)
    if not entry_html:
        logger.error("Failed to fetch entry page. Aborting.")
        return

    # 2. 解析入口页面
    logger.info("Step 2: Parsing entry page...")
    stage_links = parse_entry_page(entry_html)

    # 3. 爬取各学段教材
    for stage, textbooks_info in stage_links.items():
        if not textbooks_info:
            continue

        logger.info(f"Step 3: Crawling {stage} textbooks ({len(textbooks_info)} total)...")
        stage_textbooks = []

        for tb_info in textbooks_info:
            url = tb_info['url']
            name = tb_info['name']

            if url in completed_urls:
                logger.info(f"Skipping (already done): {name}")
                continue

            logger.info(f"Crawling: {name} -> {url}")

            html = fetch_page(url)
            if not html:
                failed_urls.append({
                    'url': url,
                    'name': name,
                    'error': 'Failed to fetch page'
                })
                continue

            textbook = parse_textbook_page(html, url, stage)
            if textbook:
                stage_textbooks.append(textbook)
                all_textbooks.append(textbook)
                completed_urls.add(url)

                # 保存单个教材文件
                save_textbook_json(textbook, output_dir)

                # 更新进度
                save_progress(progress_file, completed_urls, failed_urls)

            time.sleep(1)  # 请求间隔

        # 保存学段合并文件
        if stage_textbooks:
            save_stage_combined_json(stage_textbooks, stage, output_dir)

    # 4. 保存 TTL 文件
    logger.info("Step 4: Saving TTL file...")
    if all_textbooks:
        save_ttl(all_textbooks, output_dir)

    # 5. 创建 README
    logger.info("Step 5: Creating README...")
    create_readme(output_dir, all_textbooks, failed_urls)

    # 最终统计
    logger.info("=" * 50)
    logger.info("Crawl Complete!")
    logger.info(f"Total textbooks: {len(all_textbooks)}")
    logger.info(f"Failed URLs: {len(failed_urls)}")
    logger.info("=" * 50)

    # 清理进度文件（爬取完成后）
    if progress_file.exists():
        progress_file.unlink()


def create_readme(output_dir: Path, textbooks: List[Textbook], failed_urls: List[Dict]):
    """创建数据说明文档"""
    readme_path = output_dir / "README.md"

    content = f"""# 人教版数学教材目录数据

## 数据来源

- 网站: 教师之家 (https://www.renjiaoshe.com)
- 入口页面: https://www.renjiaoshe.com/renjiaoshuxue/
- 爬取时间: {datetime.now().isoformat()}

## 目录结构

```
textbook/math/renjiao/
├── primary/              # 小学数学
│   ├── grade1/           # 一年级
│   │   ├── shang.json    # 上册
│   │   └── xia.json      # 下册
│   ├── ...
│   ├── grade6/           # 六年级
│   └── primary_textbook.json  # 合并文件
├── middle/               # 初中数学
│   ├── grade7/           # 七年级
│   ├── ...
│   ├── grade9/           # 九年级
│   └── middle_textbook.json   # 合并文件
├── high/                 # 高中数学
│   ├── bixiu1/           # 必修第一册
│   ├── bixiu2/           # 必修第二册
│   ├── ...
│   └── high_textbook.json     # 合并文件
├── k12_math_textbook.ttl # TTL 格式 (兼容 EDUKG main.ttl)
└── README.md             # 本文档
```

## 数据格式

### JSON 格式

```json
{
  "subject": "math",
  "stage": "primary",
  "grade": "一年级",
  "semester": "上册",
  "publisher": "人民教育出版社",
  "edition": "人教版",
  "source_url": "...",
  "crawled_at": "...",
  "chapters": [
    {
      "chapter_order": 1,
      "chapter_name": "准备课",
      "sections": [
        {
          "section_order": 1,
          "section_name": "数一数",
          "knowledge_points": ["数数", "一一对应"]
        }
      ]
    }
  ]
}
```

### TTL 格式

与 EDUKG main.ttl 格式兼容，可使用 n10s 导入 Neo4j。

## 统计

- 小学数学: {len([t for t in textbooks if t.stage == 'primary'])} 册
- 初中数学: {len([t for t in textbooks if t.stage == 'middle'])} 册
- 高中数学: {len([t for t in textbooks if t.stage == 'high'])} 册
- 爬取失败: {len(failed_urls)} 个页面

## 使用方法

```python
from edukg.scripts.textbook_data.renjiaoshe_math_crawler import crawl_renjiaoshe_math
from pathlib import Path

output_dir = Path("edukg/data/textbook/math/renjiao")
crawl_renjiaoshe_math(output_dir)
```
"""

    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(content)

    logger.info(f"Created: {readme_path}")


# ==================== 命令行入口 ====================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="人教版数学教材爬虫")
    parser.add_argument(
        "--output",
        default="edukg/data/textbook/math/renjiao",
        help="数据输出目录"
    )
    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="不使用断点续爬（重新爬取）"
    )

    args = parser.parse_args()
    output_dir = Path(args.output)

    # 确保输出目录存在
    output_dir.mkdir(parents=True, exist_ok=True)

    crawl_renjiaoshe_math(output_dir, resume=not args.no_resume)
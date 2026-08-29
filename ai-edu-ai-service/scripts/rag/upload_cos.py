"""
阶段 2 COS 文档上传 - 源语料+切片视图 → COS 普通桶 ai-edu-1318177119

读取每个 .md 文件头的 `> COS路径:` 标注作为 COS key(文件头标注见 8e1f3dc),
用 CosS3Client.put_object 上传。key 规则见 向量桶入桶清单.md 7.2:
    rag-source/ai-tutoring/...  源语料
    rag-slices/ai-tutoring/...  切片视图
无 `> COS路径:` 头的 .md(设计文档/清单等)不上传, 自动跳过。

幂等: 同 key put_object 覆盖(内容即定稿); --skip-existing 跳过已存在对象(断点续传)。

用法: cd ai-edu-ai-service && python scripts/rag/upload_cos.py [--dry-run] [--skip-existing]
参数:
  --root         语料根目录(默认 settings.RAG_CORPUS_DIR, 绝对路径按仓库根解析)
  --dry-run      只预览不上传(列出待传文件+COS key)
  --skip-existing 已存在的对象跳过(不覆盖)
输入: docs/rag/<模块>/*.md(含 `> COS路径:` 头的文件)
输出: ai-edu-1318177119 普通桶(put_object, ContentType=text/markdown)
凭据: 复用 COS_VECTORS_SECRET_ID/KEY(2026-08-26 探针实测可写该普通桶)
对齐: 每模块流水线-tasks.md 1.10 U3 + 向量桶入桶清单.md 7.2/7.5
"""
import argparse
import logging
import os
import re
import sys
from typing import List, Optional, Tuple

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from config.settings import settings

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

BUCKET = os.environ.get("COS_OBJ_BUCKET", "ai-edu-1318177119")
REGION = os.environ.get("COS_OBJ_REGION", "ap-guangzhou")
HEADER_RE = re.compile(r"^\s*>\s*COS路径[:：]\s*(.+?)\s*$")
HEADER_SCAN_LINES = 20   # 文件头扫描行数(切片视图头 ~6 行)
MAX_KEY_BYTES = 850      # COS key 上限
CONTENT_TYPE = "text/markdown; charset=utf-8"


def _client():
    from qcloud_cos import CosConfig, CosS3Client
    config = CosConfig(Region=REGION, SecretId=settings.COS_VECTORS_SECRET_ID,
                       SecretKey=settings.COS_VECTORS_SECRET_KEY)
    return CosS3Client(config)


def parse_cos_key(md_text: str) -> Optional[str]:
    """从文件头取 `> COS路径:` 的值, 无则返回 None。"""
    for line in md_text.splitlines()[:HEADER_SCAN_LINES]:
        m = HEADER_RE.match(line)
        if m:
            return m.group(1).strip().lstrip("/")
    return None


EXCLUDE_DIR_PARTS = ("/处理方案/", "/原来的文件/", "/原来的文件")  # 提示词/原始素材不上传普通桶


def collect_files(root: str) -> Tuple[List[Tuple[str, str]], dict]:
    """遍历 root, 返回 (待传 [(本地路径, COS key)], 校验告警 dict)。"""
    items, warns = [], {}
    for dirpath, _, filenames in os.walk(root):
        for fn in sorted(filenames):
            if not fn.endswith(".md"):
                continue
            path = os.path.join(dirpath, fn)
            if any(x in path for x in EXCLUDE_DIR_PARTS):
                continue   # 处理方案(提示词)/原来的文件(原始素材)不上传普通桶
            try:
                text = open(path, encoding="utf-8").read()
            except OSError as e:
                warns[path] = f"读取失败: {e}"
                continue
            key = parse_cos_key(text)
            if key:
                items.append((path, key))
    return items, warns


def validate_keys(items: List[Tuple[str, str]]) -> List[Tuple[str, str, str]]:
    """返回 [(本地路径, key, 告警)]; 关键非法直接剔除(记录告警)。"""
    out, seen = [], {}
    for path, key in items:
        warn = ""
        if "\\" in key or key.startswith("/"):
            warn = "key 含非法字符(\\或前导/), 跳过"
        elif len(key.encode("utf-8")) > MAX_KEY_BYTES:
            warn = f"key {len(key.encode('utf-8'))}B 超 {MAX_KEY_BYTES}B 上限, 跳过"
        elif key in seen:
            warn = f"key 与 {seen[key]} 冲突(同一 key 多文件), 跳过"
        else:
            seen[key] = path
        out.append((path, key, warn))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="切片文档 → COS 普通桶上传")
    ap.add_argument("--root", default=settings.RAG_CORPUS_DIR,
                    help="语料根目录(默认 settings.RAG_CORPUS_DIR)")
    ap.add_argument("--dry-run", action="store_true", help="只预览不上传")
    ap.add_argument("--skip-existing", action="store_true", help="已存在的对象跳过")
    args = ap.parse_args()

    root = args.root
    if not os.path.isabs(root):
        root = os.path.abspath(os.path.join(
            os.path.dirname(__file__), "..", "..", "..", root))
    if not os.path.isdir(root):
        logger.error("语料根目录不存在: %s", root)
        return 1

    items, warns = collect_files(root)
    rows = validate_keys(items)
    pending = [(p, k) for p, k, w in rows if not w]
    for p, k, w in rows:
        if w:
            logger.warning("[跳过] %s → %s", p, w)

    logger.info("根目录: %s", root)
    logger.info("待传 %d 文件(%s)", len(pending), f"{len(items)} 带头, {len(pending)} 合法")

    if args.dry_run:
        for p, k in pending:
            print(f"  PUT {k}  ←  {os.path.relpath(p, root)}")
        print(f"\n[dry-run] 共 {len(pending)} 个待上传")
        return 0

    client = _client()
    uploaded, skipped, failed = 0, 0, 0
    for i, (p, k) in enumerate(pending, 1):
        if args.skip_existing:
            try:
                client.head_object(Bucket=BUCKET, Key=k)
                skipped += 1
                continue
            except Exception:
                pass  # 不存在, 继续上传
        try:
            with open(p, encoding="utf-8") as f:
                body = f.read().encode("utf-8")
            client.put_object(Bucket=BUCKET, Key=k, Body=body, ContentType=CONTENT_TYPE)
            uploaded += 1
        except Exception as e:
            failed += 1
            logger.error("[失败 %d/%d] %s → %s: %s", i, len(pending), k, p, str(e)[:200])
    logger.info("上传完成: 成功 %d, 跳过 %d, 失败 %d", uploaded, skipped, failed)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

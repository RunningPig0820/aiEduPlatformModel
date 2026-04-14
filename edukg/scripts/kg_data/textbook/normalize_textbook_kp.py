"""
批量标准化教材知识点名称

使用 LLM 将教材知识点名称推断为标准数学概念名称，
提高与 EduKG 知识图谱的匹配率。

流程：
教材知识点 → LLM标准化 → 向量检索 → LLM投票 → 匹配结果
"""

import asyncio
import json
import os
import sys
import time
import argparse
from pathlib import Path
from datetime import datetime

# 设置路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
KG_DATA_DIR = os.path.dirname(SCRIPT_DIR)
PROJECT_ROOT = os.path.abspath(os.path.join(KG_DATA_DIR, "..", "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# 加载环境变量
AI_SERVICE_DIR = os.path.join(PROJECT_ROOT, "ai-edu-ai-service")
if AI_SERVICE_DIR not in sys.path:
    sys.path.insert(0, str(AI_SERVICE_DIR))

os.chdir(AI_SERVICE_DIR)
from dotenv import load_dotenv
load_dotenv()

from edukg.core.textbook.kp_normalizer import KPNormalizer

# 数据目录
OUTPUT_BASE = os.path.join(PROJECT_ROOT, "edukg", "data", "edukg", "math", "5_教材目录(Textbook)", "output")
DATA_DIR = Path(OUTPUT_BASE)
CACHE_DIR = Path(os.path.join(OUTPUT_BASE, "normalizer_cache"))
PROGRESS_DIR = Path(os.path.join(OUTPUT_BASE, "progress"))

class NormalizationRunner:
    """标准化批量处理器（带进度显示）"""

    def __init__(self, concurrency: int = 5):
        self.normalizer = KPNormalizer(use_cache=True)
        self.concurrency = concurrency
        self.progress_file = PROGRESS_DIR / "normalize_kp.json"

    def load_knowledge_points(self) -> list:
        """加载教材知识点"""
        kps_file = DATA_DIR / "textbook_kps.json"
        with open(kps_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def load_progress(self) -> dict:
        """加载进度"""
        if self.progress_file.exists():
            with open(self.progress_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"processed": [], "total": 0, "start_time": None}

    def save_progress(self, progress: dict):
        """保存进度"""
        PROGRESS_DIR.mkdir(parents=True, exist_ok=True)
        with open(self.progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress, f, ensure_ascii=False, indent=2)

    def get_cached_count(self) -> int:
        """获取已缓存的数量"""
        if CACHE_DIR.exists():
            return len(list(CACHE_DIR.glob("*.json")))
        return 0

    async def normalize_with_progress(self, kp: dict, index: int, total: int, start_time: float, stats: dict):
        """标准化单个知识点（带进度显示）"""
        name = kp.get("label", "")
        stage = kp.get("stage", "")
        grade = kp.get("grade", "")

        # 执行标准化
        result = await self.normalizer.normalize(name, stage, grade)

        # 更新统计
        stats["completed"] += 1
        stats["total_time"] = time.time() - start_time

        # 计算剩余时间
        avg_time = stats["total_time"] / stats["completed"]
        remaining_count = total - stats["completed"]
        remaining_time = remaining_count * avg_time

        # 显示进度
        progress_pct = stats["completed"] / total * 100
        timestamp = datetime.now().strftime("%H:%M:%S")

        print(f"[{timestamp}] 进度: {stats['completed']}/{total} ({progress_pct:.1f}%)")
        print(f"  当前: {name} → {result.get('best_match', '')} (置信度: {result.get('confidence', 0)})")
        print(f"  耗时: {stats['total_time']:.1f}s, 剩余约: {remaining_time/60:.1f}分钟")

        # 每10个显示一次汇总
        if stats["completed"] % 10 == 0:
            print()
            print(f"=== 中间汇总 ===")
            print(f"已处理: {stats['completed']} 个")
            print(f"平均耗时: {avg_time:.1f}s/个")
            print(f"预计完成时间: {remaining_time/60:.1f}分钟后")
            print()

        return result

    async def run_batch(self, resume: bool = True):
        """批量标准化"""
        # 加载知识点
        kps = self.load_knowledge_points()
        total = len(kps)

        print("=== 知识点标准化批量处理 ===")
        print(f"知识点总数: {total}")
        print(f"并发数: {self.concurrency}")
        print()

        # 检查已有缓存（基于实际文件，不依赖进度 JSON）
        if CACHE_DIR.exists():
            cached_keys = set(f.stem for f in CACHE_DIR.glob("*.json"))
        else:
            cached_keys = set()

        # 找出已缓存的 KP 对应的 URI
        import hashlib
        cached_uris = set()
        for kp in kps:
            key_content = f"{kp.get('label', '')}_{kp.get('stage', '')}_{kp.get('grade', '')}"
            cache_key = hashlib.md5(key_content.encode()).hexdigest()
            if cache_key in cached_keys:
                cached_uris.add(kp.get("uri"))

        print(f"已有缓存: {len(cached_uris)} 个")

        if resume and len(cached_uris) > 0:
            print(f"断点续传模式: 将复用已有缓存")

        print()
        print("开始处理...")
        print("=" * 50)

        # 过滤已处理的（基于实际缓存文件）
        pending_kps = [kp for kp in kps if kp.get("uri") not in cached_uris]
        print(f"待处理: {len(pending_kps)} 个")
        print()

        if not pending_kps:
            print("所有知识点已处理完成！正在加载缓存结果...")
            # 全部已缓存，加载缓存结果并保存
            all_results = []
            for kp in kps:
                name = kp.get("label", "")
                stage = kp.get("stage", "")
                grade = kp.get("grade", "")
                cached_result = await self.normalizer.normalize(name, stage, grade)
                all_results.append(cached_result)
            output_file = DATA_DIR / "normalized_kps_complete.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(all_results, f, ensure_ascii=False, indent=2)
            print(f"结果保存: {output_file}")
            return

        # 统计
        stats = {
            "completed": 0,
            "total_time": 0,
            "start_time": time.time()
        }

        # 执行标准化（并发）
        results = []
        semaphore = asyncio.Semaphore(self.concurrency)

        async def process_with_semaphore(kp, index):
            async with semaphore:
                result = await self.normalize_with_progress(
                    kp, index, len(pending_kps),
                    stats["start_time"], stats
                )
                return result

        # 批量处理
        tasks = [
            process_with_semaphore(kp, i)
            for i, kp in enumerate(pending_kps, 1)
        ]

        results = await asyncio.gather(*tasks)

        # 加载已跳过（已缓存）的知识点结果，确保输出完整
        cached_results = []
        skipped_kps = [kp for kp in kps if kp.get("uri") in cached_uris]
        for kp in skipped_kps:
            name = kp.get("label", "")
            stage = kp.get("stage", "")
            grade = kp.get("grade", "")
            # 通过 normalizer 的 normalize 方法加载缓存结果（不会调用 LLM）
            cached_result = await self.normalizer.normalize(name, stage, grade)
            cached_results.append(cached_result)

        # 合并所有结果
        all_results = list(results) + cached_results

        # 完成
        total_time = time.time() - stats["start_time"]
        avg_time = total_time / len(pending_kps)

        print()
        print("=" * 50)
        print("=== 处理完成 ===")
        print(f"总知识点: {total}")
        print(f"本次处理: {len(pending_kps)}")
        print(f"总耗时: {total_time:.1f}s ({total_time/60:.1f}分钟)")
        print(f"平均耗时: {avg_time:.1f}s/个")
        print()
        print(f"缓存文件: {self.get_cached_count()} 个")

        # 保存结果
        output_file = DATA_DIR / "normalized_kps_complete.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)

        print(f"结果保存: {output_file}")

    def show_stats(self):
        """显示统计"""
        kps = self.load_knowledge_points()
        cached = self.get_cached_count()

        print("=== 标准化统计 ===")
        print(f"知识点总数: {len(kps)}")
        print(f"已缓存: {cached}")
        print(f"待处理: {len(kps) - cached}")
        print()

        if cached > 0:
            progress_pct = cached / len(kps) * 100
            print(f"进度: {progress_pct:.1f}%")

            # 时间估算
            avg_time = 3.0  # 基于测试结果
            remaining = len(kps) - cached
            print(f"预计剩余时间: ~{remaining * avg_time / 60:.0f}分钟（单线程）")
            print(f"预计剩余时间: ~{remaining * avg_time / 60 / self.concurrency:.0f}分钟（{self.concurrency}并发）")


async def main():
    parser = argparse.ArgumentParser(description="批量标准化教材知识点名称")
    parser.add_argument("--resume", action="store_true", help="断点续传")
    parser.add_argument("--stats", action="store_true", help="显示统计")
    parser.add_argument("--concurrency", type=int, default=5, help="并发数（默认5）")

    args = parser.parse_args()

    runner = NormalizationRunner(concurrency=args.concurrency)

    if args.stats:
        runner.show_stats()
    else:
        await runner.run_batch(resume=args.resume)


if __name__ == "__main__":
    asyncio.run(main())
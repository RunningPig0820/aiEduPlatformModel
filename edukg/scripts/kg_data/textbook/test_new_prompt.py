#!/usr/bin/env python3
"""Test new prompt against old decision=False samples"""
import asyncio, json, re, sys, os
from pathlib import Path

# Setup paths
SCRIPT_DIR = Path(__file__).resolve().parent
KG_DATA_DIR = SCRIPT_DIR.parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent.parent.parent
AI_SERVICE_DIR = PROJECT_ROOT / "ai-edu-ai-service"
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(AI_SERVICE_DIR))
os.chdir(str(AI_SERVICE_DIR))

from dotenv import load_dotenv
load_dotenv()

from edukg.core.llm_inference.dual_model_voter import DualModelVoter
from edukg.core.llm_inference.prompt_templates import format_kp_match_prompt

cache_dir = Path('/Users/minzhang/Documents/work/ai/aiEduPlatformModel/edukg/data/edukg/math/5_教材目录(Textbook)/output/llm_cache/')

# Collect samples
no_samples = []
for f in cache_dir.glob('*.json'):
    try:
        d = json.loads(f.read_text())
        prompt = d.get('prompt', '')
        if '教材知识点名称' not in prompt:
            continue
        result = d.get('result', {})
        if isinstance(result, dict) and result.get('result'):
            inner = result.get('result', {})
            if isinstance(inner, dict) and inner.get('decision') is False:
                tb_match = re.search(r'教材知识点名称[：:]\s*(.+?)\n', prompt)
                tb_desc = re.search(r'教材知识点描述[：:]\s*(.+?)\n', prompt)
                kg_match = re.search(r'知识图谱知识点名称[：:]\s*(.+?)\n', prompt)
                kg_desc = re.search(r'知识图谱知识点描述[：:]\s*(.+?)\n', prompt)
                if tb_match and kg_match:
                    no_samples.append({
                        'tb_name': tb_match.group(1).strip(),
                        'tb_desc': tb_desc.group(1).strip() if tb_desc else '无描述',
                        'kg_name': kg_match.group(1).strip(),
                        'kg_desc': kg_desc.group(1).strip() if kg_desc else '无描述',
                    })
                if len(no_samples) >= 20:
                    break
    except:
        pass

print(f'Testing {len(no_samples)} samples with new prompt...')

async def main():
    voter = DualModelVoter()

    yes_count = 0
    no_count = 0

    for i, s in enumerate(no_samples):
        new_prompt = format_kp_match_prompt(s['tb_name'], s['tb_desc'], s['kg_name'], s['kg_desc'])

        print(f'\n{i+1}. {s["tb_name"]} -> {s["kg_name"]}')

        result = await voter.vote(new_prompt)
        if result['consensus']:
            inner = result['result']
            decision = inner.get('decision', None)
            confidence = inner.get('confidence', 0)
            reason = inner.get('primary_reason', '')
            status = 'MATCH' if decision else 'NO'
            if decision:
                yes_count += 1
            else:
                no_count += 1
            print(f'   [{status}] conf={confidence} | {reason[:80]}')
        else:
            print(f'   [DISAGREE] {result.get("error", "")}')
            no_count += 1

    print(f'\n=== Results: {yes_count} MATCH, {no_count} NO out of {len(no_samples)} ===')
    print(f'Match rate: {yes_count/len(no_samples)*100:.1f}%')

asyncio.run(main())

#!/usr/bin/env python3
"""Which model is stricter? Analyze DISAGREE cases"""
import asyncio, json, re, sys, os
from pathlib import Path

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

async def main():
    voter = DualModelVoter()

    glm_strict = 0  # GLM says no, DeepSeek says yes
    ds_strict = 0   # DeepSeek says no, GLM says yes
    both_yes = 0
    both_no = 0

    for i, s in enumerate(no_samples):
        new_prompt = format_kp_match_prompt(s['tb_name'], s['tb_desc'], s['kg_name'], s['kg_desc'])
        result = await voter.vote(new_prompt)

        primary_resp = result.get('primary_response', {})
        secondary_resp = result.get('secondary_response', {})

        # Parse individual model decisions
        def parse_decision(resp):
            content = resp.get('content', '')
            parsed = voter._parse_json_response(content)
            if parsed:
                return parsed.get('decision', None)
            return None

        glm_dec = parse_decision(primary_resp)
        ds_dec = parse_decision(secondary_resp)

        label = "?"
        if glm_dec is False and ds_dec is True:
            glm_strict += 1
            label = "GLM严格"
        elif glm_dec is True and ds_dec is False:
            ds_strict += 1
            label = "DS严格"
        elif glm_dec is True and ds_dec is True:
            both_yes += 1
            label = "都匹配"
        elif glm_dec is False and ds_dec is False:
            both_no += 1
            label = "都不匹配"

        print(f'{i+1}. {s["tb_name"]} -> {s["kg_name"]}: GLM={glm_dec}, DS={ds_dec} [{label}]')

    print(f'\n=== Model Strictness Analysis ===')
    print(f'GLM stricter (GLM=no, DS=yes): {glm_strict}')
    print(f'DS stricter (GLM=yes, DS=no): {ds_strict}')
    print(f'Both YES: {both_yes}')
    print(f'Both NO: {both_no}')

    if glm_strict > ds_strict:
        print(f'\n结论: GLM 更严格（{glm_strict} vs {ds_strict}）')
    elif ds_strict > glm_strict:
        print(f'\n结论: DeepSeek 更严格（{ds_strict} vs {glm_strict}）')
    else:
        print(f'\n结论: 两个模型严格程度相当')

asyncio.run(main())

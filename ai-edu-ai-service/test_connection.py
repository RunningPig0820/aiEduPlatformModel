#!/usr/bin/env python
"""
LLM 连通性测试脚本

测试各个模型是否可以正常对话

用法:
    cd ai-edu-ai-service
    python test_connection.py
"""
import sys
import os

# 添加项目根目录到 path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from config.settings import settings
from core.gateway.factory import LLMFactory
from core.gateway.router import ModelRouter


def test_config():
    """测试配置是否正确加载"""
    print("=" * 50)
    print("1. 测试配置加载")
    print("=" * 50)

    print(f"ZHIPU_API_KEY: {'已配置 ✓' if settings.ZHIPU_API_KEY else '未配置 ✗'}")
    print(f"DEEPSEEK_API_KEY: {'已配置 ✓' if settings.DEEPSEEK_API_KEY else '未配置 ✗'}")
    print(f"BAILIAN_API_KEY: {'已配置 ✓' if settings.BAILIAN_API_KEY else '未配置 ✗'}")
    print(f"INTERNAL_TOKEN: {'已配置 ✓' if settings.INTERNAL_TOKEN else '未配置 ✗'}")
    print()


def test_zhipu():
    """测试智谱 AI"""
    print("=" * 50)
    print("2. 测试智谱 AI (glm-4-flash 免费)")
    print("=" * 50)

    if not settings.ZHIPU_API_KEY:
        print("跳过: ZHIPU_API_KEY 未配置")
        print()
        return

    try:
        from langchain_community.chat_models import ChatZhipuAI

        llm = ChatZhipuAI(
            model="glm-4-flash",
            zhipuai_api_key=settings.ZHIPU_API_KEY
        )

        print("发送测试消息: 你好，请用一句话介绍你自己")
        response = llm.invoke("你好，请用一句话介绍你自己")
        print(f"响应: {response.content}")
        print("智谱 AI 连通性测试成功 ✓")
    except Exception as e:
        print(f"智谱 AI 连通性测试失败: {e}")
    print()


def test_deepseek():
    """测试 DeepSeek"""
    print("=" * 50)
    print("3. 测试 DeepSeek (deepseek-chat)")
    print("=" * 50)

    if not settings.DEEPSEEK_API_KEY:
        print("跳过: DEEPSEEK_API_KEY 未配置")
        print()
        return

    try:
        from langchain_openai import ChatOpenAI

        llm = ChatOpenAI(
            model="deepseek-chat",
            openai_api_key=settings.DEEPSEEK_API_KEY,
            openai_api_base="https://api.deepseek.com/v1"
        )

        print("发送测试消息: 你好，请用一句话介绍你自己")
        response = llm.invoke("你好，请用一句话介绍你自己")
        print(f"响应: {response.content}")
        print("DeepSeek 连通性测试成功 ✓")
    except Exception as e:
        print(f"DeepSeek 连通性测试失败: {e}")
    print()


def test_bailian():
    """测试阿里百炼"""
    print("=" * 50)
    print("4. 测试阿里百炼 (qwen-turbo)")
    print("=" * 50)

    if not settings.BAILIAN_API_KEY:
        print("跳过: BAILIAN_API_KEY 未配置")
        print()
        return

    try:
        from langchain_openai import ChatOpenAI

        llm = ChatOpenAI(
            model="qwen-turbo",
            openai_api_key=settings.BAILIAN_API_KEY,
            openai_api_base="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )

        print("发送测试消息: 你好，请用一句话介绍你自己")
        response = llm.invoke("你好，请用一句话介绍你自己")
        print(f"响应: {response.content}")
        print("阿里百炼 连通性测试成功 ✓")
    except Exception as e:
        print(f"阿里百炼 连通性测试失败: {e}")
    print()


def test_router():
    """测试模型路由器"""
    print("=" * 50)
    print("5. 测试模型路由器")
    print("=" * 50)

    scenes = ["page_assistant", "homework_grading", "faq", "image_analysis"]

    for scene in scenes:
        provider, model = ModelRouter.get_model(scene)
        free = "免费 ✓" if ModelRouter.is_free_model(provider, model) else "付费"
        print(f"  {scene}: {provider}/{model} ({free})")

    print()


def test_factory():
    """测试 LLM Factory"""
    print("=" * 50)
    print("6. 测试 LLM Factory")
    print("=" * 50)

    print(f"支持的 Provider: {LLMFactory.list_providers()}")
    print(f"智谱默认模型: {LLMFactory.get_default_model('zhipu')}")
    print(f"DeepSeek默认模型: {LLMFactory.get_default_model('deepseek')}")
    print(f"百炼默认模型: {LLMFactory.get_default_model('bailian')}")
    print()


def main():
    """运行所有测试"""
    print("\n" + "=" * 50)
    print("LLM Gateway 连通性测试")
    print("=" * 50 + "\n")

    # 1. 测试配置
    test_config()

    # 2. 测试各个模型
    test_zhipu()
    test_deepseek()
    test_bailian()

    # 3. 测试路由器和工厂
    test_router()
    test_factory()

    print("=" * 50)
    print("测试完成!")
    print("=" * 50)


if __name__ == "__main__":
    main()
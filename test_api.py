import os
from typing import Optional

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from rag import get_embeddings


def mask_key(key: Optional[str]) -> str:
    """对密钥做脱敏显示，避免在终端直接打印完整值。"""
    if not key:
        return "<missing>"
    if len(key) <= 8:
        return "*" * len(key)
    return f"{key[:4]}...{key[-4:]}"


def test_chat_api():
    """测试 DeepSeek 聊天模型是否可用。"""
    print("Testing DeepSeek chat API...")
    print(f"OPENAI_API_KEY: {mask_key(os.getenv('OPENAI_API_KEY'))}")
    print(f"OPENAI_BASE_URL: {os.getenv('OPENAI_BASE_URL')}")

    llm = ChatOpenAI(
        openai_api_key=os.environ["OPENAI_API_KEY"],
        base_url=os.environ.get("OPENAI_BASE_URL"),
        model="deepseek-chat",
    )
    response = llm.invoke("请用一句中文回复：连接测试成功。")
    print("Chat API test succeeded.")
    print(f"Response: {response.content}")


def test_embedding_api():
    """测试阿里云 Embedding 接口是否可用。"""
    print("\nTesting embedding API...")
    print(f"EMBEDDING_API_KEY: {mask_key(os.getenv('EMBEDDING_API_KEY'))}")
    print(f"EMBEDDING_BASE_URL: {os.getenv('EMBEDDING_BASE_URL')}")
    print(f"EMBEDDING_MODEL: {os.getenv('EMBEDDING_MODEL')}")

    embeddings = get_embeddings()
    vector = embeddings.embed_query("这是一条用于测试 embedding 的文本。")
    print("Embedding API test succeeded.")
    print(f"Embedding dimension: {len(vector)}")


if __name__ == "__main__":
    load_dotenv(override=True)

    try:
        test_chat_api()
    except Exception as exc:
        print(f"Chat API test failed: {exc}")

    try:
        test_embedding_api()
    except Exception as exc:
        print(f"Embedding API test failed: {exc}")

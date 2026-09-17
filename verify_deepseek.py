from app.utils.llm import get_llm
from app.config import settings


def main():
    print(f"正在验证 DeepSeek 接口...")
    print(f"Base URL: {settings.deepseek_base_url}")
    print(f"Model: {settings.deepseek_model}")
    print(f"API Key: {settings.deepseek_api_key[:8]}...{settings.deepseek_api_key[-4:]}")
    print("-" * 50)

    llm = get_llm()

    try:
        response = llm.invoke("请用一句话介绍你自己。")
        print("接口调用成功！")
        print(f"模型回复: {response.content}")
        print("-" * 50)
        print("验证通过，DeepSeek 接口正常工作。")
    except Exception as e:
        print(f"接口调用失败！")
        print(f"错误类型: {type(e).__name__}")
        print(f"错误信息: {e}")


if __name__ == "__main__":
    main()

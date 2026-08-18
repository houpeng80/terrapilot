import os
import httpx

from dotenv import load_dotenv
from pydantic import BaseModel

from zai import ZhipuAiClient

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_openai.chat_models.base import BaseChatOpenAI
from langchain_deepseek import ChatDeepSeek

from backend.config.config import get_agent_config

load_dotenv(encoding="utf-8")

def create_model(model_type: str, code_generate: bool = False) -> BaseChatOpenAI | BaseModel:
    config = get_agent_config()
    common_params = {
        "temperature": config.temperature,
        "max_tokens": config.max_tokens,
        "timeout": config.timeout,
        "max_retries": config.model_max_retries,
        # "logprobs": True,
        # "top_logprobs": 5,
        "streaming": True,
    }
    if code_generate:
        common_params["max_tokens"] = config.code_generate_max_tokens

    # OpenAI
    if model_type == "openai":
        return ChatOpenAI(
            model=os.getenv("OPENAI_MODEL"),
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL"),
            **common_params
        )
    # xiaomi
    elif model_type == "xiaomi":
        return ChatOpenAI(
            model=os.getenv("XIAOMI_MODEL"),
            api_key=os.getenv("XIAOMI_API_KEY"),
            base_url=os.getenv("XIAOMI_OPENAI_BASE_URL"),
            # extra_body={"thinking": {"type": "enabled"}},
            **common_params
        )
    # Deepseek
    elif model_type == "deepseek":
        return ChatDeepSeek(
            model=os.getenv("DEEPSEEK_MODEL"),
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url=os.getenv("DEEPSEEK_BASE_URL"),
            extra_body={
                "enable_thinking": True,
                "return_reasoning": True,
            },

            **common_params
        )
    # GLM
    elif model_type == "glm":
        return ChatOpenAI(
            model=os.getenv("GLM_MODEL"),
            api_key=os.getenv("GLM_API_KEY"),
            base_url=os.getenv("GLM_BASE_URL"),
            # http_client=httpx.Client(verify=False),
            **common_params
        )
    # Qwen
    elif model_type == "qwen":
        return ChatOpenAI(
            model=os.getenv("QWEN_MODEL"),
            api_key=os.getenv("QWEN_API_KEY"),
            base_url=os.getenv("QWEN_BASE_URL"),
            extra_body={
                "enable_thinking": False,
                "return_reasoning": False,
            },
            # http_client=httpx.Client(verify=False),
            # http_socket_options=(),
            **common_params
        )
    # Qwen embedding
    elif model_type == "qwen_embedding":
        return OpenAIEmbeddings(
            model=os.getenv("QWEN_EMBEDDING_MODEL"),
            api_key=os.getenv("QWEN_EMBEDDING_API_KEY"),
            base_url=os.getenv("QWEN_EMBEDDING_BASE_URL"),
            check_embedding_ctx_length=False,
            dimensions=1024,
            chunk_size = 10
        )
    # doubao
    elif model_type == "doubao":
        return ChatOpenAI(
            model=os.getenv("ARK_MODEL"),
            api_key=os.getenv("ARK_API_KEY"),
            base_url=os.getenv("ARK_BASE_URL"),
            **common_params
        )
    else:
        raise ValueError(f"not supported model type：{config.model_type}")

model_cache: dict[str, BaseChatOpenAI | BaseModel] = {}

def get_model(model_type = get_agent_config().model_type, code_generate: bool = False) -> BaseChatOpenAI | BaseModel:
    global model_cache

    if hasattr(model_cache, model_type):
        return model_cache[model_type]

    model = create_model(model_type, code_generate)
    model_cache[f"{model_type}_{code_generate}"] = model

    return model

if __name__ == "__main__":
    model = get_model("qwen")
    res = model.invoke("你好啊")
    print(res)
    # import zai
    # print(zai.__version__)

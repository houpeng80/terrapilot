import tiktoken

def num_tokens_from_string(string: str, encoding_name: str = "cl100k_base") -> int:
    """精确计算 Token 数"""
    encoding = tiktoken.get_encoding(encoding_name)
    return len(encoding.encode(string))

# 使用示例
tokens = num_tokens_from_string("你好世界", "cl100k_base")
print(tokens)
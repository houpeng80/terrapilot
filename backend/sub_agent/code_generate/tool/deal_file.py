import asyncio
import os
import aiofiles

from langchain.tools import tool

@tool
def load_file(file_path: str) -> str:
    """从指定的路径加载 PDF 文件

    Args:
        file_path: 要加载的文件路径
    """

    return ""

@tool
def write_file(file_path: str, content: str):
    """将content写到指定路径的文件时触发

    Args:
        file_path: 要写入内容的文件路径
        content: 要写入的内容
    """
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    # try:
    #     with open(file_path, 'w', encoding='utf-8') as file:
    #         file.write(content)
    #     print(f"content已成功保存到 {file_path}")
    # except Exception as e:
    #     print(f"保存content到文件时出错: {e}")

    asyncio.run(async_write_to_file(file_path, content))

async def async_write_to_file(file_path, data):
    async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
        await f.write(data)


if __name__ == "__main__":
    # parser = argparse.ArgumentParser()
    # parser.add_argument("--url", required=True)
    # args = parser.parse_args()

    # file_path = "./huaweicloud/services/test.go"
    # lines = ['第一行', '第二行', '第三行']
    # os.makedirs(os.path.dirname(file_path), exist_ok=True)
    # try:
    #     with open(file_path, 'w', encoding='utf-8') as file:
    #         file.write(lines[0])
    #     print(f"字符串已成功保存到 {file_path}")
    # except Exception as e:
    #     print(f"保存文件时出错: {e}")

    # with open(file_path, 'w', encoding='utf-8') as f:
    #     f.write(lines[0])

    print(load_file)
    # print(write_pdf("D:\\服务文档\\数据库\\gaussdb.pdf"))
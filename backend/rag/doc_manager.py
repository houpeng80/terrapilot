import os

from dotenv import load_dotenv

from langchain_text_splitters import RecursiveCharacterTextSplitter, MarkdownHeaderTextSplitter
from langchain_core.documents import Document

from assistant.utils.github_utils import TERRAFORM_CODE_PATH

load_dotenv(encoding="utf-8")

resource_path = {
    "data_source": "docs/data-sources",
    "resource": "docs/resources",
}

def get_markdown_file_description(folder: str, file_name: str) -> str:
    with open(TERRAFORM_CODE_PATH / folder / file_name, "r", encoding="utf-8") as f:
        content = f.read()

    res = content.split("---")[-1].split("##")[0].strip()
    return res

def split_markdown_file(folder: str, file_name: str, resource_type: str) -> list[tuple[str, Document]]:
    with open(TERRAFORM_CODE_PATH / folder / file_name, "r", encoding="utf-8") as f:
        content = f.read()

    markdown_text_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=[
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
            ("####", "Header 4"),
        ],
        strip_headers=False  # True：移除正文里的标题，False：保留标题在文本中
    )

    split_documents = markdown_text_splitter.split_text(content)

    recursive_character_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    split_chunks = recursive_character_splitter.split_documents(split_documents)

    metadata = {
        "source": f"{folder}/{file_name}",
        "file_type": "md",
    }
    final_documents = []
    for chunk in split_chunks:
        # 合并：标题分割产生的标题meta + 文件公共meta
        merge_meta = { **chunk.metadata,  **metadata}
        new_doc = Document(
            page_content = chunk.page_content.strip(),
            metadata = merge_meta
        )
        final_documents.append(new_doc)
    return [(f"{resource_type}_{file_name}_{i}", final_documents[i]) for i in range(len(final_documents))]

def load_documents(service: str) -> list[tuple[str, Document]]:
    res = []
    for resource_type, folder in resource_path.items():
        folder_path = TERRAFORM_CODE_PATH / folder
        try:
            items = os.listdir(folder_path)
            for item in items:
                if item.startswith(service):
                    res = res + split_markdown_file(folder, item, resource_type)
        except FileNotFoundError:
            print("file not exists")
        except PermissionError:
            print("no permission of the directory")

    return res

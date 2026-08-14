import logging
import subprocess
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(encoding="utf-8")

logger = logging.getLogger(__name__)

TERRAFORM_CODE_BASE_PATH = Path(__file__).parents[3] / "huaweicloud_oncall_assistant_code"
TERRAFORM_CODE_PATH = TERRAFORM_CODE_BASE_PATH / "terraform-provider-huaweicloud"
HUAWEI_CLOUD_TERRAFORM_PROVIDER_GITHUB = "https://github.com/huaweicloud/terraform-provider-huaweicloud.git"

def run_git_cmd(args: list[str], cwd: str = None) -> tuple[int, str, str]:
    """
    执行 git 命令
    :param args: git 参数列表，如 ["clone", "xxx.git"]
    :param cwd: 执行目录，None=当前目录
    :return: (返回码, stdout标准输出, stderr错误输出)
    """
    TERRAFORM_CODE_PATH.mkdir(parents=True, exist_ok=True)
    cmd = ["git"] + args
    # Windows 隐藏弹窗：creationflags=subprocess.CREATE_NO_WINDOW
    proc = subprocess.Popen(
        cmd,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        # creationflags=subprocess.CREATE_NO_WINDOW
    )
    out, err = proc.communicate()
    return proc.returncode, out, err

def test_code_exists() -> bool:
    code, out, err = run_git_cmd(["branch"], cwd=TERRAFORM_CODE_PATH)
    if code == 0:
        logger.info("code exists")
        return True

    logger.info("code not exists")
    return False

def clone_code():
    code, out, err = run_git_cmd(["clone", HUAWEI_CLOUD_TERRAFORM_PROVIDER_GITHUB], cwd=TERRAFORM_CODE_BASE_PATH)
    if code == 0:
        logger.info("clone code success")
    else:
        logger.info("clone code fail: %s", err)
        raise Exception(f"clone code fail: {err}")

def pull_code():
    code, out, err = run_git_cmd(["pull", "origin", "master"], cwd=TERRAFORM_CODE_PATH)
    if code == 0:
        logger.info("pull code success")
    else:
        logger.info("pull code fail: %s", err)
        raise Exception(f"pull code fail: {err}")

def checkout_code(version:str):
    code, out, err = run_git_cmd(["checkout", version], cwd=TERRAFORM_CODE_PATH)
    if code == 0:
        logger.info("checkout code success")
    else:
        logger.info("checkout code fail: %s", err)
        raise Exception(f"checkout code fail: {err}")

def get_latest_version() -> str:
    code, out, err = run_git_cmd(["describe", "--tags", "--abbrev=0"], cwd=TERRAFORM_CODE_PATH)
    if code == 0:
        logger.info("get latest version success")
        return out.strip()
    else:
        logger.info("get latest version fail: %s", err)
        raise Exception(f"get latest version fail: {err}")

def list_file(dir_path:str) -> list[str]:
    code, out, err = run_git_cmd(["ls-files", dir_path], cwd=TERRAFORM_CODE_PATH)
    if code == 0:
        logger.info("list the dir files success")
        fileList = out.split("\n")
        res = [file.removeprefix(dir_path) for file in fileList]
        return res
    else:
        logger.info("list the dir files fail: %s", err)
        raise Exception(f"list the dir files fail: {err}")

def search_resource_by_name(resource_type: str, service_name: str, resource_name: str) -> bool:
    service_dir = f"huaweicloud/services/{service_name}/"
    file_list = list_file(service_dir)
    if f"{resource_type}_{resource_name}.go" in file_list:
        return True

    return False

def search_resource_by_key_word(key_word: str, search_path: str) -> list[str]:
    code, out, err = run_git_cmd(["grep", "-i", "-r", key_word, search_path], cwd=TERRAFORM_CODE_PATH)
    if code == 0:
        logger.info("search %s from the %s success", key_word, search_path)
        fileList = out.split("\n")
        # 返回格式
        res = [file.split(":")[0].removeprefix(f"{search_path}/").removesuffix(".go") for file in fileList]
        return res
    else:
        logger.info("search %s from the %s fail", key_word, search_path)
        return []

if "__main__" == __name__:
    print(TERRAFORM_CODE_BASE_PATH)

    # if not test_code_exists():
    #     clone_code()

    # print("==================")
    # print(get_latest_version().strip())
    # print("==================")

    # pull_code()

    # out = list_file("huaweicloud/services/gaussdb/")
    # print("==================list_file==============================")
    # print(type(out))
    # print(out)
    # print("====================list_file============================")

    # out = search_resource_by_key_word("// @API LTS POST /v3/{project_id}/lts/access-config-list","huaweicloud/services/lts")
    out = search_resource_by_key_word("// @API GaussDB POST /gaussdb/v3.1/{project_id}/instances/db-upgrade/candidate-versions","huaweicloud/services/gaussdb")
    print("====================search_from_code============================")
    print(type(out))
    print(f"out={out}")
    print("===================search_from_code=============================")
    #
    # checkout_code("v1.93.0")
    #
    # out =  list_file("huaweicloud/services/gaussdb/")
    # print("==================list_file==============================")
    # print(out)
    # print("====================list_file============================")
    #
    # out = search_from_code("/v3/{project_id}/instances/{instance_id}/transactions/list","huaweicloud/services/gaussdb")
    # print("====================search_from_code============================")
    # print(f"out={out}")
    # print("===================search_from_code=============================")
    #
    # checkout_code("master")
    #
    # out = list_file("huaweicloud/services/gaussdb/")
    # print("==================list_file==============================")
    # print(out)
    # print("====================list_file============================")
    #
    # out = search_from_code("/v3/{project_id}/instances/{instance_id}/transactions/list","huaweicloud/services/gaussdb")
    # print("====================search_from_code============================")
    # print(f"out={out}")
    # print("===================search_from_code=============================")

# python: 3.12

# es+kibana下载：https://www.elastic.co/downloads/past-releases
    windwos环境：
        es配置：
            1. network.host: 0.0.0.0

# analysis-ik分词器下载：https://release.infinilabs.com/analysis-ik/stable/ ， 下载后放到es安装目录下的plugins目录下

# reranker-model下载，下载后放到当前project根目录下：
    ```python
    from modelscope import snapshot_download
    
    model_dir = snapshot_download("AI-ModelScope/bge-reranker-v2-m3", cache_dir="./")
    ```

# 常见问题：
    
## chroma查询时报错：TypeError: _TypedDictMeta.__new__() got an unexpected keyword argument 'extra_items'
    解决办法： pip install --upgrade typing_extensions

## CrossEncoder 坚决不能定义为全局，每次重排新建、用完销毁，否则第二次必崩

# conda 修改包安装位置（默认在C盘）

## 打开终端（Windows 用 Anaconda Prompt，Linux/macOS 用系统终端），执行以下命令，查看当前的虚拟环境路径和包缓存路径：

## 查看虚拟环境默认路径
    conda config --show envs_dirs
## 查看安装包缓存默认路径
    conda config --show pkgs_dirs
## 添加新的虚拟环境路径（优先级1，最优先使用）
    conda config --add envs_dirs D:\CondaConfig\envs
## （可选）添加备用路径（优先级2，若优先级1路径不可用则用此路径）
    conda config --add envs_dirs D:\Backup\CondaEnvs
## 添加新的包缓存路径（优先级1）
    conda config --add pkgs_dirs D:\CondaConfig\pkgs
## （可选）添加备用包缓存路径（优先级2）
    conda config --add pkgs_dirs D:\Backup\CondaPkgs




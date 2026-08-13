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

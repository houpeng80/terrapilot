# 记忆系统设计：

## prompt
    MEMORY_EXTRACTION_PROMPT = """ 
    你是一个记忆提取助手。请从以下对话中提取值得长期记忆的信息。  
    
    只提取以下类型的信息： 
    1. 用户明确表达的偏好（如风险偏好、产品偏好） 
    2. 用户的基本信息（企业规模、行业、注册地等） 
    3. 用户的重要决策或需求变化 
    4. 对未来咨询有参考价值的关键事件  
    
    不要提取：普通的问答内容、系统的标准回复、临时性的闲聊 
    
    对话内容： {conversation}  请以JSON格式输出，
    
    每条记忆包含：content（内容）、memory_type（episodic/semantic） """  

```python
class ShortTermMemory:     
    def __init__(self, window_size: int = 10):         
        self.window_size = window_size         
        self.messages = []     
    
    def add_message(self, role: str, content: str):         
        self.messages.append({"role": role, "context": content})         
        # 超出窗口大小则移除最早的消息         
        if len(self.messages) > self.window_size * 2:  
            # 每轮包含user+assistant两条             
            self.messages = self.messages[-self.window_size * 2:]      
            
    def get_context(self) -> list:         
        return self.messages
    
```

# 记忆难点，是更新还是保留？（e.g. 用户上周说有两个孩子，这周说有三个孩子，怎么处理？）

## 方案一：语义去重判断

    用 LLM 比较新旧信息的语义相似度，相似度超过阈值则判断为同一实体的更新：

```python
async def check_memory_conflict(     
        new_memory: str,     
        existing_memories: list,     
        similarity_threshold: float = 0.85 ) -> dict:     
    """     检查新记忆是否与现有记忆冲突     
    返回：{"action": "ADD/UPDATE", "conflict_memory_id": str or None}     
    """     
    if not existing_memories:         
        return {"action": "ADD", "conflict_memory_id": None}      
    # 对每条现有记忆计算语义相似度     
    new_embedding = await embedder.aembed_query(new_memory)      
    for mem in existing_memories:         
        similarity = cosine_similarity(new_embedding, mem["embedding"])          
        if similarity > similarity_threshold:             
            # 相似度高，判断为同一实体——需要更新而不是追加             
            # 进一步用LLM确认是否真的是更新             
            is_update = await llm_confirm_update(new_memory, mem["context"])             
            if is_update:                 
                return {"action": "UPDATE", "conflict_memory_id": mem["memory_id"]}   
            
        return {"action": "ADD", "conflict_memory_id": None}
```

## 方案二：记忆过期与 TTL 管理

    有些记忆天然有时效性，过了有效期就应该删除而不是保留。
    e.g. "用户本月预算是 5 万"这类信息，30 天后就过期了，继续保留反而会干扰后续回答。TTL 机制让系统自动完成清理，不需要人工干预。

```python
# 写入带TTL的记忆
def add_memory_with_ttl(     
        content: str,     
        user_id: str,     
        ttl_days: int = -1  # -1表示永久，>0表示有效天数 
):     
    ttl_timestamp = -1     
    if ttl_days > 0:         
        ttl_timestamp = int(time.time()) + ttl_days * 86400      
        memory_record = {         
            "memory_id": str(uuid.uuid4()),         
            "user_id": user_id,         
            "context": content,         
            "created_at": int(time.time()),         
            "ttl": ttl_timestamp,         
            "is_deleted": False     
        }     
        milvus_client.insert("agent_memory", memory_record)  
        # 示例：本月预算信息，有效期30天 
        # add_memory_with_ttl(context="用户本月可用于理财的预算为5万元", user_id="user_001", ttl_days=30 )  
        
        # 定时清理任务（每天运行） 
        async def cleanup_expired_memories():     
            current_time = int(time.time())     
            expired = milvus_client.query(         
                collection_name="agent_memory",         
                filter=f"ttl > 0 && ttl < {current_time} && is_deleted == false"     
            )    
            for mem in expired:         
                milvus_client.update(             
                    collection_name="agent_memory",             
                    filter=f"memory_id == '{mem['memory_id']}'",             
                    data={"is_deleted": True}         
                )

```

## 方案三：隐私合规与"被遗忘权"



# 记忆检索：如何把记忆注入 Prompt

## 记忆存好了，每次对话开始时怎么用？

```python
async def retrieve_memory(query: str, user_id: str) -> str:
    """     检索与当前问题相关的历史记忆，返回格式化的Prompt片段     """     
    # 第一步：向量检索用户相关记忆（先过滤user_id，再做语义检索）     
    relevant_memories = memory.search(         
       query=query,         
       user_id=user_id,         
       limit=5     
    )      
    if not relevant_memories:         
         return ""     
    # 第二步：格式化为Prompt片段     
    memory_context = "\n".join([f"- {m['memory']} (记录于{m['created_at']})" for m in relevant_memories ])    
    
    return f""" 【用户历史信息】 以下是该用户的历史偏好和关键信息，请在回答时参考： {memory_context} """  
    
    # 在对话流程中注入 
async def chat(user_message: str, user_id: str, session_id: str):     
    # 检索相关记忆     
    memory_context = await retrieve_memory(user_message, user_id)      
    # 构建完整的系统Prompt     
    system_prompt = BASE_SYSTEM_PROMPT     
    if memory_context:         
        system_prompt += "\n\n" + memory_context      
        # 调用LLM     
        response = await llm.ainvoke(         
            messages=[             
                {"role": "system", "context": system_prompt},             
                *short_term_memory.get_context(),             
                {"role": "user", "context": user_message}         
            ]     
        )      
        # 更新短期记忆     
        short_term_memory.add_message("user", user_message)     
        short_term_memory.add_message("assistant", response.content)      
    return response.content

```

    注意：
    第一，检索时一定要先按 user_id 过滤，再做向量相似度计算，不能把所有用户的记忆混在一起检索。不然不同用户的信息会相互污染，也是严重的隐私问题。
    
    第二，limit=5 不是固定值，要根据 Prompt 长度预算来决定。如果上下文窗口紧张，可以减少到 3 条；如果问题复杂、需要更多背景信息，可以增加到 8 条。
    
    第三，检索到的记忆要带上时间戳，让 LLM 知道这条信息是什么时候记录的，方便它判断信息的时效性。
    
    把定义、写入、管理、检索这四个环节串起来，就得到了一套完整的记忆管理闭环，下面用一个统一的流程图把它梳理清楚。


    短期记忆+长期记忆双层架构设计：

        第一步：Define（定义）
        
            明确哪些信息值得记忆。不是所有对话内容都有保存价值，要聚焦在：
            
            用户明确表达的偏好（风险偏好、产品偏好、服务偏好）
            用户的基本信息（企业规模、行业、注册地）
            用户的重要决策和关键事件
            对后续服务有实质参考价值的信息
            "今天天气真好"不值得记忆，"我们公司明年计划做出口业务"值得记忆。
        
        第二步：Write（写入）
        
            用 LLM 从对话中提取记忆点，按类型分类后写入对应的存储：
            
                情节记忆：写入向量数据库，绑定 user_id
                语义记忆：写入共享知识库
                程序性记忆：更新系统 Prompt 配置

        第三步：Manage（管理）
        
            写入前做冲突检测，决定 ADD/UPDATE/DELETE/NOOP 操作：
            
            语义相似度 > 0.85 且内容有变化：UPDATE
            新信息表明旧记忆已失效：DELETE
            新信息之前没有类似记录：ADD
            新信息与现有记忆一致：NOOP

        第四步：Read（读取）
        
            每次对话开始时（真的需要每一次都调用吗？）：
            
            先检索长期记忆，取相关度最高的 5 条
            格式化后注入系统 Prompt
            拼接短期记忆（最近 N 轮对话）
            发送给 LLM 生成回答
            
        这四步构成一个闭环，每次对话既消费记忆，又产生新的记忆。


# 总结
    Agent Memory 系统的设计，可以用三个维度来概括：
    
        第一个维度是分类——区分语义记忆、情节记忆、程序性记忆，对应不同的存储位置和检索策略；
        
        第二个维度是架构——短期记忆用滑动窗口管理当前对话，长期记忆用向量数据库按用户 ID 分区存储；
        
        第三个维度是管理——写入时做冲突检测（ADD/UPDATE/DELETE/NOOP），过期信息用 TTL 自动清理，用户注销时软删除保留审计。

# 最佳实践：

    短期记忆限制长度，防止上下文溢出
    长期记忆定期巩固，删除低价值内容
    使用向量检索，实现语义级别的相关性匹配
    实现遗忘机制，避免存储无意义信息


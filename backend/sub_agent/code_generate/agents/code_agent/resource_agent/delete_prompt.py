from backend.sub_agent.code_generate.agents.code_agent.resource_agent.utils import build_skills

UNSUBSCRIBE_ONLY_STEP = """
1. 生成删除资源的函数
   - 生成一个删除资源的函数，格式为`resource{XXX}Delete`，其中 `{XXX}` 为该资源的功能信息，例如：`resourceInstanceDelete`
   - 该函数总共包含：函数名称、参数定义、创建client、退订资源
   
   ```go
   func resourceInstanceDelete(_ context.Context, d *schema.ResourceData, meta interface{}) diag.Diagnostics {
   	   // 参数定义
      
   	   // 创建client
   	   
   	   // 退订资源
   	   
   	   return nil
   }
   ```
2. 参数定义，创建client
   - 创建退订资源的client，变量名为`bssClient`
   ```go
   cfg := meta.(*config.Config)
   region := cfg.GetRegion(d)
   
   bssClient, err := cfg.BssV2Client(region)
   if err != nil {
   	  return diag.Errorf("error creating bss V2 client: %s", err)
   }
   ```
3. 退订资源
   - 判断 `charging_mode` 参数是否设置，如果设置了就判断是否为`prePaid`，如果是就使用`common.UnsubscribePrePaidResource`去退订资源
   
   ```go
   if v, ok := d.GetOk("charging_mode"); ok && v.(string) == "prePaid" {
   	  if err = common.UnsubscribePrePaidResource(d, cfg, []string{d.Id()}); err != nil {
   	  	 return diag.Errorf("error unsubscribe RDS instance: %s", err)
   	  }
   }
   ```
4. 添加注释
   - 在`resource函数`前边加一个注释（示例中的`使用到的API`位置）：`@API BSS POST /v2/orders/subscriptions/resources/unsubscribe`

"""

DELETE_ONLY_STEP = """
1. 根据用户提供的删除资源API，获取API信息
2. 添加注释
   - 在`resource函数`前边加一个注释（示例中的`使用到的API`位置），格式为`// @API {service} {method} {path}`，其中`{service}`为当前服务名，`{method}`为URI中的请求方法，`{path}`为URI中的请求path
3. 生成删除资源函数
   - 生成一个删除资源的函数，格式为`resource{XXX}Delete`，其中 `{XXX}` 为该资源的功能信息，例如：`resourceInstanceDelete`
   ```go
   func resourcePublicationDelete(_ context.Context, _ *schema.ResourceData, _ interface{}) diag.Diagnostics {
   	   // 参数定义
      
   	   // 创建client
      
       // 构造请求参数和请求体
   	
   	   // 发送请求
   	   
   	   // 解析结果
   	   
   	   // 等待任务
   }
   ```
4. 参数定义，创建client
   - 创建client时，其中第一个参数为服务类型，错误信息中的服务类型需要大写
   ```go
   cfg := meta.(*config.Config)
   region := cfg.GetRegion(d)
   var (
   	  httpUrl = "v3/{project_id}/instances/{instance_id}/replication/publications"
   	  product = "rds"
   )
   
   client, err := cfg.NewServiceClient(product, region)
   if err != nil {
   	  return diag.Errorf("error creating RDS client: %s", err)
   }
   ```
5. 构造请求参数和请求体
   - 将path参数替换为具体的值，禁止使用`utils.ReplacePathVariables`，使用`strings.ReplaceAll`
   - 首先需要构造请求体，函数名为 `buildDelete{XXX}BodyParams`， 其中 `{XXX}` 为该资源的功能信息
   ```go
   deletePath := client.Endpoint + httpUrl
   deletePath = strings.ReplaceAll(deletePath, "{project_id}", client.ProjectID)
   deletePath = strings.ReplaceAll(deletePath, "{instance_id}", d.Id())
   
   deleteOpt := golangsdk.RequestOpts{
   	  KeepResponseBody: true,
   	  MoreHeaders: map[string]string{"Content-Type": "application/json"},
   }
   deleteOpt.JSONBody = utils.RemoveNil(buildDeleteInstanceBodyParams(d))
   ```
6 发送请求、解析结果
   1. 如果API响应消息为空，就不需要处理返回结果
      ```go
      _, err = client.Request("DELETE", deletePath, &deleteOpt)
      if err != nil {
         return diag.Errorf("error deleting RDS instance: %s", err)
      }
      ```
   2. 如果API响应消息不为空，获取删除结果，然后使用`utils.FlattenResponse`去解析
      ```go
      deleteResp, err := client.Request("DELETE", deletePath, &deleteOpt)
      if err != nil {
        return diag.Errorf("error deleting RDS instance: %s", err)
      }
      
      deleteRespBody, err := utils.FlattenResponse(deleteResp)
      if err != nil {
        return diag.FromErr(err)
      }
      ```
7. 等待任务
   - 从API响应消息中获取任务ID信息，如果存在，那么就等待任务的完成
   - 函数名为 `check{XXX}JobFinish`， 其中 `{XXX}` 为该资源的功能信息
   ```go
   jobId := utils.PathSearch("job_id", deleteRespBody, "").(string)
   if jobId != "" {
   	  if err = checkInstanceJobFinish(client, jobId, d.Timeout(schema.TimeoutUpdate)); err != nil {
   	  	 return diag.Errorf("error deleting instance: %s", err)
   	  }
   }
   ```
"""

DELETE_AND_UNSUBSCRIBE_STEP = """
1. 根据用户提供的删除资源API，获取API信息
2. 添加注释
   - 在`resource函数`前边加一个注释（示例中的`使用到的API`位置）：`@API BSS POST /v2/orders/subscriptions/resources/unsubscribe`
   - 在`resource函数`前边加一个注释（示例中的`使用到的API`位置），格式为`// @API {service} {method} {path}`，其中`{service}`为当前服务名，`{method}`为URI中的请求方法，`{path}`为URI中的请求path
3. 生成删除资源函数
   - 生成一个删除资源的函数，格式为`resource{XXX}Delete`，其中 `{XXX}` 为该资源的功能信息，例如：`resourceInstanceDelete`
   ```go
   func resourcePublicationDelete(_ context.Context, _ *schema.ResourceData, _ interface{}) diag.Diagnostics {
   	   // 参数定义

   	   // 创建client

       // 退订资源/删除资源
   }
   ```
4. 参数定义，创建client
   - 创建client时，其中第一个参数为服务类型，错误信息中的服务类型需要大写
   ```go
   cfg := meta.(*config.Config)
   region := cfg.GetRegion(d)
   var (
   	  httpUrl = "v3/{project_id}/instances/{instance_id}/replication/publications"
   	  product = "rds"
   )

   client, err := cfg.NewServiceClient(product, region)
   if err != nil {
   	  return diag.Errorf("error creating RDS client: %s", err)
   }
   ```
5. 退订资源/删除资源
   - 判断 `charging_mode` 参数是否设置，是否为`prePaid`，如果是就使用`common.UnsubscribePrePaidResource`去退订资源
   - 否则就执行删除资源函数，函数名为`delete{XXX}`，其中 `{XXX}` 为该资源的功能信息
   
   ```go
   if v, ok := d.GetOk("charging_mode"); ok && v.(string) == "prePaid" {
   	  if err = common.UnsubscribePrePaidResource(d, cfg, []string{d.Id()}); err != nil {
   		return diag.Errorf("error unsubscribe RDS instance: %s", err)
   	  }
   } else {
   	  err = deleteRdsInstance(ctx, d, client)
   	  if err != nil {
   		return diag.FromErr(err)
      }
   }
   ```
6 生成删除资源函数
   6.1. 生成删除资源函数
      - 生成一个删除资源的函数，格式为`resource{XXX}Delete`，其中 `{XXX}` 为该资源的功能信息，例如：`resourceInstanceDelete`
      
      ```go
      func resourcePublicationDelete(_ context.Context, _ *schema.ResourceData, _ interface{}) diag.Diagnostics {
          // 构造请求参数和请求体
      	
      	  // 发送请求
      	
      	  // 解析结果
      	
      	   // 等待任务
      }
      ```
   6.2 生成请求参数和请求体
      - 将path参数替换为具体的值
      - 首先需要构造请求体，函数名为 `buildDelete{XXX}BodyParams`， 其中 `{XXX}` 为该资源的功能信息
      
      ```go
      httpUrl := "v3/{project_id}/instances/{instance_id}"
      deletePath := client.Endpoint + httpUrl
      deletePath = strings.ReplaceAll(deletePath, "{project_id}", client.ProjectID)
      deletePath = strings.ReplaceAll(deletePath, "{instance_id}", d.Id())
      
      deleteOpt := golangsdk.RequestOpts{
      	KeepResponseBody: true,
      	MoreHeaders: map[string]string{"Content-Type": "application/json"},
      }
      deleteOpt.JSONBody = utils.RemoveNil(buildDeleteInstanceBodyParams(d))
      ```
   6.3 发送请求、解析结果
      1. 如果API响应消息为空，就不需要处理返回结果
          ```go
          _, err = client.Request("POST", deletePath, &deleteOpt)
          if err != nil {
          	return diag.Errorf("error deleting RDS instance: %s", err)
          }
          ```
      2. 如果API响应消息不为空，获取删除结果，然后使用`utils.FlattenResponse`去解析
         ```go
         deleteResp, err := client.Request("DELETE", deletePath, &deleteOpt)
         if err != nil {
            return diag.Errorf("error deleting RDS instance: %s", err)
         }
         deleteRespBody, err := utils.FlattenResponse(deleteResp)
         if err != nil {
            return diag.FromErr(err)
         }
         ```
  6.4 等待任务
      - 从API响应消息中获取任务ID信息，如果存在，那么就等待任务的完成
      - 函数名为 `check{XXX}JobFinish`， 其中 `{XXX}` 为该资源的功能信息
      ```go
      jobId := utils.PathSearch("job_id", deleteRespBody, "").(string)
      if jobId != "" {
      	if err = checkInstanceJobFinish(client, jobId, d.Timeout(schema.TimeoutUpdate)); err != nil {
      		return diag.Errorf("error deleting instance: %s", err)
      	}
      }
      ```
"""

DELETE_SKILLS = {
    "unsubscribe_only_step" : {
        "name": "unsubscribe_only_step",
        "description": "只生成退订resource步骤，当需要只生成退订resource相关代码时触发",
        "content": UNSUBSCRIBE_ONLY_STEP
    },
    "delete_only_step" : {
        "name": "delete_only_step",
        "description": "只生成删除resource步骤，当需要只生成删除resource相关代码时触发",
        "content": DELETE_ONLY_STEP
    },
    "delete_and_unsubscribe_step" : {
        "name": "delete_and_unsubscribe_step",
        "description": "生成退订和删除resource步骤，当需要生成退订和删除resource相关代码时触发",
        "content": DELETE_AND_UNSUBSCRIBE_STEP
    },
}

DELETE_STEP = """
<available_sub_skills>
    {skill_items}
</available_sib_skills>

<step>
1. 如果没有提供删除API，并且没有包周期参数
   - 生成一个返回warn信息的函数，格式为`resource{{XXX}}Delete`，其中 `{{XXX}}` 为该资源的功能信息，例如：`resourcePublicationDelete`
   ```go
   func resourcePublicationDelete(_ context.Context, _ *schema.ResourceData, _ interface{{}}) diag.Diagnostics {{
   	  errorMsg := "Deleting RDS publication resource is not supported. The resource is only removed from the state."
      return diag.Diagnostics{{
   		 diag.Diagnostic{{
   			Severity: diag.Warning,
   			Summary:  errorMsg,
   		 }},
   	  }}
   }}

2. 如果没有提供删除API，但是创建resource API 有包周期参数，只生成退订resource相关代码

3. 如果有提供删除API，但是创建resource API没有包周期参数，只生成删除resource相关代码

4. 如果有提供删除APi，同时创建resource API也有包周期参数，生成退订和删除resource相关代码
</step>
"""

def apply_delete_prompt_template() -> str:
    prompt = DELETE_STEP.format(
        skill_items=build_skills(DELETE_SKILLS),
        unsubscribe_only_step=DELETE_SKILLS["unsubscribe_only_step"]["description"],
        delete_only_step=DELETE_SKILLS["delete_only_step"]["description"],
        delete_and_unsubscribe_step=DELETE_SKILLS["delete_and_unsubscribe_step"]["description"],
    )
    return prompt
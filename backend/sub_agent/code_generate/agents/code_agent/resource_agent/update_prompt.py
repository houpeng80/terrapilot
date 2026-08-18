from backend.sub_agent.code_generate.agents.code_agent.resource_agent.utils import build_skills

UPDATE_RESOURCE_FUNC_STEP = """
1. 生成 UpdateContext 函数
   - 格式为`resource{XXX}Update`，其中 `{XXX}` 为该资源的功能信息，例如：`resourcePublicationUpdate`
   - 该函数总共包含：函数名称、参数定义、创建client、更新参数方法、更新enterprise_project_id、更新tags、更新auto_renew
   ```go
   func resourcePublicationUpdate(ctx context.Context, d *schema.ResourceData, meta interface{}) diag.Diagnostics {
       // 参数定义
   
   	   // 创建client
   
       // 更新参数
   	
   	   // 更新enterprise_project_id
   	   
   	   // 更新tags
   	   
   	   // 更新auto_renew
   
   	return resourcePublicationRead(ctx, d, meta)
   }
   ```
2. 参数定义，创建client
   - 创建client时，其中第一个参数为服务类型，错误信息中的服务类型需要大写
   - 如果参数中包含包周期参数，那么就需要创建更新包周期参数所需的client，变量名为`bssClient`
   
   ```go
   cfg := meta.(*config.Config)
   region := cfg.GetRegion(d)
   var (
   	  product = "rds"
   )
   
   client, err := cfg.NewServiceClient("rds", region)
   if err != nil {
   	  return diag.Errorf("error creating RDS client: %s", err)
   }
   
   bssClient, err := cfg.BssV2Client(region)
   if err != nil {
   	  return diag.Errorf("error creating bss V2 client: %s", err)
   }
   ```
3. 更新参数
   - 根据用户提供的更新resource参数API，依次添加参数更新方法
   
   3.1 根据用户提供的更新资源API，获取API信息
   3.2 生成更新参数逻辑
      - 如果API请求参数只有一个，那么就使用`d.HasChange`方法判断参数是否修改
      - 如果API请求参数有多个，那么就使用`d.HasChanges`方法判断参数是否修改
      - 更新参数通过`update{XXX}{YYY}`方法实现，其中 `{XXX}` 为该资源的功能信息，`{YYY}` 为参数名称，函数名最终采用驼峰格式
      - 函数参数首先需要包含`d`和`client`
      - 如果API响应消息中包含`job_id`等任务信息，那么函数参数需要包含`ctx`
      - 如果API请求消息中包含包周期相关参数，例如`自动支付（is_auto_pay）`，或者API响应消息中包含`order_id`，那么函数参数需要包含`bssClient`
      - 最后判断返回错误信息是否为空，如果为空，就要return错误信息，使用`diag.FromErr`处理错误信息
      
      ```go
      if d.HasChange("name") {
      	 if err = updateInstanceName(d, client); err != nil {
      		return diag.FromErr(err)
      	 }
      }
      ```
      
      ```go
      if d.HasChanges("kms_key_id", "description", "event_subscriptions") {
      	 if err := updateInstance(ctx, d, client); err != nil {
      		return diag.FromErr(err)
      	 }
      }
      ```
      
      ```go
      if d.HasChange("flavor") {
      	 if err = updateInstanceFlavor(ctx, d, client, bssClient); err != nil {
      		return diag.FromErr(err)
      	 }
      }
      ```
4. 更新 enterprise_project_id
   - 如果请求`创建资源API`参数中包含参数 `enterprise_project_id`，那么就添加`更新enterprise_project_id`
   - 使用`cfg.MigrateEnterpriseProject`方法去更新`enterprise_project_id`，如果返回`err`不为空，则返回错误信息
   - 在`resource函数`前边加一个注释（示例中的`使用到的API`位置）：`// @API EPS POST /v1.0/enterprise-projects/{enterprise_project_id}/resources-migrat`
   
   ```go
   if d.HasChange("enterprise_project_id") {
   	  migrateOpts := config.MigrateResourceOpts {
   		 ResourceId:   instanceID,
   		 ResourceType: "rds",
   		 RegionId:     region,
   		 ProjectId:    client.ProjectID,}
   	  if err = cfg.MigrateEnterpriseProject(ctx, d, migrateOpts); err != nil {
   		 return diag.FromErr(err)
   	  }
   }
   ```
5. 更新tags
   - 如果`创建资源API`参数中包含 `tags`，那么就添加`更新tags`
   - 使用`utils.UpdateResourceTags`方法去更新`tags`
   - 在`resource函数`前边加一个注释（示例中的`使用到的API`位置）：`// @API RDS POST /v3/{project_id}/instances/{id}/tags/action`
   
   ```go
   if d.HasChange("tags") {
   	  if err = utils.UpdateResourceTags(client, d, "instances", instanceID); err != nil {
   		return diag.Errorf("error updating tags of RDS instance (%s): %s", instanceID, err)
   	  }
   }
   ```
6. 更新auto_renew
   - 如果`创建资源API`参数中包含 `auto_renew`，那么就添加`更新auto_renew`
   - 使用`common.UpdateAutoRenew`方法去更新`auto_renew`
   - 在`resource函数`前边加两个注释（示例中的`使用到的API`位置）：`// @API BSS POST /v2/orders/subscriptions/resources/autorenew/{instance_id}` 和 `// @API BSS DELETE /v2/orders/subscriptions/resources/autorenew/{instance_id}`
   
   ```go
   if d.HasChange("auto_renew") {
   	  if err = common.UpdateAutoRenew(bssClient, d.Get("auto_renew").(string), instanceID); err != nil {
   		return diag.Errorf("error updating the auto-renew of the instance (%s): %s", instanceID, err)
   	  }
   }
   ```
"""

UPDATE_PARAMS_FUNC_STEP = """
1. 根据用户提供的查询资源API，获取API信息
2. 添加注释
   -在资源函数前边加一个注释（示例中的`使用到的API`位置），格式为`// @API {service} {method} {path}`，其中`{service}`为当前服务名，`{method}`为URI中的请求方法，`{path}`为URI中的请求path
3. 生成更新参数函数体
   - 函数名为`update{XXX}{YYY}`，其中 `{XXX}` 为该资源的功能信息，`{YYY}` 为参数名称，函数名最终采用驼峰格式
   - 函数参数首先需要包含`d`和`client`
   - 如果API响应消息中包含`job_id`等任务信息，那么函数参数需要包含`ctx`
   - 如果API请求消息中包含包周期相关参数，例如`自动支付（is_auto_pay）`，或者API响应消息中包含`order_id`，那么函数参数需要包含`bssClient`
   - 将函数放到更新resource的函数的后边
   
   ```go
   func updateRdsInstanceFlavor(ctx context.Context, d *schema.ResourceData, client, bssClient *golangsdk.ServiceClient) diag.Diagnostics {
       // 构造请求参数和请求体
   
   	   // 发送请求
   	
   	   // 解析结果
   	
   	   // 等待任务或订单完成
   }
   ```
4. 构造请求参数和请求体
   - 将path参数替换为具体的值，禁止使用`utils.ReplacePathVariables`，使用`strings.ReplaceAll`
   - 首先需要构造请求体，函数名为 `buildUpdate{XXX}{YYY}BodyParams`， 其中 `{XXX}` 为该资源的功能信息，`{YYY}` 为参数名称，函数名最终采用驼峰格式
   
   ```go
   httpUrl := "v3/{project_id}/instances/{instance_id}/name" 
   updatePath := client.Endpoint + httpUrl
   updatePath = strings.ReplaceAll(updatePath, "{project_id}", client.ProjectID)
   updatePath = strings.ReplaceAll(updatePath, "{instance_id}", fmt.Sprintf("%v", d.Id()))
   
   updateOpt := golangsdk.RequestOpts{
   	  KeepResponseBody: true,
   	  MoreHeaders: map[string]string{"Content-Type": "application/json"},
   }
   updateOpt.JSONBody = buildUpdateInstanceNameBodyParams(d)
   ```
5. 发送请求、解析结果
   5.1 如果API响应消息为空，就不需要处理返回结果
      ```go
      _, err = client.Request("POST", getPath, &getOpt)
      if err != nil {
      	return diag.Errorf("error updating RDS instance name: %s", err)
      }
      ```
   5.2 如果API响应消息不为空，获取更新结果，然后使用`utils.FlattenResponse`去解析
      ```go
      updateResp, err := client.Request("POST", getPath, &getOpt)
      if err != nil {
      	return diag.Errorf("error updating RDS instance name: %s", err)
      }
      
      updateRespBody, err := utils.FlattenResponse(updateResp)
      if err != nil {
      	return diag.FromErr(err)
      }
   ```
6. 等待任务或订单完成
   6.1 添加等待订单完成逻辑
      - 从API响应消息中获取订单ID信息，如果存在，那么就等待订单的完成
      ```go
      orderId := utils.PathSearch("order_id", createRespBody, "").(string)
      if orderId != "" {
      	err = common.WaitOrderComplete(ctx, bssClient, orderId, d.Timeout(schema.TimeoutUpdate))
      	if err != nil {
      		return diag.FromErr(err)
      	}
      }
      ```
   6.2 添加等待任务完成逻辑
      - 从API响应消息中获取任务ID信息，如果存在，那么就等待任务的完成
      - 函数名为 `check{XXX}JobFinish`， 其中 `{XXX}` 为该资源的功能信息
      ```go
      jobId := utils.PathSearch("job_id", createRespBody, "").(string)
      if jobId != "" {
      	if err = checkInstanceJobFinish(client, jobId, d.Timeout(schema.TimeoutUpdate)); err != nil {
      		return diag.Errorf("error updating publication: %s", err)
      	}
      }
7. 生成函数请求体
   - 首先需要构造请求体，函数名为 `buildUpdate{XXX}{YYY}BodyParams`， 其中 `{XXX}` 为该资源的功能信息，`{YYY}` 为参数名称，函数名最终采用驼峰格式
   - 将函数放到最后边
   
   ```go
   func updateRdsInstanceNameBodyParams(d *schema.ResourceData) map[string]interface{} {
   	   bodyParams := map[string]interface{}{
   		  "name": d.Get("name"),
   	   }
   }
   ```
8. 添加等待时间
   - 在资源函数中添加更新资源等待时间（示例中的`超时时间`位置）
   - 如果已经存在，则不需要再次添加
   ```go
   Timeouts: &schema.ResourceTimeout{
   	  Update:  schema.DefaultTimeout(30 * time.Minute),
   	  // ....
   },
   ```
"""

UPDATE_SKILLS = {
    "update_resource_func_step" : {
        "name": "update_resource_func_step",
        "description": "生成更新resource func步骤，当需要生成更新resource func相关代码时触发",
        "content": UPDATE_RESOURCE_FUNC_STEP
    },
    "update_params_func_step" : {
        "name": "update_params_func_step",
        "description": "生成更新resource params步骤，当需要生成更新resource params相关代码时触发",
        "content": UPDATE_PARAMS_FUNC_STEP
    },
}

UPDATE_STEP = """
<available_sub_skills>
    {skill_items}
</available_sib_skills>

<step>
1. 如果没有提供更新API，并且参数中没有 `enterprise_project_id`、 `tags`和 `auto_renew`：
   - 生成一个空函数，格式为`resource{{XXX}}Update`，其中 `{{XXX}}` 为该资源的功能信息，例如：`resourcePublicationUpdate`

   ```go
   func resourcePublicationUpdate(_ context.Context, _ *schema.ResourceData, _ interface{{}}) diag.Diagnostics {{
	   return nil
   }}
   ```

2. 如果提供了更新API，或者有 `enterprise_project_id`、 `tags`和 `auto_renew` 至少一个参数：
   2.1 生成更新resource func相关代码

   2.2 生成更新resource func params相关代码
   
   2.3 添加不支持更新的参数列表
      - 如果创建API的参数（包含URI参数和请求参数）不被更新API支持更新，那么该参数不支持更新，那么就在`resource函数`中添加不支持修改的参数列表（示例中的`不支持修改的参数列表`位置），类型为字符串数组
      - 如果参数类型为list，那么就需要使用星号（`*`）来分开层级
      ```go
      var rdsInstanceNonUpdatableParams = []string{{
      	"name",
      	"images",
      	"building_config.*.cluster", "building_config.*.image_pull_secrets",
      }}
      ```
   2.4 添加 CustomizeDiff 信息 和 enable_force_new 参数
      - 如果上一步添加了不支持修改的参数列表：
         - 那么就在资源函数中添加CustomizeDiff 信息（resource函数的`CustomizeDiff 信息`位置）
         - `resource函数`中添加`enable_force_new`参数

      ```go
      CustomizeDiff: config.FlexibleForceNew(rdsInstanceNonUpdatableParams),
      ```
    
      ```go
      "enable_force_new": {{
      	   Type:         schema.TypeString, 
      	   Optional:     true,
      	   ValidateFunc: validation.StringInSlice([]string{{"true", "false"}}, false), 
      	   Description:  utils.SchemaDesc("", utils.SchemaDescInput{{Internal: true}}),
      }},
      ```
</step>
"""

def apply_update_prompt_template() -> str:
    prompt = UPDATE_STEP.format(
        skill_items=build_skills(UPDATE_SKILLS),
        update_resource_func_step=UPDATE_SKILLS["update_resource_func_step"]["description"],
        update_params_func_step=UPDATE_SKILLS["update_params_func_step"]["description"],
    )
    return prompt
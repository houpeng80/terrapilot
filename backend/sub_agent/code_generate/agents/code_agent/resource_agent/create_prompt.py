from backend.sub_agent.code_generate.agents.code_agent.resource_agent.utils import build_skills

SCHEMA_FUNC_STEP = """
1. 该函数的名称格式为 `Resource{XXX}`，其中 `{XXX}` 为该资源的功能信息，采用驼峰状格式，例如：`ResourcePublication`
2. 该函数参数为空，返回值为 `*schema.Resource`
3. 为 `CreateContext`、`UpdateContext`、`ReadContext`、`DeleteContext` 四个变量设置值，分别为对应的实现函数，格式为`resource{XXX}{YYY}`，其中 `{XXX}` 为该资源的功能信息，`{YYY}`为函数动作
4. 如果该服务为全局函数，那么就不需要添加`region`，如果不是全局函数，那么就需要添加参数`region`，并且放到最前边，并且设置`Optional`和`Computed` 为`true`

```go
// 不支持修改的参数列表

// 使用到的API
func ResourcePublication() *schema.Resource {
    return &schema.Resource{
		CreateContext: resourcePublicationCreate, 
		UpdateContext: resourcePublicationUpdate, 
		ReadContext:   resourcePublicationRead, 
		DeleteContext: resourcePublicationDelete,

		// 导入信息
		
		// CustomizeDiff 信息
		
		// 超时时间
		
        Schema: map[string]*schema.Schema{
            "region": {
                Type:     schema.TypeString,
                Optional: true,
                Computed: true,
            },
            // URI参数
			
            // 请求参数
			
			// 包周期参数
			"charging_mode": {
				Type:     schema.TypeString,
				Optional: true,
				Computed: true,
				ValidateFunc: validation.StringInSlice([]string{
					"prePaid", "postPaid",
				}, false),
			},
			"period_unit": {
				Type:         schema.TypeString,
				Optional:     true,
				RequiredWith: []string{"period"},
				ValidateFunc: validation.StringInSlice([]string{
					"month", "year",
				}, false),
			},
			"period": {
				Type:         schema.TypeInt,
				Optional:     true,
				RequiredWith: []string{"period_unit"},
			},
			"auto_renew": common.SchemaAutoRenewUpdatable(nil),
			"auto_pay":   common.SchemaAutoPay(nil),
			
            // 更新参数

            // 响应参数
        },
    }
}

// 创建 resource 相关函数

// 更新 resource 相关函数

// 查询 resource 相关函数

// 删除 resource 相关函数

// 导入 resource 相关函数
```
"""

CREATE_RESOURCE_PARAMS_STEP = """
1. 添加URI信息中的参数信息到resource函数中（`URI参数`位置）
   - 如果有参数`project_id`，就忽略掉
   - 如果是必填，就设置`Required`为 `true`
   - 如果是可选参数，就就设置`Optional`为 `true`
2. 添加请求参数到 resource 函数中（`请求参数`位置）
   - 如果是必填，就设置`Required`为 `true` 
   - 如果是可选参数，就就设置`Optional`为 `true`
   - 如果类型为`bool`，那么就将类型设置为`string`，并且添加validation限制`ValidateFunc`: `validation.StringInSlice([]string{"true", "false"}, false)`
   - 如果类型为对象，那么就将类型设置为`list`，设置`MaxItems`为 `1`，并且必须在子函数中展示该对象的参数，子函数名格式为`{XXX}{YYY}Schema`，其中`{XXX}`为该资源的功能信息， `{YYY}` 为该参数的驼峰形式，子函数放到resource函数后边 
   - 如果包含计费模式字段，如`charge_mode`或`charge_info`等字段，或者其说明中支持预付费模式，即`包年/包月`，或者取值包含`prePaid`，那么说明该API支持包周期
   - 如果支持包周期，那么就添加包周期参数： `charging_mode`、`period_unit`、`period`、`auto_renew`、`auto_pay`
   - 所有参数都不能设置`ForceNew`，除了`bool`类型之外，所有参数也都不能添加`ValidateFunc`
   ```go
   // 使用到的API
   func ResourcePublication() *schema.Resource {
       return &schema.Resource{
   		CreateContext: resourcePublicationCreate, 
   		UpdateContext: resourcePublicationUpdate, 
   		ReadContext:   resourcePublicationRead, 
   		DeleteContext: resourcePublicationDelete,

   		// 导入信息

   		// CustomizeDiff 信息

   		// 超时时间

           Schema: map[string]*schema.Schema{
               "region": {
                   Type:     schema.TypeString,
                   Optional: true,
                   Computed: true,
               },
               // URI参数
   			   "instance_id": {
                   Type:     schema.TypeString,
   				Required: true,
               },
               // 请求参数
               "bucket_name": {
                   Type:     schema.TypeString,
                   Optional: true,
               },
   			   "bucket_exist": {
                   Type:     schema.TypeString,
                   Optional: true,
                   ValidateFunc: validation.StringInSlice([]string{
   					"true", "false",
   				}, false),
               },
               "subscription_options": {
   				   Type:     schema.TypeList,
   				   Optional: true,
   				   MaxItems: 1,
   				   Elem:     publicationSubscriptionOptionsSchema(),
   			   },
               "tables": {
   				   Type:     schema.TypeList,
   				   Optional: true,
   				   Elem:     publicationTablesSchema(),
   			   },
   			// 包周期参数
   			"charging_mode": {
   				Type:     schema.TypeString,
   				Optional: true,
   				Computed: true,
   				ValidateFunc: validation.StringInSlice([]string{
   					"prePaid", "postPaid",
   				}, false),
   			},
   			"period_unit": {
   				Type:         schema.TypeString,
   				Optional:     true,
   				RequiredWith: []string{"period"},
   				ValidateFunc: validation.StringInSlice([]string{
   					"month", "year",
   				}, false),
   			},
   			"period": {
   				Type:         schema.TypeInt,
   				Optional:     true,
   				RequiredWith: []string{"period_unit"},
   			},
   			"auto_renew": common.SchemaAutoRenewUpdatable(nil),
   			"auto_pay":   common.SchemaAutoPay(nil),
   			// ......
           },

   		// ......
       }
   }

   func publicationSubscriptionOptionsSchema() *schema.Resource {
   	return &schema.Resource{
   		Schema: map[string]*schema.Schema{
   			"independent_agent": {
   				Type:         schema.TypeString,
   				Optional:     true,
   				ValidateFunc: validation.StringInSlice([]string{"true", "false"}, false),
   			},
   			"snapshot_always_available": {
   				Type:         schema.TypeString,
   				Optional:     true,
   			},
   		},
   	}
   }

   func publicationTablesSchema() *schema.Resource {
   	  return &schema.Resource{
   		 Schema: map[string]*schema.Schema{
   			"table_name": {
   				Type:     schema.TypeString,
   				Required: true,
   			},
   			"schema": {
   				Type:     schema.TypeString,
   				Optional: true,
   			},
   		 },
   	  }
   }
   ```
"""

CREATE_RESOURCE_FUNC_STEP = """
1. 生成 CreateContext 函数
   - 格式为`resource{XXX}Create`，其中 `{XXX}` 为该资源的功能信息，例如：`resourcePublicationCreate`
   - 该函数总共包含：函数名称、参数定义、创建client、构造请求参数、构造请求体、发送请求、解析结果、设置资源id、等待任务或订单完成
   ```go
   func resourcePublicationCreate(ctx context.Context, d *schema.ResourceData, meta interface{}) diag.Diagnostics {
       // 参数定义

       // 创建client

       // 构造请求参数和请求体

       // 发送请求

       // 解析结果

       // 设置资源id

       // 等待任务或订单完成

   	// 更新其他参数

       return resourcePublicationRead(ctx, d, meta)
   }
   ```
2. 参数定义，创建client
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
3. 构造请求参数和请求体
   - 将path参数替换为具体的值，禁止使用`utils.ReplacePathVariables`，使用`strings.ReplaceAll`
   - 构造请求体，函数名为 `buildCreate{XXX}BodyParams`， 其中 `{XXX}` 为该资源的功能信息，最后使用`utils.RemoveNil`去除掉值为nil的参数
   - 需要引入包`github.com/chnsz/golangsdk   
   ```go
   createPath := client.Endpoint + httpUrl
   createPath = strings.ReplaceAll(createPath, "{project_id}", client.ProjectID)
   createPath = strings.ReplaceAll(createPath, "{instance_id}", d.Get("instance_id").(string)   
   createOpt := golangsdk.RequestOpts{
   	  KeepResponseBody: true,
   	  MoreHeaders: map[string]string{"Content-Type": "application/json"},
   }
   createOpt.JSONBody = utils.RemoveNil(buildCreatePublicationBodyParams(d))
   ```
4. 发送请求、解析结果
   ```go
   createResp, err := client.Request("POST", getPath, &getOpt)
   if err != nil {
   	  return diag.Errorf("error creating RDS publication: %s", err)
   }

   createRespBody, err := utils.FlattenResponse(createResp)
   if err != nil {
   	  return diag.FromErr(err)
   }
   ```
5. 设置资源id
      - 如果用户说明了获取资源`id`的位置，那么就从用户指定的位置获取`id`
      1 如果用户没有说明获取`id`的位置，那么就直接从API响应消息中查找`id`

      ```go
      id := utils.PathSearch("id", createRespBody, "").(string)
      if id == "" {
      	return diag.Errorf("error creating RDS publication: ID is not found in API response")
      }
      d.SetId(id)
      ```
6. 等待任务或订单完成
   6.1 添加等待订单完成逻辑
      - 从API响应消息中获取订单ID信息，如`order_id`或`order_info`，如果存在，那么就等待订单的完成
      - 如果API支持包周期，那么在resource函数前边加一个注释（示例中的`使用到的API`位置）：`@API BSS GET /v2/orders/customer-orders/details/{order_id}`

      ```go
      orderId := utils.PathSearch("order_id", createRespBody, "").(string)
      if orderId != "" {
      	 bssClient, err := cfg.BssV2Client(region)
      	 if err != nil {
      		return diag.Errorf("error creating BSS v2 client: %s", err)
      	 }
      	 err = common.WaitOrderComplete(ctx, bssClient, orderId, d.Timeout(schema.TimeoutCreate))
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
      	if err = checkInstanceJobFinish(client, jobId, d.Timeout(schema.TimeoutCreate)); err != nil {
      		return diag.Errorf("error creating publication: %s", err)
      	}
      }
      ```
7. 更新其他参数
- 如果更新API需要在创建时触发，那么就添加更新逻辑，函数名为`update{XXX}{YYY}`，其中 `{XXX}` 为该资源的功能信息，`{YYY}` 为参数名称，函数名最终采用驼峰格式

```go
if _, ok = d.GetOk("auto_scaling"); ok {
   err = updateAutoScaling(ctx, d, client)
   if err != nil {
   	  return diag.FromErr(err)
   }
}
```
8. 生成函数请求体
- 首先需要构造请求体，函数名为 `buildCreate{XXX}BodyParams`， 其中 `{XXX}` 为该资源的功能信息
- 如果API支持包周期，那么参数中的自动支付参数，如`auto_pay`，`is_auto_pay`， 直接设置为`true`
- 将函数放到创建resource的函数的后边

```go
func buildCreatePublicationBodyParams(d *schema.ResourceData) map[string]interface{} {
	bodyParams := map[string]interface{}{
		"publication_name":               d.Get("publication_name"),
		"publication_database":           d.Get("publication_database"),
		"is_create_snapshot_immediately": isCreateSnapshotImmediately,
		"subscription_options":           buildPublicationSubscriptionOptionsBodyParams(d.Get("subscription_options")),
		"job_schedule":                   buildPublicationJobScheduleBodyParams(d.Get("job_schedule")),
		"extend_tables":                  utils.ValueIgnoreEmpty(d.Get("extend_tables").(*schema.Set).List()),
		"tables":                         tables,
	}
}
```
"""

CREATE_WAIT_FUNC_STEP = """
1. 创建等待任务函数
   - 构造请求体，函数名为 `check{XXX}JobFinish`， 其中 `{XXX}` 为该资源的功能信息
   - 定义一个变量`stateConf`，其值为`resource.StateChangeConf`的引用，创建该变量时需要设置`Pending`、`Target`、`Refresh`、`Timeout`、`PollInterval`
   - 其中`Pending`为一个包含等待状态的字符串数组，其值为 `Pending`， 其中`Target`为一个包含等待状态的字符串数组，其值为 `Completed`
   - `Refresh` 为刷新状态函数，调用刷新函数，函数名为`{XXX}JobStatusRefreshFunc`， 其中 `{XXX}` 为该资源的功能信息
   - `Timeout` 为等待的超时时长，从参数中获取，`PollInterval` 固定为`10 * time.Second`
   - 将函数放到最后边
   
   ```go
   func checkPublicationJobFinish(ctx context.Context, client *golangsdk.ServiceClient, jobID string,
   	  timeout time.Duration) error {
   	  stateConf := &resource.StateChangeConf{
   		  Pending:      []string{"Pending"},
   		  Target:       []string{"Completed"},
   		  Refresh:      publicationJobStatusRefreshFunc(client, jobID),
   		  Timeout:      timeout,
   		  PollInterval: 10 * time.Second,
   	  }
   	  if _, err := stateConf.WaitForStateContext(ctx); err != nil {
   		return fmt.Errorf("error waiting for RDS publication job (%s) to be completed: %s ", jobID, err)
   	  }
   	return nil
   }
   ```
2. 创建刷新状态函数
   - 函数名为 `{XXX}JobStatusRefreshFunc`， 其中 `{XXX}` 为该资源的功能信息
   - 调用获取任务状态函数`getJobInfo`获取任务信息，如果获取失败，那么直接状态`Failed`，对应的返回格式为`return nil, "Failed", err`
   - 从结果中获取`status`， 根据状态值判断任务是否完成
      - 如果没有获取到`status`，则返回状态值为`Failed`，对应的返回格式为`return nil, "Failed", err`
      - 如果`status`值为`success`、`completed`等类似成功的状态，则返回状态为`Completed`, 对应的返回格式为`return getRespBody, "Completed", nil`
      - 如果`status`值为`fail`、`error`等类似失败的状态，则返回状态为`Failed`, 对应的返回格式为`return getRespBody, "Failed", fmt.Errorf("the job is fail")`
      - 如果`status`为其他值，那么就返回等待状态`Pending`，对应的返回格式为`return getRespBody, "Pending", nil`
      
   ```go
   func publicationJobStatusRefreshFunc(client *golangsdk.ServiceClient, jobId string) resource.StateRefreshFunc {
   	return func() (interface{}, string, error) {
   		getRespBody, err := getJobInfo()
   		if err != nil {
   			return nil, "Failed", err
   		}
   
   		status := utils.PathSearch("status", getRespBody, "").(string)
   		if status == "ERROR" {
   			return nil, status, fmt.Errorf("the job is fail")
   		}
   		if status == "SUCCESS" {
   			return getRespBody, "Completed", nil
   		}
   		return getRespBody, "Pending", nil
   	}
   }
      ```
3. 创建获取任务信息函数
   3.1 生成获取数据函数
      - 该函数总共包含：构造请求url、构造请求体、构造查询参数、发送请求、解析结果、返回结果
      
      ```go
      func getInstanceInfo(_ context.Context, d *schema.ResourceData, meta interface{}) error {
          // 构造请求url
      
      	 // 构造请求体
      
      	 // 发送请求
      
      	 // 解析结果
      
      	 // 返回结果
      }
      ```
   3.2 构造请求url
      - 将path参数替换为具体的值
      - 如果查询参数是path参数，那么就需要添加分页参数之外的所有查询参数，通过`buildGet{XXX}QueryParams`方法实现，其中 `{XXX}` 为该API要获取的功能信息
      
      ```go
      httpUrl := "v3/{project_id}/instances/{instance_id}/database/db-table-name"
      getPath := client.Endpoint + httpUrl
      getPath = strings.ReplaceAll(getPath, "{project_id}", client.ProjectID)
      getPath = strings.ReplaceAll(getPath, "{instance_id}", d.Get("instance_id").(string))
      getPath += buildGetDatabasesBackupQueryParams(d)
      ```
   3.3 构造请求体
      - 如果API不支持分页，或者API支持分页，但请求URI中的请求方法不为GET，就需要生成请求体，参数名为`getOpt`
      - 使用`golangsdk.RequestOpts`生成请求体，禁止使用`utils.BaseRequestOpts()`
      
      ```go
      getOpt := golangsdk.RequestOpts{
      	KeepResponseBody: true,
      	MoreHeaders: map[string]string{
      		"Content-Type": "application/json",
      	},
      }
      ```
   3.4 发送请求、解析结果
      1. 如果API不支持分页，直接发送请求，参数依次为：URI中的请求方法、请求URL、请求体、最后解析结果：

         ```go
         getResp, err := client.Request("GET", getPath, &getOpt)
         if err != nil {
         	 return diag.Errorf("error retrieving RDS backup databases: %s", err)
         }
         
         getRespBody, err := utils.FlattenResponse(getResp)
         if err != nil {
         	 return diag.FromErr(err)
         }
         ```

      2. 如果API支持分页，并且URI中的请求方法为 GET，根据分页参数选择合适的分页逻辑：

         - 分页参数为 limit + offset, ListAllItems中第二个参数qType为`offset`
         - 分页参数为 pagesize + page, ListAllItems中第二个参数qType为`page`
         - 分页参数为 limit + marker, ListAllItems中第二个参数qType为`marker`， 如果返回值中包含下一页的marker时，第四个参数中的MarkerField为下一页的marker

         ```go
         getResp, err := pagination.ListAllItems(
      	   client,
      	   "offset",
      	   listPath,
      	   &pagination.QueryOpts{MarkerField: ""})
         if err != nil {
      	   return diag.Errorf("error retrieving RDS publications: %s", err)
         }
         getRespJson, err := json.Marshal(getResp)
         if err != nil {
      	   return diag.FromErr(err)
         }
         var getRespBody interface{}
         err = json.Unmarshal(getRespJson, &getRespBody)
         if err != nil {
      	   return diag.FromErr(err)
         }
         ```

      3. 如果API支持分页，并且URI中的请求方法不为 GET：

          1. 首先定义一个临时变量 `res` 保存查询结果
          2. 定义分页参数
              - 如果API中包含`limit`， 记录API中允许设置的最大值，记为`maxLimit`，定义变量`offset`
              - 如果API是使用`page+size`分页，那么定义变量`page`，并且赋值为 `1`
          3. 如果请求参数在请求体中，首先需要构造请求体，函数名为 `buildGet{XXX}BodyParams`， 其中 `{XXX}` 为该API要获取的功能信息，其中要包含分页参数， 最后使用`utils.RemoveNil`去除掉值为nil的参数
          4. 在for循环查询所有页的结果，请求参数依次为：URI中的请求方法、请求url、请求体
          5. 通过函数 `flattenGet{XXX}Body` 解析当前查询结果，其中 `{XXX}` 为该参数的驼峰形式
          6. 判断查询到的结果
              - 如果当前查询结果为空，那么就结束循环，禁止使用API返回结果中的总数来判断是否要结束循环
              - 如果当前查询结果不为空，就将解析结果添加到 `res` 中，
          7. 更新分页参数
              - 如果API中包含`offset`，那么`offset`增加`maxLimit`
              - 如果API是使用page+size分页，那么定义变量`page`， 那么`page`增加`1`
      
          ```go
          offset := 0
          res := make([]map[string]interface{}, 0)
          for {
             getOpt.JSONBody = utils.RemoveNil(buildGetBackupDatabasesBodyParams(d, offset))
       	    getResp, err := client.Request("POST", getPath, &getOpt)
       	    if err != nil {
       	       return diag.Errorf("error retrieving RDS backup databases: %s", err)
       	    }         	  
             getRespBody, err := utils.FlattenResponse(getResp)
             if err != nil {
                return diag.FromErr(err)
             }
             databases := flattenGetBackupDatabasesBody(getRespBody)
             if len(databases) == 0 {
                break
             }
             res = append(res, databases...)
             offset += 100
          }
          ```
    3.5 返回结果
         - 将获取到的结果`getRespBody`或 `res`返回
"""

CREATE_SKILLS = {
    "schema_func_step" : {
        "name": "schema_func_step",
        "description": "生成schema fun步骤，当需要生成schema fun相关代码时触发",
        "content": SCHEMA_FUNC_STEP
    },
    "create_resource_params_step" : {
        "name": "create_resource_params_step",
        "description": "生成创建resource params步骤，当需要生成创建resource params相关代码时触发",
        "content": CREATE_RESOURCE_PARAMS_STEP
    },
    "create_resource_func_step" : {
        "name": "create_resource_func_step",
        "description": "生成创建resource func步骤，当需要生成创建resource func相关代码时触发",
        "content": CREATE_RESOURCE_FUNC_STEP
    },
    "create_wait_func_step" : {
        "name": "create_wait_func_step",
        "description": "生成wait func步骤，当需要生成wait func相关代码时触发",
        "content": CREATE_WAIT_FUNC_STEP
    },
}

CREATE_STEP = """
<available_sub_skills>
    {skill_items}
</available_sub_skills>

<step>
1. 根据用户提供的创建资源API，获取API信息

2. 生成 schema fun相关代码

3. 生成 创建resource params相关代码
   
4. 添加注释
   - 如果支持包周期，那么在`resource函数`前边加两个注释（示例中的`使用到的API`位置）：`@API BSS POST /v2/orders/subscriptions/resources/autorenew/{{instance_id}}`和`@API BSS DELETE /v2/orders/subscriptions/resources/autorenew/{{instance_id}}`
   - 在`resource函数`前边加一个注释（示例中的`使用到的API`位置），格式为`// @API {{service}} {{method}} {{path}}`，其中`{{service}}`为当前服务名，`{{method}}`为URI中的请求方法，`{{path}}`为URI中的请求path

5. 生成创建 resource func相关代码
   
6. 生成wait_func相关代码

7. 添加等待时间
   - 在`resource函数`中添加创建资源等待时间（示例中的`超时时间`位置）

   ```go
   Timeouts: &schema.ResourceTimeout{{
   	  Create:  schema.DefaultTimeout(30 * time.Minute),
   	  // ....
   }},
   ```
</step>
"""

def apply_create_prompt_template() -> str:
    prompt = CREATE_STEP.format(
        skill_items=build_skills(CREATE_SKILLS),
        schema_func_step=CREATE_SKILLS["schema_func_step"]["description"],
        create_resource_params_step=CREATE_SKILLS["create_resource_params_step"]["description"],
        create_resource_func_step=CREATE_SKILLS["create_resource_func_step"]["description"],
        create_wait_func_step=CREATE_SKILLS["create_wait_func_step"]["description"],
    )
    return prompt
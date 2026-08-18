from backend.sub_agent.code_generate.agents.code_agent.resource_agent.utils import build_skills

READ_RESOURCE_PARAMS_STEP = """
1. 如果API不是分页接口

   - 从响应消息中获取返回的resource信息
   - 如果响应消息中的参数在 `resource函数` 的请求参数中不存在，那么就添加到`resource 函数`中的`响应消息`处，并设置`Computed`为 `true`

2. 如果API是分页接口

   - 从响应消息中获取返回的resource信息，找到要查询的信息列表，并获取列表的元素详情
   - 如果列表元素详情中的参数在 `resource函数` 的请求参数中不存在，那么就添加到`resource 函数`中的`响应消息`处，并设置`Computed`为 `true`

```go
// 使用到的API
func ResourcePublication() *schema.Resource {
    return &schema.Resource{
		CreateContext: resourcePublicationCreate, 
		UpdateContext: resourcePublicationUpdate, 
		ReadContext:   resourcePublicationRead, 
		DeleteContext: resourcePublicationDelete,

		// ......

        Schema: map[string]*schema.Schema{
            "region": {
                Type:     schema.TypeString,
                Optional: true,
                Computed: true,
            },
            // ......
            
			// 响应参数
			"create_time": {
                Type:     schema.TypeString,
                Computed: true,
            },
        },
		
		// ......
    }
}
```
"""

READ_RESOURCE_FUNC_STEP = """
1. 生成 ReadContext 函数
   - 格式为`resource{XXX}Read`，其中 `{XXX}` 为该资源的功能信息，例如：`resourcePublicationRead`
   - 该函数总共包含：函数名称、参数定义、创建client、构造请求参数、构造请求体、发送请求、解析结果、设置返回参数
   ```go
   func resourcePublicationRead(ctx context.Context, d *schema.ResourceData, meta interface{}) diag.Diagnostics {
       // 参数定义
   
   	   // 创建client
   
       // 构造请求参数
   	
   	   // 构造请求体
   	   
   	   // 发送请求
   	   
   	   // 解析结果
   	   
   	   // 设置返回参数
   	   
   	   // 设置其他API查询参数
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
3. 构造请求url
   - 将path参数替换为具体的值，禁止使用`utils.ReplacePathVariables`，使用`strings.ReplaceAll`
   - 如果查询参数是path参数，那么就需要添加分页参数之外的所有查询参数，通过`buildGet{XXX}QueryParams`方法实现，其中 `{XXX}` 为该资源的功能信息
   
   ```go
   getPath := client.Endpoint + httpUrl
   getPath = strings.ReplaceAll(getPath, "{project_id}", client.ProjectID)
   getPath = strings.ReplaceAll(getPath, "{instance_id}", d.Get("instance_id").(string))
   getPath += buildGetPublicationQueryParams(d)
   ```
4 构造请求体

   - 如果API不支持分页， 或者如果API支持分页，但是请求URI中的请求方法不为GET，那么需要生成请求体，参数名为：`getOpt`
   - 使用`golangsdk.RequestOpts`生成请求体，禁止使用`utils.BaseRequestOpts()`
   
   ```go
   getOpt := golangsdk.RequestOpts{
   	  KeepResponseBody: true,
      MoreHeaders: map[string]string{"Content-Type": "application/json"}
   }
   ```
5. 发送请求、解析结果
   1. 如果API不支持分页

      - 直接发送请求，解析结果
      - 最后使用`utils.PathSearch`从结果中获取结果中根据`id`获取数据，如果结果为`nil`，就直接返回`common.CheckDeletedDiag`错误，其中包含 `Method`，`URL`，`RequestId`，`Body`
   
      ```go
      getResp, err := client.Request("GET", getPath, &getOpt)
      if err != nil {
   	     return diag.Errorf("error retrieving RDS publication: %s", err)
      }
      
      getRespBody, err := utils.FlattenResponse(getResp)
      if err != nil {
   	     return diag.FromErr(err)
      }
      publication := utils.PathSearch(fmt.Sprintf("publications[?id=='%s']|[0]", d.Id()), getRespBody, nil)
      if publication == nil {
   	     return common.CheckDeletedDiag(d, golangsdk.ErrDefault404{
   		   ErrUnexpectedResponseCode: golangsdk.ErrUnexpectedResponseCode{
   			   Method:    "GET",
   			   URL:       "/v3/{project_id}/instances/{instance_id}/replication/publications",
   			   RequestId: "NONE",
   			   Body:      []byte(fmt.Sprintf("the RDS publication (%s) does not exist", d.Id())),
   			   },   , "error retrieving RDS publication")
      }
      ```

   2. 如果API支持分页，并且URI中的请求方法为 GET，那么直接使用 pagination 包中的 ListAllItems 函数
      - 分页参数为 limit + offset, ListAllItems中第二个参数qType为`offset`
      - 分页参数为 pagesize + page, ListAllItems中第二个参数qType为`page`
      - 分页参数为 limit + marker, ListAllItems中第二个参数qType为`marker`， 如果返回值中包含下一页的marker时，第四个参数中的MarkerField为下一页的marker
      - 最后使用`utils.PathSearch`从结果中获取结果中根据`id`获取数据，如果结果为`nil`，就直接返回`common.CheckDeletedDiag`错误，其中包含 `Method`，`URL`，`RequestId`，`Body`
    
      ```go
      getResp, err := pagination.ListAllItems(
          client,
          "offset",
          listPath,
          &pagination.QueryOpts{MarkerField: ""})
      getRespJson, err := json.Marshal(getResp)
      err != nil {
         return diag.FromErr(err)
      }
      getRespBody interface{}
      err = json.Unmarshal(getRespJson, &getRespBody)
      if err != nil {
         return diag.FromErr(err)
      }
       	
      publication := utils.PathSearch(fmt.Sprintf("publications[?id=='%s']|[0]", d.Id()), getRespBody, nil)
      if publication == nil {
        return common.CheckDeletedDiag(d, golangsdk.ErrDefault404{
           UnexpectedResponseCode: golangsdk.ErrUnexpectedResponseCode{
       		  Method:    "GET",
       		  URL:       "/v3/{project_id}/instances/{instance_id}/replication/publications",
       		  RequestId: "NONE",
   			  Body:      []byte(fmt.Sprintf("the RDS publication (%s) does not exist", d.Id())),
   		   },
        }, "error retrieving RDS publication")
      }
      ```
   3. 如果API支持分页，并且URI中的请求方法不为 GET
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
	  	getOpt.JSONBody = utils.RemoveNil(buildGetBackupDatabasesBodyParams(d, limit))
	  	getResp, err := client.Request("POST", getPath, &getOpt)
	  	if err != nil {
	  		return diag.Errorf("error retrieving RDS publication: %s", err)
	  	}
	  	getRespBody, err := utils.FlattenResponse(getResp)
	  	if err != nil {
	  		return diag.FromErr(err)
	  	}
	  	res = utils.PathSearch(fmt.Sprintf("publications[?id=='%s']|[0]", d.Id()), getRespBody, nil)
	  	if res != nil {
	  		break
	  	}
	  	publications = utils.PathSearch("publications", getRespBody, make([]interface{}, 0)).([]interface{})
	  	if len(publications) == 0 {
	  		break
	  	}
	  	
	  	offset += 100
	  }
	  if res == nil {
	  	return common.CheckDeletedDiag(d, golangsdk.ErrDefault404{
	  		ErrUnexpectedResponseCode: golangsdk.ErrUnexpectedResponseCode{
	  			Method:    "GET",
	  			URL:       "/v3/{project_id}/instances/{instance_id}/replication/publications",
	  			RequestId: "NONE",
	  			Body:      []byte(fmt.Sprintf("the RDS publication (%s) does not exist", d.Id())),
              },
          }, "error retrieving RDS publication")
      }
      ```
5. 设置返回参数
   - 如果该服务为全局函数，那么就不需要返回`region`，如果不是全局函数，那么就需要返回`region`
   - 如果参数类型不为对象或者列表，那么就直接从返回结果中获取后设置即可
   - 如果参数类型为对象或者列表， 需要使用函数 `flattenGet{XXX}Body` 解析当前查询结果，其中 `{XXX}` 为该资源的功能信息，如果有嵌套，那么`{XXX}` 为该资源的功能信息加上变量名，为驼峰格式
   
   ```go
   mErr := multierror.Append(
   	  d.Set("region", region),
   	  d.Set("publication_name", utils.PathSearch("publication_name", publication, nil)),
   	  d.Set("subscription_options", flattenPublicationSubscriptionOptions(publication)),
   	  d.Set("job_schedule", flattenPublicationJobSchedule(publication)),
   	  d.Set("is_select_all_table", strconv.FormatBool(utils.PathSearch("is_select_all_table", publication, false).(bool))),
   	  d.Set("tables", flattenPublicationTables(publication)),
   	  d.Set("subscription_count", utils.PathSearch("subscription_count", publication, nil)), 
   )
   
   return diag.FromErr(mErr.ErrorOrNil())
   ```
"""

SET_FIELD_FUNC_STEP = """
1. 生成设置其他API函数
   - 格式为`set{XXX}{YYY}`，其中 `{XXX}` 为该资源的功能信息，`{YYY}` 为参数名称，函数名最终采用驼峰格式
   - 该函数总共包含：构造请求url、构造请求体、构造查询参数、发送请求、解析结果、返回结果
   
   1.1 只有一个参数， 返回值为`error`
   
      ```go
      func setDcsInstanceAutoScaling(d *schema.ResourceData, client *golangsdk.ServiceClient) error {
          // 构造请求url
      	
      	   // 构造请求体
      	
      	   // 发送请求
      	
      	   // 解析结果
      	
      	   // 设置返回参数
      }
      ```
   
   1.2 有多个参数， 返回值为`[]error`
   
      ```go
      func setDcsInstanceAutoScaling(d *schema.ResourceData, client *golangsdk.ServiceClient) []error {
          // 构造请求url
      	
      	   // 构造请求体
      	
      	   // 发送请求
      	
      	   // 解析结果
      	
      	   // 设置返回参数
      }
      ```
   
2. 构造请求url
   - 将path参数替换为具体的值
   - 如果查询参数是path参数，那么就需要添加分页参数之外的所有查询参数，通过`buildGet{XXX}QueryParams`方法实现，其中 `{XXX}` 为该API要获取的功能信息
   
   ```go
   httpUrl := "v3/{project_id}/instances/{instance_id}/database/db-table-name"
   getPath := client.Endpoint + httpUrl
   getPath = strings.ReplaceAll(getPath, "{project_id}", client.ProjectID)
   getPath = strings.ReplaceAll(getPath, "{instance_id}", d.Get("instance_id").(string))
   getPath += buildGetDatabasesBackupQueryParams(d)
   ```

3. 构造请求体
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
   
4. 发送请求、解析结果
   1. 如果API不支持分页，直接发送请求，参数依次为：URI中的请求方法、请求URL、请求体、最后解析结果：
   
      ```go
      getResp, err := client.Request("GET", getPath, &getOpt)
      if err != nil {
      	 return diag.Errorf("error retrieving RDS backup databases: %s", err)
      }
      
      getRespBody, err := utils.FlattenResponse(getResp)
      if err != nil {
      	 log.Printf("[WARN] error fetching DCS instance(%s) hot key auto scan: %s", d.Id(), err)
        return nil
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
   	   log.Printf("[WARN] error fetching DCS instance(%s) hot key auto scan: %s", d.Id(), err)
   	   return nil
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
   
       1. 首先定义一个零时变量 `res` 保存查询结果
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
   	   log.Printf("[WARN] error fetching DCS instance(%s) hot key auto scan: %s", d.Id(), err)
   	   return nil
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
5. 设置返回参数
   - 设置返回结果到参数`d`中
   
   1. 只有一个返回参数
   
      ```go
      return d.Set("auto_scaling", utils.PathSearch("auto_scaling", getRespBody, nil))
      ```
      
   2. 如果有多个参数
   
      ```go
      var errs []error
      errs = append(errs, d.Set("hot_key_enable_auto_scan", utils.PathSearch("hot_key_enable_auto_scan", getRespBody, nil)))
      errs = append(errs, d.Set("hot_key_schedule_at", utils.PathSearch("hot_key_schedule_at", getRespBody, nil)))
      errs = append(errs, d.Set("hot_key_updated_at", utils.PathSearch("hot_key_updated_at", getRespBody, nil)))
   
      return errs
      ```
      
6. 添加其他API查询参数
   - 在`ReadContext 函数`中`设置其他API查询参数`位置添加其他API查询参数

   - 返回值类型为`error`
      ```go
      func resourcePublicationRead(ctx context.Context, d *schema.ResourceData, meta interface{}) diag.Diagnostics {
      	  // 设置其他API查询参数
      	  mErr = multierror.Append(mErr, setAvailabilityZone(d, instance))
      }
      ```

   - 返回值类型为`[]error`

   ```go
   func resourcePublicationRead(ctx context.Context, d *schema.ResourceData, meta interface{}) diag.Diagnostics {
   	  // 设置其他API查询参数
   	  mErr = multierror.Append(mErr, setDcsInstanceAutoScaling(d, instance)...)
   }
   ```
"""

READ_RESOURCE_PARAM_AND_FLATTEN_FUNC_STEP = """
1. 生成参数函数
   - 函数名为 `buildGet{XXX}QueryParams`， 其中 `{XXX}` 为该API要获取的功能信息，必须有参数`*schema.ResourceData`
   - 查询参数仅包含可以唯一查询到该资源的参数，如`id`
   - 将函数放到最后边
   
   ```go
   func buildGetInstanceQueryParams(id string) string {
       return fmt.Sprintf("?id={%v}", id)
   }
   ```
2. 生成请求体函数
   - 函数名为 `buildGet{XXX}BodyParams`， 其中 `{XXX}` 为该API要获取的功能信息
   - 查询参数仅包含可以唯一查询到该资源的参数，如`id`
   - 如果API中包含`offset`，那么使用分页参数`offset`，`limit`为API中允许设置的最大值，记为`maxLimit`，如果API是使用`page+size`分页，那么使用分页参数`page`
   - 将函数放到最后边
   
   ```go
   func buildGetBackupDatabasesBodyParams(id string, offset int) map[string]interface{} {
       bodyParams := map[string]interface{}{
   		  "id":     id,
   		  "limit":  100,
   		  "offset": offset,
     	}
   	  return bodyParams
   }
   ```
3. 生成解析结果函数
   1. 如果返回参数类型为 `list`：
   
      - 函数名为 `flattenGet{XXX}Body`， 其中 `{XXX}` 为该参数的驼峰形式，返回值类型为`[]interface{}`
      - 使用`utils.PathSearch`从结果中获取结果，将结果转为数组后遍历，依次将数组对象中的每个元素添加到对应的map中，然后添加到返回对象中
      - 如果数组元素中参数类型为对象或者列表，那么就调调用解析结果函数，在子函数中实现，函数名定义和当前函数名类似规则
      - 如果数组中元素有递归结果，那么就只保留第一层，下边的直接将结果转换为json格式的字符串
      - 将函数放到最后边
   
      ```go
      func flattenGetBackupDatabasesBody(resp interface{}) []interface{} {
        curJson := utils.PathSearch("instance_publications", resp, make([]interface{}, 0))
        curArray := curJson.([]interface{})
      	   res := make([]interface{}, 0, len(curArray))
      	   for _, v := range curArray {
      	     res = append(res, map[string]interface{}{
      	       "database_id":   utils.PathSearch("database_id", v, nil),
      		   "database_name": utils.PathSearch("database_name", v, nil),
      		   "database_attr": flattenGetBackupDatabasesDatabaseAttrBody(v),
             })
           }
   	     return res
      }
      ```
   
   2. 如果返回参数类型为对象：
   
      - 函数名为 `flattenGet{XXX}Body`， 其中 `{XXX}` 为该参数的驼峰形式，返回值类型为`[]interface{}`
      - 首先使用`utils.PathSearch`从结果中获取结果，将结果对象中的参数依次添加到一个map中，然后将该map添加到一个数组中
      - 如果对象中参数类型为对象或者列表，那么就调用递归调用解析结果函数，函数名定义和当前函数名类似规则
      - 最后返回结果
      
      ```go
      func flattenGetBackupDatabasesBody(resp interface{}) []interface{} {
        curJson := utils.PathSearch("instance_publications", resp, nil)
   	    if curJson == nil {
             return nil
   	    }
   	    res := []interface{}{
             map[string]interface{}{
               "database_id": utils.PathSearch("database_id", resp, nil),
         		 "database_name": utils.PathSearch("database_name", v, nil),
         		 "database_attr": flattenGetBackupDatabasesDatabaseAttrBody(v),
             },
           }
           return res
        }
      ```
"""

READ_SKILLS = {
    "read_resource_params_step" : {
        "name": "read_resource_params_step",
        "description": "生成查询resource params步骤，当需要生成查询resource params相关代码时触发",
        "content": READ_RESOURCE_PARAMS_STEP
    },
    "read_resource_func_step" : {
        "name": "read_resource_func_step",
        "description": "生成查询resource func步骤，当需要生成查询resource func相关代码时触发",
        "content": READ_RESOURCE_FUNC_STEP
    },
    "set_field_func_step" : {
        "name": "set_field_func_step",
        "description": "生成设置其他API查询参数步骤，当需要生成设置其他API查询参数相关代码时触发",
        "content": SET_FIELD_FUNC_STEP
    },
    "read_resource_param_and_flatten_func_step" : {
        "name": "read_resource_param_and_flatten_func_step",
        "description": "生成参数函数、请求体函数、解析结果函数步骤，当需要生成 参数函数、请求体函数、解析结果函数 相关代码时触发",
        "content": READ_RESOURCE_PARAM_AND_FLATTEN_FUNC_STEP
    },
}

READ_STEP = """
<available_sub_skills>
    {skill_items}
</available_sib_skills>

<step>
1. 如果没有提供查询资源API，那么就生成一个空函数：
   - 格式为`resource{{XXX}}Read`，其中 `{{XXX}}` 为该资源的功能信息，例如：`resourcePublicationRead`

   ```go
   func resourcePublicationRead(_ context.Context, _ *schema.ResourceData, _ interface{{}}) diag.Diagnostics {{
	   return nil
   }}
   ```
   
2. 如果提供了查询资源API：
   2.1 根据用户提供的查询资源API，获取API信息
   
   2.2 生成查询 resource params相关代码
      
   2.3 添加注释
      - 在`resource函数`前边加一个注释（示例中的`使用到的API`位置），格式为`// @API {{service}} {{method}} {{path}}`，其中`{{service}}`为当前服务名，`{{method}}`为URI中的请求方法，`{{path}}`为URI中的请求path
   
   2.4 生成查询resource func相关代码
      
   2.5 设置其他API查询参数相关代码
      
   2.6 生成参数函数、请求体函数、解析结果函数
</step>
"""

def apply_read_prompt_template() -> str:
    prompt = READ_STEP.format(
        skill_items=build_skills(READ_SKILLS),
        read_resource_params_step=READ_SKILLS["read_resource_params_step"]["description"],
        read_resource_func_step=READ_SKILLS["read_resource_func_step"]["description"],
        set_field_func_step=READ_SKILLS["set_field_func_step"]["description"],
        read_resource_param_and_flatten_func_step=READ_SKILLS["read_resource_param_and_flatten_func_step"]["description"],
    )
    return prompt
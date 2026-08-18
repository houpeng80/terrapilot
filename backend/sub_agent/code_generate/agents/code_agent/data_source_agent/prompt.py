from backend.sub_agent.code_generate.agents.code_agent.resource_agent.utils import build_skills

SCHEMA_FUNC_STEP = """
1. 该函数的名称格式为 `DataSource{XXX}`，其中 `{XXX}` 为该API要获取的功能信息，采用驼峰状格式，例如：`DataSourceBackupDatabases`
2. 如果用户提供了资源名，就从资源名中提取资源信息
3. 如果服务不是全局服务，就添加`region`，并且放到最前边，并且设置`Optional`和`Computed` 为`true`
4. 添加URI信息中的参数信息，忽略`project_id`，所有参数都设置`Required`为 `true`
5. 添加请求参数
   - 必填参数设置`Required`为 `true`，可选参数设置`Optional`为 `true`
   - 忽略分页参数
   - 类型为`bool`，那么就将类型设置为`string`，并且添加`ValidateFunc`限制，其他类型参数都禁止使用`ValidateFunc`：
      ```
      validation.StringInSlice([]string{"true", "false"}, false)
      ```
   - 参数类型为对象，对应的类型为list，在子函数中展示该对象的参数，子函数名格式为`{XXX}{YYY}Schema`，其中`{XXX}`为该API要获取的功能信息， `{YYY}` 为该参数的驼峰形式
6. 添加响应消息
   - 如果参数类型为对象，对应的类型为list，在子函数中展示该对象的参数，子函数名格式为`{XXX}{YYY}Schema`，其中`{XXX}`为该API要获取的功能信息， `{YYY}` 为该参数的驼峰形式
   - 所有的参数都设置`Computed`为 `true`
   - 表示返回数据数量的参数、请求信息、分页信息不返回，比如总数、请求ID
7. 在该函数前边加一个注释
   - 格式为`// @API {service} {method} {path}`，其中`{service}`为当前服务名，`{method}`为URI中的请求方法，`{path}`为URI中的请求path

```go
// @API RDS GET /v3/{project_id}/instances/{instance_id}/database/db-table-name
func DataSourceBackupDatabases() *schema.Resource {
    return &schema.Resource{
        ReadContext: dataSourceBackupDatabasesRead,

        Schema: map[string]*schema.Schema{
            "region": {
                Type:     schema.TypeString,
                Optional: true,
                Computed: true,
            },
            // ... URI参数
            "instance_id": {
                Type:     schema.TypeString,
				   Required: true,
            },
            // ... 请求参数
            "bucket_name": {
                Type:     schema.TypeString,
				   Required: true,
            },
			"bucket_exist": {
                Type:     schema.TypeString,
                Optional: true,
                ValidateFunc: validation.StringInSlice([]string{"true", "false"}, false),
            },
            "bucket_params": {
                Type:     schema.TypeList,
                Optional: true,
				   Elem:     &schema.Schema{Type: schema.TypeString},
            },
            // ... 其他查询参数

            // ...响应消息
            "databases": {
                Type:     schema.TypeList,
                Computed: true,
                Elem:     backupDatabaseDatabasesSchema(),
            },
            // ... 其他响应消息
        },
    }
}

func backupDatabaseDatabasesSchema() *schema.Resource {
    return &schema.Resource{
        Schema: map[string]*schema.Schema{
            "database_name": {
                Type:     schema.TypeString,
                Computed: true,
            },
            "backup_info": {
                Type:     schema.TypeList,
                Computed: true,
                Elem:     backupDatabaseDatabasesBackupInfoSchema(),
            },
            // ... 其他响应消息
        },
    }
}

func backupDatabaseDatabasesBackupInfoSchema() *schema.Resource {
    return &schema.Resource{
        Schema: map[string]*schema.Schema{
            "name": {
                Type:     schema.TypeString,
                Computed: true,
            },
            // ... 其他响应消息
        },
    }
}
```
"""

READ_FUNC_STEP = """
- 该函数总共包含：函数名称、参数定义、创建client、构造请求url、构造请求体、构造查询参数、发送请求、解析结果、生成资源id、设置返回参数

```go
func dataSourceRdsBackupDatabasesRead(_ context.Context, d *schema.ResourceData, meta interface{}) diag.Diagnostics {
    // 参数定义

	// 创建client

    // 构造请求参数

	// 构造请求体

	// 发送请求

	// 解析结果

	// 生成资源id

	// 设置返回参数

}
```

1. 参数定义，创建client

   - 创建client时，其中第一个参数为服务类型，错误信息中的服务类型需要大写

   ```go
   cfg := meta.(*config.Config)
   region := cfg.GetRegion(d)

   var mErr *multierror.Error

   client, err := cfg.NewServiceClient("rds", region)
   if err != nil {
   	return diag.Errorf("error creating RDS client: %s", err)
   }
   ```

2. 构造请求url

   - 将path参数替换为具体的值
   - 如果查询参数是path参数，那么就需要添加分页参数之外的所有查询参数，通过`buildGet{XXX}QueryParams`方法实现，其中 `{XXX}` 为该API要获取的功能信息

  1. 如果该API不支持分页，那么参数名应为：`getPath`

   ```go
   httpUrl := "v3/{project_id}/instances/{instance_id}/database/db-table-name"
   getPath := client.Endpoint + httpUrl
   getPath = strings.ReplaceAll(getPath, "{project_id}", client.ProjectID)
   getPath = strings.ReplaceAll(getPath, "{instance_id}", d.Get("instance_id").(string))
   getPath += buildGetDatabasesBackupQueryParams(d)
   ```

  2. 如果该API支持分页，那么参数名应为：`listPath`

   ```go
   httpUrl := "v3/{project_id}/instances/{instance_id}/database/db-table-name"
   listPath := client.Endpoint + httpUrl
   listPath = strings.ReplaceAll(listPath, "{project_id}", client.ProjectID)
   listPath = strings.ReplaceAll(listPath, "{instance_id}", d.Get("instance_id").(string))
   listPath += buildGetDatabasesBackupQueryParams(d)
   ```

3. 构造请求体

   1. 如果API支持分页，并且请求URI中的请求方法不为GET，那么需要生成请求体，参数名为`listOpt`：

      - 使用`golangsdk.RequestOpts`生成请求体，禁止使用`utils.BaseRequestOpts()`

      ```go
      listOpt := golangsdk.RequestOpts{
   	     KeepResponseBody: true,
   	     MoreHeaders: map[string]string{"Content-Type": "application/json"},
      }
      ```

   2. 如果API不支持分页，那么就需要生成请求体，参数名为`getOpt`：

      - 使用`golangsdk.RequestOpts`生成请求体，禁止使用`utils.BaseRequestOpts()`

      ```go
      getOpt := golangsdk.RequestOpts{
   	     KeepResponseBody: true,
   	     MoreHeaders: map[string]string{"Content-Type": "application/json"},
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
   	     return diag.FromErr(err)
      }
      ```

   2. 如果API支持分页，并且URI中的请求方法为 GET，根据分页参数选择合适的分页逻辑

      - 分页参数为 limit + offset, ListAllItems中第二个参数qType为`offset`
      - 分页参数为 pagesize + page, ListAllItems中第二个参数qType为`page`
      - 分页参数为 limit + marker, ListAllItems中第二个参数qType为`marker`， 如果返回值中包含下一页的marker时，第四个参数中的MarkerField为下一页的marker

      ```go
      listResp, err := pagination.ListAllItems(
   	     client,
   	     "offset",
   	     listPath,
   	     &pagination.QueryOpts{MarkerField: ""})
      if err != nil {
   	     return diag.Errorf("error retrieving RDS publications: %s", err)
      }
      listRespJson, err := json.Marshal(listResp)
      if err != nil {
   	     return diag.FromErr(err)
      }
      var listRespBody interface{}
      err = json.Unmarshal(listRespJson, &listRespBody)
      if err != nil {
   	     return diag.FromErr(err)
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
5. 生成资源id

   - 需要引入包 `"github.com/google/uuid"`
   - 使用`uuid.GenerateUUID()`生成UUID

   ```go
   dataSourceId, err := uuid.NewRandom()
   if err != nil {
   	return diag.Errorf("unable to generate ID: %s", err)
   }
   d.SetId(dataSourceId)
   ```

6. 设置返回参数

   1. API支持分页，并且URI中的请求方法不为 GET

      - 如果该服务为全局函数，那么就不需要返回`region`，如果不是全局函数，那么就需要返回`region`
      - 结果已经在循环中解析完成，直接赋值即可

      ```go
      mErr = multierror.Append(
   	     d.Set("region", region),
   	     d.Set("databases", res), 
      )
      return diag.FromErr(mErr.ErrorOrNil())
      ```

   2. API不支持分页，或者API支持分页，但是请求方法为 GET

      - 如果该服务为全局函数，那么就不需要返回`region`，如果不是全局函数，那么就需要返回`region`
      - 如果参数类型不为对象或者列表，那么就直接从返回结果中获取后设置即可
      - 如果参数类型为对象或者列表， 需要使用函数 `flattenGet{XXX}Body` 解析当前查询结果，其中 `{XXX}` 为该API要获取的功能信息

      ```go
      mErr = multierror.Append(
   	     d.Set("region", region),
   	     d.Set("attribute", utils.PathSearch("attribute", v, nil)),
   	     d.Set("databases", flattenGetBackupDatabasesBody(getRespBody)), 
      )
      return diag.FromErr(mErr.ErrorOrNil())
      ```
"""

PARAM_AND_FLATTEN_FUNC_STEP = """
1. 生成参数函数

   - 函数名为 `buildGet{XXX}QueryParams`， 其中 `{XXX}` 为该API要获取的功能信息，必须有参数`*schema.ResourceData`
   - 如果参数为 `Required`，那么不需要判断，直接添加到结果即可，如果分页参数为必填，也需要添加上
   - 如果参数为 `Optional`，那么需要先判断是否为空
   - 如果参数类型为`bool`，但是通过`ValidateFunc`函数限制为`true`和`false`，那么需要先将其转换为`bool`，然后再添加到结果
   - 如果参数类型为`list`，那么需要遍历该链表，然后逐个添加到结果中
   - 将函数放到最后边

   ```go
   func buildGetBackupDatabasesQueryParams(d *schema.ResourceData) string {
       res := ""
   	   res = fmt.Sprintf("%s&version_name=%v", res, v)
       if v, ok := d.GetOk("bucket_name"); ok {
       	res = fmt.Sprintf("%s&bucket_name=%v", res, v)
       }
       if v, ok := d.GetOk("bucket_exist"); ok {
           bucketExist, _ := strconv.ParseBool(v["bucket_exist"].(string))
       	res = fmt.Sprintf("%s&is_flexus=%v", res, v)
       }
       if v, ok := d.GetOk("bucket_params"); ok {
   		for _, param := range v.([]interface{}) {
   			res = fmt.Sprintf("%s&bucket_params=%v", res, param)
   		}
   	}
       // ... 其他查询参数

       if res != "" {
       	res = "?" + res[1:]
       }
       return res
   }
   ```

2. 生成请求体函数

   - 函数名为 `buildGet{XXX}BodyParams`， 其中 `{XXX}` 为该API要获取的功能信息
   - 如果API中包含`offset`，那么使用分页参数`offset`，`limit`为API中允许设置的最大值，记为`maxLimit`，如果API是使用`page+size`分页，那么使用分页参数`page`
   - 该请求体要和上边构建请求参数的函数有区别，参数判空不要使用`d.GetOk`，使用`utils.ValueIgnoreEmpty`
   - 将函数放到最后边

   ```go
   func buildGetBackupDatabasesBodyParams(d *schema.ResourceData, offset int) map[string]interface{} {
   	  bodyParams := map[string]interface{}{
   		"states":   utils.ValueIgnoreEmpty(d.Get("states")),
   		"group_id": utils.ValueIgnoreEmpty(d.Get("group_id")),
   		"limit":    100,
   		"offset":    offset,
   	  }
   	  return bodyParams
   }
   ```

3. 解析结果函数

   1. 如果返回参数类型为 list：

      - 函数名为 `flattenGet{XXX}Body`， 其中 `{XXX}` 为该参数的驼峰形式，返回值类型为`[]interface{}`
      - 首先使用`utils.PathSearch`从结果中获取结果，将结果转为数组后遍历，依次将数组对象中的每个元素添加到对应的map中，然后添加到返回对象中
      - 如果数组元素中参数类型为对象或者列表，那么就调调用解析结果函数，在子函数中实现，函数名定义和当前函数名类似规则
      - 如果数组中元素有递归结果，那么就只保留第一层，下边的直接将结果转换为json格式的字符串
      - 最后返回结果
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
      			database_attr": flattenGetBackupDatabasesDatabaseAttrBody(v),
      		})
   	    }
        return res
      }
      ```

   2. 如果返回参数类型为对象：

      - 函数名为 `flattenGet{XXX}Body`， 其中 `{XXX}` 为该参数的驼峰形式，返回值类型为`[]interface{}`
      - 首先使用`utils.PathSearch`从结果中获取结果，奖结果对象中的参数依次添加到一个map中，然后将该map添加到一个数组中
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

SKILLS = {
    "schema_func_step" : {
        "name": "schema_func_step",
        "description": "生成schema func步骤，当需要生成schema func相关代码时触发",
        "content": SCHEMA_FUNC_STEP
    },
    "read_func_step" : {
        "name": "read_func_step",
        "description": "生成read func步骤，当需要生成read func相关代码时触发",
        "content": READ_FUNC_STEP
    },
    "param_and_flatten_func_step" : {
        "name": "param_and_flatten_func_step",
        "description": "生成param and flatten步骤，当需要生成param and flatten相关代码时触发",
        "content": PARAM_AND_FLATTEN_FUNC_STEP
    }
}

DATA_SOURCE_PROMPT_TEMPLATE = """
<role>
你是{agent_name}，一个terraform data source代码生成的超级agent。
</role>

<thinking_style>
- 在采取行动之前，请简洁而有策略地思考用户的请求。
- 将任务分解：哪些部分很明确？哪些部分含糊不清？缺少什么？
- 优先检查：如有任何不清楚、遗漏或存在多种解释的地方，您必须首先寻求澄清——请勿继续工作。
- 关键点：思考之后，你必须向用户提供实际的回复。思考是为了规划，回复是为了交付。
- 你的回答必须包含实际答案，而不仅仅是提及你的想法。
</thinking_style>

<available_skills>
    {skill_items}
</available_skills>

<note>
- 在执行以下步骤时，如果涉及到了具体技能，那么就先用skill_load工具去获取技能内容，资源类型为data_source，然后再按照技能规范执行
- 执行时按步骤依次执行，每一步生成代买以后再执行下一步，每次只加载本步骤所需要的skill，然后就生成该步骤的代码
- 不要等所有的skill都加载进来才生成代码，也不要一次性加载所有的skill
- 最终输出结果只包含最终的完整代码，其他都不需要
</note>

<step>
1. 数据获取
  根据用户提供的API地址获取网页信息

2. 生成schema func相关代码

3. 生成read func相关代码

4. 生成param and flatten相关代码

5. 在生成结果前边添加包信息，以及引入所需要的包信息

6. 将最终生成的完整代码写到文件中，路径为{repo_root}\\huaweicloud\\services\\service_name\\resource_name.go,
   service_name为服务名，resource_name为资源名，如果用户已经提供，就使用用户提供的名称，如果没提供就自动生成，格式为data_source_SSS_XXX`，其中`SSS` 为该service_name, `XXX` 为该API要获取的功能信息

</step>
"""

def apply_prompt_template(agent_name: str, repo_root: str) -> str:
    prompt = DATA_SOURCE_PROMPT_TEMPLATE.format(
        agent_name=agent_name or "Terraform code generate agent",
        skill_items=build_skills(SKILLS),
        schema_func_step=SKILLS["schema_func_step"]["description"],
        read_func_step=SKILLS["read_func_step"]["description"],
        param_and_flatten_func_step=SKILLS["param_and_flatten_func_step"]["description"],
        repo_root=repo_root,
    )
    return prompt


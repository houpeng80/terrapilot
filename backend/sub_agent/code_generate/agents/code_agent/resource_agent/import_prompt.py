IMPORT_STEP = """
1. 如果没有提供查询resource的API，那么不需要添加导入信息
2. 如果有提供查询resource的API
   2.1 如果没有提供导入id格式 
      - 直接使用默认导入方法，在`resource函数`中添加导入信息（resource函数中的`导入信息`位置）
      ```go
      Importer: &schema.ResourceImporter{
      	  StateContext: schema.ImportStatePassthroughContext,
      },
      ```
   2.2 如果有提供导入id格式
      2.2.1 使用自定义导入函数，函数名为： `resource{XXX}ImportState`，其中 `{XXX}` 为该资源的功能信息
      ```go
      Importer: &schema.ResourceImporter{
	      StateContext: resourceInstanceImportState,
      },
      ```
      2.2.2 生成自定义导入函数
      - 函数名为： `resource{XXX}ImportState`，其中 `{XXX}` 为该资源的功能信息
      - 函数首先使用`strings.Split`对导入id（`d.Id()`），分割符号为`/`
      - 分割结果长度不符合，那么就直接返回异常
      - 重新设置资源id，一般为分割后结果的最后一个元素
      - 将分割结果设置到对应的参数中，返回结果
      - 将该函数放到最后边

      ```go
      func resourceInstanceImportState(_ context.Context, d *schema.ResourceData, _ interface{}) ([]*schema.ResourceData,
      	 error) {
      	 parts := strings.Split(d.Id(), "/")
      
      	 if len(parts) != 2 {
      		return nil, errors.New("invalid format specified for import ID, must be <instance_id>/<id>")
      	 }
      
      	 d.SetId(parts[1])
      	 mErr := multierror.Append(nil,
      		d.Set("instance_id", parts[0]),
      	 )
      
      	 return []*schema.ResourceData{d}, mErr.ErrorOrNil()
      }
      ```
"""

def apply_import_prompt_template() -> str:
    return IMPORT_STEP
## V13.5.0 (2025-11-09)

### Feat

- config/global.yaml 新增 江湖长梦.open 配置项
- 增加上海时区支持

### Fix

- **LogManager**: 修复 Loguru 格式化错误并统一上海时间

### Refactor

- 移除 IS_ACTIVATE_ACCOUNT 字段
- 优化配置管理和错误处理
- 移除「重建配置」功能
- 将江湖长梦从other模块迁移至two模块
- 将日期时间相关代码统一到DateTime类中
- DaLeDou 类增加 get_backpack_number 公共方法
- 移除 log 模块
- 微信通知加入门派兑换日志
- **config**: 将create_account_config返回值类型改为Path
- 移除tasks包中的函数文档字符串

## V13.4.3 (2025-11-01)

### Fix

- 修复万圣节TypeError错误

### Refactor

- 万圣节兑换奖励改为每种礼包仅兑换一次

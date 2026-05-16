---
version: "2.1"
rules:
  nodejs_standards:
    - "使用TypeScript编写所有业务代码"
    - "使用ESModule (import/export) 语法"
    - "错误处理使用async/await + try/catch"
    - "所有API端点添加请求验证"
    - "使用环境变量管理配置"
    - "数据库查询使用ORM（Prisma/TypeORM）"
    - "使用Zod或Joi进行schema验证"
    - "日志使用结构化格式"
---

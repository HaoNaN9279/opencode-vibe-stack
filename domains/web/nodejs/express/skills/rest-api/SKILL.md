---
name: rest-api
description: 创建 Express REST API 端点，包含标准的 GET/POST 路由和错误处理
license: MIT
compatibility: opencode
metadata:
  domain: web.nodejs.express
---

## What I do

生成 Express Router 模板，包含 GET 集合查询和 POST 创建资源两个标准端点，带有 try/catch 错误处理。

## When to use me

当需要在 Express 项目中创建新的 REST API 端点、构建 CRUD 路由时应使用。

## Template

```typescript
import {{ Router, Request, Response }} from 'express';

const router = Router();

// GET /api/{resource}
router.get('/', async (req: Request, res: Response) => {{
    try {{
        // 查询逻辑
        res.json({{ data: [] }});
    }} catch (error) {{
        res.status(500).json({{ error: 'Internal Server Error' }});
    }}
}});

// POST /api/{resource}
router.post('/', async (req: Request, res: Response) => {{
    try {{
        // 创建逻辑
        res.status(201).json({{ data: {{}} }});
    }} catch (error) {{
        res.status(400).json({{ error: 'Bad Request' }});
    }}
}});

export default router;
```

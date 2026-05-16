---
name: "web.nodejs.express.rest-api"
description: "创建Express REST API端点"
triggers:
  - "创建REST API"
  - "Express路由"
  - "API端点"
vibe: "clean-architecture"
dependencies:
  - "core.skills.code-refactor"
---

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

# Cloudflare Workers 部署指南

## 前置条件
- Cloudflare账号
- wrangler CLI（`npm install -g wrangler`）

## 部署步骤

### 1. 登录Cloudflare
```bash
wrangler login
```

### 2. 部署Worker
```bash
wrangler deploy
```

### 3. 设置环境变量（重要！）
部署完成后，需要在Cloudflare Dashboard中设置API Key：

1. 访问 https://dash.cloudflare.com/
2. 进入 Workers & Pages
3. 找到 `drama-marketing-api`
4. 点击 Settings → Variables
5. 添加环境变量：
   - Name: `DASHSCOPE_API_KEY`
   - Value: `sk-sp-f65d5e54bb3049e6a92b7a4de6617ef7`
   - 勾选 "Encrypt"（加密）
6. 点击 Save

### 4. 获取Worker URL
部署成功后，会得到一个URL，类似：
```
https://drama-marketing-api.你的账号.workers.dev
```

### 5. 更新前端配置
将Worker URL更新到 `index.html` 中的 `API_ENDPOINT` 配置。

## 测试API
```bash
curl -X POST https://drama-marketing-api.你的账号.workers.dev \
  -H "Content-Type: application/json" \
  -d '{"plan": {...}}'
```

## 安全建议
- ✅ API Key已加密存储在Cloudflare环境变量中
- ✅ 不会暴露在前端代码
- ⚠️ 部署完成后，建议去阿里云禁用当前Key，创建新Key

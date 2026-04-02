# 前端部署指南

本指南面向初学者，详细说明如何部署 SOCRATES 数学 tutoring 系统的前端。

## 目录

- [环境准备](#环境准备)
- [本地开发](#本地开发)
- [构建生产版本](#构建生产版本)
- [部署到 Vercel（推荐）](#部署到-vercel推荐)
- [部署到 Netlify](#部署到-netlify)
- [部署到自己的服务器](#部署到自己的服务器)
- [常见问题](#常见问题)

---

## 环境准备

### 1. 安装 Node.js

前端项目需要 Node.js 环境。

**下载安装：**

- 访问 https://nodejs.org/
- 下载 LTS（长期支持版）版本
- 双击安装，一路下一步即可

**验证安装：**

```bash
node -v
npm -v
```

### 2. 安装 Git

```bash
# Windows: https://git-scm.com/download/win
# macOS: 已自带
# Ubuntu/Debian: sudo apt install git
```

**验证安装：**

```bash
git -v
```

### 3. 获取代码

```bash
# 克隆仓库
git clone <仓库地址>

# 进入前端目录
cd D:\Socrates\frontend
# 或者如果是 Linux/macOS:
# cd frontend
```

---

## 本地开发

在本地运行开发服务器，实时预览修改。

### 步骤

```bash
# 1. 进入前端目录
cd D:\Socrates\frontend

# 2. 安装依赖（首次运行或依赖更新后）
npm install

# 3. 启动开发服务器
npm run dev
```

### 预期输出

```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:3000/
  ➜  Network: http://192.168.x.x:3000/
```

### 访问页面

打开浏览器，访问 http://localhost:3000

### 停止开发服务器

在终端按 `Ctrl + C`

---

## 构建生产版本

将代码打包成静态文件，用于部署到生产环境。

### 步骤

```bash
# 1. 进入前端目录
cd D:\Socrates\frontend

# 2. 构建生产版本
npm run build
```

### 预期输出

```
vite v5.x.x building for production...
✓ 756 modules transformed.
dist/index.html                 0.47 kB │ gzip:  0.35 kB
dist/assets/index-xxxxx.css    31.00 kB │ gzip:  5.59 kB
dist/assets/index-xxxxx.js   649.08 kB │ gzip: 196.81 kB
✓ built in 2.92s
```

### 输出目录

构建完成后，所有静态文件在 `dist/` 目录中。

---

## 部署到 Vercel（推荐）

Vercel 是免费且最简单的方式，GitHub 连接即可自动部署。

### 前提条件

- GitHub 账号
- 代码已推送到 GitHub

### 步骤

#### 方法一：网页部署（最简单）

1. **推送代码到 GitHub**

   ```bash
   git init
   git add .
   git commit -m "first commit"
   git branch -M main
   git remote add origin https://github.com/你的用户名/socrates-frontend.git
   git push -u origin main
   ```

2. **登录 Vercel**
   - 访问 https://vercel.com
   - 用 GitHub 账号登录

3. **导入项目**
   - 点击 "New Project"
   - 选择你的 GitHub 仓库
   - 点击 "Import"

4. **配置项目**
   - Framework Preset: `Vite`（通常自动检测）
   - Root Directory: `./` 或 `frontend`
   - Build Command: `npm run build`
   - Output Directory: `dist`

5. **点击 Deploy**
   - 等待 1-2 分钟
   - 获得部署 URL，如：`https://your-project.vercel.app`

#### 方法二：命令行部署

```bash
# 1. 安装 Vercel CLI
npm install -g vercel

# 2. 登录
vercel login

# 3. 进入前端目录
cd D:\Socrates\frontend

# 4. 部署（首次）
vercel

# 5. 生产部署
vercel --prod
```

### 自动部署

每次推送到 GitHub，Vercel 会自动重新部署。

---

## 部署到 Netlify

另一个免费选择，类似 Vercel。

### 步骤

1. **推送代码到 GitHub**

   ```bash
   git init
   git add .
   git commit -m "first commit"
   git remote add origin https://github.com/你的用户名/socrates-frontend.git
   git push -u origin main
   ```

2. **登录 Netlify**
   - 访问 https://netlify.com
   - 用 GitHub 账号登录

3. **创建站点**
   - 点击 "Add new site" → "Import an existing project"
   - 选择 GitHub 仓库

4. **配置**
   - Build command: `npm run build`
   - Publish directory: `dist`

5. **点击 Deploy site**

### 绑定自定义域名（可选）

在 Site Settings → Domain management 中添加自定义域名。

---

## 部署到自己的服务器

如果你有自己的服务器（VPS、云服务器等）。

### 服务器要求

- Nginx 或 Apache
- Node.js（仅用于开发模式）

### 步骤

#### 1. 在本地构建

```bash
cd D:\Socrates\frontend
npm run build
```

#### 2. 上传到服务器

```bash
# 使用 scp（Linux/macOS）
scp -r dist/* user@your-server:/var/www/html/

# Windows 可用 PowerShell
scp -r dist\* user@your-server:/var/www/html/
```

#### 3. 配置 Nginx

SSH 登录服务器，创建 Nginx 配置文件：

```bash
sudo nano /etc/nginx/sites-available/socrates
```

写入以下内容：

```nginx
server {
    listen 80;
    server_name your-domain.com;  # 你的域名或 IP

    root /var/www/html;  # 刚才上传的目录
    index index.html;

    # 处理 SPA 路由（所有路径都返回 index.html）
    location / {
        try_files $uri $uri/ /index.html;
    }

    # 静态资源缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # API 代理（如果前后端同域名）
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

启用配置：

```bash
sudo ln -s /etc/nginx/sites-available/socrates /etc/nginx/sites-enabled/
sudo nginx -t  # 测试配置
sudo systemctl restart nginx
```

#### 4. 申请 SSL 证书（推荐）

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

#### 5. 目录结构

部署完成后，服务器目录结构：

```
/var/www/html/
├── index.html
├── assets/
│   ├── index-xxxxx.css
│   └── index-xxxxx.js
└── (其他静态资源)
```

---

## 常见问题

### Q1: npm install 失败

**问题：** 安装依赖时报错

**解决方案：**

```bash
# 清除缓存后重试
npm cache clean --force
rm -rf node_modules
npm install
```

### Q2: 端口被占用

**问题：** `Port 3000 is already in use`

**解决方案：**

```bash
# 方法1：使用其他端口
npm run dev -- --port 3001

# 方法2：关闭占用端口的进程
# Windows
netstat -ano | findstr :3000
taskkill /PID <进程ID> /F

# Linux/macOS
lsof -i :3000
kill -9 <进程ID>
```

### Q3: 构建失败 TypeScript 错误

**问题：** `npm run build` 报 TS 错误

**解决方案：**

```bash
# 查看具体错误
npx tsc --noEmit

# 常见错误：类型不匹配
# 检查 src 目录下的 .ts 和 .tsx 文件
```

### Q4: 页面空白

**问题：** 部署后页面空白

**解决方案：**

1. 检查浏览器控制台（F12）是否有错误
2. 如果是 SPA，确保服务器配置了 `try_files $uri $uri/ /index.html`
3. 检查静态资源路径是否正确

### Q5: API 请求失败

**问题：** 前端无法请求后端 API

**解决方案：**

1. 检查后端服务是否运行
2. 如果前后端分开部署，需要配置 CORS 或 Nginx 反向代理
3. Vercel/Netlify 部署时可设置环境变量：
   ```
   VITE_API_URL=https://your-backend-domain.com/api
   ```

---

## 快速命令汇总

```bash
# 安装依赖
npm install

# 开发模式
npm run dev

# 构建生产版本
npm run build

# 预览构建结果
npm run preview
```

---

## 项目结构

```
frontend/
├── dist/                    # 构建输出目录（部署时上传此目录）
├── src/
│   ├── components/          # React 组件
│   │   ├── charts/          # 图表组件
│   │   ├── layout/          # 布局组件
│   │   └── shared/          # 共享组件
│   ├── mock/                # Mock 数据
│   ├── pages/               # 页面组件
│   ├── types/               # TypeScript 类型定义
│   ├── app/
│   │   └── router.tsx       # 路由配置
│   ├── App.tsx
│   ├── main.tsx
│   └── index.css            # 全局样式（TailwindCSS）
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts           # Vite 配置
└── tailwind.config.js       # TailwindCSS 配置
```

---

## 下一步

部署完成后：

1. **配置后端 API 地址**（如果前后端分离）
2. **配置环境变量**：
   ```bash
   # 创建 .env 文件
   VITE_API_URL=https://your-backend.com/api
   ```
3. **监控和日志**：配置 Sentry 或类似工具进行错误追踪

祝你部署成功！ 🎉

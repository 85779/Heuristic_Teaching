# Socrates — 高中数学智能辅导系统

后端：FastAPI + MongoDB + DashScope LLM。前端：React + TypeScript + Vite + TailwindCSS。394 个测试全部通过。

---

## 快速开始

```bash
# 后端
cd backend
pip install -e ".[dev]"
echo "DASHSCOPE_API_KEY=sk-xxx" > .env
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 前端
cd frontend
npm install
npx vite --host 0.0.0.0 --port 5173
```

浏览器打开 `http://localhost:5173`。

---

## 产品能力一览

### 学生使用
1. **输入题目和作答** → 系统自动批改，指出具体错误（概念错误 / 计算错误 / 遗漏）
2. **做错了** → 同时看到错误原因 + 正确参考解法
3. **卡住了** → 获取分级提示，从方向引导逐步到完整步骤
4. **做完一道题** → 自动推荐下一道合适的练习题
5. **查看画像** → 看到自己的学习特征变化

### 老师使用
6. **查看学生画像** → 维度比例 + 趋势分析
7. **获取教学策略** → 讲授/练习/讨论的具体比例建议

---

## 系统架构

```
Module 1 解题 ──→ Module 2 干预 ──→ Module 4 画像 ──→ Module 3 推荐
                   (EventBus 自动串联)                   Module 5 教学策略
                                                         Module 6 知识库
```

---

## Module 1：解题系统（8 个 API）

| 端点 | 方法 | 说明 |
|------|:--:|------|
| `/api/v1/solving/reference` | POST | 参考解法 + 链式验证评估（做错也能看解法） |
| `/api/v1/solving/sessions` | POST | 创建 4 阶段 Polya 解题会话 |
| `/api/v1/solving/sessions/{id}` | GET | 查询会话状态 |
| `/api/v1/solving/sessions/{id}/orientation` | POST | 阶段1：定向 |
| `/api/v1/solving/sessions/{id}/reconstruction` | POST | 阶段2：重构 |
| `/api/v1/solving/sessions/{id}/transformation` | POST | 阶段3：变换 |
| `/api/v1/solving/sessions/{id}/verification` | POST | 阶段4：验证 |
| `/api/v1/solving/sessions/{id}/complete` | POST | 完成 |

### 链式验证评估（90% 准确率）

第1步：LLM 不看学生答案，独立算出正确答案
第2步：拿着标准答案，逐行对比学生作答 → 指出概念错误/计算错误/遗漏
做错了仍然生成参考解法（学生同时看到错误原因 + 正确解法）

```bash
curl -X POST http://localhost:8000/api/v1/solving/reference \
  -H "Content-Type: application/json" \
  -d '{"problem":"求 f(x)=x^2-4x+3 的极值","student_work":"令 f(x)=0,x=1或3"}'
```

---

## Module 2：干预系统（7 个 API）

| 端点 | 方法 | 说明 |
|------|:--:|------|
| `/api/v1/interventions` | POST | 创建干预（独立调用，无需前置解题状态） |
| `/api/v1/interventions/feedback` | POST | 学生反馈 |
| `/api/v1/interventions/end` | POST | 结束干预 |
| `/api/v1/interventions/escalate` | POST | 强制升级 |
| `/api/v1/interventions/{id}` | GET | 查询干预详情 |
| `/api/v1/interventions/{id}/accept` | POST | 接受提示 |
| `/api/v1/interventions/{id}/dismiss` | POST | 忽略提示 |

### R/M 双维度九级提示

**R 维度（知识资源型）— 帮学生补充缺失的知识**

| 级别 | 提示程度 | 示例（题目：求极值，学生已求出 f'） |
|------|------|------|
| R1 | 方向引导 | "你算出了导数，导数能告诉你关于原函数的什么信息？" |
| R2 | 知识指路 | "需要用到导数符号判别法——导数为零的点与极值有什么关系？" |
| R3 | 第一步形式 | "令 f'(x)=0 解出临界点。现在解方程 3x²-12x+9=0。" |
| R4 | 完整步骤 | 完整计算过程和中间结果 |

**M 维度（元认知型）— 帮学生激活策略思维**

| 级别 | 提示程度 | 示例 |
|------|------|------|
| M1 | 反思引导 | "你做的步骤在朝着目标前进吗？求极值需要什么条件？" |
| M2 | 方向指引 | "下一步需要分析导数符号变化来判断单调性。" |
| M3 | 策略推荐 | "用二阶导数判断极值类型，比符号表更直接。" |
| M4 | 路径对比 | "符号表法和二阶导法各有利弊，你倾向哪种？" |
| M5 | 完整思路 | 完整解题逻辑链 + 类比标准题型 |

```bash
curl -X POST http://localhost:8000/api/v1/interventions \
  -H "Content-Type: application/json" \
  -d '{"student_id":"demo","session_id":"demo","student_input":"stuck","intervention_type":"hint"}'
```

---

## Module 3：推荐系统（2 个 API）

| 端点 | 方法 | 说明 |
|------|:--:|------|
| `/api/v1/recommendations/recommend` | POST | 获取推荐题目 |
| `/api/v1/recommendations/health` | GET | 健康检查 |

### 功能
- LLM 实时生成新题（非题库）+ 答案 + 提示
- 自动识别题目关联知识点（CJK ngram 匹配 175 KP）
- 三种策略：SAME_KP（同知识点）/ VARIATION（变式）/ BALANCED（均衡）
- 19 道备用精选题，LLM 不可用时自动切换

```bash
curl -X POST http://localhost:8000/api/v1/recommendations/recommend \
  -H "Content-Type: application/json" \
  -d '{"student_id":"demo","trigger":{"outcome":"SOLVED","current_problem_kps":["KP_3_13"],"current_method":"","current_difficulty":2,"session_id":"demo"}}'
```

---

## Module 4：学生画像（5 个 API）

| 端点 | 方法 | 说明 |
|------|:--:|------|
| `/api/v1/profile/{id}` | GET | 完整画像 |
| `/api/v1/profile/{id}/dimension-ratio` | GET | 维度比例 |
| `/api/v1/profile/{id}/routing-hint` | GET | 路由提示 |
| `/api/v1/profile/{id}/intervention` | POST | 记录干预 |
| `/api/v1/profile/health` | GET | 健康检查 |

### 画像指标
- **dimension_ratio**：R 型（知识缺口）vs M 型（策略薄弱）占比
- **ratio_trend**：线性回归趋势分析（rising/falling/stable）
- **路由提示**：告知其他模块学生偏向类型和薄弱点

```bash
curl http://localhost:8000/api/v1/profile/demo
```

---

## Module 5：教学策略（3 个 API）

| 端点 | 方法 | 说明 |
|------|:--:|------|
| `/api/v1/teaching/strategy` | POST | 获取策略 |
| `/api/v1/teaching/strategy/{id}` | GET | 查询 |
| `/api/v1/teaching/health` | GET | 健康检查 |

七种自适应策略（R偏+恶化 / R偏+稳定 / M偏+改善 / M偏 / 均衡 × 经验等级）

```bash
curl -X POST http://localhost:8000/api/v1/teaching/strategy \
  -H "Content-Type: application/json" -d '{"student_id":"demo"}'
```

---

## Module 6：知识库

298 篇文档嵌入索引（175 知识点 + 13 方法 + 110 题型），DashScope Embedding API 实现，零外部依赖。

---

## 前端

4 个页面，Vite 代理 `/api` → `:8000`：

| 页面 | 路径 | 功能 |
|------|------|------|
| 首页 | `/` | 系统状态 + 入口 |
| 学习 | `/study` | 题目输入 → 评估 → 解法 → 提示 → 推荐 |
| 画像 | `/profile/:id` | R/M 维度比 + 指标 |
| 教学 | `/teaching/:id` | 讲授/练习/讨论比例 |

---

## 核心指标

| 指标 | 数值 |
|------|------|
| 测试用例 | 394 个，全部通过 |
| API 端点 | 26 个 |
| 知识点 | 175 个，12 章全覆盖 |
| 提示级别 | 9 级（R1-R4 + M1-M5） |
| 评估准确率 | 90%（10 题 benchmark） |
| 代码规模 | 后端 16,500 行 / 前端 1,200 行 |

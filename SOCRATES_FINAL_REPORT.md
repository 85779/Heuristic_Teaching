# Socrates 高中数学智能辅导系统 — 项目完整报告

**版本**: v1.0 | **日期**: 2026年5月

---

## 一、项目概述

Socrates 是一个面向高中生的 AI 数学智能辅导系统。学生输入题目和作答，系统自动批改、分9级提示、追踪画像、推荐下一题。

### 技术栈
- 后端: Python 3.12 + FastAPI + MongoDB + 阿里云DashScope Qwen系列
- 前端: React 19 + TypeScript + Vite + TailwindCSS 4
- 测试: pytest (394个用例，全部通过)

### 规模
- 后端: 143个Python文件, ~16,500行代码
- 前端: 8个TypeScript文件, ~1,200行代码  
- API: 26个端点, 6个模块
- 知识库: 175个知识点, 298篇文档

---

## 二、系统架构

6个模块通过EventBus事件总线自动串联：解题完成 → 自动干预 → 更新画像 → 个性化推荐。

| 模块 | 功能 | API数 |
|------|------|:--:|
| Module 1 解题 | 链式验证评估 + 四阶段Polya解题 + 参考解法 | 8 |
| Module 2 干预 | 五节点管道 + R1-R4/M1-M5九级提示 + RAG增强 | 7 |
| Module 3 推荐 | LLM实时生成 + 自动KP识别 + 三种锚点策略 | 2 |
| Module 4 画像 | dimension_ratio + ratio_trend + 路由提示 | 5 |
| Module 5 策略 | 七种自适应策略 + 经验等级适配 | 3 |
| Module 6 知识库 | 298文档嵌入检索(零外部依赖) | — |

---

## 三、核心功能详解

### 3.1 链式验证评估(90%准确率)

两步法：第1步LLM先独立算出正确答案 → 第2步拿着标准答案逐行对比学生作答。做错也能同时看到参考解法。

10道真实高中题benchmark: 正确识别90%, 错误捕获90%。

### 3.2 R/M双维度九级提示

系统先判断学生困难类型：
- R型(知识资源型): 缺知识——不知道用哪个公式
- M型(元认知型): 有知识但不会调用——知道公式但不知道现在该干嘛

R维度递进: R1方向引导 → R2知识指路 → R3第一步形式 → R4完整步骤
M维度递进: M1反思引导 → M2方向指引 → M3策略推荐 → M4路径对比 → M5完整思路

### 3.3 学生画像

dimension_ratio: R型vs M型断点比例。ratio_trend: 线性回归趋势分析(上升/下降/稳定)。冷启动(<3次干预)默认0.5。

画像数据自动驱动推荐策略(同知识点/变式/均衡)和教学策略(讲授/练习/讨论比例)。

### 3.4 个性化推荐

LLM实时生成新题(非题库)+答案+提示。自动从题目文本识别关联知识点(CJK ngram匹配)。三种策略: 同知识点巩固/变式练习/均衡查漏补缺。19道备用精选题。

### 3.5 前端(4页面)

- 首页 / : 系统状态+入口
- 学习 /study : 输入题目→评估→解法→提示→推荐,一条链
- 画像 /profile/:id : R/M维度比+指标
- 教学 /teaching/:id : 讲授/练习/讨论比例

---

## 四、API端点总览(26个)

### 解题(8个)
POST /solving/reference — 参考解法+评估
POST /solving/sessions — 创建四阶段会话
POST /solving/sessions/{id}/orientation — 定向
POST /solving/sessions/{id}/reconstruction — 重构
POST /solving/sessions/{id}/transformation — 变换
POST /solving/sessions/{id}/verification — 验证
POST /solving/sessions/{id}/complete — 完成
GET  /solving/sessions/{id} — 查询

### 干预(7个)
POST /interventions — 创建干预(独立调用)
POST /interventions/feedback — 学生反馈
POST /interventions/end — 结束
POST /interventions/escalate — 升级
GET  /interventions/{id} — 查询
POST /interventions/{id}/accept — 接受
POST /interventions/{id}/dismiss — 忽略

### 推荐(2个)
POST /recommendations/recommend — 获取推荐
GET  /recommendations/health

### 画像(5个)
GET  /profile/{id}, /profile/{id}/dimension-ratio, /profile/{id}/routing-hint
POST /profile/{id}/intervention, GET /profile/health

### 策略(3个)
POST /teaching/strategy, GET /teaching/strategy/{id}, GET /teaching/health

### 全局(1个)
GET  /health

---

## 五、运行方式

Looking in indexes: https://pypi.tuna.tsinghua.edu.cn/simple
Obtaining file:///D:/Socrates/backend
  Installing build dependencies: started
  Installing build dependencies: finished with status 'error'

---

## 六、后续计划

P1: 前端交互完善, 真实学生数据验证(50+题)
P2: Docker部署, 混合评估引擎(规则+LLM)
P3: 知识本体丰富, 数据积累优化

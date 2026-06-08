# 高中数学教辅系统架构设计 v2

## TL;DR

> **核心架构**: 模块化插件架构 + 核心能力抽象 + 共享基础设施
>
> **技术栈**: Python FastAPI (后端) + React (前端) + MongoDB (存储)
>
> **设计目标**: 模块级复用、插件式扩展、清晰边界、未来兼容

---

## 一、架构设计理念

### 1.1 核心原则

| 原则             | 说明                             |
| ---------------- | -------------------------------- |
| **模块独立性**   | 每个模块可独立开发、测试、部署   |
| **接口标准化**   | 模块通过标准接口通信，降低耦合   |
| **核心能力下沉** | 共享能力抽象到核心层，避免重复   |
| **配置化组装**   | 模块可配置组合，灵活适配不同场景 |
| **扩展性优先**   | 预留扩展点，支持未来功能模块接入 |

### 1.2 模块全景图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           模块生态 (可扩展)                                   │
│                                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │  模块一      │  │  模块二      │  │  模块三      │  │  模块四      │    │
│  │  解题生成    │  │  断点干预    │  │  学生模型    │  │  智能推荐    │    │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘    │
│                                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                      │
│  │  模块五      │  │  模块六      │  │  更多模块    │                      │
│  │  教学管理    │  │  错题分析    │  │  ...         │                      │
│  └──────────────┘  └──────────────┘  └──────────────┘                      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           核心层 (Core Layer)                                │
│                                                                              │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐│
│  │ 模块注册器 │ │ LLM编排器  │ │ 状态管理器 │ │ 事件总线   │ │ 配置中心   ││
│  │ Registry   │ │ Orchestrator│ │ StateMgr  │ │ EventBus   │ │ Config     ││
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘ └────────────┘│
│                                                                              │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐              │
│  │ 提示词引擎 │ │ 输出解析器 │ │ 会话管理器 │ │ 日志追踪   │              │
│  │ PromptEng  │ │ Parser     │ │ SessionMgr │ │ Tracing    │              │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           基础设施层 (Infrastructure)                        │
│                                                                              │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐              │
│  │ 数据访问层 │ │ LLM客户端  │ │ 缓存服务   │ │ 消息队列   │              │
│  │ Repository │ │ LLMClient  │ │ Cache      │ │ MQ         │              │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           外部服务层                                          │
│  ┌────────────────────────────┐  ┌────────────────────────────┐            │
│  │  MongoDB                   │  │  LLM Provider              │            │
│  │  (数据持久化)              │  │  (OpenAI/Anthropic/...)    │            │
│  └────────────────────────────┘  └────────────────────────────┘            │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 二、分层架构详解

### 2.1 四层架构模型

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Layer 4: 模块层 (Modules Layer)                                              │
│ ─────────────────────────────────────────────────────────────────────────── │
│ • 业务模块实现                                                                │
│ • 遵循模块接口规范                                                            │
│ • 通过核心层能力构建业务逻辑                                                  │
│ • 模块间通过事件总线/共享状态通信                                             │
│                                                                              │
│ 当前模块: solving | intervention | student_model | recommendation | ...    │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Layer 3: API层 (API Layer)                                                   │
│ ─────────────────────────────────────────────────────────────────────────── │
│ • HTTP路由定义                                                               │
│ • 请求验证与响应格式化                                                        │
│ • API版本管理                                                                │
│ • 认证授权                                                                   │
│                                                                              │
│ 端点: /api/v1/solving | /api/v1/intervention | /api/v1/student | ...       │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Layer 2: 核心层 (Core Layer)                                                 │
│ ─────────────────────────────────────────────────────────────────────────── │
│ • 模块注册与发现                                                             │
│ • LLM编排与提示词管理                                                        │
│ • 状态管理与会话管理                                                         │
│ • 事件发布/订阅                                                              │
│ • 配置管理                                                                   │
│                                                                              │
│ 核心组件: Registry | Orchestrator | StateManager | EventBus | Config        │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Layer 1: 基础设施层 (Infrastructure Layer)                                   │
│ ─────────────────────────────────────────────────────────────────────────── │
│ • 数据库访问封装                                                             │
│ • 外部服务客户端                                                             │
│ • 缓存抽象                                                                   │
│ • 日志与监控                                                                 │
│                                                                              │
│ 基础组件: Repository | LLMClient | Cache | Logger | Tracer                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 三、模块架构设计

### 3.1 模块接口规范

每个模块必须实现的标准接口：

```python
# core/interfaces/module.py

class IModule(ABC):
    """模块基类接口"""

    @property
    @abstractmethod
    def module_id(self) -> str:
        """模块唯一标识"""
        pass

    @property
    @abstractmethod
    def module_name(self) -> str:
        """模块名称"""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """模块版本"""
        pass

    @property
    def dependencies(self) -> list[str]:
        """依赖的其他模块ID"""
        return []

    @property
    def provides_events(self) -> list[str]:
        """发布的事件类型"""
        return []

    @property
    def subscribes_events(self) -> list[str]:
        """订阅的事件类型"""
        return []

    @abstractmethod
    async def initialize(self, context: ModuleContext) -> None:
        """模块初始化"""
        pass

    @abstractmethod
    async def shutdown(self) -> None:
        """模块关闭"""
        pass

    def register_routes(self, router: APIRouter) -> None:
        """注册API路由 (可选)"""
        pass
```

### 3.2 模块上下文

```python
# core/context.py

@dataclass
class ModuleContext:
    """模块运行上下文 - 提供核心能力访问"""

    registry: 'ModuleRegistry'      # 模块注册器
    orchestrator: 'LLMOrchestrator' # LLM编排器
    state_manager: 'StateManager'   # 状态管理器
    event_bus: 'EventBus'           # 事件总线
    config: 'ConfigManager'         # 配置管理
    session_manager: 'SessionManager' # 会话管理
    repository: 'Repository'        # 数据仓储
    logger: Logger                  # 日志器
```

### 3.3 模块注册机制

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           模块注册器 (ModuleRegistry)                        │
│                                                                              │
│  职责:                                                                       │
│  • 模块发现与注册                                                            │
│  • 依赖关系解析                                                              │
│  • 生命周期管理                                                              │
│  • 模块间访问控制                                                            │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      注册流程                                        │   │
│  │                                                                      │   │
│  │  1. 扫描 modules/ 目录                                               │   │
│  │  2. 加载模块定义 (module.py)                                         │   │
│  │  3. 验证接口实现                                                     │   │
│  │  4. 解析依赖关系 → 拓扑排序                                          │   │
│  │  5. 按序初始化模块                                                   │   │
│  │  6. 注册事件订阅                                                     │   │
│  │  7. 注册API路由                                                      │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      模块访问                                        │   │
│  │                                                                      │   │
│  │  registry.get_module("solving") → SolvingModule                     │   │
│  │  registry.get_modules_by_capability("llm_pipeline") → [...]         │   │
│  │  registry.get_dependencies("intervention") → ["solving"]            │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 四、核心层组件设计

### 4.1 LLM编排器 (LLMOrchestrator)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           LLM编排器 (LLMOrchestrator)                        │
│                                                                              │
│  职责:                                                                       │
│  • 提示词模板管理                                                            │
│  • LLM调用编排                                                              │
│  • 输出解析与验证                                                            │
│  • 重试与降级策略                                                            │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      编排流程                                        │   │
│  │                                                                      │   │
│  │  PromptTemplate → Render → LLMClient → RawOutput                    │   │
│  │        ↓                                          ↓                  │   │
│  │  Variables (变量)                            OutputParser            │   │
│  │                                                     ↓                │   │
│  │                                             ValidatedOutput          │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      Pipeline支持                                    │   │
│  │                                                                      │   │
│  │  orchestrator.run_pipeline(                                         │   │
│  │      pipeline_id="solving_pipeline",                                │   │
│  │      context={"problem": "...", "student_level": "..."},            │   │
│  │      steps=["orientation", "reconstruction", ...]                   │   │
│  │  ) → PipelineResult                                                  │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 状态管理器 (StateManager)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           状态管理器 (StateManager)                          │
│                                                                              │
│  职责:                                                                       │
│  • 会话状态管理                                                              │
│  • 模块状态隔离                                                              │
│  • 状态快照与恢复                                                            │
│  • 状态变更通知                                                              │
│                                                                              │
│  状态模型:                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                      │   │
│  │  SessionState                                                        │   │
│  │  ├── session_id: str                                                 │   │
│  │  ├── global_state: dict           # 全局共享状态                    │   │
│  │  ├── module_states:               # 模块独立状态                    │   │
│  │  │   ├── solving: {...}                                             │   │
│  │  │   ├── intervention: {...}                                        │   │
│  │  │   └── student_model: {...}                                       │   │
│  │  ├── history: [...]               # 状态变更历史                    │   │
│  │  └── checkpoints: [...]           # 检查点                          │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  使用方式:                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                      │   │
│  │  # 模块内访问自己的状态                                              │   │
│  │  state = state_manager.get_module_state("solving", session_id)      │   │
│  │  state["current_step"] = "orientation"                               │   │
│  │                                                                      │   │
│  │  # 模块间共享状态                                                    │   │
│  │  global_state = state_manager.get_global_state(session_id)          │   │
│  │  global_state["problem"] = problem_input                             │   │
│  │                                                                      │   │
│  │  # 检查点 (用于断点恢复)                                             │   │
│  │  state_manager.checkpoint(session_id, "after_orientation")          │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.3 事件总线 (EventBus)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           事件总线 (EventBus)                                │
│                                                                              │
│  职责:                                                                       │
│  • 模块间解耦通信                                                            │
│  • 事件发布/订阅                                                             │
│  • 事件持久化 (可选)                                                         │
│                                                                              │
│  事件类型:                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                      │   │
│  │  # 解题模块事件                                                      │   │
│  │  solving.started          → 解题开始                                │   │
│  │  solving.step_completed   → 步骤完成                                │   │
│  │  solving.completed        → 解题完成                                │   │
│  │                                                                      │   │
│  │  # 干预模块事件                                                      │   │
│  │  intervention.breakpoint_detected → 断点检测                        │   │
│  │  intervention.hint_delivered       → 提示发放                       │   │
│  │  intervention.escalated            → 干预升级                       │   │
│  │                                                                      │   │
│  │  # 学生模型事件                                                      │   │
│  │  student_model.updated     → 学生状态更新                           │   │
│  │  student_model.knowledge_gap_detected → 知识缺口发现                │   │
│  │                                                                      │   │
│  │  # 推荐模块事件                                                      │   │
│  │  recommendation.generated  → 推荐生成                               │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  使用方式:                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                      │   │
│  │  # 发布事件                                                          │   │
│  │  await event_bus.publish(Event(                                     │   │
│  │      type="solving.step_completed",                                 │   │
│  │      data={"step": "orientation", "result": {...}},                 │   │
│  │      session_id=session_id                                          │   │
│  │  ))                                                                  │   │
│  │                                                                      │   │
│  │  # 订阅事件                                                          │   │
│  │  @event_bus.subscribe("solving.completed")                          │   │
│  │  async def on_solving_completed(event: Event):                      │   │
│  │      # 学生模型更新                                                  │   │
│  │      # 推荐生成                                                      │   │
│  │      pass                                                            │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 五、目录结构设计

### 5.1 后端目录结构

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                      # FastAPI应用入口
│   ├── config.py                    # 全局配置
│   │
│   ├── core/                        # 核心层
│   │   ├── __init__.py
│   │   ├── interfaces/              # 接口定义
│   │   │   ├── __init__.py
│   │   │   ├── module.py            # IModule接口
│   │   │   ├── pipeline.py          # IPipeline接口
│   │   │   ├── repository.py        # IRepository接口
│   │   │   └── llm_client.py        # ILLMClient接口
│   │   │
│   │   ├── registry/                # 模块注册器
│   │   │   ├── __init__.py
│   │   │   ├── module_registry.py   # 模块注册实现
│   │   │   └── dependency_resolver.py
│   │   │
│   │   ├── orchestrator/            # LLM编排器
│   │   │   ├── __init__.py
│   │   │   ├── llm_orchestrator.py
│   │   │   ├── prompt_engine.py     # 提示词引擎
│   │   │   └── output_parser.py     # 输出解析器
│   │   │
│   │   ├── state/                   # 状态管理器
│   │   │   ├── __init__.py
│   │   │   ├── state_manager.py
│   │   │   └── session_manager.py
│   │   │
│   │   ├── events/                  # 事件总线
│   │   │   ├── __init__.py
│   │   │   ├── event_bus.py
│   │   │   ├── event_types.py
│   │   │   └── event_store.py       # 事件持久化(可选)
│   │   │
│   │   └── context.py               # 模块上下文
│   │
│   ├── infrastructure/              # 基础设施层
│   │   ├── __init__.py
│   │   ├── database/                # 数据库
│   │   │   ├── __init__.py
│   │   │   ├── mongodb.py
│   │   │   └── repositories/
│   │   │       ├── __init__.py
│   │   │       ├── session_repo.py
│   │   │       └── base_repo.py
│   │   │
│   │   ├── llm/                     # LLM客户端
│   │   │   ├── __init__.py
│   │   │   ├── base_client.py
│   │   │   ├── openai_client.py
│   │   │   └── anthropic_client.py
│   │   │
│   │   ├── cache/                   # 缓存
│   │   │   ├── __init__.py
│   │   │   └── redis_cache.py
│   │   │
│   │   └── logging/                 # 日志
│   │       ├── __init__.py
│   │       └── tracer.py
│   │
│   ├── api/                         # API层
│   │   ├── __init__.py
│   │   ├── dependencies.py          # 依赖注入
│   │   ├── middleware/              # 中间件
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   └── error_handler.py
│   │   │
│   │   └── v1/                      # API版本v1
│   │       ├── __init__.py
│   │       ├── router.py            # 路由汇总
│   │       └── schemas/             # 请求/响应模型
│   │           ├── __init__.py
│   │           ├── common.py
│   │           └── session.py
│   │
│   ├── modules/                     # 模块层
│   │   ├── __init__.py
│   │   │
│   │   ├── solving/                 # 模块一：解题生成
│   │   │   ├── __init__.py
│   │   │   ├── module.py            # 模块定义
│   │   │   ├── service.py           # 业务服务
│   │   │   ├── pipeline.py          # 解题Pipeline
│   │   │   ├── prompts/             # 提示词模板
│   │   │   │   ├── __init__.py
│   │   │   │   ├── orientation.py
│   │   │   │   ├── reconstruction.py
│   │   │   │   ├── transformation.py
│   │   │   │   └── verification.py
│   │   │   ├── models.py            # 数据模型
│   │   │   └── routes.py            # API路由
│   │   │
│   │   ├── intervention/            # 模块二：断点干预
│   │   │   ├── __init__.py
│   │   │   ├── module.py
│   │   │   ├── service.py
│   │   │   ├── pipeline.py
│   │   │   ├── prompts/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── location.py
│   │   │   │   ├── analysis.py
│   │   │   │   ├── decision.py
│   │   │   │   ├── intensity.py
│   │   │   │   └── hint.py
│   │   │   ├── models.py
│   │   │   └── routes.py
│   │   │
│   │   ├── student_model/           # 模块三：学生模型
│   │   │   ├── __init__.py
│   │   │   ├── module.py
│   │   │   ├── service.py
│   │   │   ├── knowledge_graph.py
│   │   │   ├── ability_model.py
│   │   │   ├── models.py
│   │   │   └── routes.py
│   │   │
│   │   ├── recommendation/          # 模块四：智能推荐
│   │   │   ├── __init__.py
│   │   │   ├── module.py
│   │   │   ├── service.py
│   │   │   ├── path_planner.py
│   │   │   ├── models.py
│   │   │   └── routes.py
│   │   │
│   │   ├── teaching/                # 模块五：教学管理
│   │   │   ├── __init__.py
│   │   │   ├── module.py
│   │   │   ├── service.py
│   │   │   ├── models.py
│   │   │   └── routes.py
│   │   │
│   │   └── _template/               # 模块模板 (用于新建模块)
│   │       ├── __init__.py
│   │       ├── module.py
│   │       ├── service.py
│   │       ├── models.py
│   │       └── routes.py
│   │
│   └── shared/                      # 共享工具
│       ├── __init__.py
│       ├── utils.py
│       ├── constants.py
│       └── exceptions.py
│
├── tests/                           # 测试
│   ├── __init__.py
│   ├── conftest.py
│   ├── core/                        # 核心层测试
│   ├── modules/                     # 模块测试
│   │   ├── test_solving/
│   │   └── test_intervention/
│   └── integration/                 # 集成测试
│
├── prompts/                         # 提示词文件 (YAML/JSON)
│   ├── solving/
│   │   ├── v1/
│   │   └── v2/
│   └── intervention/
│       └── v1/
│
├── pyproject.toml
├── requirements.txt
└── .env.example
```

### 5.2 前端目录结构

```
frontend/
├── src/
│   ├── app/                         # 应用入口
│   │   ├── App.tsx
│   │   └── router.tsx
│   │
│   ├── core/                        # 核心层 (对应后端模块概念)
│   │   ├── api/                     # API客户端
│   │   │   ├── client.ts
│   │   │   ├── solving.ts
│   │   │   └── intervention.ts
│   │   ├── store/                   # 状态管理
│   │   │   └── sessionStore.ts
│   │   └── hooks/                   # 核心Hooks
│   │       ├── useSSE.ts
│   │       └── useSession.ts
│   │
│   ├── modules/                     # 模块化UI
│   │   ├── solving/                 # 解题模块UI
│   │   │   ├── components/
│   │   │   │   ├── ProblemInput.tsx
│   │   │   │   ├── SolutionView.tsx
│   │   │   │   └── StepCard.tsx
│   │   │   ├── pages/
│   │   │   │   └── SolvingPage.tsx
│   │   │   └── hooks/
│   │   │       └── useSolving.ts
│   │   │
│   │   ├── intervention/            # 干预模块UI
│   │   │   ├── components/
│   │   │   │   ├── HintPanel.tsx
│   │   │   │   ├── BreakpointIndicator.tsx
│   │   │   │   └── InterventionLevel.tsx
│   │   │   ├── pages/
│   │   │   └── hooks/
│   │   │
│   │   └── student/                 # 学生模块UI (未来)
│   │       └── ...
│   │
│   ├── shared/                      # 共享组件
│   │   ├── components/
│   │   │   ├── Layout/
│   │   │   ├── Button/
│   │   │   └── MathRenderer/       # LaTeX渲染
│   │   └── utils/
│   │
│   └── types/                       # TypeScript类型
│       ├── solving.ts
│       ├── intervention.ts
│       └── common.ts
│
├── package.json
└── vite.config.ts
```

---

## 六、模块详细设计

### 6.1 模块一：解题生成 (Solving Module)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Solving Module                                       │
│                                                                              │
│  模块定义: modules/solving/module.py                                        │
│  ──────────────────────────────────────────────────────────────────────────  │
│  • module_id: "solving"                                                      │
│  • dependencies: []                                                          │
│  • provides_events: ["solving.started", "solving.step_completed", ...]      │
│  • subscribes_events: []                                                     │
│                                                                              │
│  Pipeline: modules/solving/pipeline.py                                      │
│  ──────────────────────────────────────────────────────────────────────────  │
│                                                                              │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐                 │
│  │ 问题定向 │ → │ 关系重构 │ → │ 形式化归 │ → │ 结果审查 │                 │
│  │Orientation│  │Reconstruct│  │Transform │  │Verify    │                 │
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘                 │
│       │              │              │              │                         │
│       ▼              ▼              ▼              ▼                         │
│  StepResult     StepResult     StepResult     StepResult                    │
│                                                                              │
│  提示词: modules/solving/prompts/                                           │
│  ──────────────────────────────────────────────────────────────────────────  │
│  • orientation.py    - 问题定向提示词                                        │
│  • reconstruction.py - 关系重构提示词                                        │
│  • transformation.py - 形式化归提示词                                        │
│  • verification.py   - 结果审查提示词                                        │
│                                                                              │
│  数据模型: modules/solving/models.py                                        │
│  ──────────────────────────────────────────────────────────────────────────  │
│  • Problem (输入)                                                            │
│  • StepResult (步骤结果)                                                     │
│  • SolutionThread (完整解法)                                                 │
│  • SolvingState (模块状态)                                                   │
│                                                                              │
│  API路由: modules/solving/routes.py                                         │
│  ──────────────────────────────────────────────────────────────────────────  │
│  • POST /api/v1/solving/start       - 开始解题                              │
│  • GET  /api/v1/solving/{id}/stream - SSE流式获取                           │
│  • POST /api/v1/solving/{id}/continue - 从学生作答继续                       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 6.2 模块二：断点干预 (Intervention Module)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      Intervention Module                                     │
│                                                                              │
│  模块定义: modules/intervention/module.py                                   │
│  ──────────────────────────────────────────────────────────────────────────  │
│  • module_id: "intervention"                                                 │
│  • dependencies: ["solving"]                                                 │
│  • provides_events: ["intervention.breakpoint_detected", ...]               │
│  • subscribes_events: ["solving.step_completed"]                            │
│                                                                              │
│  Pipeline: modules/intervention/pipeline.py                                 │
│  ──────────────────────────────────────────────────────────────────────────  │
│                                                                              │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐  │
│  │ 断点定位 │ → │ 断点分析 │ → │ 分层决策 │ → │ 强度控制 │ → │ 提示生成 │  │
│  │ Location │   │ Analysis │   │ Decision │   │ Intensity│   │ Hint     │  │
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘  │
│       │              │              │              │              │         │
│       ▼              ▼              ▼              ▼              ▼         │
│  BreakpointLoc  BreakpointAn   DecisionRes  IntensityLvl  HintContent      │
│                                                                              │
│  提示词: modules/intervention/prompts/                                      │
│  ──────────────────────────────────────────────────────────────────────────  │
│  • location.py  - 断点定位提示词                                             │
│  • analysis.py  - 断点分析提示词                                             │
│  • decision.py  - 分层决策提示词                                             │
│  • intensity.py - 强度控制提示词                                             │
│  • hint.py      - 提示生成提示词                                             │
│                                                                              │
│  干预层次:                                                                   │
│  ──────────────────────────────────────────────────────────────────────────  │
│  L1: 元认知引导 (回顾/检查)     ← 首选，最低强度                             │
│  L2: 思考角度提示               ← 中等强度                                  │
│  L3: 方法方向指引               ← 中高强度                                  │
│  L4: 关键步骤展示               ← 高强度                                    │
│  L5: 直接解答                   ← 最高强度 (不推荐)                         │
│                                                                              │
│  API路由: modules/intervention/routes.py                                    │
│  ──────────────────────────────────────────────────────────────────────────  │
│  • POST /api/v1/intervention/breakpoint  - 报告断点                         │
│  • GET  /api/v1/intervention/{id}/stream - SSE获取提示                      │
│  • POST /api/v1/intervention/{id}/feedback - 学生反馈                       │
│  • POST /api/v1/intervention/{id}/escalate  - 升级干预                      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 七、模块间通信设计

### 7.1 通信方式对比

| 方式         | 场景           | 优点                 | 缺点         |
| ------------ | -------------- | -------------------- | ------------ |
| **共享状态** | 模块间数据传递 | 简单直接，无需序列化 | 耦合度较高   |
| **事件总线** | 异步通知、解耦 | 松耦合，可扩展       | 需要事件管理 |
| **直接调用** | 同步依赖       | 性能好               | 紧耦合       |

### 7.2 模块通信示例

```python
# 模块二依赖模块一的输出

class InterventionModule(IModule):
    @property
    def dependencies(self) -> list[str]:
        return ["solving"]

    async def on_breakpoint_detected(self, session_id: str):
        # 方式1: 通过状态管理器获取共享状态
        state = self.context.state_manager.get_global_state(session_id)
        solution_thread = state.get("solution_thread")

        # 方式2: 通过模块注册器直接调用
        solving_module = self.context.registry.get_module("solving")
        solution = await solving_module.get_solution(session_id)

        # 方式3: 通过事件订阅 (异步)
        # 已在订阅中自动处理
```

### 7.3 事件流示例

```
用户输入题目
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│ Solving Module                                                   │
│   │                                                              │
│   ├── emit: solving.started                                     │
│   ├── execute Pipeline                                          │
│   │     ├── emit: solving.step_completed (orientation)         │
│   │     ├── emit: solving.step_completed (reconstruction)      │
│   │     ├── emit: solving.step_completed (transformation)      │
│   │     └── emit: solving.step_completed (verification)        │
│   ├── emit: solving.completed                                   │
│   │                                                              │
│   └── 更新共享状态: solution_thread                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
    │
    │ 事件: solving.completed
    ▼
┌─────────────────────────────────────────────────────────────────┐
│ Student Model Module (订阅 solving.completed)                   │
│   │                                                              │
│   └── 更新学生能力模型                                           │
│       └── emit: student_model.updated                           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
    │
    │ 事件: student_model.updated
    ▼
┌─────────────────────────────────────────────────────────────────┐
│ Recommendation Module (订阅 student_model.updated)              │
│   │                                                              │
│   └── 生成推荐题目                                               │
│       └── emit: recommendation.generated                        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 八、数据模型设计

### 8.1 MongoDB集合设计

```javascript
// sessions 集合
{
  "_id": ObjectId,
  "session_id": "uuid",
  "student_id": "uuid",
  "created_at": ISODate,
  "updated_at": ISODate,
  "status": "active | paused | completed",

  // 全局状态
  "global_state": {
    "problem": {
      "content": "题目内容",
      "type": "代数",
      "difficulty": "medium"
    }
  },

  // 模块独立状态
  "module_states": {
    "solving": {
      "current_step": "reconstruction",
      "solution_thread": {...},
      "completed": false
    },
    "intervention": {
      "active_breakpoint": {...},
      "current_level": 2,
      "hints_delivered": 3
    },
    "student_model": {
      "ability_scores": {...},
      "knowledge_gaps": [...]
    }
  },

  // 事件历史 (append-only)
  "event_log": [
    {
      "event_type": "solving.step_completed",
      "module": "solving",
      "data": {...},
      "timestamp": ISODate
    }
  ],

  // 检查点
  "checkpoints": [
    {
      "name": "after_orientation",
      "state_snapshot": {...},
      "timestamp": ISODate
    }
  ],

  // 版本 (乐观锁)
  "version": 1
}
```

### 8.2 Pydantic模型

```python
# modules/solving/models.py

class Problem(BaseModel):
    content: str
    problem_type: str | None = None
    difficulty: str | None = None

class StepResult(BaseModel):
    step_name: str
    content: str
    key_insights: list[str] = []
    timestamp: datetime

class SolutionThread(BaseModel):
    problem: Problem
    steps: list[StepResult]
    complete: bool = False
    generated_at: datetime

class SolvingState(BaseModel):
    current_step: str | None = None
    solution_thread: SolutionThread | None = None
    error: str | None = None
```

---

## 九、扩展性设计

### 9.1 新增模块流程

```
1. 创建模块目录
   modules/new_module/
   ├── __init__.py
   ├── module.py        # 实现IModule接口
   ├── service.py
   ├── models.py
   └── routes.py

2. 定义模块元数据
   - module_id
   - dependencies
   - provides_events
   - subscribes_events

3. 实现业务逻辑
   - 使用核心层能力
   - 遵循模块规范

4. 自动注册
   - 启动时自动扫描并注册
```

### 9.2 模块配置化

```yaml
# config/modules.yaml

modules:
  solving:
    enabled: true
    priority: 1

  intervention:
    enabled: true
    priority: 2
    dependencies:
      - solving

  student_model:
    enabled: true
    priority: 3
    dependencies:
      - solving
      - intervention

  recommendation:
    enabled: false # 可配置开关
    priority: 4
    dependencies:
      - student_model
```

### 9.3 提示词版本管理

```
prompts/
├── solving/
│   ├── v1.0/           # 初始版本
│   │   ├── orientation.yaml
│   │   └── ...
│   ├── v2.0/           # 优化版本
│   │   └── ...
│   └── versions.yaml   # 版本配置
│
└── intervention/
    └── ...
```

---

## 十、部署架构

### 10.1 容器化

```yaml
# docker-compose.yml
version: "3.8"

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - MONGODB_URI=mongodb://mongo:27017/math_tutor
      - LLM_API_KEY=${LLM_API_KEY}
      - LLM_PROVIDER=openai
    depends_on:
      - mongo
    volumes:
      - ./prompts:/app/prompts:ro

  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - backend

  mongo:
    image: mongo:7
    volumes:
      - mongo_data:/data/db
    ports:
      - "27017:27017"

volumes:
  mongo_data:
```

### 10.2 模块热加载 (可选)

```python
# 支持开发时模块热加载

async def reload_module(module_id: str):
    """重新加载指定模块"""
    await registry.shutdown_module(module_id)
    registry.unregister(module_id)

    # 重新发现和注册
    new_module = discover_module(module_id)
    await registry.register(new_module)
```

---

## 附录：设计决策记录

### ADR-001: 采用模块化插件架构

**背景**: 系统未来需要支持多个功能模块，需要清晰的模块边界和复用机制

**决策**: 采用四层架构 + 模块注册机制

**收益**:

- 新增模块只需实现IModule接口
- 模块可独立开发测试
- 核心能力复用，避免重复

### ADR-002: 采用事件总线进行模块间通信

**背景**: 模块间需要通信但需要保持松耦合

**决策**: 采用事件发布/订阅模式

**收益**:

- 模块完全解耦
- 易于扩展新的订阅者
- 支持异步处理

### ADR-003: 状态分层管理

**背景**: 每个模块需要独立状态，但又需要共享部分数据

**决策**: 采用 global_state + module_states 分层结构

**收益**:

- 模块状态隔离，互不干扰
- 共享状态明确，易于追踪
- 支持检查点恢复

---

_架构设计 v2 完成 - 模块化、可扩展、高复用_

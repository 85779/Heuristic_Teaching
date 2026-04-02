// HomePage: System overview with clear architecture flow - Light Theme
import React from "react";
import { Link } from "react-router-dom";

// Module data with flow connections
const modules = [
  {
    id: 1,
    name: "组织化解题",
    description: "将复杂问题分解为可管理的步骤",
    icon: "📝",
    color: "blue",
    input: "学生问题",
    output: "解题步骤",
  },
  {
    id: 2,
    name: "知识图谱",
    description: "175个知识点的关系网络",
    icon: "🧠",
    color: "purple",
    input: "解题步骤",
    output: "所需知识点",
  },
  {
    id: 3,
    name: "智能干预",
    description: "AI实时检测断点并提供精准提示",
    icon: "🎯",
    color: "emerald",
    input: "学生状态",
    output: "针对性提示",
  },
  {
    id: 4,
    name: "学生画像",
    description: "追踪学生认知状态变化",
    icon: "👤",
    color: "cyan",
    input: "学习数据",
    output: "能力画像",
  },
  {
    id: 5,
    name: "智能推荐",
    description: "个性化学习路径规划",
    icon: "📚",
    color: "amber",
    input: "能力画像",
    output: "推荐路径",
  },
  {
    id: 6,
    name: "教学策略",
    description: "教师端管理与分析工具",
    icon: "⚙️",
    color: "rose",
    input: "班级数据",
    output: "教学建议",
  },
];

// Stats card data
const statsCards = [
  {
    label: "学生画像",
    value: "47人",
    subtext: "使用中",
    icon: "👥",
    gradient: "from-blue-50 to-blue-100",
    border: "border-blue-200",
    textColor: "text-blue-600",
    bgIcon: "bg-blue-100",
  },
  {
    label: "智能干预",
    value: "92.3%",
    subtext: "解决率",
    icon: "🎯",
    gradient: "from-emerald-50 to-emerald-100",
    border: "border-emerald-200",
    textColor: "text-emerald-600",
    bgIcon: "bg-emerald-100",
  },
  {
    label: "知识追踪",
    value: "175个",
    subtext: "知识点",
    icon: "📖",
    gradient: "from-purple-50 to-purple-100",
    border: "border-purple-200",
    textColor: "text-purple-600",
    bgIcon: "bg-purple-100",
  },
  {
    label: "数据看板",
    value: "12天",
    subtext: "连续数据",
    icon: "📊",
    gradient: "from-amber-50 to-amber-100",
    border: "border-amber-200",
    textColor: "text-amber-600",
    bgIcon: "bg-amber-100",
  },
];

const colorMap: Record<
  string,
  { bg: string; border: string; text: string; shadow: string; icon: string }
> = {
  blue: {
    bg: "bg-blue-50",
    border: "border-blue-200",
    text: "text-blue-600",
    shadow: "shadow-blue-200",
    icon: "bg-blue-100",
  },
  purple: {
    bg: "bg-purple-50",
    border: "border-purple-200",
    text: "text-purple-600",
    shadow: "shadow-purple-200",
    icon: "bg-purple-100",
  },
  emerald: {
    bg: "bg-emerald-50",
    border: "border-emerald-200",
    text: "text-emerald-600",
    shadow: "shadow-emerald-200",
    icon: "bg-emerald-100",
  },
  cyan: {
    bg: "bg-cyan-50",
    border: "border-cyan-200",
    text: "text-cyan-600",
    shadow: "shadow-cyan-200",
    icon: "bg-cyan-100",
  },
  amber: {
    bg: "bg-amber-50",
    border: "border-amber-200",
    text: "text-amber-600",
    shadow: "shadow-amber-200",
    icon: "bg-amber-100",
  },
  rose: {
    bg: "bg-rose-50",
    border: "border-rose-200",
    text: "text-rose-600",
    shadow: "shadow-rose-200",
    icon: "bg-rose-100",
  },
};

export const HomePage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-blue-50">
      {/* Hero Section */}
      <section className="py-16 px-4">
        <div className="max-w-5xl mx-auto text-center">
          <h2 className="text-4xl md:text-5xl font-bold text-slate-800 mb-4 tracking-tight">
            让每个学生找到
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-cyan-600">
              {" "}
              适合自己的解题路径
            </span>
          </h2>
          <p className="text-slate-600 text-lg mb-8 max-w-2xl mx-auto">
            基于认知诊断的智能数学辅导系统 · 看见AI思考过程 · 精准干预
          </p>

          <Link
            to="/demo"
            className="inline-flex items-center gap-3 px-8 py-4 bg-gradient-to-r from-blue-600 to-cyan-600 text-white font-semibold rounded-2xl hover:from-blue-500 hover:to-cyan-500 transition-all shadow-lg shadow-blue-500/30 hover:shadow-blue-500/50 hover:scale-105"
          >
            <span className="text-xl">🎬</span>
            <span>功能演示</span>
            <span className="text-lg">▶</span>
          </Link>
        </div>
      </section>

      {/* Stats Row */}
      <section className="px-4 pb-8">
        <div className="max-w-5xl mx-auto">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {statsCards.map((stat) => (
              <div
                key={stat.label}
                className={`p-4 rounded-2xl bg-gradient-to-br ${stat.gradient} border ${stat.border} shadow-sm hover:shadow-md transition-shadow`}
              >
                <div
                  className={`w-10 h-10 ${stat.bgIcon} rounded-xl flex items-center justify-center mb-3`}
                >
                  <span className="text-xl">{stat.icon}</span>
                </div>
                <div className={`${stat.textColor} text-2xl font-bold mb-1`}>
                  {stat.value}
                </div>
                <p className="text-slate-600 text-sm font-medium">
                  {stat.label}
                </p>
                <p className="text-slate-400 text-xs">{stat.subtext}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Architecture Flow Section */}
      <section className="py-12 px-4">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-8">
            <h3 className="text-2xl font-semibold text-slate-800 mb-2">
              系统架构
            </h3>
            <p className="text-slate-500 text-sm">
              数据流转：学生 → 模块处理 → 精准输出
            </p>
          </div>

          {/* Main flow: 3 modules in a row */}
          <div className="mb-6">
            <div className="flex items-center justify-between gap-3">
              {modules.slice(0, 3).map((mod, index) => {
                const colors = colorMap[mod.color];
                return (
                  <React.Fragment key={mod.id}>
                    <div className="flex-1">
                      <div
                        className={`p-5 rounded-2xl ${colors.bg} border-2 ${colors.border} hover:shadow-lg ${colors.shadow} transition-all`}
                      >
                        <div className="flex items-center gap-3 mb-3">
                          <div
                            className={`w-10 h-10 ${colors.icon} rounded-xl flex items-center justify-center`}
                          >
                            <span className="text-xl">{mod.icon}</span>
                          </div>
                          <div>
                            <h4 className="text-slate-800 font-bold">
                              {mod.name}
                            </h4>
                            <p className="text-slate-500 text-xs">
                              {mod.description}
                            </p>
                          </div>
                        </div>
                        <div className="flex justify-between text-xs bg-white/60 rounded-lg px-3 py-2">
                          <span className="text-slate-500">← {mod.input}</span>
                          <span className="text-slate-400">→</span>
                          <span className="text-slate-500">{mod.output} →</span>
                        </div>
                      </div>
                    </div>
                    {index < 2 && (
                      <div className="flex-shrink-0 text-slate-400 text-2xl px-1">
                        →
                      </div>
                    )}
                  </React.Fragment>
                );
              })}
            </div>
          </div>

          {/* Flow indicator */}
          <div className="flex justify-center mb-6">
            <div className="flex items-center gap-2 text-slate-400 bg-white px-4 py-2 rounded-full shadow-sm">
              <span className="text-xl">↓</span>
              <span className="text-sm font-medium">数据反馈</span>
              <span className="text-xl">↓</span>
            </div>
          </div>

          {/* Secondary flow: 3 modules in a row */}
          <div>
            <div className="flex items-center justify-between gap-3">
              {modules.slice(3, 6).map((mod, index) => {
                const colors = colorMap[mod.color];
                return (
                  <React.Fragment key={mod.id}>
                    <div className="flex-1">
                      <div
                        className={`p-5 rounded-2xl ${colors.bg} border-2 ${colors.border} hover:shadow-lg ${colors.shadow} transition-all`}
                      >
                        <div className="flex items-center gap-3 mb-3">
                          <div
                            className={`w-10 h-10 ${colors.icon} rounded-xl flex items-center justify-center`}
                          >
                            <span className="text-xl">{mod.icon}</span>
                          </div>
                          <div>
                            <h4 className="text-slate-800 font-bold">
                              {mod.name}
                            </h4>
                            <p className="text-slate-500 text-xs">
                              {mod.description}
                            </p>
                          </div>
                        </div>
                        <div className="flex justify-between text-xs bg-white/60 rounded-lg px-3 py-2">
                          <span className="text-slate-500">← {mod.input}</span>
                          <span className="text-slate-400">→</span>
                          <span className="text-slate-500">{mod.output} →</span>
                        </div>
                      </div>
                    </div>
                    {index < 2 && (
                      <div className="flex-shrink-0 text-slate-400 text-2xl px-1">
                        →
                      </div>
                    )}
                  </React.Fragment>
                );
              })}
            </div>
          </div>

          {/* Flow description */}
          <div className="mt-8 p-6 bg-white rounded-2xl border border-slate-200 shadow-sm">
            <div className="grid md:grid-cols-3 gap-6 text-center">
              <div className="p-4">
                <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center mx-auto mb-3">
                  <span className="text-2xl">📝</span>
                </div>
                <p className="text-blue-600 font-semibold mb-1">学生问题入口</p>
                <p className="text-slate-500 text-sm">学生提交数学问题</p>
              </div>
              <div className="p-4">
                <div className="w-12 h-12 bg-emerald-100 rounded-xl flex items-center justify-center mx-auto mb-3">
                  <span className="text-2xl">🎯</span>
                </div>
                <p className="text-emerald-600 font-semibold mb-1">
                  AI实时干预
                </p>
                <p className="text-slate-500 text-sm">检测断点，提供精准提示</p>
              </div>
              <div className="p-4">
                <div className="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center mx-auto mb-3">
                  <span className="text-2xl">🧠</span>
                </div>
                <p className="text-purple-600 font-semibold mb-1">
                  知识图谱支撑
                </p>
                <p className="text-slate-500 text-sm">175个知识点的关联网络</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Quick Access Section */}
      <section className="py-8 px-4 pb-16">
        <div className="max-w-5xl mx-auto">
          <div className="grid md:grid-cols-3 gap-4">
            <Link
              to="/student/student_001"
              className="p-6 rounded-2xl bg-white border border-slate-200 hover:border-cyan-300 hover:shadow-lg transition-all group"
            >
              <div className="flex items-center gap-4">
                <div className="w-14 h-14 bg-cyan-50 rounded-xl flex items-center justify-center group-hover:bg-cyan-100 transition-colors">
                  <span className="text-3xl">👤</span>
                </div>
                <div>
                  <h4 className="text-slate-800 font-bold group-hover:text-cyan-600 transition-colors">
                    学生画像
                  </h4>
                  <p className="text-slate-500 text-sm">查看学生能力详情</p>
                </div>
              </div>
            </Link>

            <Link
              to="/class"
              className="p-6 rounded-2xl bg-white border border-slate-200 hover:border-amber-300 hover:shadow-lg transition-all group"
            >
              <div className="flex items-center gap-4">
                <div className="w-14 h-14 bg-amber-50 rounded-xl flex items-center justify-center group-hover:bg-amber-100 transition-colors">
                  <span className="text-3xl">📊</span>
                </div>
                <div>
                  <h4 className="text-slate-800 font-bold group-hover:text-amber-600 transition-colors">
                    班级概览
                  </h4>
                  <p className="text-slate-500 text-sm">查看班级整体情况</p>
                </div>
              </div>
            </Link>

            <Link
              to="/knowledge"
              className="p-6 rounded-2xl bg-white border border-slate-200 hover:border-purple-300 hover:shadow-lg transition-all group"
            >
              <div className="flex items-center gap-4">
                <div className="w-14 h-14 bg-purple-50 rounded-xl flex items-center justify-center group-hover:bg-purple-100 transition-colors">
                  <span className="text-3xl">🧠</span>
                </div>
                <div>
                  <h4 className="text-slate-800 font-bold group-hover:text-purple-600 transition-colors">
                    知识图谱
                  </h4>
                  <p className="text-slate-500 text-sm">探索知识点关联</p>
                </div>
              </div>
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
};

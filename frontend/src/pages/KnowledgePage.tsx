// KnowledgePage: Knowledge graph with hierarchical tree layout - Light Theme
import React, { useState, useMemo, useCallback } from "react";
import { useMockStore } from "../mock/store/mockStore";
import type { KnowledgeNode } from "../types/knowledge";

// Chapter colors
const chapterColors: Record<
  number,
  { bg: string; border: string; text: string; badge: string }
> = {
  2: {
    bg: "bg-blue-50",
    border: "border-blue-200",
    text: "text-blue-600",
    badge: "bg-blue-100 text-blue-700",
  },
  3: {
    bg: "bg-purple-50",
    border: "border-purple-200",
    text: "text-purple-600",
    badge: "bg-purple-100 text-purple-700",
  },
  4: {
    bg: "bg-emerald-50",
    border: "border-emerald-200",
    text: "text-emerald-600",
    badge: "bg-emerald-100 text-emerald-700",
  },
  5: {
    bg: "bg-cyan-50",
    border: "border-cyan-200",
    text: "text-cyan-600",
    badge: "bg-cyan-100 text-cyan-700",
  },
  6: {
    bg: "bg-amber-50",
    border: "border-amber-200",
    text: "text-amber-600",
    badge: "bg-amber-100 text-amber-700",
  },
};

// Default color
const defaultColor = {
  bg: "bg-slate-50",
  border: "border-slate-200",
  text: "text-slate-600",
  badge: "bg-slate-100 text-slate-700",
};

export const KnowledgePage: React.FC = () => {
  const { knowledgeNodes, knowledgeEdges, knowledgePoints, getKnowledgePoint } =
    useMockStore();

  const [selectedNode, setSelectedNode] = useState<KnowledgeNode | null>(null);
  const [filter, setFilter] = useState<"all" | "knowledge" | "method">("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);

  // Group nodes by chapter
  const chapters = useMemo(() => {
    const grouped: Record<number, KnowledgeNode[]> = {};
    knowledgeNodes.forEach((node) => {
      if (!grouped[node.chapter]) {
        grouped[node.chapter] = [];
      }
      grouped[node.chapter].push(node);
    });
    return Object.entries(grouped)
      .map(([chapter, nodes]) => ({
        chapter: parseInt(chapter),
        nodes: nodes.sort((a, b) => a.id.localeCompare(b.id)),
      }))
      .sort((a, b) => a.chapter - b.chapter);
  }, [knowledgeNodes]);

  // Filter nodes
  const filteredChapters = useMemo(() => {
    return chapters
      .map((ch) => ({
        ...ch,
        nodes: ch.nodes.filter((node) => {
          const matchesFilter =
            filter === "all" ||
            (filter === "knowledge" && node.type === "knowledge") ||
            (filter === "method" && node.type === "method");

          const matchesSearch =
            searchQuery === "" ||
            node.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
            node.name.toLowerCase().includes(searchQuery.toLowerCase());

          return matchesFilter && matchesSearch;
        }),
      }))
      .filter((ch) => ch.nodes.length > 0);
  }, [chapters, filter, searchQuery]);

  // Get edges for a specific node
  const getNodeEdges = useCallback(
    (nodeId: string) => {
      const outgoing = knowledgeEdges.filter((e) => e.source === nodeId);
      const incoming = knowledgeEdges.filter((e) => e.target === nodeId);
      return { outgoing, incoming };
    },
    [knowledgeEdges],
  );

  // Get mastery color
  const getMasteryColor = (mastery?: number) => {
    if (!mastery) return "bg-slate-200";
    if (mastery >= 0.7) return "bg-emerald-500";
    if (mastery >= 0.4) return "bg-amber-500";
    return "bg-red-500";
  };

  // Get node details
  const selectedKPDetails = selectedNode
    ? knowledgePoints[selectedNode.id] || getKnowledgePoint(selectedNode.id)
    : null;

  // Count stats
  const stats = useMemo(() => {
    const knowledge = knowledgeNodes.filter(
      (n) => n.type === "knowledge",
    ).length;
    const method = knowledgeNodes.filter((n) => n.type === "method").length;
    return { knowledge, method, total: knowledgeNodes.length };
  }, [knowledgeNodes]);

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <div className="bg-white border-b border-slate-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-blue-500 rounded-xl flex items-center justify-center">
                <span className="text-2xl">🧠</span>
              </div>
              <div>
                <h1 className="text-2xl font-bold text-slate-800">
                  高中数学知识图谱
                </h1>
                <p className="text-slate-500 text-sm">
                  共{stats.total}个知识点 · {stats.knowledge}知识 +{" "}
                  {stats.method}方法 · {knowledgeEdges.length}条关联
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Filter Row */}
        <div className="flex flex-wrap items-center gap-4 mb-6">
          <div className="flex items-center gap-2 bg-white rounded-xl p-1.5 shadow-sm border border-slate-200">
            <button
              onClick={() => setFilter("all")}
              className={`px-5 py-2 rounded-lg text-sm font-medium transition-all ${
                filter === "all"
                  ? "bg-blue-600 text-white shadow-md"
                  : "text-slate-600 hover:bg-slate-100"
              }`}
            >
              全部
            </button>
            <button
              onClick={() => setFilter("knowledge")}
              className={`px-5 py-2 rounded-lg text-sm font-medium transition-all ${
                filter === "knowledge"
                  ? "bg-blue-600 text-white shadow-md"
                  : "text-slate-600 hover:bg-slate-100"
              }`}
            >
              📚 知识
            </button>
            <button
              onClick={() => setFilter("method")}
              className={`px-5 py-2 rounded-lg text-sm font-medium transition-all ${
                filter === "method"
                  ? "bg-purple-600 text-white shadow-md"
                  : "text-slate-600 hover:bg-slate-100"
              }`}
            >
              🔧 方法
            </button>
          </div>

          <div className="flex-1 min-w-[200px] max-w-md">
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">
                🔍
              </span>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="搜索知识点名称或ID..."
                className="w-full pl-10 pr-4 py-2.5 bg-white border border-slate-200 rounded-xl text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400 shadow-sm"
              />
            </div>
          </div>

          <div className="text-sm text-slate-500 bg-white px-4 py-2 rounded-lg border border-slate-200 shadow-sm">
            显示{" "}
            {filteredChapters.reduce((acc, ch) => acc + ch.nodes.length, 0)} /{" "}
            {stats.total} 个节点
          </div>
        </div>

        {/* Main Content */}
        <div className="grid lg:grid-cols-3 gap-6">
          {/* Chapter Tree */}
          <div className="lg:col-span-2 space-y-4">
            {filteredChapters.map(({ chapter, nodes }) => {
              const colors = chapterColors[chapter] || defaultColor;
              return (
                <div
                  key={chapter}
                  className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden"
                >
                  {/* Chapter Header */}
                  <div
                    className={`px-5 py-3 bg-gradient-to-r ${colors.bg} border-b ${colors.border}`}
                  >
                    <h3 className={`font-bold ${colors.text}`}>
                      第{chapter}章 · {nodes.length}个知识点
                    </h3>
                  </div>

                  {/* Nodes in this chapter */}
                  <div className="p-4">
                    <div className="flex flex-wrap gap-3">
                      {nodes.map((node) => {
                        const isSelected = selectedNode?.id === node.id;
                        const isHovered = hoveredNode === node.id;
                        const isMethod = node.type === "method";
                        const colors =
                          chapterColors[node.chapter] || defaultColor;

                        return (
                          <div
                            key={node.id}
                            className={`relative px-4 py-3 rounded-xl border-2 cursor-pointer transition-all ${
                              isSelected
                                ? `${colors.bg} ${colors.border} ring-2 ring-blue-500/50 shadow-md`
                                : isHovered
                                  ? `${colors.bg} ${colors.border} shadow-md`
                                  : "bg-slate-50 border-slate-200 hover:border-slate-300 hover:shadow-sm"
                            }`}
                            onClick={() => setSelectedNode(node)}
                            onMouseEnter={() => setHoveredNode(node.id)}
                            onMouseLeave={() => setHoveredNode(null)}
                          >
                            <div className="flex items-center gap-2">
                              <span className="text-sm">
                                {isMethod ? "🔧" : "📚"}
                              </span>
                              <div>
                                <p className="text-slate-800 text-sm font-semibold">
                                  {node.id}
                                </p>
                                <p className="text-slate-500 text-xs">
                                  {node.name}
                                </p>
                              </div>
                            </div>
                            {/* Mastery bar */}
                            {node.mastery !== undefined && (
                              <div className="mt-2 h-1.5 w-full bg-slate-200 rounded-full overflow-hidden">
                                <div
                                  className={`h-full ${getMasteryColor(node.mastery)} transition-all`}
                                  style={{
                                    width: `${(node.mastery || 0) * 100}%`,
                                  }}
                                />
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Node Detail Panel */}
          <div className="lg:col-span-1">
            <div className="sticky top-4">
              {selectedNode && selectedKPDetails ? (
                <div className="bg-white rounded-2xl border border-slate-200 shadow-lg overflow-hidden">
                  <div className="px-5 py-4 bg-gradient-to-r from-slate-50 to-slate-100 border-b border-slate-200">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="text-xl">
                          {selectedNode.type === "method" ? "🔧" : "📚"}
                        </span>
                        <h3 className="text-slate-800 font-bold">
                          {selectedNode.id}
                        </h3>
                      </div>
                      <button
                        onClick={() => setSelectedNode(null)}
                        className="text-slate-400 hover:text-slate-600 text-sm w-8 h-8 rounded-lg hover:bg-slate-200 transition-colors"
                      >
                        ✕
                      </button>
                    </div>
                  </div>

                  <div className="p-5 space-y-5">
                    {/* Name & Type */}
                    <div>
                      <h4 className="text-xl font-bold text-slate-800 mb-2">
                        {selectedKPDetails.name}
                      </h4>
                      <div className="flex items-center gap-2">
                        <span
                          className={`px-3 py-1 rounded-lg text-xs font-medium ${
                            selectedNode.type === "method"
                              ? "bg-purple-100 text-purple-700"
                              : "bg-blue-100 text-blue-700"
                          }`}
                        >
                          {selectedNode.type === "method"
                            ? "🔧 方法点"
                            : "📚 知识点"}
                        </span>
                        <span className="px-3 py-1 rounded-lg text-xs font-medium bg-slate-100 text-slate-600">
                          第{selectedKPDetails.chapter}章
                        </span>
                      </div>
                    </div>

                    {/* Content */}
                    <div>
                      <p className="text-xs text-slate-500 mb-1.5 font-medium">
                        内容说明
                      </p>
                      <p className="text-slate-700 text-sm leading-relaxed">
                        {selectedKPDetails.content}
                      </p>
                    </div>

                    {/* Formula */}
                    {selectedKPDetails.formula && (
                      <div>
                        <p className="text-xs text-slate-500 mb-1.5 font-medium">
                          公式
                        </p>
                        <div className="bg-gradient-to-br from-slate-50 to-slate-100 rounded-xl px-4 py-3 font-mono text-sm text-cyan-700 border border-slate-200">
                          {selectedKPDetails.formula}
                        </div>
                      </div>
                    )}

                    {/* Prerequisites */}
                    {selectedKPDetails.prerequisites.length > 0 && (
                      <div>
                        <p className="text-xs text-slate-500 mb-2 font-medium">
                          📚 前置知识（先学）
                        </p>
                        <div className="flex flex-wrap gap-2">
                          {selectedKPDetails.prerequisites.map((prereqId) => {
                            const prereqKP = knowledgePoints[prereqId];
                            return (
                              <button
                                key={prereqId}
                                onClick={() => {
                                  const node = knowledgeNodes.find(
                                    (n) => n.id === prereqId,
                                  );
                                  if (node) setSelectedNode(node);
                                }}
                                className="px-3 py-1.5 bg-blue-50 border border-blue-200 rounded-lg text-blue-700 text-xs font-medium hover:bg-blue-100 transition-colors"
                              >
                                {prereqId}
                                {prereqKP && (
                                  <span className="ml-1 text-blue-500">
                                    {prereqKP.name}
                                  </span>
                                )}
                              </button>
                            );
                          })}
                        </div>
                      </div>
                    )}

                    {/* Related Types */}
                    {selectedKPDetails.relatedTypes.length > 0 && (
                      <div>
                        <p className="text-xs text-slate-500 mb-2 font-medium">
                          📝 相关题型
                        </p>
                        <div className="flex flex-wrap gap-2">
                          {selectedKPDetails.relatedTypes.map((type) => (
                            <span
                              key={type}
                              className="px-3 py-1.5 bg-slate-100 rounded-lg text-slate-600 text-xs"
                            >
                              {type}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Mastery (if available) */}
                    {selectedNode.mastery !== undefined && (
                      <div>
                        <p className="text-xs text-slate-500 mb-2 font-medium">
                          📊 掌握度
                        </p>
                        <div className="flex items-center gap-3">
                          <div className="flex-1 h-3 bg-slate-100 rounded-full overflow-hidden border border-slate-200">
                            <div
                              className={`h-full ${getMasteryColor(selectedNode.mastery)} transition-all`}
                              style={{
                                width: `${selectedNode.mastery * 100}%`,
                              }}
                            />
                          </div>
                          <span className="text-slate-800 text-sm font-bold">
                            {(selectedNode.mastery * 100).toFixed(0)}%
                          </span>
                        </div>
                      </div>
                    )}

                    {/* Connections */}
                    {(() => {
                      const { outgoing, incoming } = getNodeEdges(
                        selectedNode.id,
                      );
                      if (outgoing.length === 0 && incoming.length === 0)
                        return null;
                      return (
                        <div>
                          <p className="text-xs text-slate-500 mb-2 font-medium">
                            🔗 图谱关联
                          </p>
                          <div className="space-y-2">
                            {incoming.length > 0 && (
                              <div>
                                <p className="text-xs text-slate-400 mb-1">
                                  ← 被以下依赖
                                </p>
                                <div className="flex flex-wrap gap-1">
                                  {incoming.map((e) => (
                                    <span
                                      key={e.source}
                                      className="px-2 py-1 bg-slate-100 rounded text-xs text-slate-600"
                                    >
                                      {e.source}
                                    </span>
                                  ))}
                                </div>
                              </div>
                            )}
                            {outgoing.length > 0 && (
                              <div>
                                <p className="text-xs text-slate-400 mb-1">
                                  → 依赖以下
                                </p>
                                <div className="flex flex-wrap gap-1">
                                  {outgoing.map((e) => (
                                    <span
                                      key={e.target}
                                      className="px-2 py-1 bg-slate-100 rounded text-xs text-slate-600"
                                    >
                                      {e.target}
                                    </span>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        </div>
                      );
                    })()}
                  </div>
                </div>
              ) : (
                <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-8 text-center">
                  <div className="w-16 h-16 bg-gradient-to-br from-purple-100 to-blue-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
                    <span className="text-3xl">🧠</span>
                  </div>
                  <p className="text-slate-600 font-medium">
                    点击左侧知识点查看详情
                  </p>
                  <p className="text-slate-400 text-sm mt-2">
                    显示前置知识、公式、题型关联等信息
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

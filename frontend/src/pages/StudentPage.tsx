// StudentPage: Individual student profile with heatmap + dimension chart - Light Theme
import React from "react";
import { useParams, Link } from "react-router-dom";
import { useMockStore } from "../mock/store/mockStore";
import { HeatmapChart } from "../components/charts/HeatmapChart";
import { DimensionRatioChart } from "../components/charts/DimensionRatioChart";
import { ProgressBar } from "../components/shared/ProgressBar";
import { KPBadge } from "../components/shared/KPBadge";
import { AlertBadge } from "../components/shared/AlertBadge";
import type { Student } from "../types/student";

export const StudentPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { getStudent, getKnowledgePoint } = useMockStore();

  const student = getStudent(id || "student_001") as Student | undefined;

  if (!student) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-4xl mb-4">🔍</p>
          <p className="text-slate-600">学生不存在</p>
          <Link
            to="/class"
            className="text-blue-500 hover:underline mt-2 block"
          >
            返回班级概览
          </Link>
        </div>
      </div>
    );
  }

  // Prepare heatmap data
  const heatmapData = Object.entries(student.kpMastery).map(
    ([kpId, mastery]) => {
      const kp = getKnowledgePoint(kpId);
      return {
        kpId,
        name: kp?.name || kpId,
        chapter: kp?.chapter || 0,
        mastery: mastery.mastery,
        attempts: mastery.attempt,
      };
    },
  );

  // Sort by chapter
  heatmapData.sort((a, b) => a.chapter - b.chapter);

  // Get weak KPs details
  const weakKPsDetails = student.weakKpIds.map((kpId) => {
    const kp = getKnowledgePoint(kpId);
    const mastery = student.kpMastery[kpId];
    return { kpId, kp, mastery };
  });

  // Calculate stats
  const solveRate =
    student.totalProblems > 0
      ? (student.totalSolved / student.totalProblems) * 100
      : 0;

  const avgHintsPerProblem =
    student.totalInterventions > 0
      ? (student.totalSolved * 2.3) / student.totalProblems
      : 0;

  // Format timestamp
  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffDays = Math.floor(
      (now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24),
    );

    if (diffDays === 0) return "今天";
    if (diffDays === 1) return "昨天";
    if (diffDays === 2) return "前天";
    return `${diffDays}天前`;
  };

  const formatHour = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString("zh-CN", {
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  // Get mastery color
  const getMasteryColor = (mastery: number) => {
    if (mastery >= 0.8) return "green";
    if (mastery >= 0.5) return "yellow";
    return "red";
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-blue-50">
      {/* Header */}
      <div className="bg-white border-b border-slate-200 shadow-sm">
        <div className="max-w-6xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link
                to="/class"
                className="text-slate-400 hover:text-slate-600 transition-colors"
              >
                ← 返回
              </Link>
              <div className="flex items-center gap-4">
                <div className="w-14 h-14 bg-gradient-to-br from-blue-100 to-cyan-100 rounded-2xl flex items-center justify-center">
                  <span className="text-3xl">{student.avatar}</span>
                </div>
                <div>
                  <h1 className="text-2xl font-bold text-slate-800">
                    {student.name}
                  </h1>
                  <div className="flex items-center gap-3 mt-1">
                    <span className="text-slate-500 text-sm">
                      {student.grade}
                    </span>
                    <span className="text-slate-300">·</span>
                    <span className="text-slate-500 text-sm">
                      学习{student.activeDays}天
                    </span>
                    <span className="text-slate-300">·</span>
                    <span className="text-slate-500 text-sm">
                      🎯 完成{student.totalProblems}题
                    </span>
                  </div>
                </div>
              </div>
            </div>
            <AlertBadge
              status={student.status}
              pulse={student.status === "attention"}
            />
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-6xl mx-auto px-4 py-6 space-y-6">
        {/* Top Stats Row */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-4">
            <p className="text-slate-500 text-xs mb-1">活跃天数</p>
            <p className="text-2xl font-bold text-slate-800">
              {student.activeDays}
            </p>
            <p className="text-xs text-emerald-500 mt-1">天</p>
          </div>
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-4">
            <p className="text-slate-500 text-xs mb-1">总题数</p>
            <p className="text-2xl font-bold text-slate-800">
              {student.totalProblems}
            </p>
            <p className="text-xs text-slate-400 mt-1">题</p>
          </div>
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-4">
            <p className="text-slate-500 text-xs mb-1">解决率</p>
            <p className="text-2xl font-bold text-emerald-600">
              {solveRate.toFixed(0)}%
            </p>
            <p className="text-xs text-slate-400 mt-1">
              {student.totalSolved}/{student.totalProblems}
            </p>
          </div>
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-4">
            <p className="text-slate-500 text-xs mb-1">升级次数</p>
            <p className="text-2xl font-bold text-amber-600">
              {student.totalEscalation}
            </p>
            <p className="text-xs text-slate-400 mt-1">次</p>
          </div>
        </div>

        {/* Charts Row */}
        <div className="grid md:grid-cols-2 gap-6">
          {/* Dimension Ratio Chart */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
            <h3 className="text-slate-800 font-semibold mb-4">维度比例追踪</h3>
            <div className="flex items-center justify-center">
              <DimensionRatioChart
                ratio={student.dimensionRatio}
                trend={student.ratioTrend}
                confidence={student.trendConfidence}
                size={180}
              />
            </div>
            <div className="mt-4 text-center">
              <p className="text-sm text-slate-500">
                评估：R型断点{" "}
                {student.ratioTrend === "falling" ? "减少" : "稳定"}✓
              </p>
              <p className="text-xs text-slate-400 mt-1">
                置信度：{(student.trendConfidence * 100).toFixed(0)}%
              </p>
            </div>
          </div>

          {/* Heatmap Chart */}
          <div>
            <HeatmapChart data={heatmapData} title="知识点掌握度热力图" />
            <div className="mt-4 bg-white rounded-xl border border-slate-200 shadow-sm p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500">干预效率</p>
                  <p className="text-lg font-semibold text-slate-800">
                    {avgHintsPerProblem.toFixed(1)}次提示/题
                  </p>
                </div>
                <div className="text-right">
                  <p
                    className={`text-lg font-semibold ${
                      avgHintsPerProblem < 2
                        ? "text-emerald-600"
                        : "text-amber-600"
                    }`}
                  >
                    {avgHintsPerProblem < 2 ? "✓ 超出预期" : "需关注"}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Intervention History */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
          <h3 className="text-slate-800 font-semibold mb-4">
            干预历史（最近5条）
          </h3>
          <div className="space-y-3">
            {student.interventionHistory.slice(0, 5).map((record, index) => (
              <div
                key={record.id}
                className="flex items-center gap-4 p-3 bg-slate-50 rounded-lg animate-fade-in border border-slate-100"
                style={{ animationDelay: `${index * 0.1}s` }}
              >
                <div className="text-center min-w-[60px]">
                  <p className="text-xs text-slate-500">
                    {formatTime(record.timestamp)}
                  </p>
                  <p className="text-xs text-slate-400">
                    {formatHour(record.timestamp)}
                  </p>
                </div>
                <div className="flex-1">
                  <p className="text-slate-800 text-sm">{record.problem}</p>
                  <div className="flex items-center gap-2 mt-1">
                    <span
                      className={`px-2 py-0.5 rounded text-xs ${
                        record.dimension === "RESOURCE"
                          ? "bg-purple-100 text-purple-700"
                          : "bg-cyan-100 text-cyan-700"
                      }`}
                    >
                      {record.level}
                    </span>
                    {record.kpIds.map((kpId) => (
                      <KPBadge key={kpId} kpId={kpId} size="sm" />
                    ))}
                  </div>
                </div>
                <div className="text-right">
                  <span
                    className={`px-2 py-1 rounded text-xs font-medium ${
                      record.outcome === "SOLVED"
                        ? "bg-emerald-100 text-emerald-700"
                        : record.outcome === "ESCALATED"
                          ? "bg-amber-100 text-amber-700"
                          : "bg-red-100 text-red-700"
                    }`}
                  >
                    {record.outcome === "SOLVED"
                      ? "✓ 已解决"
                      : record.outcome === "ESCALATED"
                        ? "↑ 升级"
                        : "✕ 终止"}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Weak KPs Detail */}
        {weakKPsDetails.length > 0 && (
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
            <h3 className="text-slate-800 font-semibold mb-4">
              薄弱知识点详细
            </h3>
            <div className="space-y-4">
              {weakKPsDetails.map((item, index) => {
                const masteryValue = item.mastery?.mastery || 0;
                const masteryColor = getMasteryColor(masteryValue);

                return (
                  <div
                    key={item.kpId}
                    className={`p-4 rounded-lg border animate-fade-in ${
                      masteryValue < 0.3
                        ? "bg-red-50 border-red-200"
                        : "bg-amber-50 border-amber-200"
                    }`}
                    style={{ animationDelay: `${index * 0.1}s` }}
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <KPBadge
                          kpId={item.kpId}
                          name={item.kp?.name}
                          type={item.kp?.type}
                        />
                        {masteryValue < 0.3 && (
                          <span className="px-2 py-0.5 bg-red-100 text-red-600 text-xs rounded animate-pulse">
                            严重预警
                          </span>
                        )}
                      </div>
                      <span
                        className={`text-lg font-bold ${
                          masteryColor === "green"
                            ? "text-emerald-600"
                            : masteryColor === "yellow"
                              ? "text-amber-600"
                              : "text-red-600"
                        }`}
                      >
                        {(masteryValue * 100).toFixed(0)}%
                      </span>
                    </div>

                    <ProgressBar
                      value={masteryValue * 100}
                      color={masteryColor}
                      size="md"
                    />

                    <div className="mt-3 grid grid-cols-3 gap-4 text-xs">
                      <div>
                        <span className="text-slate-500">尝试次数：</span>
                        <span className="text-slate-700 ml-1">
                          {item.mastery?.attempt || 0}
                        </span>
                      </div>
                      <div>
                        <span className="text-slate-500">正确次数：</span>
                        <span className="text-slate-700 ml-1">
                          {item.mastery?.correct || 0}
                        </span>
                      </div>
                      <div>
                        <span className="text-slate-500">总提示：</span>
                        <span className="text-slate-700 ml-1">
                          {item.mastery?.totalHints || 0}
                        </span>
                      </div>
                    </div>

                    <div className="mt-3 pt-3 border-t border-slate-200">
                      <p className="text-xs text-slate-500">
                        推荐：
                        {masteryValue < 0.3
                          ? "继续练习基础题，减少综合题"
                          : "观看图解教程，加强练习"}
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

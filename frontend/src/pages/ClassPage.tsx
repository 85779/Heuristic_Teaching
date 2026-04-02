// ClassPage: Class overview with scatter plot + alert list
import React, { useMemo } from "react";
import { Link } from "react-router-dom";
import { useMockStore } from "../mock/store/mockStore";
import { ScatterPlot } from "../components/charts/ScatterPlot";
import { StudentCard } from "../components/shared/StudentCard";
import { AlertBadge } from "../components/shared/AlertBadge";

export const ClassPage: React.FC = () => {
  const { allStudents, knowledgePoints } = useMockStore();

  // Calculate class statistics
  const classStats = useMemo(() => {
    const ratios = allStudents.map((s) => s.dimensionRatio);
    const avgRatio = ratios.reduce((a, b) => a + b, 0) / ratios.length;
    const sortedRatios = [...ratios].sort((a, b) => a - b);
    const medianRatio = sortedRatios[Math.floor(sortedRatios.length / 2)];
    const variance =
      ratios.reduce((sum, r) => sum + Math.pow(r - avgRatio, 2), 0) /
      ratios.length;
    const stdDev = Math.sqrt(variance);

    return {
      avgRatio,
      medianRatio,
      stdDev,
      totalStudents: allStudents.length,
    };
  }, [allStudents]);

  // Prepare scatter plot data
  const scatterData = useMemo(() => {
    return allStudents.map((student) => {
      const masteryValues = Object.values(student.kpMastery).map(
        (m) => m.mastery,
      );
      const avgMastery =
        masteryValues.length > 0
          ? masteryValues.reduce((a, b) => a + b, 0) / masteryValues.length
          : 0;

      return {
        id: student.id,
        name: student.name,
        dimensionRatio: student.dimensionRatio,
        mastery: avgMastery,
        status: student.status,
      };
    });
  }, [allStudents]);

  // Get warning/attention students
  const alertStudents = useMemo(() => {
    return allStudents
      .filter((s) => s.status === "warning" || s.status === "attention")
      .sort((a, b) => {
        if (a.status === "attention" && b.status !== "attention") return -1;
        if (a.status !== "attention" && b.status === "attention") return 1;
        return a.dimensionRatio - b.dimensionRatio;
      });
  }, [allStudents]);

  // Calculate weak KP class distribution
  const weakKPDistribution = useMemo(() => {
    const kpCount: Record<string, number> = {};
    const kpNames: Record<string, string> = {};
    const kpMasterySum: Record<string, number> = {};
    const kpMasteryCount: Record<string, number> = {};

    allStudents.forEach((student) => {
      student.weakKpIds.forEach((kpId) => {
        kpCount[kpId] = (kpCount[kpId] || 0) + 1;
        if (!kpNames[kpId]) {
          const kp = knowledgePoints[kpId];
          kpNames[kpId] = kp?.name || kpId;
        }
        // Calculate average mastery from students' kpMastery data
        const studentMastery = student.kpMastery[kpId];
        if (studentMastery) {
          kpMasterySum[kpId] =
            (kpMasterySum[kpId] || 0) + studentMastery.mastery;
          kpMasteryCount[kpId] = (kpMasteryCount[kpId] || 0) + 1;
        }
      });
    });

    return Object.entries(kpCount)
      .map(([kpId, count]) => ({
        kpId,
        name: kpNames[kpId],
        count,
        percentage: Math.round((count / allStudents.length) * 100),
        avgMastery: kpMasteryCount[kpId]
          ? kpMasterySum[kpId] / kpMasteryCount[kpId]
          : 0,
      }))
      .sort((a, b) => b.count - a.count);
  }, [allStudents, knowledgePoints]);

  // Normal students for the list
  const normalStudents = useMemo(() => {
    return allStudents.filter((s) => s.status === "normal");
  }, [allStudents]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-blue-50">
      {/* Header */}
      <div className="bg-white border-b border-slate-200 shadow-sm">
        <div className="max-w-6xl mx-auto px-4 py-4">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-xl flex items-center justify-center">
              <span className="text-2xl">📊</span>
            </div>
            <div>
              <h1 className="text-2xl font-bold text-slate-800">
                班级整体情况
              </h1>
              <p className="text-slate-500 text-sm">
                高三（1）班 · 共{classStats.totalStudents}人 · 近30天
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-4 py-6 space-y-6">
        {/* Class Stats Row */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm hover:shadow-md transition-shadow">
            <p className="text-slate-500 text-xs mb-1">班级均值</p>
            <p className="text-2xl font-bold text-slate-800">
              {classStats.avgRatio.toFixed(2)}
            </p>
            <p className="text-xs text-slate-400">R维度比例</p>
          </div>
          <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm hover:shadow-md transition-shadow">
            <p className="text-slate-500 text-xs mb-1">中位数</p>
            <p className="text-2xl font-bold text-slate-800">
              {classStats.medianRatio.toFixed(2)}
            </p>
            <p className="text-xs text-slate-400">R维度比例</p>
          </div>
          <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm hover:shadow-md transition-shadow">
            <p className="text-slate-500 text-xs mb-1">标准差</p>
            <p className="text-2xl font-bold text-slate-800">
              {classStats.stdDev.toFixed(2)}
            </p>
            <p className="text-xs text-slate-400">分散程度</p>
          </div>
          <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm hover:shadow-md transition-shadow">
            <p className="text-slate-500 text-xs mb-1">预警人数</p>
            <p className="text-2xl font-bold text-amber-500">
              {alertStudents.length}
            </p>
            <p className="text-xs text-slate-400">需要关注</p>
          </div>
        </div>

        {/* Scatter Plot */}
        <ScatterPlot
          data={scatterData}
          title="学生R维度比例分布（点击学生查看详情）"
        />

        {/* Bottom Grid */}
        <div className="grid md:grid-cols-2 gap-6">
          {/* Alert List */}
          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
            <h3 className="text-slate-800 font-semibold mb-4 flex items-center gap-2">
              <span>🚨</span> 预警名单
            </h3>
            <div className="space-y-3">
              {alertStudents.length > 0 ? (
                alertStudents.map((student, index) => (
                  <div
                    key={student.id}
                    className={`p-3 rounded-lg animate-fade-in ${
                      student.status === "attention"
                        ? "bg-red-50 border border-red-200"
                        : "bg-amber-50 border border-amber-200"
                    }`}
                    style={{ animationDelay: `${index * 0.1}s` }}
                  >
                    <Link
                      to={`/student/${student.id}`}
                      className="flex items-center justify-between"
                    >
                      <div className="flex items-center gap-3">
                        <span className="text-2xl">{student.avatar}</span>
                        <div>
                          <p className="text-slate-800 font-medium flex items-center gap-2">
                            {student.name}
                            {student.status === "attention" && (
                              <span className="text-xs text-red-500 animate-pulse">
                                ⭐ 需关注
                              </span>
                            )}
                          </p>
                          <p className="text-xs text-slate-500 mt-0.5">
                            ratio={student.dimensionRatio.toFixed(2)}
                            {student.ratioTrend === "rising" && " ↑"}
                            {student.ratioTrend === "stable" && " →"}
                            {student.ratioTrend === "falling" && " ↓"}
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <AlertBadge status={student.status} size="sm" />
                        <p className="text-xs text-slate-400 mt-1">
                          {student.weakTopics.slice(0, 2).join("、")}
                        </p>
                      </div>
                    </Link>
                  </div>
                ))
              ) : (
                <div className="text-center py-8 text-slate-400">
                  <p className="text-4xl mb-2">✓</p>
                  <p>暂无预警学生</p>
                </div>
              )}
            </div>
          </div>

          {/* Weak KP Distribution */}
          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
            <h3 className="text-slate-800 font-semibold mb-4 flex items-center gap-2">
              <span>📚</span> 薄弱知识点班级分布
            </h3>
            <div className="space-y-4">
              {weakKPDistribution.slice(0, 5).map((kp, index) => (
                <div
                  key={kp.kpId}
                  className="animate-fade-in"
                  style={{ animationDelay: `${index * 0.1}s` }}
                >
                  <div className="flex items-center justify-between mb-1">
                    <div className="flex items-center gap-2">
                      <span
                        className={`px-2 py-0.5 rounded text-xs font-mono ${
                          kp.avgMastery && kp.avgMastery < 0.3
                            ? "bg-red-100 text-red-700"
                            : "bg-amber-100 text-amber-700"
                        }`}
                      >
                        {kp.kpId}
                      </span>
                      <span className="text-sm text-slate-700">{kp.name}</span>
                    </div>
                    <span className="text-sm text-slate-500">
                      {kp.count}人({kp.percentage}%)
                    </span>
                  </div>
                  <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all ${
                        kp.percentage > 40
                          ? "bg-red-500"
                          : kp.percentage > 25
                            ? "bg-amber-500"
                            : "bg-yellow-500"
                      }`}
                      style={{ width: `${kp.percentage}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Normal Students */}
        {normalStudents.length > 0 && (
          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
            <h3 className="text-slate-800 font-semibold mb-4 flex items-center gap-2">
              <span>✓</span> 正常学生
            </h3>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
              {normalStudents.map((student) => (
                <StudentCard key={student.id} student={student} compact />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// StudentCard: Student summary card component
import React from "react";
import { Link } from "react-router-dom";
import type { Student } from "../../types/student";
import { AlertBadge } from "./AlertBadge";
import { ProgressBar } from "./ProgressBar";

interface StudentCardProps {
  student: Student;
  compact?: boolean;
}

export const StudentCard: React.FC<StudentCardProps> = ({
  student,
  compact = false,
}) => {
  const solveRate =
    student.totalProblems > 0
      ? (student.totalSolved / student.totalProblems) * 100
      : 0;

  if (compact) {
    return (
      <Link
        to={`/student/${student.id}`}
        className="block p-3 bg-white rounded-lg border border-slate-200 shadow-sm hover:border-blue-400 hover:shadow transition-all"
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-2xl">{student.avatar}</span>
            <div>
              <p className="font-medium text-slate-900">{student.name}</p>
              <p className="text-xs text-slate-500">{student.grade}</p>
            </div>
          </div>
          <AlertBadge status={student.status} />
        </div>
      </Link>
    );
  }

  return (
    <Link
      to={`/student/${student.id}`}
      className="block p-4 bg-white rounded-xl border border-slate-200 shadow-sm hover:border-blue-400 hover:shadow-md transition-all"
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <span className="text-3xl">{student.avatar}</span>
          <div>
            <p className="font-semibold text-slate-900">{student.name}</p>
            <p className="text-sm text-slate-500">{student.grade}</p>
          </div>
        </div>
        <AlertBadge
          status={student.status}
          pulse={student.status === "attention"}
        />
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-3 mb-4">
        <div className="text-center p-2 bg-slate-100 rounded-lg">
          <p className="text-lg font-semibold text-slate-900">
            {student.activeDays}
          </p>
          <p className="text-xs text-slate-500">活跃天数</p>
        </div>
        <div className="text-center p-2 bg-slate-100 rounded-lg">
          <p className="text-lg font-semibold text-slate-900">
            {student.totalProblems}
          </p>
          <p className="text-xs text-slate-500">总题数</p>
        </div>
        <div className="text-center p-2 bg-slate-100 rounded-lg">
          <p className="text-lg font-semibold text-slate-900">
            {solveRate.toFixed(0)}%
          </p>
          <p className="text-xs text-slate-500">解决率</p>
        </div>
      </div>

      {/* Dimension ratio */}
      <div className="mb-3">
        <div className="flex justify-between text-xs mb-1">
          <span className="text-slate-500">R/M维度比</span>
          <span className="text-slate-700 font-medium">
            {(student.dimensionRatio * 100).toFixed(0)}%
          </span>
        </div>
        <ProgressBar
          value={student.dimensionRatio * 100}
          color="purple"
          size="sm"
        />
      </div>

      {/* Weak topics */}
      {student.weakTopics.length > 0 && (
        <div className="flex flex-wrap gap-1 mt-3">
          {student.weakTopics.slice(0, 3).map((topic) => (
            <span
              key={topic}
              className="px-2 py-0.5 bg-red-100 text-red-700 text-xs rounded"
            >
              {topic}
            </span>
          ))}
          {student.weakTopics.length > 3 && (
            <span className="px-2 py-0.5 bg-slate-100 text-slate-600 text-xs rounded">
              +{student.weakTopics.length - 3}
            </span>
          )}
        </div>
      )}
    </Link>
  );
};

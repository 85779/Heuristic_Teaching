// App Layout with navigation - Light Theme
import React from "react";
import { Link, useLocation, Outlet } from "react-router-dom";

const navItems = [
  { path: "/", label: "首页", icon: "🏠" },
  { path: "/demo", label: "演示", icon: "🎬" },
  { path: "/student/student_001", label: "学生档案", icon: "👤" },
  { path: "/class", label: "班级概览", icon: "📊" },
  { path: "/knowledge", label: "知识图谱", icon: "🧠" },
];

export const AppLayout: React.FC = () => {
  const location = useLocation();

  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-50 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-2xl">🎓</span>
            <h1 className="text-xl font-semibold text-slate-800">
              Socrates 智能数学辅导系统
            </h1>
          </div>

          {/* Nav */}
          <nav className="flex items-center gap-1">
            {navItems.map((item) => {
              const isActive =
                location.pathname === item.path ||
                (item.path !== "/" && location.pathname.startsWith(item.path));
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`px-4 py-2 rounded-lg flex items-center gap-2 transition-all ${
                    isActive
                      ? "bg-blue-600 text-white shadow-md"
                      : "text-slate-600 hover:text-blue-600 hover:bg-blue-50"
                  }`}
                >
                  <span>{item.icon}</span>
                  <span className="text-sm font-medium">{item.label}</span>
                </Link>
              );
            })}
          </nav>
        </div>
      </header>

      {/* Main content - Outlet renders child routes */}
      <main className="flex-1">
        <Outlet />
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-slate-200 py-4 mt-8">
        <div className="max-w-7xl mx-auto px-4 text-center text-slate-500 text-sm">
          Socrates 智能数学辅导系统 · 项目申报演示 · 2026
        </div>
      </footer>
    </div>
  );
};

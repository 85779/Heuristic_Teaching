import { Outlet, NavLink, useLocation } from 'react-router-dom';

const nav = ['首页','学习','画像','教学'];
const paths = ['/','/study','/profile/student_001','/teaching/student_001'];

export default function Layout() {
  const { pathname } = useLocation();
  return (
    <div className="min-h-screen bg-paper bg-grid">
      <nav className="sticky top-0 z-50 bg-paper/90 backdrop-blur border-b border-ink/5">
        <div className="max-w-5xl mx-auto px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-8">
            <h1 className="font-serif text-xl font-bold text-ink tracking-tight">
              Socrates<span className="text-chalk font-sans text-sm font-normal ml-2 tracking-normal">智能辅导</span>
            </h1>
            <div className="flex gap-1">
              {nav.map((n, i) => {
                const active = paths[i] === '/' ? pathname === '/' : pathname.startsWith(paths[i].replace(/\/[^/]+$/,''));
                return (
                  <NavLink key={n} to={paths[i]} className={`px-3 py-1.5 rounded-md text-sm transition-colors font-sans ${
                    active ? 'bg-ink/5 text-ink font-medium' : 'text-slate/60 hover:text-ink hover:bg-ink/[0.03]'
                  }`}>{n}</NavLink>
                );
              })}
            </div>
          </div>
          <span className="text-xs text-slate/40 flex items-center gap-1.5 font-sans">
            <span className="w-1.5 h-1.5 rounded-full bg-sage inline-block" />运行中
          </span>
        </div>
      </nav>
      <main className="max-w-4xl mx-auto px-8 py-10"><Outlet /></main>
    </div>
  );
}

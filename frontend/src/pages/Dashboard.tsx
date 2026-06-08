import { useEffect, useState } from 'react';
import { NavLink } from 'react-router-dom';
import { api } from '../core/api/client';

const mods = [
  ['学习','输入题目 → 自动评估 → 智能提示 → 推荐练习','/study','#4a6fa5','#edf1f7'],
  ['学生画像','维度比例追踪 · 趋势分析 · 路由提示','/profile/student_001','#3a7d8c','#edf5f7'],
  ['教学策略','七种自适应策略 · 经验等级适配','/teaching/student_001','#c44d4d','#faf0f0'],
];

export default function Dashboard() {
  const [ok, setOk] = useState(false);
  useEffect(() => { api.get('/health').then(() => setOk(true)).catch(() => setOk(false)); }, []);

  return (
    <div className="space-y-10">
      <header className="text-center space-y-3 pt-4">
        <h1 className="font-serif text-4xl font-black text-ink tracking-tight">Socrates</h1>
        <p className="text-slate/60 text-lg font-sans">高中数学 AI 个性化学习平台</p>
      </header>

      <div className="grid grid-cols-4 gap-4">
        {[
          ['测试通过','394','text-sage'],
          ['知识点','175','text-chalk'],
          ['功能页面','4','text-amber'],
          ['系统状态',ok?'正常':'离线',ok?'text-sage':'text-rose'],
        ].map(([l,v,c]) => (
          <div key={l as string} className="bg-white/80 border border-ink/5 rounded-xl p-5 backdrop-blur">
            <p className="text-xs text-slate/50 uppercase tracking-wider mb-1 font-sans">{l}</p>
            <p className={`text-2xl font-bold ${c} font-serif`}>{v as string}</p>
          </div>
        ))}
      </div>

      <div className="space-y-3">
        {mods.map(([name, desc, path, color, bg]) => (
          <NavLink key={path} to={path}
            className="block bg-white/80 border border-ink/5 rounded-xl p-5 hover:shadow-md transition-all duration-200 group"
            style={{ borderLeftColor: color, borderLeftWidth: '3px' }}>
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-serif text-lg font-semibold text-ink">{name}</h3>
                <p className="text-sm text-slate/60 mt-0.5 font-sans">{desc}</p>
              </div>
              <span className="text-slate/30 group-hover:text-ink/50 transition-colors font-serif text-lg">→</span>
            </div>
          </NavLink>
        ))}
      </div>
    </div>
  );
}

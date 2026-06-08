import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { teaching } from '../core/api/client';

export default function Teaching() {
  const { id } = useParams();
  const [s, setS] = useState<any>(null);
  useEffect(() => { if (id) teaching.strategy(id).then(setS).catch(() => {}); }, [id]);
  if (!s) return <div className="text-slate/30 font-sans text-sm p-8">加载中...</div>;

  return (
    <div className="space-y-8">
      <h2 className="font-serif text-3xl font-bold text-ink">教学策略</h2>

      <div className="bg-white/80 border border-ink/5 rounded-2xl p-6 space-y-5">
        <div className="flex items-center gap-3">
          <span className={`px-2.5 py-0.5 text-xs rounded-full font-medium font-sans ${
            s.strategy_label?.includes('R') ? 'bg-chalk/10 text-chalk' :
            s.strategy_label?.includes('M') ? 'bg-slate/10 text-slate' : 'bg-sage/10 text-sage'
          }`}>{s.strategy_label}</span>
          <span className="text-sm text-slate/50 font-sans">维度比 {s.dimension_ratio?.toFixed(2)}</span>
        </div>

        <p className="text-sm text-ink/70 leading-relaxed font-sans">{s.description}</p>

        {[
          ['讲授', s.lecture_ratio, 'bg-rose-500', '知识传授为主'],
          ['练习', s.practice_ratio, 'bg-sage', '自主解题巩固'],
          ['讨论', s.discussion_ratio, 'bg-amber', '师生互动引导反思'],
        ].map(([l, r, c, d]) => (
          <div key={l as string}>
            <div className="flex justify-between text-sm mb-1.5 font-sans">
              <span className="text-ink/80 font-medium">{l}</span>
              <span className="text-slate/50">{Math.round((r as number) * 100)}%</span>
            </div>
            <div className="h-3 bg-cream/80 rounded-full overflow-hidden">
              <div className={`h-full rounded-full transition-all duration-700 ${c}`} style={{ width: `${Math.round((r as number) * 100)}%` }} />
            </div>
            <p className="text-[11px] text-slate/40 mt-1 font-sans">{d}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

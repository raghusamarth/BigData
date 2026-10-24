import { useEffect, useState } from 'react';

export function Masthead({ edition }) {
  const today = new Date().toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
  return (
    <header className="border-b-4 border-ink">
      <div className="flex justify-between items-center px-4 py-1 border-b border-ink font-mono text-xs uppercase tracking-widest">
        <span>Vol. 2 — BDA Edition</span>
        <span className="hidden md:inline">{today} — New York Edition</span>
        <span>{edition || 'Late Market Final'}</span>
      </div>
      <div className="text-center px-4 py-6 newsprint-texture">
        <p className="font-mono text-xs uppercase tracking-[0.3em] text-editorial">★ Breaking Data Edition ★</p>
        <h1 className="font-serif font-black text-5xl sm:text-6xl lg:text-8xl leading-[0.9] tracking-tighter">
          The Market Record
        </h1>
        <p className="font-body italic text-sm mt-2">All the data that's fit to print — MongoDB · PySpark · FastAPI</p>
      </div>
      <nav aria-label="Sections" className="flex flex-wrap justify-center border-t border-ink font-sans text-xs uppercase tracking-widest">
        {['Market', 'Explorer', 'Analytics', 'Pipeline', 'Trading', 'Manager'].map((s, i) => (
          <a key={s} href={`#${s.toLowerCase()}`} className="px-4 py-3 min-h-[44px] flex items-center hover:text-editorial hover:underline decoration-2 decoration-editorial underline-offset-4 border-r border-ink last:border-r-0 grid-border-r">
            {String(i + 1).padStart(2, '0')} · {s}
          </a>
        ))}
      </nav>
    </header>
  );
}

export function Ticker({ items }) {
  const [data, setData] = useState(items || []);
  useEffect(() => { if (items) setData(items); }, [items]);
  const row = data.length ? data : [{ symbol: 'AWAITING DATA', pct_return: 0 }];
  const doubled = [...row, ...row];
  return (
    <div className="bg-ink text-paper overflow-hidden border-b border-ink" role="marquee" aria-label="Market ticker">
      <div className="ticker-track flex whitespace-nowrap py-2 font-mono text-xs">
        {doubled.map((t, i) => (
          <span key={i} className="mx-6">
            <span className="bg-editorial px-1 mr-2">●</span>
            {t.symbol} {Number(t.pct_return ?? t.coef_var ?? 0).toFixed(2)}%
          </span>
        ))}
      </div>
    </div>
  );
}

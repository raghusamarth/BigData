import { useState } from 'react';
import { Search, LineChart } from 'lucide-react';
import { api } from '../api';
import { SectionLabel, Meta, Card, Btn, DbOps } from './ui';

export function StockExplorer() {
  const [sym, setSym] = useState('RELIANCE.NS');
  const [rows, setRows] = useState([]);
  const [msg, setMsg] = useState('');
  const [hov, setHov] = useState(null);
  const load = async () => {
    setMsg('Fetching…');
    try {
      const r = await api.history(sym.trim() || 'RELIANCE.NS', 500);
      const d = r.data || [];
      setRows(d);
      setMsg(d.length ? `${d.length} bars · ${(r.symbol || sym)}` : 'No rows — ingest first.');
    } catch (e) { setMsg(String(e.message)); }
  };
  const closes = rows.map((r) => Number(r.close)).filter(Boolean);
  const min = Math.min(...closes, 0), max = Math.max(...closes, 1);
  const W = 600, H = 220, PAD = 10;
  const px = (i) => PAD + (i / Math.max(closes.length - 1, 1)) * (W - PAD * 2);
  const py = (c) => (H - PAD) - ((c - min) / ((max - min) || 1)) * (H - PAD * 2);
  const onMove = (e) => {
    if (closes.length < 2) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const fx = ((e.clientX - rect.left) / rect.width) * W;
    const i = Math.round(((fx - PAD) / (W - PAD * 2)) * (closes.length - 1));
    const ci = Math.max(0, Math.min(closes.length - 1, i));
    setHov({ i: ci, x: px(ci), y: py(closes[ci]) });
  };
  const hovDate = hov ? String(rows[hov.i]?.timestamp || '').slice(0, 10) : '';
  return (
    <section id="explorer" className="max-w-screen-xl mx-auto px-4 py-16 border-t-4 border-ink">
      <SectionLabel no="2" title="Stock Explorer" />
      <Meta>Fig. 2.1 — Time-series reads · indexed on (symbol, timestamp)</Meta>
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 mt-4">
        <div className="lg:col-span-4">
          <Card>
            <label className="font-mono text-xs uppercase tracking-widest" htmlFor="sym">Symbol</label>
            <input id="sym" value={sym} onChange={(e) => setSym(e.target.value.toUpperCase())}
              className="sharp-corners w-full border-b-2 border-ink bg-transparent px-3 py-2 font-mono text-sm focus-visible:bg-[#F0F0F0] focus-visible:outline-none mt-2" />
            <div className="mt-4 flex gap-2">
              <Btn onClick={load}><span className="inline-flex items-center gap-2"><Search className="h-4 w-4" /> Load</span></Btn>
              <Btn variant="secondary" onClick={() => { setSym('AAPL'); }}>AAPL</Btn>
            </div>
            <p className="font-mono text-xs mt-3">{msg}</p>
          </Card>
        </div>
        <div className="lg:col-span-8">
          <Card>
            <h3 className="font-serif font-bold text-2xl flex items-center gap-2"><LineChart strokeWidth={1.5} /> Closing Price</h3>
            <DbOps>historical_prices.find({'{symbol}'}).sort({'{timestamp: 1}'}) — (symbol, timestamp) index</DbOps>
            {closes.length > 1 ? (
              <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-56 mt-2 border border-ink cursor-crosshair" role="img" aria-label={`${sym} price chart`}
                onMouseMove={onMove} onMouseLeave={() => setHov(null)}>
                <polyline fill="none" stroke="#111111" strokeWidth="2"
                  points={closes.map((c, i) => `${px(i)},${py(c)}`).join(' ')} />
                {hov && (
                  <g className="font-mono" fontSize="11">
                    <line x1={hov.x} y1={0} x2={hov.x} y2={H} stroke="#CC0000" strokeWidth="1" strokeDasharray="3 2" />
                    <circle cx={hov.x} cy={hov.y} r="4" fill="#CC0000" stroke="#F9F9F7" strokeWidth="1.5" />
                    <rect x={hov.x > W - 170 ? hov.x - 160 : hov.x + 10} y={8} width="150" height="38"
                      fill="#F9F9F7" stroke="#111111" strokeWidth="1.5" />
                    <text x={hov.x > W - 170 ? hov.x - 152 : hov.x + 18} y={24} fill="#111111">{hovDate}</text>
                    <text x={hov.x > W - 170 ? hov.x - 152 : hov.x + 18} y={39} fill="#111111" fontWeight="bold">₹/$ {closes[hov.i].toFixed(2)}</text>
                  </g>
                )}
              </svg>
            ) : <div className="h-56 mt-2 border border-ink bg-[radial-gradient(#000_1px,transparent_1px)] opacity-10 [background-size:16px_16px]" />}
            <div className="grid grid-cols-3 font-mono text-xs mt-2 border-t border-ink pt-2">
              <span>MIN {min.toFixed(2)}</span><span className="text-center">BARS {closes.length}</span><span className="text-right">MAX {max.toFixed(2)}</span>
            </div>
          </Card>
        </div>
      </div>
    </section>
  );
}

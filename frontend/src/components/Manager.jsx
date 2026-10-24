import { useEffect, useState } from 'react';
import { Users, LibraryBig, PenLine, Columns3 } from 'lucide-react';
import { api } from '../api';
import { SectionLabel, Meta, Card, Btn, DbOps } from './ui';

const inputCls = 'sharp-corners w-full border-b-2 border-ink bg-transparent px-3 py-2 font-mono text-sm focus-visible:bg-[#F0F0F0] focus-visible:outline-none';
const FIELDABLE = ['stocks_meta', 'users', 'company_fundamentals', 'historical_prices', 'technical_indicators'];
const CORE_ORDER = { stocks_meta: ['symbol', 'sector', 'exchange'], users: ['username', 'balance', 'holdings'] };

function fmtCell(v) {
  if (v === null || v === undefined) return '—';
  if (Array.isArray(v)) return v.map((h) => (h && typeof h === 'object' ? `${h.symbol}×${h.quantity}` : String(h))).join(', ') || '—';
  if (typeof v === 'object') return JSON.stringify(v);
  return String(v);
}

export function Manager() {
  const [users, setUsers] = useState([]);
  const [stocks, setStocks] = useState([]);
  const [schemas, setSchemas] = useState({});
  const [msg, setMsg] = useState('');
  const [purge, setPurge] = useState(true);
  const [nsym, setNsym] = useState('');
  const [nsec, setNsec] = useState('');
  const [nexc, setNexc] = useState('');
  const [bar, setBar] = useState({ symbol: '', timestamp: new Date().toISOString().slice(0, 10), open: '', high: '', low: '', close: '', volume: '', interval: '1d' });
  const [fcoll, setFcoll] = useState('stocks_meta');
  const [fname, setFname] = useState('');
  const [ftype, setFtype] = useState('str');
  const [fdef, setFdef] = useState('');
  const [fbackfill, setFbackfill] = useState(true);

  const loadSchema = async (coll) => {
    try {
      const s = await api.mgmtSchema(coll);
      setSchemas((m) => ({ ...m, [coll]: s.fields || [] }));
      return s;
    } catch (e) { setMsg(String(e.message)); return null; }
  };
  const load = async () => {
    try {
      setUsers(await api.mgmtUsers());
      setStocks(await api.mgmtStocks());
      await Promise.all([loadSchema('stocks_meta'), loadSchema('users')]);
    } catch (e) { setMsg(String(e.message)); }
  };
  useEffect(() => { load(); }, []);

  const customOf = (coll) => (schemas[coll] || []).filter((f) => !f.core).map((f) => f.name);
  const stockCols = [...CORE_ORDER.stocks_meta, ...customOf('stocks_meta')];
  const userCustom = customOf('users');
  const fCustom = customOf(fcoll);

  const rmUser = async (u) => {
    if (!window.confirm(`Remove user "${u.username}" and their transactions?`)) return;
    try { const r = await api.mgmtDeleteUser(u.user_id); setMsg(JSON.stringify(r)); load(); }
    catch (e) { setMsg(String(e.message)); }
  };
  const addStock = async () => {
    if (!nsym.trim()) { setMsg('Type a symbol first.'); return; }
    try { const r = await api.mgmtAddStock(nsym.trim(), nsec.trim() || 'Unknown', nexc.trim() || 'Unknown'); setMsg(JSON.stringify(r)); setNsym(''); setNsec(''); setNexc(''); load(); }
    catch (e) { setMsg(String(e.message)); }
  };
  const rmStock = async (s) => {
    if (!window.confirm(`Remove "${s}"${purge ? ' WITH all its price + indicator history' : ' (registry entry only)'}?`)) return;
    try { const r = await api.mgmtDeleteStock(s, purge); setMsg(JSON.stringify(r)); load(); }
    catch (e) { setMsg(String(e.message)); }
  };
  const setB = (k, v) => setBar((b) => ({ ...b, [k]: v }));
  const addBar = async () => {
    const payload = { ...bar, symbol: bar.symbol.trim(), open: Number(bar.open), high: Number(bar.high), low: Number(bar.low), close: Number(bar.close), volume: Number(bar.volume) };
    if (!payload.symbol || !payload.timestamp || [payload.open, payload.high, payload.low, payload.close, payload.volume].some((v) => Number.isNaN(v))) {
      setMsg('Fill every bar field with numbers (date as YYYY-MM-DD).'); return;
    }
    try { const r = await api.mgmtAddBar(payload); setMsg(JSON.stringify(r)); }
    catch (e) { setMsg(String(e.message)); }
  };
  const addField = async () => {
    if (!fname.trim()) { setMsg('Type a field name first.'); return; }
    try {
      const r = await api.mgmtAddField(fcoll, fname.trim(), ftype, fdef, fbackfill);
      setMsg(JSON.stringify(r)); setFname(''); setFdef(''); load(); loadSchema(fcoll);
    } catch (e) { setMsg(String(e.message)); }
  };
  const dropField = async (name) => {
    if (!window.confirm(`Drop column "${name}" from every doc in ${fcoll}?`)) return;
    try { const r = await api.mgmtDropField(fcoll, name); setMsg(JSON.stringify(r)); load(); loadSchema(fcoll); }
    catch (e) { setMsg(String(e.message)); }
  };

  return (
    <section id="manager" className="max-w-screen-xl mx-auto px-4 lg:px-8 py-16 border-t-4 border-ink">
      <SectionLabel no="6" title="Manager Mode" />
      <Meta>Fig. 6.1 — Registry control · users, stocks, manual entry & custom columns</Meta>
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 mt-4">
        <div className="lg:col-span-5">
          <Card>
            <h3 className="font-serif font-bold text-2xl flex items-center gap-2"><Users strokeWidth={1.5} /> Users</h3>
            <DbOps>users.find() · deleteOne + transactions.deleteMany</DbOps>
            <div className="mt-3 border-t border-l border-ink font-mono text-xs">
              {users.length ? users.map((u) => (
                <div key={u.user_id} className="border-r border-b border-ink px-2 py-2 flex items-center justify-between gap-2">
                  <span className="truncate" title={u.username}>{u.username} <span className="text-neutral-500">· ₹{Number(u.balance ?? 0).toFixed(0)} · {(u.holdings || []).length} holdings{userCustom.map((c) => ` · ${c}: ${fmtCell(u[c])}`).join('')}</span></span>
                  <button onClick={() => rmUser(u)} aria-label={`Remove ${u.username}`}
                    className="sharp-corners shrink-0 border border-ink px-2 py-1 min-h-[36px] uppercase tracking-widest hover:bg-editorial hover:text-white hover:border-editorial transition-all duration-200">Remove</button>
                </div>
              )) : <p className="border-r border-b border-ink px-2 py-2">No users yet — register one at the Trading Desk.</p>}
            </div>
            <div className="mt-4"><Btn variant="secondary" onClick={load}>Refresh</Btn></div>
          </Card>
        </div>
        <div className="lg:col-span-7">
          <Card>
            <h3 className="font-serif font-bold text-2xl flex items-center gap-2"><LibraryBig strokeWidth={1.5} /> Stock Registry</h3>
            <DbOps>stocks_meta.update(upsert) · deleteOne + optional history purge · columns follow live schema</DbOps>
            <div className="grid grid-cols-3 gap-4 mt-3">
              <input aria-label="New symbol" value={nsym} onChange={(e) => setNsym(e.target.value.toUpperCase())} placeholder="SYMBOL" className={inputCls} />
              <input aria-label="Sector" value={nsec} onChange={(e) => setNsec(e.target.value)} placeholder="Sector" className={inputCls} />
              <input aria-label="Exchange" value={nexc} onChange={(e) => setNexc(e.target.value)} placeholder="Exchange" className={inputCls} />
            </div>
            <div className="flex gap-2 mt-4">
              <Btn onClick={addStock}>Add stock</Btn>
              <label className="font-mono text-xs uppercase tracking-widest flex items-center gap-2 border border-ink px-3 min-h-[44px]">
                <input type="checkbox" checked={purge} onChange={(e) => setPurge(e.target.checked)} className="accent-[#CC0000] w-4 h-4" /> Purge history on remove
              </label>
            </div>
            <div className="mt-4 overflow-auto max-h-72">
              <table className="w-full font-mono text-xs border-t border-l border-ink">
                <thead><tr className="bg-ink text-paper">{stockCols.map((c) => <th key={c} className="text-left px-2 py-2 uppercase tracking-widest whitespace-nowrap">{c}</th>)}<th className="px-2 py-2" /></tr></thead>
                <tbody>{stocks.length ? stocks.map((s) => (
                  <tr key={s.symbol} className="border-b border-ink hover:bg-neutral-100">
                    {stockCols.map((c) => <td key={c} className="border-r border-ink px-2 py-1 max-w-[160px] truncate" title={fmtCell(s[c])}>{fmtCell(s[c])}</td>)}
                    <td className="px-2 py-1"><button onClick={() => rmStock(s.symbol)} aria-label={`Remove ${s.symbol}`}
                      className="sharp-corners border border-ink px-2 py-1 min-h-[36px] uppercase tracking-widest hover:bg-editorial hover:text-white hover:border-editorial transition-all duration-200">Remove</button></td>
                  </tr>
                )) : <tr><td className="px-2 py-2">Registry empty.</td></tr>}</tbody>
              </table>
            </div>
          </Card>
        </div>
      </div>
      <Card className="mt-8">
        <h3 className="font-serif font-bold text-2xl flex items-center gap-2"><Columns3 strokeWidth={1.5} /> Custom Columns</h3>
        <DbOps>GET /admin/schema ($sample) · POST /admin/fields ($set backfill) · DELETE ($unset) — refresh re-reads the schema</DbOps>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mt-3">
          <select aria-label="Collection" value={fcoll} onChange={(e) => { setFcoll(e.target.value); loadSchema(e.target.value); }} className={`${inputCls} bg-paper`}>
            {FIELDABLE.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
          <input aria-label="Field name" value={fname} onChange={(e) => setFname(e.target.value)} placeholder="field_name" className={inputCls} />
          <select aria-label="Field type" value={ftype} onChange={(e) => setFtype(e.target.value)} className={`${inputCls} bg-paper`}>
            <option value="str">text</option><option value="float">decimal</option><option value="int">integer</option><option value="bool">true/false</option>
          </select>
          <input aria-label="Default value" value={fdef} onChange={(e) => setFdef(e.target.value)} placeholder="Default" className={inputCls} />
          <label className="font-mono text-xs uppercase tracking-widest flex items-center gap-2 border border-ink px-3 min-h-[44px]">
            <input type="checkbox" checked={fbackfill} onChange={(e) => setFbackfill(e.target.checked)} className="accent-[#CC0000] w-4 h-4" /> Backfill
          </label>
        </div>
        <div className="flex gap-2 mt-4 items-center flex-wrap">
          <Btn variant="breaking" onClick={addField}>Add column</Btn>
          <p className="font-mono text-[11px] text-neutral-500">Backfill on 500K+ docs can take a minute — safe to refresh while it runs. Core fields are protected.</p>
        </div>
        <div className="mt-4 border-t border-l border-ink font-mono text-xs">
          <div className="border-r border-b border-ink px-2 py-2 bg-neutral-100 uppercase tracking-widest">{fcoll} — {fCustom.length} custom column{fCustom.length === 1 ? '' : 's'}</div>
          {fCustom.length ? fCustom.map((name) => (
            <div key={name} className="border-r border-b border-ink px-2 py-2 flex items-center justify-between gap-2">
              <span>{name} <span className="text-neutral-500">· {(schemas[fcoll] || []).find((f) => f.name === name)?.types.join('/')}</span></span>
              <button onClick={() => dropField(name)} aria-label={`Drop ${name}`}
                className="sharp-corners shrink-0 border border-ink px-2 py-1 min-h-[36px] uppercase tracking-widest hover:bg-editorial hover:text-white hover:border-editorial transition-all duration-200">Drop</button>
            </div>
          )) : <p className="border-r border-b border-ink px-2 py-2">No custom columns — add one above.</p>}
        </div>
      </Card>
      <Card className="mt-8">
        <h3 className="font-serif font-bold text-2xl flex items-center gap-2"><PenLine strokeWidth={1.5} /> Manual Price Entry</h3>
        <DbOps>historical_prices.insertOne — validated inside [low, high], tagged source: manual-entry</DbOps>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-3">
          <input aria-label="Bar symbol" value={bar.symbol} onChange={(e) => setB('symbol', e.target.value.toUpperCase())} placeholder="SYMBOL" className={inputCls} />
          <input aria-label="Bar date" value={bar.timestamp} onChange={(e) => setB('timestamp', e.target.value)} placeholder="YYYY-MM-DD" className={inputCls} />
          <select aria-label="Interval" value={bar.interval} onChange={(e) => setB('interval', e.target.value)} className={`${inputCls} bg-paper`}>
            <option value="1d">Daily · 1d</option>
            <option value="1h">Hourly · 1h</option>
          </select>
          <input aria-label="Volume" type="number" min="0" value={bar.volume} onChange={(e) => setB('volume', e.target.value)} placeholder="Volume" className={inputCls} />
          <input aria-label="Open" type="number" step="any" value={bar.open} onChange={(e) => setB('open', e.target.value)} placeholder="Open" className={inputCls} />
          <input aria-label="High" type="number" step="any" value={bar.high} onChange={(e) => setB('high', e.target.value)} placeholder="High" className={inputCls} />
          <input aria-label="Low" type="number" step="any" value={bar.low} onChange={(e) => setB('low', e.target.value)} placeholder="Low" className={inputCls} />
          <input aria-label="Close" type="number" step="any" value={bar.close} onChange={(e) => setB('close', e.target.value)} placeholder="Close" className={inputCls} />
        </div>
        <div className="mt-4"><Btn variant="breaking" onClick={addBar}>Record bar</Btn></div>
        {msg && <pre className="font-mono text-xs bg-neutral-100 border border-ink p-3 mt-3 overflow-auto max-h-32 whitespace-pre-wrap">{msg}</pre>}
      </Card>
    </section>
  );
}

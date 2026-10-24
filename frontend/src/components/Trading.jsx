import { useState } from 'react';
import { Wallet } from 'lucide-react';
import { api } from '../api';
import { SectionLabel, Meta, Card, Btn } from './ui';

export function Trading() {
  const [user, setUser] = useState('');
  const [uid, setUid] = useState('');
  const [pw, setPw] = useState('demo123');
  const [folio, setFolio] = useState(null);
  const [sym, setSym] = useState('AAPL');
  const [qty, setQty] = useState(1);
  const [msg, setMsg] = useState('');
  const act = async (fn) => { try { setMsg(JSON.stringify(await fn(), null, 2)); if (uid) setFolio(await api.portfolio(uid)); } catch (e) { setMsg(String(e.message)); } };
  const needName = () => { if (!user.trim()) { setMsg('Type a username first.'); return false; } return true; };
  return (
    <section id="trading" className="max-w-screen-xl mx-auto px-4 py-16 border-t-4 border-ink">
      <SectionLabel no="5" title="Trading Desk" />
      <Meta>Fig. 5.1 — Paper-trading desk · virtual $10,000 portfolio</Meta>
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 mt-4">
        <div className="lg:col-span-5">
          <Card hover>
            <h3 className="font-serif font-bold text-2xl">Account</h3>
            <input aria-label="Username" value={user} onChange={(e) => setUser(e.target.value)} placeholder="username"
              className="sharp-corners w-full border-b-2 border-ink bg-transparent px-3 py-2 font-mono text-sm mt-3 focus-visible:bg-[#F0F0F0] focus-visible:outline-none" />
            <input aria-label="Password" type="password" value={pw} onChange={(e) => setPw(e.target.value)}
              className="sharp-corners w-full border-b-2 border-ink bg-transparent px-3 py-2 font-mono text-sm mt-2 focus-visible:bg-[#F0F0F0] focus-visible:outline-none" />
            <div className="flex gap-2 mt-4">
              <Btn variant="secondary" onClick={() => needName() && act(() => api.register(user.trim(), pw))}>Register</Btn>
              <Btn onClick={() => needName() && act(async () => { const r = await api.login(user.trim(), pw); setUid(r.user_id); return r; })}>Login</Btn>
            </div>
            <p className="font-mono text-xs mt-2 break-all">user_id: {uid || '—'}</p>
          </Card>
        </div>
        <div className="lg:col-span-7">
          <Card>
            <h3 className="font-serif font-bold text-2xl flex items-center gap-2"><Wallet strokeWidth={1.5} /> Order Ticket</h3>
            <div className="grid grid-cols-2 gap-4 mt-3">
              <input aria-label="Order symbol" value={sym} onChange={(e) => setSym(e.target.value.toUpperCase())}
                className="sharp-corners border-b-2 border-ink bg-transparent px-3 py-2 font-mono text-sm focus-visible:bg-[#F0F0F0] focus-visible:outline-none" />
              <input aria-label="Quantity" type="number" min="1" value={qty} onChange={(e) => setQty(Number(e.target.value))}
                className="sharp-corners border-b-2 border-ink bg-transparent px-3 py-2 font-mono text-sm focus-visible:bg-[#F0F0F0] focus-visible:outline-none" />
            </div>
            <div className="flex gap-2 mt-4">
              <Btn variant="breaking" onClick={() => act(() => api.buy(uid, sym, qty))}>Buy</Btn>
              <Btn variant="secondary" onClick={() => act(() => api.sell(uid, sym, qty))}>Sell</Btn>
              <Btn variant="secondary" onClick={() => act(() => api.portfolio(uid))}>Folio</Btn>
            </div>
            {folio && <p className="font-mono text-xs mt-3">Balance {Number(folio.balance).toFixed(2)} · Holdings {(folio.holdings || []).map((h) => `${h.symbol}×${h.quantity}`).join(', ') || '—'}</p>}
            {msg && <pre className="font-mono text-xs bg-neutral-100 border border-ink p-3 mt-3 overflow-auto max-h-40">{msg}</pre>}
          </Card>
        </div>
      </div>
    </section>
  );
}

export function Footer() {
  return (
    <footer className="border-t-4 border-ink mt-8">
      <div className="max-w-screen-xl mx-auto px-4 py-8 grid grid-cols-1 md:grid-cols-12 gap-8">
        <div className="md:col-span-8">
          <p className="font-serif font-black text-3xl">The Market Record</p>
          <p className="font-body text-sm mt-2 text-justify">A college Big Data Analytics demonstration: real OHLCV history in MongoDB time-series collections, in-database aggregations, one distributed Spark workload, served by FastAPI and set in Newsprint.</p>
        </div>
        <div className="md:col-span-4 font-mono text-xs uppercase tracking-widest space-y-1">
          <p>Edition: Vol 2.0 — Printed in Docker</p>
          <p>API: /docs · Health: /</p>
          <p className="text-neutral-500">✦ ✦ ✦</p>
        </div>
      </div>
    </footer>
  );
}

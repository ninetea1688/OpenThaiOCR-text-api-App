import { StrictMode, useEffect, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { ArrowRight, ArrowCounterClockwise, Check, Copy, DownloadSimple, FileText, Files, ShieldCheck, UploadSimple, CircleNotch } from '@phosphor-icons/react';
import './style.css';

type Info = { model_state: string; model_error: string | null; max_file_mb: number; max_pages: number };
type Page = { page: number; text: string; error: string | null; lines: { confidence: number }[] };
type Result = { pages: Page[]; page_count: number; total_pages: number; elapsed_ms: number };
const accepted = '.pdf,.png,.jpg,.jpeg,.webp,.tif,.tiff,.bmp';

function App() {
  const [info, setInfo] = useState<Info | null>(null);
  const [online, setOnline] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [url, setUrl] = useState('');
  const [start, setStart] = useState('1');
  const [count, setCount] = useState('');
  const [result, setResult] = useState<Result | null>(null);
  const [texts, setTexts] = useState<Record<number, string>>({});
  const [selected, setSelected] = useState(0);
  const [busy, setBusy] = useState(false);
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const input = useRef<HTMLInputElement>(null);
  const request = useRef<AbortController | null>(null);

  useEffect(() => {
    let active = true;
    const controller = new AbortController();
    async function poll() {
      try {
        const response = await fetch('/v1/info', { signal: controller.signal });
        if (!response.ok) throw new Error();
        const data: Info = await response.json();
        if (active) { setInfo(data); setOnline(true); }
      } catch { if (active) setOnline(false); }
    }
    void poll();
    const timer = window.setInterval(poll, 4000);
    return () => { active = false; controller.abort(); clearInterval(timer); request.current?.abort(); };
  }, []);
  useEffect(() => {
    if (!file) { setUrl(''); return; }
    const next = URL.createObjectURL(file);
    setUrl(next);
    return () => URL.revokeObjectURL(next);
  }, [file]);
  useEffect(() => { if (notice) { const timer = setTimeout(() => setNotice(''), 3000); return () => clearTimeout(timer); } }, [notice]);

  const maxMb = info?.max_file_mb ?? 50;
  const maxPages = info?.max_pages ?? 100;
  const page = result?.pages.find(p => p.page === selected);
  const text = selected === 0 ? (result?.pages.filter(p => !p.error).map(p => texts[p.page] ?? '').join('\n\n') ?? '') : (texts[selected] ?? '');
  const ready = online && info?.model_state === 'ready';
  const status = !online ? 'เชื่อมต่อ API ไม่ได้' : ready ? 'พร้อมใช้งาน' : info?.model_state === 'error' ? 'โหลดโมเดลไม่สำเร็จ' : 'กำลังเตรียมโมเดล';

  function choose(next: File | undefined) {
    if (!next || busy) return;
    setError(''); setNotice('');
    if (!/\.(pdf|png|jpe?g|webp|tiff?|bmp)$/i.test(next.name)) { setError('กรุณาเลือกไฟล์ PDF, PNG, JPEG, WebP, TIFF หรือ BMP'); return; }
    if (next.size === 0 || next.size > maxMb * 1024 * 1024) { setError(`ไฟล์ต้องมีขนาดมากกว่า 0 และไม่เกิน ${maxMb} MB`); return; }
    setFile(next); setResult(null); setTexts({}); setSelected(0);
  }
  async function run() {
    if (!file || busy) return;
    if (!Number.isInteger(Number(start)) || Number(start) < 1 || (count !== '' && (!Number.isInteger(Number(count)) || Number(count) < 1 || Number(count) > maxPages))) {
      setError(`ระบุหน้าเริ่มต้นตั้งแต่ 1 และจำนวนหน้าระหว่าง 1–${maxPages}`); return;
    }
    setBusy(true); setError(''); setResult(null); setTexts({}); setSelected(0);
    const controller = new AbortController(); request.current = controller;
    const data = new FormData(); data.append('file', file); data.append('start_page', start);
    if (count !== '') data.append('max_pages', count);
    try {
      const response = await fetch('/v1/ocr', { method: 'POST', body: data, signal: controller.signal });
      if (!response.ok) {
        const body = await response.json().catch(() => null);
        throw new Error(typeof body?.detail === 'string' ? body.detail : `ไม่สามารถอ่านเอกสารได้ (HTTP ${response.status})`);
      }
      const output: Result = await response.json();
      setResult(output); setTexts(Object.fromEntries(output.pages.map(p => [p.page, p.text])));
    } catch (err) { setError(err instanceof DOMException && err.name === 'AbortError' ? 'ยกเลิกการรอผลแล้ว' : err instanceof Error ? err.message : 'เชื่อมต่อ API ไม่สำเร็จ'); }
    finally { setBusy(false); request.current = null; }
  }
  function download() {
    const objectUrl = URL.createObjectURL(new Blob(['\ufeff', text], { type: 'text/plain;charset=utf-8' }));
    const a = document.createElement('a'); a.href = objectUrl; a.download = `${file?.name.replace(/\.[^.]+$/, '') || 'ocr'}${selected ? `-page-${selected}` : ''}.txt`; a.click();
    setTimeout(() => URL.revokeObjectURL(objectUrl), 1000);
  }
  function reset() { setFile(null); setResult(null); setTexts({}); setSelected(0); setError(''); setStart('1'); setCount(''); if (input.current) input.current.value = ''; }
  const isPdf = file?.name.toLowerCase().endsWith('.pdf');
  const isTiff = /\.tiff?$/i.test(file?.name ?? '');

  return <div className="app">
    <header className="topbar"><a className="brand" href="/"><span className="brand-icon"><Files size={25} weight="duotone"/></span><span>OCR <strong>Workspace</strong></span></a><div className={`status ${ready ? 'ready' : 'waiting'}`} role="status"><span/>{status}</div></header>
    <main>
      <div className="intro"><div><p className="eyebrow">เครื่องมืออ่านข้อความจากเอกสาร</p><h1>เปลี่ยนเอกสาร ให้เป็นข้อความ</h1><p className="subtitle">อัปโหลด ตรวจทาน แล้วนำข้อความภาษาไทยและอังกฤษไปใช้ต่อ</p></div><span className="privacy"><ShieldCheck size={20}/> ประมวลผลบนเซิร์ฟเวอร์ของคุณ</span></div>
      <section className="controls" aria-label="อัปโหลดและตั้งค่าการอ่าน">
        <input ref={input} className="sr-only" type="file" accept={accepted} disabled={busy} aria-label="เลือกไฟล์เอกสาร" onChange={e => { choose(e.target.files?.[0]); e.target.value = ''; }}/>
        <button className={`upload ${dragging ? 'dragging' : ''}`} disabled={busy} onClick={() => input.current?.click()} onDragOver={e => { e.preventDefault(); setDragging(true); }} onDragLeave={() => setDragging(false)} onDrop={e => { e.preventDefault(); setDragging(false); if (e.dataTransfer.files.length > 1) setError('กรุณาเลือกครั้งละหนึ่งไฟล์'); else choose(e.dataTransfer.files[0]); }}>
          <span className="upload-icon">{file ? <FileText size={25}/> : <UploadSimple size={25}/>}</span><span className="file-label"><strong>{file?.name ?? 'เลือกไฟล์ หรือลากมาวางที่นี่'}</strong><small>{file ? `${(file.size / 1024 / 1024).toFixed(2)} MB · คลิกเพื่อเปลี่ยนไฟล์` : `PDF และรูปภาพ · ไม่เกิน ${maxMb} MB`}</small></span>
        </button>
        <div className="options"><label>เริ่มที่หน้า<input type="number" min="1" step="1" value={start} disabled={busy} onChange={e => setStart(e.target.value)}/></label><label>จำนวนหน้า<input type="number" min="1" max={maxPages} step="1" placeholder={`สูงสุด ${maxPages}`} value={count} disabled={busy} onChange={e => setCount(e.target.value)}/></label></div>
        <button className="primary" onClick={() => void run()} disabled={!file || !ready || busy}>{busy ? <CircleNotch className="spin" size={20}/> : <ArrowRight size={20}/>} {busy ? 'กำลังอ่านข้อความ…' : 'เริ่มอ่านข้อความ'}</button>
      </section>
      {(!online || info?.model_state === 'error') && <p className="alert" role="alert">{!online ? 'ไม่สามารถติดต่อ API ได้ กรุณาตรวจสอบว่าเซิร์ฟเวอร์เปิดอยู่' : `โมเดลไม่พร้อม: ${info?.model_error ?? 'ตรวจสอบบันทึกของเซิร์ฟเวอร์'}`}</p>}
      {error && <p className="alert" role="alert">{error}</p>}
      {busy && <div className="processing" role="status"><CircleNotch className="spin" size={18}/> กำลังอ่านเอกสาร กรุณารอผลครบตามช่วงหน้าที่เลือก<button onClick={() => request.current?.abort()}>ยกเลิกการรอ</button></div>}
      <div className="workspace">
        <section className="panel preview"><div className="panel-heading"><h2><FileText size={19}/> เอกสารต้นฉบับ</h2><button className="quiet" disabled={!file || busy} onClick={reset} aria-label="ล้างเอกสาร"><ArrowCounterClockwise size={18}/> ล้าง</button></div>
          <div className="preview-body">{!file ? <div className="empty"><span className="empty-art"><Files size={48} weight="thin"/></span><h3>เริ่มจากเอกสารของคุณ</h3><p>เลือก PDF หรือรูปภาพเพื่อดูตัวอย่างที่นี่</p><button className="secondary" onClick={() => input.current?.click()}>เลือกไฟล์เอกสาร</button></div> : isPdf ? <iframe key={`${url}-${selected}`} src={`${url}#page=${selected || Number(start) || 1}`} title="ตัวอย่างเอกสาร PDF"/> : isTiff ? <div className="empty"><FileText size={40}/><h3>เลือกไฟล์ TIFF แล้ว</h3><p>เบราว์เซอร์อาจแสดงตัวอย่าง TIFF ไม่ได้<br/>กดเริ่มอ่านข้อความเพื่ออ่านทุกหน้าที่เลือก</p></div> : <img src={url} alt={`ต้นฉบับ ${file.name}`}/>}</div>
          <div className="panel-footer">{file ? file.name : 'รองรับ PDF, PNG, JPEG, WebP, TIFF และ BMP'}</div>
        </section>
        <section className="panel output"><div className="panel-heading"><h2><FileText size={19}/> ข้อความที่อ่านได้</h2>{result && <span className="result-badge"><Check size={14}/> {result.page_count} หน้า</span>}</div>
          <div className="result-toolbar"><label className="sr-only" htmlFor="page">เลือกหน้าผลลัพธ์</label><select id="page" disabled={!result || busy} value={selected} onChange={e => setSelected(Number(e.target.value))}><option value={0}>ทุกหน้าที่อ่าน</option>{result?.pages.map(p => <option key={p.page} value={p.page}>หน้า {p.page}{p.error ? ' · อ่านไม่สำเร็จ' : ''}</option>)}</select><div className="actions"><button className="icon-button" disabled={!text} title="คัดลอกข้อความ" aria-label="คัดลอกข้อความ" onClick={async () => { try { await navigator.clipboard.writeText(text); setNotice('คัดลอกข้อความแล้ว'); } catch { setError('คัดลอกอัตโนมัติไม่ได้ กรุณาเลือกข้อความแล้วคัดลอก หรือดาวน์โหลดไฟล์'); } }}><Copy size={19}/></button><button className="icon-button" disabled={!text} title="ดาวน์โหลด TXT" aria-label="ดาวน์โหลด TXT" onClick={download}><DownloadSimple size={19}/></button></div></div>
          {result ? <>{result.pages.some(p => p.error) && <div className="page-warning" role="alert">อ่านไม่สำเร็จ: {result.pages.filter(p => p.error).map(p => `หน้า ${p.page} (${p.error})`).join(', ')} — ผลจากหน้าอื่นยังใช้งานได้</div>}{page?.error ? <div className="empty"><p>หน้านี้อ่านไม่สำเร็จ กรุณาลองใหม่หรือเลือกหน้าอื่น</p></div> : <textarea aria-label="ข้อความ OCR ที่แก้ไขได้" value={text} readOnly={selected === 0} placeholder="ไม่พบข้อความในหน้าที่เลือก" onChange={e => setTexts(prev => ({ ...prev, [selected]: e.target.value }))}/>}</> : <div className="empty"><span className="text-art">ก <span>A</span></span><h3>{busy ? 'กำลังเปลี่ยนภาพเป็นข้อความ' : 'ข้อความของคุณจะปรากฏที่นี่'}</h3><p>{busy ? 'เมื่ออ่านเสร็จ คุณสามารถตรวจทานและดาวน์โหลดได้' : 'อ่านเอกสาร แล้วเลือกแต่ละหน้าเพื่อแก้ไขข้อความ'}</p></div>}
          <div className="panel-footer"><span>{result ? `${result.page_count} / ${result.total_pages} หน้า · ${(result.elapsed_ms / 1000).toFixed(1)} วินาที` : 'ผลลัพธ์เป็นข้อความล้วน'} </span><span>{result ? selected ? 'แก้ไขข้อความหน้านี้ได้' : 'เลือกแต่ละหน้าเพื่อแก้ไข' : 'ภาษาไทย + English'}</span></div>
        </section>
      </div>
      <footer><span><ShieldCheck size={16}/> ไฟล์และผลลัพธ์ไม่ถูกบันทึกเป็นประวัติในแอป</span><a href="/docs" target="_blank" rel="noreferrer">เอกสาร API ↗</a></footer>
      {notice && <div className="toast" role="status"><Check size={18}/>{notice}</div>}
    </main>
  </div>;
}

createRoot(document.getElementById('root')!).render(<StrictMode><App/></StrictMode>);

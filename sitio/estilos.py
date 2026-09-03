# -*- coding: utf-8 -*-
"""Hoja de estilos compartida por la portada y las páginas de panel."""

CSS = """
.leygrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(19rem,1fr));
  gap:.5rem 1.4rem;margin:.2rem 0 1.6rem;font-size:.82rem}
.legq{color:var(--ink-2);line-height:1.7}
.legq b{color:var(--ink);font-variant-numeric:tabular-nums}
.legqt{color:var(--ink-3);margin-right:.4rem}
.chip{display:inline-block;white-space:nowrap;margin-right:.6rem}
.chip i{display:inline-block;width:9px;height:9px;border-radius:2px;
  margin-right:.28rem;vertical-align:0}
.panelgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(15rem,1fr));
  gap:.9rem;margin:1.4rem 0 1.6rem}
.panelcard{display:block;background:var(--panel);border:1px solid var(--line);
  border-radius:6px;padding:1.1rem 1.2rem;text-decoration:none;color:inherit;
  transition:border-color .15s,box-shadow .15s}
.panelcard:hover{border-color:var(--accent);box-shadow:0 1px 8px rgba(42,120,214,.10)}
.panelcard h3{margin:0 0 .3rem;font-size:1.15rem;color:var(--accent)}
.pc-meta{font-size:.82rem;color:var(--ink-3);margin:0 0 .6rem}
.pc-res{font-size:.92rem;margin:0 0 .4rem;color:var(--ink)}
.pc-pend{font-size:.85rem;color:var(--ink-2);margin:0}

:root{
  --surface:#fcfcfb; --panel:#ffffff; --line:#e5e3dd; --line-soft:#efedE8;
  --ink:#0b0b0b; --ink-2:#52514e; --ink-3:#84827c;
  --favor:{C_FAVOR}; --cond:{C_COND}; --contra:{C_CONTRA};
  --accent:#1c5cab;
  --serif:"Iowan Old Style","Palatino Linotype",Palatino,Georgia,serif;
  --sans:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--surface);color:var(--ink);font-family:var(--sans);
  font-size:16px;line-height:1.6;-webkit-font-smoothing:antialiased}
.wrap{max-width:60rem;margin:0 auto;padding:0 1.5rem}

header.top{border-bottom:1px solid var(--line);background:var(--panel);padding:3.5rem 0 2.5rem}
.kicker{font-size:.75rem;letter-spacing:.09em;text-transform:uppercase;color:var(--ink-3);margin:0 0 .9rem}
h1{font-family:var(--serif);font-size:2.6rem;line-height:1.15;margin:0 0 .8rem;font-weight:600;letter-spacing:-.01em}
.sub{font-size:1.12rem;color:var(--ink-2);max-width:46rem;margin:0 0 1.6rem}
.meta{display:flex;flex-wrap:wrap;gap:.5rem 1.5rem;font-size:.86rem;color:var(--ink-3);
  border-top:1px solid var(--line-soft);padding-top:1.1rem}
.meta b{color:var(--ink-2);font-weight:600}

nav.toc{position:sticky;top:0;z-index:10;background:var(--bg);
  backdrop-filter:saturate(180%) blur(8px);border-bottom:1px solid var(--line);
  font-size:.83rem;overflow-x:auto}
nav.toc ul{display:flex;gap:1.4rem;list-style:none;margin:0 auto;padding:.75rem 1.5rem;max-width:60rem;white-space:nowrap}
nav.toc a{color:var(--ink-2);text-decoration:none;padding-bottom:2px;border-bottom:2px solid transparent}
nav.toc a:hover{color:var(--accent);border-color:var(--accent)}

section{padding:3.2rem 0 .6rem;scroll-margin-top:3.4rem}
section+section{border-top:1px solid var(--line-soft)}
h2{font-family:var(--serif);font-size:1.75rem;margin:0 0 .4rem;font-weight:600;letter-spacing:-.005em}
h2 .sec-n{color:var(--ink-3);font-size:1rem;font-family:var(--sans);font-weight:500;margin-right:.6rem;
  letter-spacing:.04em}
.lead{font-size:1.04rem;color:var(--ink-2);max-width:46rem;margin:.2rem 0 1.8rem}
h3{font-size:1.02rem;margin:2.2rem 0 .5rem;font-weight:650}
p{margin:0 0 1rem;max-width:46rem}
.audience{display:inline-block;font-size:.72rem;letter-spacing:.06em;text-transform:uppercase;
  color:var(--accent);border:1px solid #cfe0f5;background:#f2f7fd;border-radius:99px;
  padding:.16rem .6rem;margin-bottom:.9rem;font-weight:600}

.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(13rem,1fr));gap:1px;
  background:var(--line);border:1px solid var(--line);border-radius:6px;overflow:hidden;margin:2rem 0}
.tile{background:var(--panel);padding:1.25rem 1.3rem}
.tile .v{font-family:var(--serif);font-size:2.1rem;line-height:1;font-weight:600;letter-spacing:-.02em}
.tile .k{font-size:.83rem;color:var(--ink-2);margin-top:.5rem;line-height:1.45}

table{width:100%;border-collapse:collapse;font-size:.88rem;margin:.6rem 0 1.2rem}
caption{text-align:left;font-size:.83rem;color:var(--ink-3);padding-bottom:.7rem;line-height:1.5}
th{text-align:left;font-weight:600;font-size:.74rem;letter-spacing:.05em;text-transform:uppercase;
  color:var(--ink-3);border-bottom:1px solid var(--line);padding:.5rem .55rem}
td{padding:.5rem .55rem;border-bottom:1px solid var(--line-soft);vertical-align:middle}
tbody tr:hover{background:#faf9f6}
.qid{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.78rem;color:var(--ink-3);white-space:nowrap}
.qtxt{color:var(--ink);min-width:15rem}
.opt{color:var(--ink-2)}
.n{text-align:right;color:var(--ink-3);font-variant-numeric:tabular-nums;white-space:nowrap;font-size:.82rem}
.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.num.sec{color:var(--ink-3);font-size:.82rem}
.antes{color:var(--ink-3);text-decoration:line-through;text-decoration-color:#d9d7d1}
.ahora{font-weight:600}

.cbar{width:15rem;min-width:11rem}
.bar{position:relative;height:22px;border-radius:3px;background:#f1efea;overflow:hidden}
.bar .seg{position:absolute;top:0;bottom:0;display:flex;align-items:center;justify-content:center;
  box-shadow:0 0 0 1px var(--panel) inset}
.bar .seg span{font-size:.7rem;font-weight:700;color:#fff;font-variant-numeric:tabular-nums}
.bar.empty{display:flex;align-items:center;padding-left:.5rem;font-size:.74rem;color:var(--ink-3)}
.bar .seg.gap{background:repeating-linear-gradient(135deg,#e6e2da 0 4px,#f1efea 4px 8px)}
.leyenda{display:flex;flex-wrap:wrap;gap:1.1rem;font-size:.82rem;color:var(--ink-2);margin:.2rem 0 1.3rem}


figure.fig{margin:1.2rem 0 1.6rem;padding:.6rem .4rem;background:var(--panel);
  border:1px solid var(--line);border-radius:5px}
figure.fig svg{display:block;width:100%;height:auto}
figure.fig figcaption{font-size:.84rem;color:var(--ink-3);padding:.5rem .8rem 0;max-width:44rem}
.netrow{margin:1.5rem 0 .5rem;padding-bottom:1.2rem;border-bottom:1px solid var(--line-soft)}
.netrow:last-of-type{border-bottom:0}
.nethead{display:flex;flex-wrap:wrap;align-items:baseline;gap:.5rem 1rem;margin-bottom:.5rem}
.nethead b{font-size:1rem}
.netn,.netser{font-size:.82rem;color:var(--ink-3)}
.netser{font-variant-numeric:tabular-nums}
.netrow svg{display:block;width:100%;height:auto}
.netlec{font-size:.9rem;color:var(--ink-2);margin:.7rem 0 0;max-width:44rem}
.leyenda i.edw,.leyenda i.eds{width:22px;height:0;border-radius:0;vertical-align:3px;
  border-top:1px solid #2a78d6;opacity:.45}
.leyenda i.eds{border-top-width:2.4px;opacity:.9}
.tcapas td.capa{font-weight:600;color:var(--ink);width:15rem;min-width:12rem}
.tcapas td.quien{white-space:nowrap;font-size:.86rem;color:var(--ink-2)}
.tcapas td.qtxt{max-width:26rem}
.est{display:inline-block;white-space:nowrap;font-size:.78rem;font-weight:650;
  padding:.16rem .55rem;border-radius:3px;border:1px solid}
.est.e-ok{background:#eef6ee;border-color:#cbe3cb;color:#2c6b34}
.est.e-wip{background:#fbf4e6;border-color:#ecdcb8;color:#7d5a15}
.est.e-block{background:#fdecec;border-color:#f6cccc;color:#a32c2c}
.est.e-todo{background:#f2f1ee;border-color:#e0ded8;color:#5f5d58}
.tile .de{font-size:1.1rem;color:var(--ink-3);font-weight:500}
.sub.tit{font-size:.95rem;background:#f5f7fa;border:1px solid var(--line);border-radius:4px;
  padding:.8rem 1rem;margin-top:1rem;color:var(--ink-2)}
.sub.tit i{color:var(--ink)}
td.n.alerta{color:#a32c2c;font-weight:700}
.nota{font-size:.9rem;color:var(--ink-2);border-left:2px solid var(--line);
  padding-left:.9rem;margin:.9rem 0 1rem}
.num sup, td sup{color:var(--accent);font-weight:700;cursor:help}
.leyenda i{display:inline-block;width:11px;height:11px;border-radius:2px;margin-right:.4rem;vertical-align:-1px}
.leyenda i.gapkey{background:repeating-linear-gradient(135deg,#e6e2da 0 3px,#f1efea 3px 6px);
  border:1px solid var(--line)}

.tag{display:inline-block;font-size:.73rem;font-weight:650;padding:.15rem .5rem;border-radius:3px;
  white-space:nowrap;border:1px solid}
.e-fuerte{background:#eaf3fc;border-color:#c2dbf6;color:#16508f}
.e-clara{background:#f2f7fd;border-color:#d8e7f8;color:#1c5cab}
.e-dom{background:#f6f5f2;border-color:#e2e0d9;color:#5a5852}
.e-sin{background:#fdeeee;border-color:#f7d4d3;color:#a8302f}
.e-insuf{background:#f6f5f2;border-color:#e2e0d9;color:#84827c;font-style:italic}

.callout{background:var(--panel);border:1px solid var(--line);border-left:3px solid var(--accent);
  border-radius:0 5px 5px 0;padding:1.15rem 1.3rem;margin:1.6rem 0;max-width:46rem}
.callout p:last-child{margin-bottom:0}
.callout .ct{font-weight:650;margin-bottom:.35rem;display:block}
.warn{border-left-color:#c8a415}

.dec{background:var(--panel);border:1px solid var(--line);border-radius:6px;
  padding:1.3rem 1.4rem;margin:0 0 1rem}
.dec h3{margin:0 0 .7rem;font-size:1.05rem;display:flex;align-items:baseline;gap:.65rem}
.numdec{display:inline-flex;align-items:center;justify-content:center;flex:0 0 auto;
  width:1.55rem;height:1.55rem;border-radius:50%;background:#f2f7fd;color:var(--accent);
  border:1px solid #cfe0f5;font-size:.8rem;font-weight:700}
.dec p{margin:0 0 .6rem;font-size:.92rem;max-width:none}
.dec p:last-child{margin-bottom:0}
.dec .lab{display:block;font-size:.7rem;letter-spacing:.06em;text-transform:uppercase;
  color:var(--ink-3);font-weight:650;margin-bottom:.15rem}
.dec-ev{color:var(--ink-2)}
.dec-ask{background:#faf9f6;border-radius:4px;padding:.7rem .85rem;margin-top:.85rem!important}

ol.fases{list-style:none;counter-reset:f;padding:0;margin:1.4rem 0}
ol.fases li{counter-increment:f;position:relative;padding:0 0 1.15rem 2.6rem;
  border-left:2px solid var(--line);margin-left:.7rem}
ol.fases li:last-child{border-left-color:transparent;padding-bottom:0}
ol.fases li::before{content:counter(f);position:absolute;left:-.78rem;top:0;width:1.5rem;height:1.5rem;
  border-radius:50%;background:var(--panel);border:1px solid var(--line);color:var(--ink-3);
  font-size:.76rem;font-weight:700;display:flex;align-items:center;justify-content:center}
ol.fases li.done::before{content:"✓";background:#eaf3fc;border-color:#c2dbf6;color:#16508f}
ol.fases > li > b{display:block;font-size:.97rem;margin-bottom:.15rem}
ol.fases span{font-size:.9rem;color:var(--ink-2)}
ol.fases .estado{font-size:.72rem;letter-spacing:.05em;text-transform:uppercase;font-weight:650;
  color:var(--ink-3);margin-left:.5rem}
ol.fases li.done .estado{color:#16508f}

footer{border-top:1px solid var(--line);margin-top:3.5rem;padding:2rem 0 3rem;
  font-size:.83rem;color:var(--ink-3)}
footer p{max-width:46rem}

@media (max-width:640px){
  h1{font-size:1.95rem} h2{font-size:1.42rem}
  .cbar{width:8rem;min-width:7rem}
  .qtxt{min-width:9rem;font-size:.85rem}
  table{font-size:.82rem}
  .scroll{overflow-x:auto}
}
@media print{
  nav.toc{display:none} body{font-size:11pt} section{page-break-inside:avoid}
  .dec,.tiles{page-break-inside:avoid}
}
"""

const RAW_DATA  = __DATA_JSON__;
const ALL_ORGAOS = __ORGAOS_JSON__;
const HOJE  = "__HOJE__";
const TOTAL = __TOTAL__;

let activeOrg  = 'all';
let activeTier = 'all';

/* ── Utils ────────────────────────────────────────────────────── */
function fmtBRL(v) {
  if (v === undefined || v === null || isNaN(v)) return '—';
  return 'R$ ' + v.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2});
}

function pillClass(pct) {
  return pct >= 30 ? 'pill-red' : pct >= 20 ? 'pill-amber' : 'pill-green';
}

const C = {
  blue: '#0EA5E9', blueLight: '#BAE6FD',
  green: '#10B981', amber: '#F59E0B', red: '#EF4444',
  text: '#0F172A', muted: '#64748B', border: '#E2E8F0',
  palette: ['#0EA5E9','#6366F1','#8B5CF6','#10B981','#F59E0B','#EF4444','#14B8A6','#EC4899'],
};

const BASE_LAYOUT = {
  paper_bgcolor: 'white',
  plot_bgcolor:  'white',
  font: {family: "'Plus Jakarta Sans', sans-serif"},
};

const CHART_CFG = {displayModeBar: false, responsive: true};

/* ── Filter ───────────────────────────────────────────────────── */
function getFiltered() {
  const q = document.getElementById('searchInput').value.toLowerCase().trim();
  return RAW_DATA.filter(r => {
    if (q && !r.nome.toLowerCase().includes(q) && !r.cargo.toLowerCase().includes(q)) return false;
    if (activeOrg !== 'all' && r.orgao !== activeOrg) return false;
    if (activeTier === 'high' && r.pctDesc < 30) return false;
    if (activeTier === 'mid'  && (r.pctDesc < 20 || r.pctDesc >= 30)) return false;
    if (activeTier === 'low'  && r.pctDesc >= 20) return false;
    return true;
  });
}

function getSorted(data) {
  const v = document.getElementById('sortSelect').value;
  return [...data].sort((a, b) => {
    if (v === 'liquida-desc') return b.liquida - a.liquida;
    if (v === 'liquida-asc')  return a.liquida - b.liquida;
    if (v === 'pct-desc')     return b.pctDesc  - a.pctDesc;
    if (v === 'pct-asc')      return a.pctDesc  - b.pctDesc;
    if (v === 'nome-asc')     return a.nome.localeCompare(b.nome, 'pt-BR');
    return 0;
  });
}

/* ── KPIs ─────────────────────────────────────────────────────── */
function updateKPIs(data) {
  const n     = data.length;
  const folha = data.reduce((s, r) => s + r.liquida, 0);
  const media = n ? folha / n : 0;
  const maior = n ? Math.max(...data.map(r => r.liquida)) : 0;
  const menor = n ? Math.min(...data.map(r => r.liquida)) : 0;

  document.getElementById('kpi-total').textContent     = n;
  document.getElementById('kpi-total-sub').textContent =
    n === TOTAL ? `Consulta em ${HOJE}` : `de ${TOTAL} total`;
  document.getElementById('kpi-folha').textContent     = fmtBRL(folha);
  document.getElementById('kpi-media').textContent     = fmtBRL(media);
  document.getElementById('kpi-media-sub').textContent =
    n ? `${fmtBRL(menor)} – ${fmtBRL(maior)}` : '—';
  document.getElementById('kpi-maior').textContent     = fmtBRL(maior);
  document.getElementById('kpi-menor-sub').textContent = n ? `Menor: ${fmtBRL(menor)}` : '—';
  document.getElementById('badge-count').textContent   =
    `${n} servidor${n !== 1 ? 'es' : ''}`;
}

/* ── Table ────────────────────────────────────────────────────── */
function updateTable(data) {
  const tbody = document.getElementById('tableBody');
  const empty = document.getElementById('emptyState');
  document.getElementById('table-count').textContent =
    `${data.length} resultado${data.length !== 1 ? 's' : ''}`;

  if (!data.length) {
    tbody.innerHTML = '';
    empty.style.display = 'flex';
    return;
  }
  empty.style.display = 'none';
  tbody.innerHTML = data.map(r => {
    const pc    = pillClass(r.pctDesc);
    const cargo = r.cargo.length > 44 ? r.cargo.slice(0, 44) + '…' : r.cargo;
    return `<tr>
      <td><strong>${r.nome}</strong></td>
      <td><span class="orgao-tag">${r.orgao}</span></td>
      <td class="cargo-cell" title="${r.cargo}">${cargo}</td>
      <td class="num">${r.fixaFmt}</td>
      <td class="num">${r.eventuaisFmt}</td>
      <td class="num"><strong style="color:#0EA5E9">${r.liquidaFmt}</strong></td>
      <td class="num">${fmtBRL(r.desconto)}</td>
      <td><span class="pill ${pc}">${r.pctDesc.toFixed(1)}%</span></td>
    </tr>`;
  }).join('');
}

/* ── Charts ───────────────────────────────────────────────────── */
function tracesBarLiquida(data) {
  const s = [...data].sort((a, b) => a.liquida - b.liquida);
  return [{
    type: 'bar', orientation: 'h',
    x: s.map(r => r.liquida),
    y: s.map(r => r.nomeCurto),
    marker: {
      color: s.map((_, i) => i === s.length - 1 ? C.blue : C.blueLight),
      line: {width: 0},
    },
    text: s.map(r => fmtBRL(r.liquida)),
    textposition: 'outside', textfont: {size: 11, color: C.muted},
    hovertemplate: '<b>%{y}</b><br>Líquida: R$ %{x:,.2f}<extra></extra>',
  }];
}

function tracesDonut(data) {
  const g = {};
  data.forEach(r => { g[r.orgao] = (g[r.orgao] || 0) + r.liquida; });
  const labels = Object.keys(g);
  const values = labels.map(k => g[k]);
  return [{
    type: 'pie', labels, values, hole: 0.55,
    marker: {colors: C.palette.slice(0, labels.length), line: {color: 'white', width: 3}},
    hovertemplate: '<b>%{label}</b><br>R$ %{value:,.2f}<br>%{percent}<extra></extra>',
    textinfo: 'label+percent', textfont: {size: 10, color: C.text},
    showlegend: false, direction: 'clockwise', sort: true,
  }];
}

function layoutDonut(data) {
  const total = data.reduce((s, r) => s + r.liquida, 0);
  return {
    ...BASE_LAYOUT, height: 300,
    margin: {l: 10, r: 10, t: 10, b: 10},
    annotations: [{
      text: `<b>${fmtBRL(total)}</b><br><span style='font-size:11px'>Total</span>`,
      x: 0.5, y: 0.5, showarrow: false,
      font: {size: 13, color: C.text}, align: 'center',
    }],
  };
}

function tracesGrouped(data) {
  const s = [...data].sort((a, b) => b.liquida - a.liquida);
  return [
    {
      type: 'bar', name: 'Rem. Fixa',
      x: s.map(r => r.nomeCurto), y: s.map(r => r.fixa),
      marker: {color: C.blueLight, line: {width: 0}},
      text: s.map(r => `R$${(r.fixa / 1000).toFixed(1)}k`),
      textposition: 'outside', textfont: {size: 9, color: C.muted},
      hovertemplate: '<b>%{x}</b><br>Fixa: R$ %{y:,.2f}<extra></extra>',
    },
    {
      type: 'bar', name: 'Rem. Líquida',
      x: s.map(r => r.nomeCurto), y: s.map(r => r.liquida),
      marker: {color: C.blue, line: {width: 0}},
      text: s.map(r => `R$${(r.liquida / 1000).toFixed(1)}k`),
      textposition: 'outside', textfont: {size: 9, color: C.muted},
      hovertemplate: '<b>%{x}</b><br>Líquida: R$ %{y:,.2f}<extra></extra>',
    },
  ];
}

function tracesDesconto(data) {
  const s = [...data].sort((a, b) => a.pctDesc - b.pctDesc);
  return [{
    type: 'bar', orientation: 'h',
    x: s.map(r => r.pctDesc),
    y: s.map(r => r.nomeCurto),
    marker: {
      color: s.map(r => r.pctDesc >= 30 ? C.red : r.pctDesc >= 20 ? C.amber : C.green),
      line: {width: 0},
    },
    text: s.map(r => `${r.pctDesc}%`),
    textposition: 'outside', textfont: {size: 11, color: C.muted},
    hovertemplate: '<b>%{y}</b><br>Desconto: %{x:.1f}%<extra></extra>',
  }];
}

function updateCharts(data) {
  if (!data.length) return;
  const maxP = Math.max(...data.map(r => r.pctDesc), 10);

  Plotly.react('chart-bar', tracesBarLiquida(data), {
    ...BASE_LAYOUT, height: 320,
    margin: {l: 10, r: 90, t: 10, b: 10},
    xaxis: {tickprefix: 'R$ ', gridcolor: C.border, zeroline: false, tickfont: {color: C.muted, size: 10}},
    yaxis: {gridcolor: C.border, tickfont: {color: C.text, size: 11}, autorange: 'reversed'},
  }, CHART_CFG);

  Plotly.react('chart-donut', tracesDonut(data), layoutDonut(data), CHART_CFG);

  Plotly.react('chart-grouped', tracesGrouped(data), {
    ...BASE_LAYOUT, height: 320,
    barmode: 'group', bargap: 0.25, bargroupgap: 0.05,
    margin: {l: 10, r: 10, t: 30, b: 65},
    legend: {
      orientation: 'h', yanchor: 'bottom', y: 1.02,
      xanchor: 'right', x: 1,
      font: {size: 11, color: C.muted}, bgcolor: 'rgba(0,0,0,0)',
    },
    xaxis: {tickangle: -30, tickfont: {color: C.text, size: 10}, gridcolor: C.border},
    yaxis: {tickprefix: 'R$ ', gridcolor: C.border, zeroline: false, tickfont: {color: C.muted, size: 10}},
  }, CHART_CFG);

  Plotly.react('chart-desc', tracesDesconto(data), {
    ...BASE_LAYOUT, height: 320,
    margin: {l: 10, r: 60, t: 10, b: 10},
    xaxis: {ticksuffix: '%', gridcolor: C.border, zeroline: false, tickfont: {color: C.muted, size: 10}, range: [0, maxP * 1.25]},
    yaxis: {gridcolor: C.border, tickfont: {color: C.text, size: 11}, autorange: 'reversed'},
  }, CHART_CFG);
}

/* ── Apply all ────────────────────────────────────────────────── */
function applyFilters() {
  const filtered = getFiltered();
  const sorted   = getSorted(filtered);
  updateKPIs(filtered);
  updateTable(sorted);
  updateCharts(filtered);
}

/* ── Export CSV ───────────────────────────────────────────────── */
function exportCSV() {
  const data = getSorted(getFiltered());
  const headers = ['Nome','Órgão','Cargo','Rem. Fixa','Eventuais','Rem. Líquida','Desconto','% Desc.'];
  const rows = data.map(r => [
    r.nome, r.orgao, r.cargo,
    r.fixaFmt, r.eventuaisFmt, r.liquidaFmt,
    fmtBRL(r.desconto), r.pctDesc.toFixed(1) + '%',
  ]);
  const csv = [headers, ...rows]
    .map(row => row.map(c => `"${String(c).replace(/"/g, '""')}"`).join(','))
    .join('\r\n');
  const blob = new Blob(['\ufeff' + csv], {type: 'text/csv;charset=utf-8;'});
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement('a');
  a.href = url; a.download = 'servidores_ms.csv'; a.click();
  URL.revokeObjectURL(url);
}

/* ── Org chips ────────────────────────────────────────────────── */
function initOrgChips() {
  const container = document.getElementById('orgChips');
  document.querySelector('[data-org="all"]').onclick = () => setOrg('all');
  ALL_ORGAOS.forEach(org => {
    const btn = document.createElement('button');
    btn.className   = 'chip';
    btn.textContent = org;
    btn.dataset.org = org;
    btn.onclick     = () => setOrg(org);
    container.appendChild(btn);
  });
}

function setOrg(org) {
  activeOrg = org;
  document.querySelectorAll('#orgChips .chip').forEach(b =>
    b.classList.toggle('chip-active', b.dataset.org === org));
  applyFilters();
}

function setTier(tier) {
  activeTier = tier;
  ['all', 'high', 'mid', 'low'].forEach(t =>
    document.getElementById(`tier-${t}`).classList.toggle('chip-active', t === tier));
  applyFilters();
}

function clearAllFilters() {
  document.getElementById('searchInput').value = '';
  document.getElementById('sortSelect').value  = 'liquida-desc';
  setOrg('all');
  setTier('all');
}

/* ── Init ─────────────────────────────────────────────────────── */
document.getElementById('searchInput').addEventListener('input', applyFilters);
initOrgChips();
applyFilters();

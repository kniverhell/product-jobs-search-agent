(() => {
  const PAGE = 2;
  const BUDGET = 750;
  const text = s => (s || '').replace(/\s+/g, ' ').trim();
  const cap = s => (s.length > 60 ? s.slice(0, 59) + '…' : s);
  const frames = [];
  const docs = [document];
  document.querySelectorAll('iframe, frame').forEach(f => {
    let d = null;
    try { d = f.contentDocument; } catch (e) { d = null; }
    if (d) docs.push(d);
    else frames.push(cap(f.getAttribute('src') || '(inline)'));
  });
  const labelOf = (el, d) => {
    if (el.id) {
      const l = d.querySelector('label[for="' + CSS.escape(el.id) + '"]');
      if (l) return text(l.textContent);
    }
    const wrap = el.closest('label');
    if (wrap) return text(wrap.textContent);
    if (el.getAttribute('aria-label')) return text(el.getAttribute('aria-label'));
    const by = el.getAttribute('aria-labelledby');
    if (by) return text(by.split(' ').map(id => (d.getElementById(id) || {}).textContent).join(' '));
    return text(el.placeholder || el.name || el.id);
  };
  const rows = [];
  const groups = new Map();
  docs.forEach((d, n) => {
    const where = n === 0 ? '' : ' [frame]';
    d.querySelectorAll('input, select, textarea, button').forEach(el => {
      const type = el.tagName === 'INPUT' ? (el.type || 'text') : el.tagName.toLowerCase();
      if (type === 'hidden') return;
      const label = cap(labelOf(el, d));
      if (type === 'radio' || type === 'checkbox') {
        const fs = el.closest('fieldset');
        const lg = fs && fs.querySelector('legend');
        const q = lg ? cap(text(lg.textContent)) : label;
        const key = n + '|' + type + '|' + (el.name || q);
        if (!groups.has(key)) {
          groups.set(key, { type: type, q: q, opts: [], on: [], where: where });
          rows.push(groups.get(key));
        }
        const g = groups.get(key);
        g.opts.push(lg ? label : 'this box');
        if (el.checked) g.on.push(lg ? label : 'checked');
      } else if (type === 'password' || type === 'file') {
        const has = type === 'file' ? el.files.length > 0 : el.value !== '';
        rows.push(type + ' | ' + label + ' | has value: ' + (has ? 'yes' : 'no') + where);
      } else if (type === 'select') {
        const sel = Array.from(el.selectedOptions).map(o => text(o.textContent)).join(', ');
        const opts = Array.from(el.options).map(o => text(o.textContent)).join(', ');
        rows.push('select | ' + label + ' | selected: ' + cap(sel || 'none') + ' | options: ' + cap(opts) + where);
      } else if (['button', 'submit', 'reset', 'image'].includes(type)) {
        rows.push('button | ' + label + where);
      } else {
        rows.push(type + ' | ' + label + ' | value: ' + (el.value === '' ? '(empty)' : '"' + cap(el.value) + '"') + where);
      }
    });
  });
  const lines = rows.map((r, i) => (i + 1) + '. ' + (typeof r === 'string' ? r
    : r.type + ' | ' + r.q + ' | options: ' + cap(r.opts.join(', ')) + ' | checked: ' + cap(r.on.join(', ') || 'none') + r.where));
  const pages = [];
  let cur = '';
  lines.forEach(l => {
    if (cur && cur.length + l.length + 1 > BUDGET) { pages.push(cur); cur = ''; }
    cur += l + '\n';
  });
  if (cur || !pages.length) pages.push(cur);
  const head = 'page ' + PAGE + ' of ' + pages.length + ' | unreadable frames: '
    + (frames.length ? frames.length + ' (' + frames.slice(0, 2).join(', ') + ')' : 'none') + '\n';
  if (PAGE > pages.length) return head + 'END: there is no page ' + PAGE;
  const foot = PAGE < pages.length ? 'MORE: run page ' + (PAGE + 1) : 'END: ' + lines.length + ' fields';
  return head + pages[PAGE - 1] + foot;
})()

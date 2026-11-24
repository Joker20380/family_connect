(() => {
  const source = document.getElementById('charts-data');
  const formatTime = epoch => new Date(epoch * 1000).toLocaleString('ru-RU', {timeZone: 'UTC'});
  document.querySelectorAll('[data-epoch]').forEach(element => { element.textContent = formatTime(Number(element.dataset.epoch)) + ' UTC'; });
  if (!source) return;
  const charts = JSON.parse(source.textContent);
  const colors = ['#2ed1c5', '#68a9ff', '#f0c778'];
  const namespace = 'http://www.w3.org/2000/svg';
  function node(name, attrs, text) {
    const element = document.createElementNS(namespace, name);
    Object.entries(attrs).forEach(([key, value]) => element.setAttribute(key, value));
    if (text !== undefined) element.textContent = text;
    return element;
  }
  function format(value, unit) {
    if (unit === 'Б/с') {
      if (value >= 1048576) return (value / 1048576).toFixed(2) + ' МиБ/с';
      if (value >= 1024) return (value / 1024).toFixed(1) + ' КиБ/с';
    }
    return value.toLocaleString('ru-RU', {maximumFractionDigits: 1}) + ' ' + unit;
  }
  function draw(container) {
    container.replaceChildren();
    container.parentElement.querySelector('.chart-legend')?.remove();
    const data = charts[Number(container.dataset.chart)];
    const available = data.points.filter(point => data.series.some(series => Number.isFinite(point[series.key])));
    if (!available.length) { container.textContent = 'Нет измерений за выбранный период'; container.classList.add('empty'); return; }
    const width = Math.max(280, container.clientWidth), height = 250, left = 70, right = 14, top = 20, bottom = 36;
    const start = data.points[0].at, end = data.points[data.points.length - 1].at;
    const maximum = Math.max(1, ...available.flatMap(point => data.series.map(series => point[series.key] || 0))) * 1.1;
    const horizontal = epoch => left + (epoch - start) / Math.max(1, end - start) * (width - left - right);
    const vertical = value => height - bottom - value / maximum * (height - top - bottom);
    const svg = node('svg', {viewBox: `0 0 ${width} ${height}`, role: 'group', tabindex: '0', 'aria-label': data.title + ' · стрелки влево/вправо для выбора измерения'});
    for (let index = 0; index <= 4; index++) {
      const value = maximum * index / 4, position = vertical(value);
      svg.append(node('line', {x1: left, y1: position, x2: width - right, y2: position, class: 'axis'}));
      svg.append(node('text', {x: left - 10, y: position + 3, 'text-anchor': 'end'}, format(value, data.unit)));
      const epoch = start + (end - start) * index / 4;
      svg.append(node('text', {x: horizontal(epoch), y: height - 10, 'text-anchor': index === 0 ? 'start' : index === 4 ? 'end' : 'middle'},
        new Date(epoch * 1000).toLocaleTimeString('ru-RU', {timeZone: 'UTC', hour: '2-digit', minute: '2-digit'})));
    }
    data.series.forEach((series, index) => {
      let path = '', previous = null;
      data.points.forEach((point, pointIndex) => {
        const value = point[series.key];
        if (!Number.isFinite(value)) { previous = null; return; }
        const next = data.points[pointIndex + 1];
        const connectedBefore = previous !== null && point.at - previous <= 300;
        const connectedAfter = next && Number.isFinite(next[series.key]) && next.at - point.at <= 300;
        if (!connectedBefore && !connectedAfter) {
          svg.append(node('circle', {cx: horizontal(point.at), cy: vertical(value), r: 3, fill: colors[index]}));
        }
        path += (previous !== null && point.at - previous <= 300 ? ' L' : ' M') + horizontal(point.at) + ',' + vertical(value);
        previous = point.at;
      });
      svg.prepend(node('path', {d: path, stroke: colors[index], class: 'chart-line'}));
    });
    let selected = data.points.length - 1;
    const marker = node('line', {x1: horizontal(data.points[selected].at), x2: horizontal(data.points[selected].at), y1: top, y2: height - bottom, class: 'axis'});
    svg.append(marker);
    function announce() {
      const point = data.points[selected];
      marker.setAttribute('x1', horizontal(point.at)); marker.setAttribute('x2', horizontal(point.at));
      container.parentElement.querySelector('.chart-tooltip').textContent = formatTime(point.at) + ' UTC · ' + data.series.map(series =>
        series.label + ': ' + (Number.isFinite(point[series.key]) ? format(point[series.key], data.unit) : point.reason || 'нет измерения')).join(' · ');
    }
    svg.addEventListener('mousemove', event => {
      const position = (event.clientX - svg.getBoundingClientRect().left) / svg.getBoundingClientRect().width * width;
      const epoch = start + (position - left) / (width - left - right) * (end - start);
      let low = 0, high = data.points.length - 1;
      while (low < high) { const middle = Math.floor((low + high) / 2); if (data.points[middle].at < epoch) low = middle + 1; else high = middle; }
      selected = low; announce();
    });
    svg.addEventListener('focus', announce);
    svg.addEventListener('keydown', event => {
      if (!['ArrowLeft', 'ArrowRight'].includes(event.key)) return;
      event.preventDefault(); selected = Math.max(0, Math.min(data.points.length - 1, selected + (event.key === 'ArrowLeft' ? -1 : 1))); announce();
    });
    container.append(svg);
    const legend = document.createElement('div'); legend.className = 'chart-legend';
    data.series.forEach((series, index) => { const label = document.createElement('span'); label.className = 'series-' + index; label.textContent = series.label; legend.append(label); });
    container.after(legend);
  }
  const observer = new ResizeObserver(entries => entries.forEach(entry => {
    const width = Math.round(entry.contentRect.width);
    if (entry.target.dataset.width !== String(width)) {
      entry.target.dataset.width = String(width);
      draw(entry.target);
    }
  }));
  document.querySelectorAll('[data-chart]').forEach(container => observer.observe(container));
})();

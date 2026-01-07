import { Chart, Tooltip } from 'chart.js';
Chart.register(Tooltip);

if (!Chart.Tooltip.positioners.netDash) {
  Chart.Tooltip.positioners.netDash = function (items, eventPosition) {
    if (!items?.length) return eventPosition;
    const chart = items[0].chart;
    const netIdx = chart.data.datasets.findIndex(d => d.netIndicator);
    const dataIndex = items[0].dataIndex;
    if (netIdx === -1) return eventPosition;
    const meta = chart.getDatasetMeta(netIdx);
    const point = meta?.data?.[dataIndex];
    const fallbackPoint = items[0].element;
    if (point) return { x: point.x, y: point.y - 8 };
    if (fallbackPoint) return { x: fallbackPoint.x, y: fallbackPoint.y - 8 };
    return eventPosition ?? { x: 0, y: 0 };
  };
}

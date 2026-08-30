/**
 * Inline-SVG chart primitives for the V8 Analytics Dashboard.
 * Zero dependencies — everything is hand-rolled SVG so we can match
 * the dashboard's dark theme and keep the bundle small.
 */
import React from 'react';

const COLORS = {
  axis: '#374151',
  text: '#9ca3af',
  accent: '#60a5fa',
  accent2: '#34d399',
  accent3: '#f59e0b',
  accent4: '#f472b6',
  warn: '#f87171',
};

// ── Line / area chart ──────────────────────────────────────────────
export interface LinePoint {
  date: string;
  value: number;
}

export function LineChart({
  points,
  height = 160,
  color = COLORS.accent,
  fillBelow = true,
  yMax,
  yLabel,
  formatY = (v: number) => v.toFixed(0),
}: {
  points: LinePoint[];
  height?: number;
  color?: string;
  fillBelow?: boolean;
  yMax?: number;
  yLabel?: string;
  formatY?: (v: number) => string;
}) {
  if (points.length === 0) {
    return <EmptyChart label="No data yet" height={height} />;
  }

  const width = 600;
  const padL = 40;
  const padR = 10;
  const padT = 10;
  const padB = 24;
  const innerW = width - padL - padR;
  const innerH = height - padT - padB;

  const maxV = yMax ?? Math.max(1, ...points.map((p) => p.value));
  const minV = 0;

  const x = (i: number) =>
    padL + (points.length === 1 ? innerW / 2 : (i / (points.length - 1)) * innerW);
  const y = (v: number) =>
    padT + innerH - ((v - minV) / (maxV - minV)) * innerH;

  const path = points
    .map((p, i) => `${i === 0 ? 'M' : 'L'} ${x(i)} ${y(p.value)}`)
    .join(' ');
  const areaPath = `${path} L ${x(points.length - 1)} ${padT + innerH} L ${x(0)} ${padT + innerH} Z`;

  // y-axis ticks
  const ticks = 4;
  const yTicks = Array.from({ length: ticks + 1 }, (_, i) => (maxV / ticks) * i);

  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-auto">
      {yTicks.map((t, i) => (
        <g key={i}>
          <line
            x1={padL}
            x2={width - padR}
            y1={y(t)}
            y2={y(t)}
            stroke={COLORS.axis}
            strokeDasharray={i === 0 ? '0' : '2 2'}
          />
          <text
            x={padL - 6}
            y={y(t) + 3}
            textAnchor="end"
            className="text-[9px] fill-gray-500"
          >
            {formatY(t)}
          </text>
        </g>
      ))}
      {fillBelow && (
        <path d={areaPath} fill={color} opacity={0.15} />
      )}
      <path d={path} fill="none" stroke={color} strokeWidth={2} />
      {points.map((p, i) => (
        <circle
          key={i}
          cx={x(i)}
          cy={y(p.value)}
          r={3}
          fill={color}
        />
      ))}
      {yLabel && (
        <text
          x={4}
          y={padT}
          className="text-[9px] fill-gray-500"
        >
          {yLabel}
        </text>
      )}
      {/* x labels: first, middle, last */}
      {[0, Math.floor(points.length / 2), points.length - 1].map((i) => (
        <text
          key={i}
          x={x(i)}
          y={height - 4}
          textAnchor="middle"
          className="text-[9px] fill-gray-500"
        >
          {points[i].date.slice(5)}
        </text>
      ))}
    </svg>
  );
}

// ── Bar chart (horizontal, ranked) ───────────────────────────────
export interface BarItem {
  label: string;
  value: number;
  sublabel?: string;
  color?: string;
  meta?: Record<string, string | number>;
}

export function BarChart({
  items,
  height,
  color = COLORS.accent,
  formatValue = (v: number) => v.toFixed(2),
  max,
}: {
  items: BarItem[];
  height?: number;
  color?: string;
  formatValue?: (v: number) => string;
  max?: number;
}) {
  if (items.length === 0) {
    return <EmptyChart label="No data yet" />;
  }
  const width = 600;
  const rowH = 26;
  const labelW = 160;
  const valueW = 50;
  const barAreaW = width - labelW - valueW - 20;
  const autoH = items.length * rowH + 16;
  const finalH = height ?? autoH;

  const maxV = max ?? Math.max(0.01, ...items.map((i) => i.value));

  return (
    <svg viewBox={`0 0 ${width} ${finalH}`} className="w-full h-auto">
      {items.map((it, i) => {
        const y = 8 + i * rowH;
        const barW = Math.max(1, (it.value / maxV) * barAreaW);
        const fill = it.color ?? color;
        return (
          <g key={i}>
            <text
              x={labelW - 8}
              y={y + 14}
              textAnchor="end"
              className="text-[10px] fill-gray-300"
            >
              {it.label.length > 22 ? it.label.slice(0, 21) + '…' : it.label}
            </text>
            <rect
              x={labelW}
              y={y + 4}
              width={barW}
              height={14}
              fill={fill}
              opacity={0.7}
              rx={2}
            />
            <text
              x={labelW + barW + 6}
              y={y + 14}
              className="text-[10px] fill-gray-400"
            >
              {formatValue(it.value)}
              {it.sublabel && (
                <tspan className="fill-gray-600"> · {it.sublabel}</tspan>
              )}
              {it.meta?.attempts !== undefined && (
                <tspan className="fill-gray-600"> · {it.meta.attempts} att</tspan>
              )}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

// ── Knowledge graph (force-positioned, but deterministic) ─────────
export interface GraphNode {
  id: string;
  label: string;
  weight: number;
}
export interface GraphEdge {
  source: string;
  target: string;
  weight: number;
}

export function KnowledgeGraph({
  nodes,
  edges,
  height = 360,
}: {
  nodes: GraphNode[];
  edges: GraphEdge[];
  height?: number;
}) {
  if (nodes.length === 0) {
    return <EmptyChart label="No knowledge graph yet — study something first" height={height} />;
  }

  const width = 720;
  // Deterministic circular layout (radius proportional to weight)
  const cx = width / 2;
  const cy = height / 2;
  const radius = Math.min(width, height) / 2 - 40;
  const positioned: Record<string, { x: number; y: number; r: number }> = {};
  nodes.forEach((n, i) => {
    const angle = (i / nodes.length) * 2 * Math.PI;
    positioned[n.id] = {
      x: cx + Math.cos(angle) * radius,
      y: cy + Math.sin(angle) * radius,
      r: 6 + n.weight * 12,
    };
  });

  // Pick the top edges by weight
  const topEdges = [...edges].sort((a, b) => b.weight - a.weight).slice(0, 200);

  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-auto">
      {topEdges.map((e, i) => {
        const s = positioned[e.source];
        const t = positioned[e.target];
        if (!s || !t) return null;
        const op = Math.min(0.7, 0.1 + e.weight * 0.15);
        return (
          <line
            key={i}
            x1={s.x}
            y1={s.y}
            x2={t.x}
            y2={t.y}
            stroke={COLORS.accent}
            opacity={op}
            strokeWidth={Math.min(3, 0.5 + e.weight * 0.5)}
          />
        );
      })}
      {nodes.map((n) => {
        const p = positioned[n.id];
        return (
          <g key={n.id}>
            <circle
              cx={p.x}
              cy={p.y}
              r={p.r}
              fill={COLORS.accent2}
              opacity={0.85}
            />
            <text
              x={p.x}
              y={p.y - p.r - 4}
              textAnchor="middle"
              className="text-[9px] fill-gray-300"
            >
              {n.label.length > 22 ? n.label.slice(0, 21) + '…' : n.label}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

// ── Donut (single value as % of max) ─────────────────────────────
export function Donut({
  value,
  label,
  max = 100,
  size = 110,
  color = COLORS.accent,
}: {
  value: number;
  label: string;
  max?: number;
  size?: number;
  color?: string;
}) {
  const pct = Math.max(0, Math.min(1, value / max));
  const r = size / 2 - 6;
  const c = 2 * Math.PI * r;
  return (
    <svg viewBox={`0 0 ${size} ${size}`} className="inline-block">
      <circle
        cx={size / 2}
        cy={size / 2}
        r={r}
        stroke={COLORS.axis}
        strokeWidth={8}
        fill="none"
      />
      <circle
        cx={size / 2}
        cy={size / 2}
        r={r}
        stroke={color}
        strokeWidth={8}
        fill="none"
        strokeDasharray={`${c * pct} ${c}`}
        strokeDashoffset={c / 4}
        transform={`rotate(-90 ${size / 2} ${size / 2})`}
      />
      <text
        x={size / 2}
        y={size / 2 - 2}
        textAnchor="middle"
        className="text-[16px] font-bold fill-white"
      >
        {typeof value === 'number' ? value.toFixed(1) : String(value)}
      </text>
      <text
        x={size / 2}
        y={size / 2 + 14}
        textAnchor="middle"
        className="text-[9px] fill-gray-400"
      >
        {label}
      </text>
    </svg>
  );
}

// ── Sparkline (tiny inline line) ─────────────────────────────────
export function Sparkline({
  values,
  color = COLORS.accent,
  width = 80,
  height = 22,
}: {
  values: number[];
  color?: string;
  width?: number;
  height?: number;
}) {
  if (values.length < 2) {
    return <span className="text-gray-600 text-xs">–</span>;
  }
  const max = Math.max(...values, 0.01);
  const pts = values
    .map((v, i) => {
      const x = (i / (values.length - 1)) * width;
      const y = height - (v / max) * height;
      return `${i === 0 ? 'M' : 'L'} ${x} ${y}`;
    })
    .join(' ');
  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="inline-block align-middle">
      <path d={pts} fill="none" stroke={color} strokeWidth={1.5} />
    </svg>
  );
}

// ── Empty placeholder ────────────────────────────────────────────
function EmptyChart({ label, height = 160 }: { label: string; height?: number }) {
  return (
    <div
      style={{ height }}
      className="flex items-center justify-center text-xs text-gray-600 italic border border-dashed border-gray-700 rounded"
    >
      {label}
    </div>
  );
}
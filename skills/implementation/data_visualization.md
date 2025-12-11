---
name: Data Visualization Developer
id: data_visualization
version: 1.0
category: visualization
domain: [web, frontend, dashboard]
task_types: [implementation, design, feature]
keywords: [chart, graph, visualization, d3, plot, dashboard, metrics, recharts, chart.js, bar chart, line chart, pie chart, data viz, analytics, scatter, area, heatmap, sparkline]
complexity: [normal, complex]
pairs_with: [html5_canvas, api_designer, frontend_design]
source: original
---

# Data Visualization Developer

## Role

You implement clear, accessible data visualizations. You select appropriate chart types, use color effectively, ensure accessibility, and optimize for performance with large datasets.

## Core Competencies

- Chart type selection
- Library selection (Chart.js, D3.js, Recharts)
- Color theory for data
- Accessibility (colorblind-safe, ARIA)
- Responsive design
- Performance optimization

## Chart Type Selection

| Chart Type | Use When | Avoid When |
|------------|----------|------------|
| **Line** | Trends over time, continuous data | Categorical comparisons |
| **Bar** | Comparing categories, rankings | Too many categories (>10) |
| **Pie/Donut** | Part-to-whole (max 5-6 slices) | Comparing similar values, many categories |
| **Scatter** | Correlation between two variables | No clear relationship |
| **Area** | Cumulative totals, volume over time | Overlapping series (use stacked) |
| **Histogram** | Distribution of values | Small sample sizes |

### Decision Tree
```
What question are you answering?
├─ "How has X changed over time?" → Line or Area
├─ "How does X compare to Y?" → Bar (horizontal for many items)
├─ "What portion is X of total?" → Pie (≤5 slices) or Stacked Bar
├─ "Is there correlation between X and Y?" → Scatter
├─ "How is X distributed?" → Histogram or Box Plot
└─ "What's the current value of X?" → Single Number or Gauge
```

## Library Selection

| Library | Best For | Trade-offs |
|---------|----------|------------|
| **Chart.js** | Simple charts, quick setup, React wrappers | Limited customization |
| **Recharts** | React apps, declarative API | React-only, bundle size |
| **D3.js** | Custom/complex visualizations | Steep learning curve |
| **Plotly** | Scientific data, 3D charts | Large bundle |

**Default recommendation**: Chart.js for dashboards, D3 for custom.

## Implementation Patterns

### Chart.js Basic Setup
```javascript
import { Chart, registerables } from 'chart.js';
Chart.register(...registerables);

const chart = new Chart(ctx, {
  type: 'line',
  data: {
    labels: ['Jan', 'Feb', 'Mar', 'Apr'],
    datasets: [{
      label: 'Revenue',
      data: [1200, 1900, 3000, 2500],
      borderColor: '#3b82f6',
      backgroundColor: 'rgba(59, 130, 246, 0.1)',
      fill: true,
      tension: 0.3  // Smooth lines
    }]
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { position: 'top' },
      tooltip: {
        callbacks: {
          label: (ctx) => `$${ctx.parsed.y.toLocaleString()}`
        }
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        ticks: {
          callback: (value) => `$${value.toLocaleString()}`
        }
      }
    }
  }
});
```

### Recharts (React)
```jsx
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

function RevenueChart({ data }) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="month" />
        <YAxis tickFormatter={(v) => `$${v.toLocaleString()}`} />
        <Tooltip formatter={(v) => [`$${v.toLocaleString()}`, 'Revenue']} />
        <Line
          type="monotone"
          dataKey="revenue"
          stroke="#3b82f6"
          strokeWidth={2}
          dot={{ fill: '#3b82f6' }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
```

### D3.js Pattern
```javascript
// Container setup
const margin = { top: 20, right: 30, bottom: 40, left: 50 };
const width = container.clientWidth - margin.left - margin.right;
const height = 300 - margin.top - margin.bottom;

const svg = d3.select(container)
  .append('svg')
  .attr('width', width + margin.left + margin.right)
  .attr('height', height + margin.top + margin.bottom)
  .append('g')
  .attr('transform', `translate(${margin.left},${margin.top})`);

// Scales
const x = d3.scaleTime()
  .domain(d3.extent(data, d => d.date))
  .range([0, width]);

const y = d3.scaleLinear()
  .domain([0, d3.max(data, d => d.value)])
  .nice()
  .range([height, 0]);

// Axes
svg.append('g')
  .attr('transform', `translate(0,${height})`)
  .call(d3.axisBottom(x));

svg.append('g')
  .call(d3.axisLeft(y).tickFormat(d => `$${d}`));

// Line
const line = d3.line()
  .x(d => x(d.date))
  .y(d => y(d.value))
  .curve(d3.curveMonotoneX);

svg.append('path')
  .datum(data)
  .attr('fill', 'none')
  .attr('stroke', '#3b82f6')
  .attr('stroke-width', 2)
  .attr('d', line);
```

## Color Palettes

### Categorical (distinct groups)
```javascript
// 8-color colorblind-safe palette (Paul Tol)
const categorical = [
  '#332288', // indigo
  '#117733', // green
  '#44AA99', // teal
  '#88CCEE', // cyan
  '#DDCC77', // sand
  '#CC6677', // rose
  '#AA4499', // purple
  '#882255'  // wine
];
```

### Sequential (low to high)
```javascript
// Blues for single variable intensity
const sequential = ['#f7fbff', '#deebf7', '#c6dbef', '#9ecae1', '#6baed6', '#4292c6', '#2171b5', '#084594'];
```

### Diverging (negative to positive)
```javascript
// Red-Blue for positive/negative
const diverging = ['#b2182b', '#d6604d', '#f4a582', '#fddbc7', '#f7f7f7', '#d1e5f0', '#92c5de', '#4393c3', '#2166ac'];
```

### Colorblind Simulation
Test your charts at: [Coblis](https://www.color-blindness.com/coblis-color-blindness-simulator/)

**Rule**: Never encode meaning with color alone. Use patterns, labels, or shapes.

## Accessibility

### ARIA Labels
```html
<div
  role="img"
  aria-label="Line chart showing revenue growth from $1,200 in January to $2,500 in April"
>
  <canvas id="chart"></canvas>
</div>

<!-- Data table alternative -->
<details>
  <summary>View data as table</summary>
  <table>
    <caption>Monthly Revenue</caption>
    <thead>
      <tr><th>Month</th><th>Revenue</th></tr>
    </thead>
    <tbody>
      <tr><td>January</td><td>$1,200</td></tr>
      <!-- ... -->
    </tbody>
  </table>
</details>
```

### Contrast Requirements
- Text: 4.5:1 minimum (WCAG AA)
- Large text: 3:1 minimum
- Non-text (chart lines): 3:1 against background

### Keyboard Navigation
```javascript
// For interactive charts, implement focus management
chart.canvas.tabIndex = 0;
chart.canvas.addEventListener('keydown', (e) => {
  if (e.key === 'ArrowRight') highlightNext();
  if (e.key === 'ArrowLeft') highlightPrev();
  if (e.key === 'Enter') showDetail();
});
```

## Responsive Design

### Container-Based Sizing
```css
.chart-container {
  position: relative;
  width: 100%;
  height: 300px;  /* Fixed height */
  min-height: 200px;
}

@media (max-width: 640px) {
  .chart-container {
    height: 250px;
  }
}
```

### Mobile Considerations
- Rotate labels or use shorter formats
- Reduce data point density
- Move legend below chart
- Increase touch target size (44px minimum)
- Consider alternative viz for complex charts

## Performance Optimization

### Large Datasets
```javascript
// Downsample for display
function downsample(data, maxPoints) {
  if (data.length <= maxPoints) return data;

  const factor = Math.ceil(data.length / maxPoints);
  return data.filter((_, i) => i % factor === 0);
}

// Or aggregate
function aggregateByPeriod(data, period) {
  const buckets = new Map();

  for (const point of data) {
    const key = Math.floor(point.timestamp / period) * period;
    if (!buckets.has(key)) {
      buckets.set(key, { sum: 0, count: 0 });
    }
    const bucket = buckets.get(key);
    bucket.sum += point.value;
    bucket.count++;
  }

  return Array.from(buckets, ([timestamp, { sum, count }]) => ({
    timestamp,
    value: sum / count
  }));
}
```

### Animation Performance
```javascript
// Disable animations for large datasets
const options = {
  animation: data.length > 500 ? false : {
    duration: 300,
    easing: 'easeOutQuart'
  }
};

// Use CSS transforms where possible
```

### Canvas vs SVG
| | Canvas | SVG |
|---|--------|-----|
| Points | 10,000+ | < 1,000 |
| Interaction | Manual hit detection | DOM events |
| Accessibility | Requires extra work | Native |
| Export | Image only | Vector |

## Edge Cases

### Empty Data
```jsx
function Chart({ data }) {
  if (!data || data.length === 0) {
    return (
      <div className="chart-empty">
        <p>No data available for this period</p>
        <p className="text-muted">Try adjusting your filters</p>
      </div>
    );
  }
  return <ActualChart data={data} />;
}
```

### Single Data Point
```javascript
// Don't show line chart with one point
if (data.length === 1) {
  return <SingleValueDisplay value={data[0]} />;
}
```

### Outliers
```javascript
// Option 1: Log scale for extreme ranges
scales: { y: { type: 'logarithmic' } }

// Option 2: Truncate with indicator
const cap = percentile(data, 95);
const capped = data.map(d => Math.min(d, cap));
// Show "values above X truncated" note
```

## Anti-Patterns

| Anti-Pattern | Problem | Better Approach |
|--------------|---------|-----------------|
| Pie chart > 5 slices | Hard to compare | Horizontal bar chart |
| 3D charts | Distorts perception | Always use 2D |
| Dual Y-axes | Confusing correlation | Two separate charts |
| Truncated Y-axis | Exaggerates differences | Start at zero (usually) |
| Rainbow colors | No semantic meaning | Sequential/categorical palette |
| Animation on load | Delays comprehension | Animate on interaction only |
| Legend far from chart | Requires eye movement | Inline labels when possible |

## Output Expectations

When this skill is applied, the agent should:

- [ ] Select appropriate chart type for the data
- [ ] Use colorblind-safe palette
- [ ] Include proper axis labels and units
- [ ] Make chart responsive
- [ ] Handle empty/loading states
- [ ] Provide accessible alternative (data table)
- [ ] Optimize for data size

---

*Skill Version: 1.0*

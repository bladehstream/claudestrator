---
name: Web Artifacts Builder
id: web_artifacts_builder
version: 1.0
category: implementation
domain: [web, frontend, react]
task_types: [implementation, feature, creation]
keywords: [artifact, web, react, html, component, bundle, tailwind, shadcn, typescript, vite]
complexity: [complex]
pairs_with: [frontend_design, html5_canvas]
source: https://github.com/anthropics/skills/tree/main/skills/web-artifacts-builder
---

# Web Artifacts Builder

## Role

Suite of tools for creating elaborate, multi-component web artifacts using modern frontend web technologies (React, Tailwind CSS, shadcn/ui). Use for complex artifacts requiring state management, routing, or shadcn/ui components - not for simple single-file HTML/JSX artifacts.

## Technology Stack

- React 18
- TypeScript
- Vite (development)
- Parcel (bundling)
- Tailwind CSS
- shadcn/ui (40+ pre-installed components)
- Radix UI utilities

## Five-Phase Workflow

### Phase 1: Project Initialization

Run setup script to configure complete development environment:

```bash
./scripts/init-artifact.sh my-artifact
cd my-artifact
```

This creates:
- Vite + React + TypeScript setup
- Tailwind CSS configuration
- 40+ shadcn/ui components pre-installed
- Build and bundle scripts

### Phase 2: Development

**Project Structure**:
```
my-artifact/
├── src/
│   ├── App.tsx           # Main component
│   ├── components/       # Custom components
│   │   └── ui/          # shadcn/ui components
│   ├── hooks/           # Custom hooks
│   ├── lib/             # Utilities
│   └── main.tsx         # Entry point
├── index.html
├── tailwind.config.js
├── vite.config.ts
└── package.json
```

**Available shadcn/ui Components**:
- Accordion, Alert, AlertDialog
- Avatar, Badge, Button
- Calendar, Card, Checkbox
- Collapsible, Command, ContextMenu
- Dialog, Drawer, DropdownMenu
- Form, HoverCard, Input
- Label, Menubar, NavigationMenu
- Popover, Progress, RadioGroup
- ScrollArea, Select, Separator
- Sheet, Skeleton, Slider
- Switch, Table, Tabs
- Textarea, Toast, Toggle
- Tooltip, and more...

**Example Component**:
```tsx
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

export function MyComponent() {
  return (
    <Card className="w-[350px]">
      <CardHeader>
        <CardTitle>Create Project</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid w-full items-center gap-4">
          <Input placeholder="Project name" />
          <Button>Create</Button>
        </div>
      </CardContent>
    </Card>
  );
}
```

### Phase 3: Bundling

Create self-contained HTML artifact:

```bash
./scripts/bundle-artifact.sh
```

This produces `bundle.html` with:
- All JavaScript inlined
- All CSS inlined
- All dependencies bundled
- Single portable file

### Phase 4: Sharing

The `bundle.html` file is ready for:
- Claude conversations
- Direct browser viewing
- Embedding in other applications

### Phase 5: Testing (Optional)

Defer testing until after presenting initial output to minimize latency.

```bash
npm run dev    # Development server
npm run build  # Production build
```

## Design Principles

### Avoid Generic AI Aesthetics

**Anti-Patterns to Avoid**:
- Excessive centered layouts
- Purple gradients on white backgrounds
- Uniform rounded corners everywhere
- Inter font as default
- Generic card layouts

**Better Approaches**:
- Asymmetric, intentional layouts
- Distinctive color choices
- Varied border radii
- Custom or varied typography
- Unique component arrangements

### Component Best Practices

```tsx
// Use semantic structure
<main className="container mx-auto py-8">
  <header className="mb-8">
    <h1 className="text-3xl font-bold">Dashboard</h1>
  </header>
  <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
    {/* Content */}
  </section>
</main>

// Leverage Tailwind effectively
<div className="
  relative overflow-hidden
  bg-gradient-to-br from-slate-900 to-slate-800
  rounded-xl shadow-2xl
  p-6 md:p-8
">
  {/* Distinctive styling */}
</div>
```

## State Management

For complex state, use React patterns:

```tsx
// Context for global state
const AppContext = createContext<AppState | null>(null);

// Custom hooks for logic
function useData() {
  const [data, setData] = useState<Data[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData().then(setData).finally(() => setLoading(false));
  }, []);

  return { data, loading };
}

// Reducer for complex state
const [state, dispatch] = useReducer(reducer, initialState);
```

## Routing (if needed)

```tsx
import { BrowserRouter, Routes, Route } from 'react-router-dom';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>
    </BrowserRouter>
  );
}
```

## When NOT to Use

This skill is for **complex** artifacts. For simple cases, use:
- Single HTML file with inline styles
- Simple JSX component
- Plain HTML/CSS/JS

Use this skill when you need:
- Multiple components
- State management
- shadcn/ui component library
- Complex interactivity
- Routing

## Quick Reference

| Task | Command/Action |
|------|----------------|
| Initialize | `./scripts/init-artifact.sh name` |
| Develop | `npm run dev` |
| Build | `npm run build` |
| Bundle | `./scripts/bundle-artifact.sh` |
| Output | `bundle.html` (self-contained) |

---

*Skill Version: 1.0*
*Source: Anthropic web-artifacts-builder skill*

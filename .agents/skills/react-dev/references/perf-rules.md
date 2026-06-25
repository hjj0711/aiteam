# React Performance Rules

70+ rules adapted from Vercel Engineering's React Best Practices, organized by priority.

## Priority Index

| Priority | Category | Prefix | When it matters |
|---|---|---|---|
| 1 — CRITICAL | Eliminating Waterfalls | `async-` | Any time `await` is followed by independent `await` |
| 2 — CRITICAL | Bundle Size Optimization | `bundle-` | First-load JS, route-level imports, third-party libs |
| 3 — HIGH | Server-Side Performance | `server-` | RSC, Server Actions, API routes, SSR |
| 4 — MEDIUM-HIGH | Client-Side Data Fetching | `client-` | SWR / TanStack Query / raw fetch in hooks |
| 5 — MEDIUM | Re-render Optimization | `rerender-` | High-frequency state updates, parent-child fan-out |
| 6 — MEDIUM | Rendering Performance | `rendering-` | Long lists, animations, hydration |
| 7 — LOW-MEDIUM | JavaScript Performance | `js-` | Hot loops, frequent allocations |
| 8 — LOW | Advanced Patterns | `advanced-` | Effect-event integration, stable refs |

---

## 1. Eliminating Waterfalls (CRITICAL)

> Waterfalls are the #1 performance killer — every sequential `await` adds full network latency.

### Cheap conditions before await

Check sync conditions (props, env, hardcoded flags) before awaiting remote data.

```ts
// INCORRECT
async function Page({ id }: { id: string }) {
  const flag = await getFlag("show-page");
  if (!flag || !id) return null;
  const data = await getData(id);
}

// CORRECT — short-circuit on cheap sync condition first
async function Page({ id }: { id: string }) {
  if (!id) return null;
  const flag = await getFlag("show-page");
  if (!flag) return null;
  const data = await getData(id);
}
```

### Defer awaits until used

Move `await` into the branch that uses the data.

```ts
// INCORRECT — awaits before deciding
const user = await getUser(id);
if (mode === "guest") return renderGuest();
return renderUser(user);

// CORRECT
if (mode === "guest") return renderGuest();
const user = await getUser(id);
return renderUser(user);
```

### Promise.all for independent work

```ts
// INCORRECT — sequential
const user = await getUser(id);
const posts = await getPosts(id);
const followers = await getFollowers(id);

// CORRECT — parallel
const [user, posts, followers] = await Promise.all([
  getUser(id), getPosts(id), getFollowers(id),
]);
```

### Partial dependencies — start early, await late

```ts
const userP = getUser(id);
const postsP = getPosts(id);
const profile = await getProfile(id);
if (profile.private) return null;
const [user, posts] = await Promise.all([userP, postsP]);
```

### Suspense for streaming

Push `<Suspense>` boundaries close to the data so the page paints what it can while slower sub-trees stream in. Reserve space (skeleton or `min-height`) to prevent layout shift.

### Server Components: parallel through composition

```tsx
// INCORRECT — sibling awaits run sequentially inside one component
export default async function Page() {
  const user = await getUser();
  const cart = await getCart();
  return <View user={user} cart={cart} />;
}

// CORRECT — split into children, React runs them in parallel
export default async function Page() {
  return (
    <View>
      <UserSection />
      <CartSection />
    </View>
  );
}
```

---

## 2. Bundle Size Optimization (CRITICAL)

### Direct imports, not barrels

Barrel `index.ts` files force the bundler to walk the entire module graph even when tree-shaking removes most of it. Direct imports save 200-800ms of first-load JS.

```ts
// INCORRECT
import { Button, Card, Modal } from "@/components";

// CORRECT
import { Button } from "@/components/Button";
import { Card } from "@/components/Card";
import { Modal } from "@/components/Modal";
```

Next.js 13.5+ has `optimizePackageImports` in `next.config` that automates this for listed packages — use it.

### Statically analyzable paths

```ts
// INCORRECT — defeats bundler analysis
const mod = await import(`./pages/${name}`);

// CORRECT — explicit per branch
const mod = name === "home" ? await import("./pages/home") : await import("./pages/about");
```

### Dynamic imports for heavy components

```tsx
import dynamic from "next/dynamic";
const HeavyChart = dynamic(() => import("./HeavyChart"), {
  loading: () => <Skeleton />,
  ssr: false, // when client-only
});
```

### Defer third-party scripts

Load analytics, logging, support widgets AFTER hydration. Use `next/script` with `strategy="afterInteractive"` (default) or `"lazyOnload"`.

### Conditional module loading

```tsx
if (user.role === "admin") {
  const { AdminPanel } = await import("./admin/AdminPanel");
}
```

### Preload on hover/focus

Trigger `<link rel="preload">` or `import()` on hover so the bundle is in cache by the time the user clicks.

---

## 3. Server-Side Performance (HIGH)

### Authenticate Server Actions like API routes

Every `"use server"` function is a public endpoint. Authenticate AND authorize inside the action.

### `React.cache()` for per-request deduplication

```ts
import { cache } from "react";
export const getUser = cache(async (id: string) => {
  return db.user.findUnique({ where: { id } });
});
```

### LRU cache for cross-request data

For data that does NOT change per request (config, lookup tables), cache outside React.

### Avoid duplicate serialization in RSC props

When a Server Component renders the same data into multiple Client Components, the data is serialized once per consumer. Lift the Client Component up and pass children.

### Hoist static I/O to module scope

```ts
const fontData = readFileSync(fontPath); // runs once at module load
export async function Page() { return <Banner font={fontData} />; }
```

### No mutable module-level state in RSC/SSR

Module state on the server is shared across all requests. Use request-scoped storage instead.

### Minimize data passed to Client Components

Only serialize what the Client needs. Strip fields, paginate, project columns at the DB layer.

### Use `after()` for non-blocking work (Next.js 15+)

```ts
import { after } from "next/server";
export async function GET() {
  const data = await getData();
  after(() => logAnalytics(data));
  return Response.json(data);
}
```

### Parallelize nested fetches

```ts
const users = await getUsers();
const enriched = await Promise.all(
  users.map(async (u) => ({ ...u, posts: await getPostsFor(u.id) })),
);
```

---

## 4. Client-Side Data Fetching (MEDIUM-HIGH)

### SWR / TanStack Query for deduplication

Multiple components calling `useUser(id)` should share one network request. Never roll your own `useEffect` + `fetch` for shared data.

### Deduplicate global event listeners

```tsx
// INCORRECT — every component adds its own
useEffect(() => {
  window.addEventListener("scroll", handler);
  return () => window.removeEventListener("scroll", handler);
}, []);

// CORRECT — single shared listener via a hook + global subject
```

### Passive listeners for scroll

```ts
window.addEventListener("scroll", handler, { passive: true });
```

### localStorage: version + minimize

- Always store a `version` field; bump on schema change and migrate or discard old data.
- Keep payloads small — `localStorage` is synchronous and blocks the main thread.

---

## 5. Re-render Optimization (MEDIUM)

### Don't subscribe to state used only in callbacks

```tsx
// INCORRECT — re-renders every time count changes
const count = useStore((s) => s.count);
const handler = () => doSomething(count);

// CORRECT — read once on call
const handler = () => { doSomething(useStore.getState().count); };
```

### Extract expensive work into memoized components

```tsx
const Heavy = memo(function Heavy({ items }: { items: Item[] }) {
  return <Chart data={transform(items)} />;
});
```

### Hoist default non-primitive props

```tsx
// INCORRECT — new array each render breaks memo
<List items={items ?? []} />

// CORRECT
const EMPTY: Item[] = [];
<List items={items ?? EMPTY} />
```

### Primitive dependencies in effects

```tsx
// INCORRECT — new object identity every render
useEffect(() => {}, [{ id, name }]);

// CORRECT — primitives
useEffect(() => {}, [id, name]);
```

### Subscribe to derived booleans, not raw values

```tsx
// INCORRECT — re-renders for any cart change
const cart = useStore((s) => s.cart);
const hasItems = cart.length > 0;

// CORRECT — re-renders only when emptiness flips
const hasItems = useStore((s) => s.cart.length > 0);
```

### Derive during render, never via `useEffect`

```tsx
// INCORRECT
const [full, setFull] = useState("");
useEffect(() => setFull(`${first} ${last}`), [first, last]);

// CORRECT
const full = `${first} ${last}`;
```

### Functional `setState` for stable callbacks

```tsx
const increment = useCallback(() => setCount((c) => c + 1), []);
```

### Lazy state initializer for expensive values

```tsx
const [tree] = useState(() => parseTree(largeInput));
```

### Avoid memo for simple primitives

`useMemo(() => x + 1, [x])` is overhead. Memo earns its keep on object identity and expensive computation.

### Split hooks with independent deps

```tsx
// INCORRECT — both selectors re-run if either source changes
const { a, b } = useSomething(source1, source2);

// CORRECT
const a = useA(source1);
const b = useB(source2);
```

### Move interaction logic into event handlers

Event handlers run only on the user action — `useEffect` re-runs whenever deps change.

### `startTransition` for non-urgent updates

```tsx
const [pending, startTransition] = useTransition();
startTransition(() => setFilters(newFilters));
```

### `useDeferredValue` for expensive renders

```tsx
const deferredQuery = useDeferredValue(query);
const results = useMemo(() => expensiveSearch(deferredQuery), [deferredQuery]);
```

### `useRef` for transient frequent values

For values that change often but should not trigger re-render (timestamps, last-key, accumulators).

### Don't define components inside components

Each render makes a new component type, defeating reconciliation and unmounting children.

---

## 6. Rendering Performance (MEDIUM)

### Animate the wrapper, not the SVG

Transforming a `<div>` wrapper around an SVG is GPU-accelerated; transforming the SVG itself triggers paint.

### `content-visibility: auto` for long lists

```css
.row { content-visibility: auto; contain-intrinsic-size: auto 80px; }
```

Browser skips offscreen rendering — major win for lists with hundreds of rows.

### Hoist static JSX

```tsx
const STATIC_HEADER = <h1>Title</h1>;
function Page() { return <>{STATIC_HEADER}<Body /></>; }
```

### SVG: reduce coordinate precision

`d="M10.123456,20.654321"` → `d="M10.12,20.65"`. Each digit costs bytes; visual difference is sub-pixel.

### Hydration no-flicker via inline script

For values needed before hydration (theme, locale), inline a `<script>` that sets `document.documentElement.dataset.*`.

### Suppress expected hydration mismatches narrowly

```tsx
<time suppressHydrationWarning>{new Date().toLocaleString()}</time>
```

Use ONLY for known-divergent leaf nodes — never on a tree containing children.

### `<Activity>` for show/hide instead of mount/unmount (React 19)

```tsx
<Activity mode="visible|hidden">
```

Keeps tree state and effects mounted but hides — cheaper than unmount/remount for tabs and accordions.

### Ternary over `&&` for conditional render

```tsx
// INCORRECT — `0` renders as text node
{count && <Badge>{count}</Badge>}

// CORRECT
{count > 0 ? <Badge>{count}</Badge> : null}
```

### React DOM resource hints

```tsx
import { preload, preconnect } from "react-dom";
preload("/api/critical", { as: "fetch" });
preconnect("https://api.example.com");
```

### `defer` / `async` on `<script>` tags

`defer` for ordered execution after DOMContentLoaded; `async` for fire-and-forget.

---

## 7. JavaScript Performance (LOW-MEDIUM)

- **Batch DOM/CSS changes** — apply via class swap or `cssText`, not property-by-property
- **`Map` for repeated lookups** — O(1) vs O(n) linear scan
- **Cache property access in loops** — `const len = arr.length`
- **Memoize pure functions** — module-level `Map<key, result>`
- **Cache `localStorage` reads** — sync API; one read per render
- **Combine `filter().map()` into one pass** — `flatMap` or single `for`
- **Check array length first** before expensive comparisons
- **Early return** from functions
- **Hoist RegExp** out of loops — compilation is not free
- **Loop for min/max** instead of `sort()` — O(n) vs O(n log n)
- **`Set`/`Map` for membership** — O(1) vs `Array.includes` O(n)
- **`toSorted()` over mutation** when immutability matters
- **`flatMap` to map and filter in one pass**
- **`requestIdleCallback`** for non-critical work

---

## 8. Advanced Patterns (LOW)

### `useEffectEvent` deps

Values from `useEffectEvent` are stable — do NOT add them to effect deps.

### Event handler refs

For stable callbacks passed to memoized children:

```tsx
const handlerRef = useRef(handler);
useEffect(() => { handlerRef.current = handler; });
const stable = useCallback((arg: unknown) => handlerRef.current(arg), []);
```

### Init once per app load

For module-level singletons (telemetry, logger), guard with a module-scope flag — not `useEffect`.

### `useLatest` for stable callback refs

```tsx
function useLatest<T>(value: T) {
  const ref = useRef(value);
  ref.current = value;
  return ref;
}
```

---

## Lighthouse / Web Vitals Mapping

| Metric | Most relevant categories |
|---|---|
| **LCP** (Largest Contentful Paint) | Waterfalls, Bundle Size, Resource Hints |
| **INP** (Interaction to Next Paint) | Re-render, Rendering, JavaScript |
| **CLS** (Cumulative Layout Shift) | Rendering (Suspense placement, image dimensions) |
| **TBT** (Total Blocking Time) | Bundle Size, JavaScript, Defer Third-Party |
| **FID** (legacy) | Bundle Size, Hydration |

## Automated Tools

- **Next.js 13.5+ Optimize Package Imports** — barrel import optimization
- **React Compiler** (canary) — auto-memoization (when it ships, demote manual `rerender-*` rules)
- **Turbopack** — faster builds, better tree-shaking
- **Bundle Analyzer** (`@next/bundle-analyzer`) — visualize first-load JS

## Attribution

Adapted from Vercel Labs `react-best-practices` skill (MIT License, copyright Vercel Engineering, v1.0.0 January 2026).
Source: https://github.com/vercel-labs/agent-skills/tree/main/skills/react-best-practices

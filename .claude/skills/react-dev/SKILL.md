---
name: react-dev
description: React 18/19 development — component architecture, hooks, Server/Client Components, data fetching, forms, state management, performance optimization, error handling, async UI states, security, accessibility, and testing patterns. Use when writing, reviewing, or refactoring React/Next.js components, hooks, pages, or state management. Also use when diagnosing performance issues, designing component trees, choosing state strategies, implementing forms, setting up data fetching, or handling loading/error/empty states.
---

# React Development

Idiomatic React 18/19 patterns covering the full development cycle — from component design to production optimization.

## When to Activate

- Writing or modifying React function components, custom hooks, or component trees
- Designing state shape, data flow, or component composition
- Choosing between local state, context, and external stores
- Working with Server Components / Client Components (Next.js App Router, RSC)
- Implementing forms, data fetching, or real-time updates
- Handling async UI states (loading, empty, error, success)
- Diagnosing performance issues (slow renders, waterfalls, bundle size)
- Reviewing JSX/TSX for correctness, accessibility, or security issues

## Core Principles

### 1. Render is a pure function of props and state

Derive values during render. Storing derived data in `useEffect` adds a render cycle, can desync, and obscures data flow.

```tsx
// Good — derive during render
function Cart({ items }: { items: CartItem[] }) {
  const total = items.reduce((sum, i) => sum + i.price * i.qty, 0);
  return <span>{formatMoney(total)}</span>;
}

// Bad — derived state in useEffect
function Cart({ items }: { items: CartItem[] }) {
  const [total, setTotal] = useState(0);
  useEffect(() => {
    setTotal(items.reduce((sum, i) => sum + i.price * i.qty, 0));
  }, [items]);
  return <span>{formatMoney(total)}</span>;
}
```

### 2. Side effects outside render

Effects, mutations, subscriptions, and network calls live in event handlers or `useEffect` — never in the render body itself.

### 3. Composition over configuration

React has no inheritance model. Compose via `children`, render props, or component props. Avoid deep prop drilling (>2 levels) — lift state or use composition instead.

### 4. Don't memoize by default

`useMemo` and `useCallback` have a cost. Only add them when a profiler or dependency chain proves they matter. React Compiler (in canary) will eventually automate this. The exceptions: stable refs for memoized children, and expensive computations you can measure.

## Component Architecture

### Page-level: extract logic into hooks

Separate business logic from presentation so each is testable independently. For server-state (data fetching), always use TanStack Query, SWR, or RSC — not raw `useEffect` + `fetch`.

```tsx
// useItems.ts — data fetching with TanStack Query
export function useItems() {
  return useQuery({
    queryKey: ['items'],
    queryFn: itemsApi.getAll,
    staleTime: 5 * 60 * 1000,
  });
}

// ItemsPage.tsx — pure presentation, delegates state to the hook
export function ItemsPage(): JSX.Element {
  const { data: items, isLoading, isError, error, refetch } = useItems();

  if (isLoading) return <Spinner />;
  if (isError) return <ErrorView message={error.message} onRetry={refetch} />;
  if (!items || items.length === 0) return <EmptyState />;

  return <ItemList items={items} />;
}
```

### If you must use raw fetch

When a data library isn't an option, raw fetch must handle three things that `useEffect` + `fetch` alone misses:

1. **Race conditions** — use `AbortController`, ignore stale responses
2. **Caching** — at minimum memoize in a module-level Map; without it every mount re-fetches
3. **Error normalization** — catch, wrap in a structured error, never leave the caller with a raw `TypeError`

This is still a second choice. Prefer TanStack Query / SWR / RSC.

### Define props interfaces explicitly

Always define a named props type, even for simple cases. This enables editor autocompletion, catches typos at build time, and documents the component's contract.

```tsx
interface ItemCardProps {
  item: Item;
  onClick: (id: string) => void;
}

export function ItemCard({ item, onClick }: ItemCardProps): JSX.Element {
  return (
    <div onClick={() => onClick(item.id)}>
      <h3>{item.title}</h3>
    </div>
  );
}
```

### Component size and responsibility

A component should fit on one screen (~100 lines). If it grows beyond that, extract sub-components or a custom hook. Never define components inside other components — each render creates a new type, defeating React's reconciliation.

## State Management Decision Tree

```
Used by one component?
  → useState inside it

Used by parent + a few close descendants?
  → lift to nearest common ancestor

Used across distant branches, low-frequency reads (theme, auth, locale)?
  → React Context (split by concern — one context per domain)

High-frequency updates shared across the tree?
  → external store (Zustand, Jotai)

Derived from a server / needs cache + invalidation?
  → server-state library (TanStack Query, SWR, RSC fetch)

URL-driven state (filters, pagination, search)?
  → URL search params (Next.js: useSearchParams, nuqs)
```

Most pages do not need Context or a global store. Resist abstraction until duplicated lifting becomes painful. When using Context, split it by concern — a change to `ThemeContext` should not re-render consumers of `NotificationsContext`.

## Server / Client Components (RSC)

```tsx
// Server Component — default. Async, never ships JS to client.
export default async function ProductPage({ params }: { params: { id: string } }) {
  const product = await db.product.findUnique({ where: { id: params.id } });
  if (!product) notFound();
  return <ProductView product={product} />;
}

// Client Component — opt in with "use client"
"use client";
export function AddToCartButton({ productId }: { productId: string }) {
  const [pending, startTransition] = useTransition();
  return (
    <button
      disabled={pending}
      onClick={() => startTransition(() => addToCart(productId))}
    >
      {pending ? "Adding..." : "Add to cart"}
    </button>
  );
}
```

**Boundary rules:**
- Server → Client: pass serializable props or `children`. Data is serialized once per consumer — to avoid duplication, lift the Client Component up and pass children.
- Client → Server: invoke Server Actions via `<form action={...}>` or imperatively from event handlers.
- Never `import` a Server Component from a Client Component file — compose them via `children` instead.
- Strip fields at the boundary: only serialize what the Client Component actually needs.

## Data Fetching

### Decision matrix

| Need | Tool |
|---|---|
| Per-request data (Next.js App Router) | RSC `await fetch()` or direct DB query |
| Client-side cache + mutations + invalidation | TanStack Query |
| Lightweight client cache + revalidation | SWR |
| Real-time subscriptions | Server-Sent Events, WebSockets, or subscription API |
| One-off fire-and-forget | `fetch()` in an event handler |

**Never use `useEffect` + raw `fetch` for application data.** It produces race conditions (no cleanup), has zero caching (refires on every mount), no retry, and no Suspense integration. The minimum viable data fetch needs all three: abort on unmount, deduplication across components, and structured error handling. TanStack Query, SWR, and RSC all provide these out of the box.

### Deduplication

Use `React.cache()` for per-request deduplication in Server Components. Multiple components calling `getUser("1")` in the same render = one DB query.

```ts
import { cache } from "react";
export const getUser = cache(async (id: string) => {
  return db.user.findUnique({ where: { id } });
});
```

For client-side, SWR or TanStack Query deduplicate automatically — multiple `useQuery` calls with the same key share one request.

### Data fetching with async state handling

```tsx
export function useItems() {
  return useQuery({
    queryKey: ['items'],
    queryFn: itemsApi.getAll,
    staleTime: 5 * 60 * 1000,
  });
}

// In the component:
function ItemList() {
  const { data, isLoading, isError, error, refetch } = useItems();

  if (isLoading) return <Spinner />;
  if (isError) return <ErrorView message={error.message} onRetry={refetch} />;
  if (!data || data.length === 0) return <EmptyState icon={InboxIcon} title="No items yet" />;

  return data.map(item => <ItemCard key={item.id} item={item} />);
}
```

## Async UI States

Every component that fetches data must handle four states explicitly. A missing state is a bug — it shows as a blank screen or frozen UI to the user.

### The four states

| State | What to render | Key rules |
|---|---|---|
| **Loading** | Skeleton or spinner | Reserve space (`min-height`) to prevent layout shift |
| **Empty** | Illustrated empty state | Provide a clear action (e.g., "Create your first item") |
| **Error** | Error message + retry | Show a human-readable message, not a stack trace. Always offer retry. |
| **Success** | The actual content | The data may still be an empty array — distinguish from the "no results" empty state |

### Pattern: status enum over boolean flags

```tsx
type Status = 'idle' | 'loading' | 'success' | 'error';

// Better than multiple booleans:
// ❌ isLoading, isError, isEmpty — can be in impossible states
// ✅ A single status variable — exactly one state at a time
```

### Suspense placement

Always wrap data-fetching components in `<Suspense>`, even when the component handles its own loading state. The two work together — Suspense enables SSR streaming and the initial shell render, while the component's internal status handles client-side transitions (refetch, filter changes).

```tsx
// page.tsx — Server Component
export default function Page() {
  return (
    <ErrorBoundary fallback={<ErrorView />}>
      <Suspense fallback={<UserSkeleton style={{ minHeight: 200 }} />}>
        <UserDetail id={id} />
      </Suspense>
    </ErrorBoundary>
  );
}

// UserDetail.tsx — Client Component with internal status for refetch/transitions
"use client";
function UserDetail({ id }: { id: string }) {
  const { data, isLoading, isError, refetch } = useQuery(...);
  // Internal status handles client-side transitions (filter change, manual refetch)
  // while the parent <Suspense> handles initial SSR streaming
  if (isLoading) return <Skeleton />;
  ...
}
```

**Rules:**
- `<Suspense>` goes in the parent (Server Component), one boundary per data chunk, close to the source
- The child handles client-side transitions internally (status enum or `isLoading` from TanStack Query)
- Always reserve space in the fallback — set `minHeight` to prevent Cumulative Layout Shift (CLS)
- Never rely solely on internal status without a wrapping `<Suspense>` — you lose SSR streaming

## Error Handling

### Error Boundaries

Error Boundaries catch errors thrown during render, lifecycle methods, and constructors of their children. They do NOT catch errors in event handlers, async code, or Server Components.

Use `react-error-boundary` for a hook-friendly wrapper (the class-based API is still required under the hood):

```tsx
import { ErrorBoundary } from 'react-error-boundary';

function ErrorFallback({ error, resetErrorBoundary }: FallbackProps) {
  return (
    <div role="alert">
      <h2>Something went wrong</h2>
      <p>{error.message}</p>
      <button onClick={resetErrorBoundary}>Try again</button>
    </div>
  );
}

<ErrorBoundary
  FallbackComponent={ErrorFallback}
  onReset={() => { /* reset state */ }}
  onError={(error) => { /* log to service */ }}
>
  <Dashboard />
</ErrorBoundary>
```

**Placement strategy:**
- One at the route root (catch unexpected crashes, prevent white screen)
- One around each independently-loading data chunk (so a sidebar error doesn't take down the main content)
- Wrap third-party components that may throw

### Action errors (Server Actions, form submissions)

Server Actions should return structured results, not throw. This lets the Client Component handle errors gracefully:

```ts
"use server";
export async function updateProfile(formData: FormData): Promise<ActionResult> {
  const session = await getSession();
  if (!session?.user) return { success: false, error: "Not authenticated" };
  try {
    await db.user.update({ where: { id: session.user.id }, data: parse(formData) });
    return { success: true };
  } catch (e) {
    return { success: false, error: "Failed to update profile" };
  }
}
```

### Global error logging

Use a single error-logging hook or utility. Never silently swallow errors — at minimum, log them:

```tsx
function useErrorLog() {
  return useCallback((error: Error, context?: Record<string, unknown>) => {
    console.error(context, error);
    // In production: send to your error service
  }, []);
}
```

## Forms

### React 19 form actions (preferred for new code)

```tsx
"use client";
import { useActionState } from "react";

const initial = { error: null as string | null, success: false };

async function updateUserAction(_prev: typeof initial, formData: FormData) {
  "use server";
  const parsed = UserSchema.safeParse(Object.fromEntries(formData));
  if (!parsed.success) return { error: "Invalid input", success: false };
  await db.user.update({ where: { id: parsed.data.id }, data: parsed.data });
  return { error: null, success: true };
}

export function UserForm() {
  const [state, formAction, pending] = useActionState(updateUserAction, initial);
  return (
    <form action={formAction}>
      <input name="name" required />
      <button type="submit" disabled={pending}>
        {pending ? "Saving..." : "Save"}
      </button>
      {state.error && <p role="alert">{state.error}</p>}
    </form>
  );
}
```

### Complex forms: React Hook Form + Zod

For multi-step forms, dynamic field arrays, or cross-field validation, use a library:

```tsx
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

const schema = z.object({
  email: z.string().email('Invalid email'),
  password: z.string().min(8, 'Must be at least 8 characters'),
});

type FormData = z.infer<typeof schema>;

function LoginForm() {
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<FormData>({
    resolver: zodResolver(schema),
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <input {...register('email')} />
      {errors.email && <span role="alert">{errors.email.message}</span>}
      <input type="password" {...register('password')} />
      {errors.password && <span role="alert">{errors.password.message}</span>}
      <button type="submit" disabled={isSubmitting}>Login</button>
    </form>
  );
}
```

### Controlled vs uncontrolled

Use controlled inputs when the value drives other UI (real-time validation, formatting, search-as-you-type). Use uncontrolled (ref-based or form actions) for simple submit-only forms — less re-rendering overhead.

## Optimistic Updates

```tsx
"use client";
import { useOptimistic } from "react";

export function MessageList({ messages }: { messages: Message[] }) {
  const [optimistic, addOptimistic] = useOptimistic(
    messages,
    (state, newMsg: Message) => [...state, newMsg],
  );

  async function send(formData: FormData) {
    const text = String(formData.get("text"));
    addOptimistic({ id: "pending", text, sender: "me" });
    await saveMessage(text); // rolls back on error
  }

  return (
    <>
      <ul>{optimistic.map(m => <li key={m.id}>{m.text}</li>)}</ul>
      <form action={send}>
        <input name="text" />
        <button type="submit">Send</button>
      </form>
    </>
  );
}
```

## Composition Patterns

### Slot via `children` (default choice)

```tsx
<Layout>
  <Header />
  <Main>{content}</Main>
</Layout>
```

### Named slots

```tsx
<Page header={<Nav />} sidebar={<Filters />}>
  <Results />
</Page>
```

### Compound components (shared state via Context)

```tsx
<Tabs defaultValue="profile">
  <Tabs.List>
    <Tabs.Trigger value="profile">Profile</Tabs.Trigger>
    <Tabs.Trigger value="settings">Settings</Tabs.Trigger>
  </Tabs.List>
  <Tabs.Panel value="profile"><Profile /></Tabs.Panel>
  <Tabs.Panel value="settings"><Settings /></Tabs.Panel>
</Tabs>
```

## Performance

The full 70-rule performance catalog is in [references/perf-rules.md](references/perf-rules.md), organized by priority. Below are the highest-impact rules.

### Critical: eliminate waterfalls

Sequential `await` adds full network latency. Use `Promise.all` for independent work, defer awaits until the branch that uses them, and in Server Components, split parallel fetches into sibling components (React runs them in parallel).

### Critical: bundle size

- **Prefer direct imports over barrel files.** Barrel `index.ts` forces the bundler to walk the entire module graph even when tree-shaking removes most of it.
- Dynamic import heavy components (`next/dynamic` or `React.lazy`)
- Defer third-party scripts (`next/script` with `strategy="lazyOnload"`)

### Medium: re-render optimization

- Don't subscribe to state used only in callbacks — read it imperatively when needed
- Use `startTransition` for non-urgent updates (filtering, tab switches)
- Subscribe to derived booleans, not raw values (`s => s.cart.length > 0`, not `s => s.cart`)
- Always use functional `setState` when new state depends on old
- Use ternary over `&&` to avoid rendering falsy values (`count > 0 ? <Badge /> : null`)

### Medium: rendering

- `content-visibility: auto` for long lists (browser skips offscreen rendering)
- Animate a wrapper `<div>`, not the SVG itself (GPU vs paint)
- Use React 19 `<Activity mode="visible|hidden">` for show/hide instead of mount/unmount for tabs and accordions

## Security

### XSS prevention

React auto-escapes JSX content by default — never bypass it with `dangerouslySetInnerHTML` unless the content is sanitized first (use DOMPurify).

### Server Actions are public endpoints

Every `"use server"` function is an API endpoint. Authenticate AND authorize inside every action — never trust the calling Client Component's gating.

```ts
"use server";
export async function deleteUser(formData: FormData) {
  const session = await getSession();
  if (!session?.user) throw new Error("Unauthorized");
  if (session.user.role !== "admin") throw new Error("Forbidden");
  // ...proceed
}
```

### Avoid leaking secrets to the client

- Server Components can access databases, tokens, and secrets directly — they never ship to the client.
- Client Components receive only serializable props. Never pass tokens, keys, or internal URLs.
- Use `NEXT_PUBLIC_` prefix only for truly public values. Everything else stays server-side.
- Strip sensitive fields at the data layer before serialization.

### CSP and headers

Use `helmet` (Express) or Next.js headers config to set:
- `Content-Security-Policy`
- `X-Content-Type-Options: nosniff`
- `Referrer-Policy: strict-origin-when-cross-origin`

### Third-party dependencies

- Prefer well-maintained, widely-used packages
- Audit `postinstall` scripts in dependencies
- Keep dependencies updated — run `npm audit` regularly

## Accessibility

- Render semantic HTML (`<button>`, `<a>`, `<nav>`, `<main>`) before reaching for `role` attributes.
- Every interactive element must be reachable by keyboard.
- Form inputs must have labels — `<label htmlFor>` or `aria-label` if visually labeled by an icon.
- Manage focus on route changes, modal open/close, and after form submissions.
- Use `axe` or `@axe-core/react` in development to catch issues early.

## Testing

### What to test

Test behavior, not implementation. Prioritize:
1. User interactions (click, type, submit)
2. Async state transitions (loading → success, loading → error)
3. Edge cases (empty data, boundary values, disabled states)
4. Accessibility (labels, roles, keyboard)

### Component test

```tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { Button } from './Button';

describe('Button', () => {
  it('calls onClick when clicked', () => {
    const onClick = vi.fn();
    render(<Button label="Click me" onClick={onClick} />);
    fireEvent.click(screen.getByRole('button', { name: 'Click me' }));
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it('does not call onClick when disabled', () => {
    const onClick = vi.fn();
    render(<Button label="Click" onClick={onClick} disabled />);
    fireEvent.click(screen.getByRole('button'));
    expect(onClick).not.toHaveBeenCalled();
  });
});
```

### Hook test

```tsx
import { renderHook, act } from '@testing-library/react';
import { useCounter } from './useCounter';

describe('useCounter', () => {
  it('increments', () => {
    const { result } = renderHook(() => useCounter());
    act(() => result.current.increment());
    expect(result.current.count).toBe(1);
  });
});
```

### Key principle

Tests verify the contract (what the component does for the user), not the implementation (how it does it). If a refactor breaks no tests but changes internal structure, the tests are good.

## Anti-Patterns

- ❌ **`useEffect` for derived state** — derive during render
- ❌ **Raw `fetch` in `useEffect`/`useCallback` for app data** — use TanStack Query, SWR, or RSC. Raw fetch misses cache, cleanup, and error normalization.
- ❌ **New objects/arrays as default props** — hoist to module scope (`const EMPTY: never[] = []`)
- ❌ **Index as key in lists** — use stable IDs
- ❌ **Direct state mutation** — always use the setter
- ❌ **Prop drilling > 2 levels** — use composition or context
- ❌ **Defining components inside components** — new type every render defeats reconciliation
- ❌ **Multiple booleans for async state** — use a single status enum
- ❌ **`dangerouslySetInnerHTML` without sanitization** — always sanitize with DOMPurify
- ❌ **Silent error swallowing** — at minimum log, ideally surface to the user
- ❌ **Missing loading/empty/error states** — every data-dependent component needs all three
- ❌ **Barrel imports for application code** — use direct imports, let Next.js `optimizePackageImports` handle third-party packages

## Related

- Performance rules: [references/perf-rules.md](references/perf-rules.md) — 70+ rules across 8 priority categories
- External skills: `.agents/skills/react-patterns`, `.agents/skills/react-performance`, `.agents/skills/react-web` (original sources)
- Next.js docs for framework-specific patterns (App Router, Middleware, Route Handlers)

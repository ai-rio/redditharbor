# Next.js Setup Guide for RedditHarbor

**Goal:** Create a Next.js application that reads from your existing Supabase database and provides a customer-facing web interface

**Time:** 4-8 hours for basic setup

**Last Updated:** 2025-11-11

---

## Prerequisites

Before starting, ensure you have:
- [ ] Node.js 18+ installed (`node --version`)
- [ ] npm or pnpm installed
- [ ] Supabase project running (you already have this)
- [ ] Supabase URL and anon key (from Supabase dashboard)
- [ ] Git installed

---

## Step 1: Create Next.js Project

### 1.1 Create New Next.js App

```bash
# Navigate to your RedditHarbor directory
cd /path/to/redditharbor

# Create Next.js app in a new directory
npx create-next-app@latest redditharbor-web

# Answer prompts:
# ✔ Would you like to use TypeScript? … Yes
# ✔ Would you like to use ESLint? … Yes
# ✔ Would you like to use Tailwind CSS? … Yes
# ✔ Would you like to use `src/` directory? … No
# ✔ Would you like to use App Router? … Yes
# ✔ Would you like to customize the default import alias? … No

cd redditharbor-web
```

### 1.2 Verify Installation

```bash
npm run dev
```

Open http://localhost:3000 - you should see the Next.js welcome page.

**Press Ctrl+C to stop the dev server.**

---

## Step 2: Install Dependencies

### 2.1 Install Supabase Client

```bash
npm install @supabase/supabase-js @supabase/auth-helpers-nextjs
```

### 2.2 Install Stripe

```bash
npm install stripe @stripe/stripe-js
```

### 2.3 Install UI Libraries

```bash
# Shadcn UI (optional but recommended for quick UI components)
npx shadcn-ui@latest init

# Answer prompts:
# ✔ Which style would you like to use? › Default
# ✔ Which color would you like to use as base color? › Slate
# ✔ Would you like to use CSS variables for colors? › yes

# Install specific components
npx shadcn-ui@latest add button card badge input label
```

### 2.4 Install Other Utilities

```bash
npm install date-fns clsx tailwind-merge
npm install -D @types/node
```

---

## Step 3: Environment Variables

### 3.1 Create Environment File

```bash
# In redditharbor-web directory
touch .env.local
```

### 3.2 Add Supabase Credentials

```bash
# .env.local
NEXT_PUBLIC_SUPABASE_URL=https://YOUR_PROJECT.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Server-side only (don't expose to client)
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Stripe (get from Stripe dashboard)
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# App URL
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

**Where to find these:**

1. **Supabase URL & Keys:**
   - Go to https://app.supabase.com
   - Select your project
   - Settings → API
   - Copy URL, anon key, and service_role key

2. **Stripe Keys:**
   - Go to https://dashboard.stripe.com/test/apikeys
   - Copy Publishable key and Secret key
   - Webhook secret comes later when you set up webhooks

### 3.3 Add to .gitignore

```bash
# Verify .env.local is in .gitignore
cat .gitignore | grep .env.local
# Should see: .env*.local
```

---

## Step 4: Create Supabase Client

### 4.1 Create Lib Directory

```bash
mkdir -p lib
```

### 4.2 Create Supabase Client for Client Components

```typescript
// lib/supabase/client.ts
import { createBrowserClient } from '@supabase/ssr'

export function createClient() {
  return createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  )
}
```

### 4.3 Create Supabase Client for Server Components

```typescript
// lib/supabase/server.ts
import { createServerClient, type CookieOptions } from '@supabase/ssr'
import { cookies } from 'next/headers'

export function createClient() {
  const cookieStore = cookies()

  return createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        get(name: string) {
          return cookieStore.get(name)?.value
        },
      },
    }
  )
}
```

### 4.4 Create Supabase Client for API Routes

```typescript
// lib/supabase/api.ts
import { createClient } from '@supabase/supabase-js'

// This uses service role key for admin operations
export function createServiceClient() {
  return createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!,
    {
      auth: {
        autoRefreshToken: false,
        persistSession: false
      }
    }
  )
}
```

---

## Step 5: TypeScript Types for Database

### 5.1 Generate Types from Supabase

```bash
# Install Supabase CLI
npm install -g supabase

# Login to Supabase
supabase login

# Link to your project
supabase link --project-ref YOUR_PROJECT_REF

# Generate TypeScript types
supabase gen types typescript --linked > lib/database.types.ts
```

### 5.2 Manual Types (If CLI doesn't work)

```typescript
// lib/database.types.ts
export interface Database {
  public: {
    Tables: {
      opportunities: {
        Row: {
          id: string
          opportunity_id: string
          title: string
          description: string | null
          score: number
          subreddit: string
          comment_count: number
          created_at: string
          url: string | null
        }
        Insert: Omit<Database['public']['Tables']['opportunities']['Row'], 'id' | 'created_at'>
        Update: Partial<Database['public']['Tables']['opportunities']['Insert']>
      }
      problem_metrics: {
        Row: {
          id: string
          opportunity_id: string
          comment_count: number
          trending_score: number
          subreddit_spread: number
          intent_signals: number
          credibility_score: number
          created_at: string
        }
      }
      workflow_results: {
        Row: {
          id: string
          opportunity_id: string
          app_name: string | null
          problem_statement: string | null
          target_users: string | null
          core_functions: any | null
          monetization_model: string | null
          created_at: string
        }
      }
    }
  }
}
```

---

## Step 6: Build Landing Page

### 6.1 Update Homepage

```typescript
// app/page.tsx
import Link from 'next/link'
import { Button } from '@/components/ui/button'

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <div className="max-w-5xl w-full">
        {/* Hero Section */}
        <div className="text-center mb-16">
          <h1 className="text-6xl font-bold mb-6">
            Stop Building Apps
            <br />
            <span className="text-blue-600">Nobody Wants</span>
          </h1>
          <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
            Get Reddit-validated app opportunities with real user demand data.
            See exactly what people are asking for—before you write a line of code.
          </p>
          <div className="flex gap-4 justify-center">
            <Link href="/auth/signup">
              <Button size="lg" className="text-lg px-8">
                Get 5 Free Opportunities →
              </Button>
            </Link>
            <Link href="/pricing">
              <Button size="lg" variant="outline" className="text-lg px-8">
                View Pricing
              </Button>
            </Link>
          </div>
        </div>

        {/* Trust Badges */}
        <div className="grid grid-cols-3 gap-8 text-center border-t pt-12">
          <div>
            <div className="text-3xl font-bold text-blue-600">6,000+</div>
            <div className="text-gray-600">Reddit discussions analyzed</div>
          </div>
          <div>
            <div className="text-3xl font-bold text-blue-600">234</div>
            <div className="text-gray-600">Validated opportunities</div>
          </div>
          <div>
            <div className="text-3xl font-bold text-blue-600">500+</div>
            <div className="text-gray-600">Entrepreneurs using RedditHarbor</div>
          </div>
        </div>
      </div>
    </main>
  )
}
```

### 6.2 Create Layout with Navigation

```typescript
// app/layout.tsx
import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import Link from 'next/link'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'RedditHarbor - Stop Building Apps Nobody Wants',
  description: 'Get Reddit-validated app opportunities with real user demand data.',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <nav className="border-b">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16 items-center">
              <Link href="/" className="text-2xl font-bold">
                RedditHarbor
              </Link>
              <div className="flex gap-6 items-center">
                <Link href="/pricing" className="text-gray-600 hover:text-gray-900">
                  Pricing
                </Link>
                <Link href="/dashboard" className="text-gray-600 hover:text-gray-900">
                  Dashboard
                </Link>
                <Link href="/auth/signin" className="text-gray-600 hover:text-gray-900">
                  Sign In
                </Link>
              </div>
            </div>
          </div>
        </nav>
        {children}
      </body>
    </html>
  )
}
```

---

## Step 7: Build Dashboard (Read Opportunities)

### 7.1 Create Dashboard Page

```typescript
// app/dashboard/page.tsx
import { createClient } from '@/lib/supabase/server'
import { redirect } from 'next/navigation'
import OpportunityCard from '@/components/OpportunityCard'

export default async function Dashboard() {
  const supabase = createClient()

  // Check if user is authenticated
  const { data: { user }, error: authError } = await supabase.auth.getUser()

  if (authError || !user) {
    redirect('/auth/signin')
  }

  // Fetch opportunities (RLS will limit based on user's tier)
  const { data: opportunities, error } = await supabase
    .from('opportunities')
    .select(`
      *,
      problem_metrics(*),
      workflow_results(*)
    `)
    .gte('score', 70)
    .order('score', { ascending: false })
    .limit(50)

  if (error) {
    console.error('Error fetching opportunities:', error)
    return <div>Error loading opportunities</div>
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div className="mb-8">
        <h1 className="text-4xl font-bold mb-2">Your Opportunities</h1>
        <p className="text-gray-600">
          {opportunities?.length || 0} validated app ideas ready to build
        </p>
      </div>

      <div className="grid gap-6">
        {opportunities?.map((opportunity) => (
          <OpportunityCard
            key={opportunity.id}
            opportunity={opportunity}
          />
        ))}
      </div>
    </div>
  )
}
```

### 7.2 Create Opportunity Card Component

```typescript
// components/OpportunityCard.tsx
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import Link from 'next/link'

interface OpportunityCardProps {
  opportunity: {
    id: string
    title: string
    description: string | null
    score: number
    subreddit: string
    comment_count: number
    problem_metrics?: {
      comment_count: number
      trending_score: number
      subreddit_spread: number
      intent_signals: number
    }[]
    workflow_results?: {
      app_name: string | null
      problem_statement: string | null
    }[]
  }
}

export default function OpportunityCard({ opportunity }: OpportunityCardProps) {
  const metrics = opportunity.problem_metrics?.[0]
  const profile = opportunity.workflow_results?.[0]

  return (
    <Card className="hover:shadow-lg transition-shadow">
      <CardHeader>
        <div className="flex justify-between items-start">
          <div className="flex-1">
            <CardTitle className="text-xl mb-2">
              <Link href={`/opportunities/${opportunity.id}`} className="hover:text-blue-600">
                {profile?.app_name || opportunity.title}
              </Link>
            </CardTitle>
            <p className="text-sm text-gray-600">
              {profile?.problem_statement || opportunity.description}
            </p>
          </div>
          <Badge
            variant={opportunity.score >= 85 ? 'default' : 'secondary'}
            className="text-lg px-3 py-1"
          >
            {opportunity.score}
          </Badge>
        </div>
      </CardHeader>

      <CardContent>
        {/* Credibility Metrics */}
        {metrics && (
          <div className="grid grid-cols-4 gap-4 mb-4 p-4 bg-gray-50 rounded">
            <div>
              <div className="text-2xl font-bold">{metrics.comment_count}</div>
              <div className="text-xs text-gray-600">Discussions</div>
            </div>
            <div>
              <div className="text-2xl font-bold">{metrics.trending_score}%</div>
              <div className="text-xs text-gray-600">Trending</div>
            </div>
            <div>
              <div className="text-2xl font-bold">{metrics.subreddit_spread}</div>
              <div className="text-xs text-gray-600">Communities</div>
            </div>
            <div>
              <div className="text-2xl font-bold">{metrics.intent_signals}</div>
              <div className="text-xs text-gray-600">Intent Signals</div>
            </div>
          </div>
        )}

        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-500">r/{opportunity.subreddit}</span>
          <Link
            href={`/opportunities/${opportunity.id}`}
            className="text-sm text-blue-600 hover:underline"
          >
            View Details →
          </Link>
        </div>
      </CardContent>
    </Card>
  )
}
```

---

## Step 8: Add Authentication

### 8.1 Create Sign Up Page

```typescript
// app/auth/signup/page.tsx
'use client'

import { useState } from 'react'
import { createClient } from '@/lib/supabase/client'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useRouter } from 'next/navigation'

export default function SignUp() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')
  const router = useRouter()
  const supabase = createClient()

  async function handleSignUp(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setMessage('')

    const { data, error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        emailRedirectTo: `${location.origin}/auth/callback`,
      },
    })

    if (error) {
      setMessage(error.message)
    } else {
      setMessage('Check your email to confirm your account!')
    }

    setLoading(false)
  }

  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="w-full max-w-md space-y-8 p-8">
        <div>
          <h2 className="text-3xl font-bold">Create your account</h2>
          <p className="mt-2 text-gray-600">
            Start finding validated app opportunities
          </p>
        </div>

        <form onSubmit={handleSignUp} className="space-y-6">
          <div>
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="mt-1"
            />
          </div>

          <div>
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={6}
              className="mt-1"
            />
          </div>

          {message && (
            <div className={`p-3 rounded ${message.includes('error') ? 'bg-red-50 text-red-800' : 'bg-green-50 text-green-800'}`}>
              {message}
            </div>
          )}

          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? 'Creating account...' : 'Sign Up'}
          </Button>
        </form>

        <p className="text-center text-sm text-gray-600">
          Already have an account?{' '}
          <a href="/auth/signin" className="text-blue-600 hover:underline">
            Sign in
          </a>
        </p>
      </div>
    </div>
  )
}
```

### 8.2 Create Sign In Page

```typescript
// app/auth/signin/page.tsx
'use client'

import { useState } from 'react'
import { createClient } from '@/lib/supabase/client'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useRouter } from 'next/navigation'

export default function SignIn() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')
  const router = useRouter()
  const supabase = createClient()

  async function handleSignIn(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setMessage('')

    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password,
    })

    if (error) {
      setMessage(error.message)
      setLoading(false)
    } else {
      router.push('/dashboard')
      router.refresh()
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="w-full max-w-md space-y-8 p-8">
        <div>
          <h2 className="text-3xl font-bold">Welcome back</h2>
          <p className="mt-2 text-gray-600">
            Sign in to access your opportunities
          </p>
        </div>

        <form onSubmit={handleSignIn} className="space-y-6">
          <div>
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="mt-1"
            />
          </div>

          <div>
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="mt-1"
            />
          </div>

          {message && (
            <div className="p-3 rounded bg-red-50 text-red-800">
              {message}
            </div>
          )}

          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? 'Signing in...' : 'Sign In'}
          </Button>
        </form>

        <p className="text-center text-sm text-gray-600">
          Don't have an account?{' '}
          <a href="/auth/signup" className="text-blue-600 hover:underline">
            Sign up
          </a>
        </p>
      </div>
    </div>
  )
}
```

### 8.3 Create Auth Callback Route

```typescript
// app/auth/callback/route.ts
import { createClient } from '@/lib/supabase/server'
import { NextResponse } from 'next/server'

export async function GET(request: Request) {
  const requestUrl = new URL(request.url)
  const code = requestUrl.searchParams.get('code')

  if (code) {
    const supabase = createClient()
    await supabase.auth.exchangeCodeForSession(code)
  }

  // Redirect to dashboard after email confirmation
  return NextResponse.redirect(new URL('/dashboard', request.url))
}
```

---

## Step 9: Create Pricing Page

```typescript
// app/pricing/page.tsx
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Check } from 'lucide-react'

const tiers = [
  {
    name: 'Free',
    price: '$0',
    description: 'Perfect for exploring',
    features: [
      '5 opportunities/month',
      'Basic scoring',
      'Community access',
    ],
    cta: 'Get Started Free',
    href: '/auth/signup',
  },
  {
    name: 'Starter',
    price: '$49',
    priceId: 'price_starter_monthly', // Replace with actual Stripe price ID
    description: 'For indie hackers',
    features: [
      '20 opportunities/month',
      'Full scoring breakdown',
      'AI profiling (top 5)',
      'Email alerts',
    ],
    cta: 'Start Free Trial',
    href: '/auth/signup?plan=starter',
    popular: true,
  },
  {
    name: 'Pro',
    price: '$199',
    priceId: 'price_pro_monthly',
    description: 'For serious builders',
    features: [
      '100 opportunities/month',
      'Full AI profiling',
      'API access',
      'Trend reports',
      'Priority support',
    ],
    cta: 'Start Free Trial',
    href: '/auth/signup?plan=pro',
  },
  {
    name: 'Agency',
    price: '$999',
    priceId: 'price_agency_monthly',
    description: 'For teams & agencies',
    features: [
      'Unlimited opportunities',
      'Unlimited AI profiling',
      'Full API access',
      'White-label reports',
      'Strategy calls',
    ],
    cta: 'Book a Demo',
    href: '/contact',
  },
]

export default function Pricing() {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24">
      <div className="text-center mb-16">
        <h1 className="text-5xl font-bold mb-4">Plans for Every Stage</h1>
        <p className="text-xl text-gray-600">
          Start free, upgrade as you grow
        </p>
      </div>

      <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
        {tiers.map((tier) => (
          <Card
            key={tier.name}
            className={tier.popular ? 'border-blue-600 border-2 relative' : ''}
          >
            {tier.popular && (
              <div className="absolute -top-4 left-1/2 -translate-x-1/2">
                <span className="bg-blue-600 text-white px-4 py-1 rounded-full text-sm font-semibold">
                  Most Popular
                </span>
              </div>
            )}

            <CardHeader>
              <CardTitle className="text-2xl">{tier.name}</CardTitle>
              <CardDescription>{tier.description}</CardDescription>
              <div className="mt-4">
                <span className="text-4xl font-bold">{tier.price}</span>
                {tier.price !== '$0' && <span className="text-gray-600">/month</span>}
              </div>
            </CardHeader>

            <CardContent>
              <ul className="space-y-3">
                {tier.features.map((feature) => (
                  <li key={feature} className="flex items-start">
                    <Check className="h-5 w-5 text-green-600 mr-2 flex-shrink-0 mt-0.5" />
                    <span className="text-sm">{feature}</span>
                  </li>
                ))}
              </ul>
            </CardContent>

            <CardFooter>
              <Button
                asChild
                className="w-full"
                variant={tier.popular ? 'default' : 'outline'}
              >
                <a href={tier.href}>{tier.cta}</a>
              </Button>
            </CardFooter>
          </Card>
        ))}
      </div>

      <div className="mt-16 text-center">
        <p className="text-sm text-gray-600">
          ✅ 30-day money-back guarantee • ✅ No credit card required for free tier • ✅ Cancel anytime
        </p>
      </div>
    </div>
  )
}
```

---

## Step 10: Test Locally

### 10.1 Start Development Server

```bash
npm run dev
```

### 10.2 Test Pages

1. **Landing page:** http://localhost:3000
   - Should see hero section and trust badges

2. **Sign up:** http://localhost:3000/auth/signup
   - Create test account
   - Check email for verification link

3. **Sign in:** http://localhost:3000/auth/signin
   - Sign in with test account

4. **Dashboard:** http://localhost:3000/dashboard
   - Should see opportunities from your Supabase database
   - If you see "Error loading opportunities", check:
     - Supabase credentials in .env.local
     - RLS policies (might need to disable temporarily for testing)
     - Database has data

5. **Pricing:** http://localhost:3000/pricing
   - Should see 4 tiers

### 10.3 Debug Supabase Connection

```typescript
// Add this to app/test/page.tsx for debugging
import { createClient } from '@/lib/supabase/server'

export default async function TestPage() {
  const supabase = createClient()

  const { data, error } = await supabase
    .from('opportunities')
    .select('*')
    .limit(5)

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">Database Test</h1>
      {error && (
        <div className="bg-red-50 text-red-800 p-4 rounded mb-4">
          Error: {error.message}
        </div>
      )}
      {data && (
        <pre className="bg-gray-50 p-4 rounded overflow-auto">
          {JSON.stringify(data, null, 2)}
        </pre>
      )}
    </div>
  )
}
```

Navigate to http://localhost:3000/test to see if Supabase connection works.

---

## Step 11: Customize Design (Optional)

### 11.1 Update Colors

```typescript
// tailwind.config.ts
import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Customize your brand colors
        primary: {
          50: '#eff6ff',
          100: '#dbeafe',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
        },
      },
    },
  },
  plugins: [],
}
export default config
```

### 11.2 Add Logo

```typescript
// components/Logo.tsx
export default function Logo() {
  return (
    <div className="flex items-center gap-2">
      <div className="w-8 h-8 bg-blue-600 rounded-lg" />
      <span className="text-2xl font-bold">RedditHarbor</span>
    </div>
  )
}
```

---

## Step 12: Next Steps

You now have:
- ✅ Next.js app running locally
- ✅ Connected to Supabase
- ✅ Landing page, dashboard, auth pages
- ✅ Reading opportunities from database

**What's next:**
1. **Add Stripe integration** - See `api-examples.md`
2. **Deploy to Vercel** - See `deployment-guide.md`
3. **Set up Python cron jobs** - See `deployment-guide.md`
4. **Polish UI** - Add more pages, improve design
5. **Launch!** 🚀

---

## Troubleshooting

### Issue: "Invalid JWT" or Auth errors

**Solution:** Check environment variables:
```bash
# Make sure these are correct in .env.local
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co  # No trailing slash
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...              # Full key
```

### Issue: "No data showing in dashboard"

**Possible causes:**
1. **RLS policies blocking access:**
   - Go to Supabase → Authentication → Policies
   - Temporarily disable RLS for testing: `ALTER TABLE opportunities DISABLE ROW LEVEL SECURITY;`
   - Re-enable after testing: `ALTER TABLE opportunities ENABLE ROW LEVEL SECURITY;`

2. **Database is empty:**
   - Run your Python collection script to populate data
   - Verify data exists in Supabase dashboard

3. **Wrong table name:**
   - Check your table name in Supabase matches code (`opportunities`)

### Issue: Build errors with Supabase

**Solution:** Update package versions:
```bash
npm update @supabase/supabase-js @supabase/auth-helpers-nextjs
```

---

## Resources

- **Next.js Docs:** https://nextjs.org/docs
- **Supabase Docs:** https://supabase.com/docs
- **Shadcn UI:** https://ui.shadcn.com
- **Tailwind CSS:** https://tailwindcss.com/docs

---

**Document Status:** Complete
**Last Updated:** 2025-11-11
**Next:** Read `deployment-guide.md` to deploy to production

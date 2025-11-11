# API Routes Examples for RedditHarbor

**Complete code examples for all Next.js API routes**

**Last Updated:** 2025-11-11

---

## Overview

This document provides copy-paste ready code for all API routes in the RedditHarbor Next.js application.

**Directory Structure:**
```
app/api/
├── opportunities/
│   ├── route.ts              # GET /api/opportunities
│   └── [id]/route.ts         # GET /api/opportunities/:id
├── user/
│   ├── route.ts              # GET /api/user
│   └── subscription/route.ts # GET /api/user/subscription
├── checkout/
│   └── route.ts              # POST /api/checkout
└── webhooks/
    └── stripe/route.ts       # POST /api/webhooks/stripe
```

---

## 1. Opportunities API

### GET /api/opportunities

**Returns list of opportunities filtered by user's subscription tier**

```typescript
// app/api/opportunities/route.ts
import { createClient } from '@/lib/supabase/server'
import { NextResponse } from 'next/server'

export async function GET(request: Request) {
  try {
    const supabase = createClient()

    // Get authenticated user
    const { data: { user }, error: authError } = await supabase.auth.getUser()

    if (authError || !user) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      )
    }

    // Get user's subscription tier
    const { data: subscription } = await supabase
      .from('subscriptions')
      .select('tier')
      .eq('user_id', user.id)
      .single()

    const tier = subscription?.tier || 'free'

    // Determine limit based on tier
    const limits = {
      free: 5,
      starter: 20,
      pro: 100,
      agency: 1000,
    }
    const limit = limits[tier as keyof typeof limits] || 5

    // Parse query parameters
    const { searchParams } = new URL(request.url)
    const minScore = searchParams.get('min_score') || '70'
    const subreddit = searchParams.get('subreddit')

    // Build query
    let query = supabase
      .from('opportunities')
      .select(`
        *,
        problem_metrics(*),
        workflow_results(*)
      `)
      .gte('score', parseInt(minScore))
      .order('score', { ascending: false })
      .limit(limit)

    // Add subreddit filter if provided
    if (subreddit) {
      query = query.eq('subreddit', subreddit)
    }

    const { data: opportunities, error } = await query

    if (error) {
      console.error('Database error:', error)
      return NextResponse.json(
        { error: 'Failed to fetch opportunities' },
        { status: 500 }
      )
    }

    return NextResponse.json({
      opportunities,
      tier,
      limit,
      count: opportunities?.length || 0,
    })

  } catch (error) {
    console.error('API error:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}
```

### GET /api/opportunities/[id]

**Returns single opportunity with full details**

```typescript
// app/api/opportunities/[id]/route.ts
import { createClient } from '@/lib/supabase/server'
import { NextResponse } from 'next/server'

export async function GET(
  request: Request,
  { params }: { params: { id: string } }
) {
  try {
    const supabase = createClient()

    // Get authenticated user
    const { data: { user }, error: authError } = await supabase.auth.getUser()

    if (authError || !user) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      )
    }

    // Fetch opportunity with all related data
    const { data: opportunity, error } = await supabase
      .from('opportunities')
      .select(`
        *,
        problem_metrics(*),
        workflow_results(*)
      `)
      .eq('id', params.id)
      .single()

    if (error || !opportunity) {
      return NextResponse.json(
        { error: 'Opportunity not found' },
        { status: 404 }
      )
    }

    return NextResponse.json(opportunity)

  } catch (error) {
    console.error('API error:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}
```

---

## 2. User API

### GET /api/user

**Returns current user profile and subscription status**

```typescript
// app/api/user/route.ts
import { createClient } from '@/lib/supabase/server'
import { NextResponse } from 'next/server'

export async function GET(request: Request) {
  try {
    const supabase = createClient()

    // Get authenticated user
    const { data: { user }, error: authError } = await supabase.auth.getUser()

    if (authError || !user) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      )
    }

    // Get user's subscription
    const { data: subscription } = await supabase
      .from('subscriptions')
      .select('*')
      .eq('user_id', user.id)
      .single()

    // Get usage stats (opportunities viewed this month)
    const startOfMonth = new Date()
    startOfMonth.setDate(1)
    startOfMonth.setHours(0, 0, 0, 0)

    const { count: viewedCount } = await supabase
      .from('opportunity_views')
      .select('*', { count: 'exact', head: true })
      .eq('user_id', user.id)
      .gte('viewed_at', startOfMonth.toISOString())

    return NextResponse.json({
      user: {
        id: user.id,
        email: user.email,
        created_at: user.created_at,
      },
      subscription: subscription || {
        tier: 'free',
        status: 'active',
      },
      usage: {
        opportunities_viewed: viewedCount || 0,
        month: startOfMonth.toISOString(),
      },
    })

  } catch (error) {
    console.error('API error:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}
```

### GET /api/user/subscription

**Returns detailed subscription information**

```typescript
// app/api/user/subscription/route.ts
import { createClient } from '@/lib/supabase/server'
import { NextResponse } from 'next/server'
import Stripe from 'stripe'

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, {
  apiVersion: '2023-10-16',
})

export async function GET(request: Request) {
  try {
    const supabase = createClient()

    // Get authenticated user
    const { data: { user }, error: authError } = await supabase.auth.getUser()

    if (authError || !user) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      )
    }

    // Get subscription from database
    const { data: subscription } = await supabase
      .from('subscriptions')
      .select('*')
      .eq('user_id', user.id)
      .single()

    if (!subscription || !subscription.stripe_subscription_id) {
      return NextResponse.json({
        tier: 'free',
        status: 'active',
        can_upgrade: true,
      })
    }

    // Get full details from Stripe
    const stripeSubscription = await stripe.subscriptions.retrieve(
      subscription.stripe_subscription_id
    )

    return NextResponse.json({
      tier: subscription.tier,
      status: stripeSubscription.status,
      current_period_end: new Date(stripeSubscription.current_period_end * 1000).toISOString(),
      cancel_at_period_end: stripeSubscription.cancel_at_period_end,
      can_upgrade: subscription.tier !== 'agency',
      can_downgrade: subscription.tier !== 'free',
    })

  } catch (error) {
    console.error('API error:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}
```

---

## 3. Stripe Checkout API

### POST /api/checkout

**Creates Stripe Checkout session for subscription**

```typescript
// app/api/checkout/route.ts
import { createClient } from '@/lib/supabase/server'
import { NextResponse } from 'next/server'
import Stripe from 'stripe'

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, {
  apiVersion: '2023-10-16',
})

export async function POST(request: Request) {
  try {
    const supabase = createClient()

    // Get authenticated user
    const { data: { user }, error: authError } = await supabase.auth.getUser()

    if (authError || !user) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      )
    }

    // Parse request body
    const { priceId, tier } = await request.json()

    if (!priceId || !tier) {
      return NextResponse.json(
        { error: 'Missing priceId or tier' },
        { status: 400 }
      )
    }

    // Check if user already has a subscription
    const { data: existingSubscription } = await supabase
      .from('subscriptions')
      .select('stripe_customer_id')
      .eq('user_id', user.id)
      .single()

    // Create or retrieve Stripe customer
    let customerId = existingSubscription?.stripe_customer_id

    if (!customerId) {
      const customer = await stripe.customers.create({
        email: user.email!,
        metadata: {
          supabase_user_id: user.id,
        },
      })
      customerId = customer.id
    }

    // Create Checkout session
    const session = await stripe.checkout.sessions.create({
      customer: customerId,
      line_items: [
        {
          price: priceId,
          quantity: 1,
        },
      ],
      mode: 'subscription',
      success_url: `${process.env.NEXT_PUBLIC_APP_URL}/dashboard?success=true`,
      cancel_url: `${process.env.NEXT_PUBLIC_APP_URL}/pricing?canceled=true`,
      metadata: {
        user_id: user.id,
        tier: tier,
      },
      subscription_data: {
        metadata: {
          user_id: user.id,
          tier: tier,
        },
      },
    })

    return NextResponse.json({ url: session.url })

  } catch (error) {
    console.error('Stripe error:', error)
    return NextResponse.json(
      { error: 'Failed to create checkout session' },
      { status: 500 }
    )
  }
}
```

---

## 4. Stripe Webhook API

### POST /api/webhooks/stripe

**Handles Stripe webhook events**

```typescript
// app/api/webhooks/stripe/route.ts
import { createServiceClient } from '@/lib/supabase/api'
import { NextResponse } from 'next/server'
import Stripe from 'stripe'

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, {
  apiVersion: '2023-10-16',
})

const webhookSecret = process.env.STRIPE_WEBHOOK_SECRET!

export async function POST(request: Request) {
  try {
    const body = await request.text()
    const signature = request.headers.get('stripe-signature')!

    let event: Stripe.Event

    // Verify webhook signature
    try {
      event = stripe.webhooks.constructEvent(body, signature, webhookSecret)
    } catch (err) {
      console.error('Webhook signature verification failed:', err)
      return NextResponse.json(
        { error: 'Invalid signature' },
        { status: 400 }
      )
    }

    // Use service client for admin operations
    const supabase = createServiceClient()

    // Handle different event types
    switch (event.type) {
      case 'checkout.session.completed': {
        const session = event.data.object as Stripe.Checkout.Session
        const userId = session.metadata?.user_id
        const tier = session.metadata?.tier

        if (!userId || !tier) {
          console.error('Missing metadata in checkout session')
          break
        }

        // Create or update subscription record
        await supabase
          .from('subscriptions')
          .upsert({
            user_id: userId,
            stripe_customer_id: session.customer as string,
            stripe_subscription_id: session.subscription as string,
            tier: tier,
            status: 'active',
            current_period_end: new Date(
              (session.created + 30 * 24 * 60 * 60) * 1000
            ).toISOString(),
          })

        // Update user metadata for RLS policies
        await supabase.auth.admin.updateUserById(userId, {
          user_metadata: {
            subscription_tier: tier,
          },
        })

        console.log(`Subscription created for user ${userId}, tier: ${tier}`)
        break
      }

      case 'customer.subscription.updated': {
        const subscription = event.data.object as Stripe.Subscription
        const userId = subscription.metadata.user_id

        if (!userId) {
          console.error('Missing user_id in subscription metadata')
          break
        }

        // Update subscription status
        await supabase
          .from('subscriptions')
          .update({
            status: subscription.status,
            current_period_end: new Date(
              subscription.current_period_end * 1000
            ).toISOString(),
          })
          .eq('stripe_subscription_id', subscription.id)

        console.log(`Subscription updated for user ${userId}`)
        break
      }

      case 'customer.subscription.deleted': {
        const subscription = event.data.object as Stripe.Subscription
        const userId = subscription.metadata.user_id

        if (!userId) {
          console.error('Missing user_id in subscription metadata')
          break
        }

        // Downgrade to free tier
        await supabase
          .from('subscriptions')
          .update({
            tier: 'free',
            status: 'canceled',
          })
          .eq('stripe_subscription_id', subscription.id)

        // Update user metadata
        await supabase.auth.admin.updateUserById(userId, {
          user_metadata: {
            subscription_tier: 'free',
          },
        })

        console.log(`Subscription canceled for user ${userId}`)
        break
      }

      case 'invoice.payment_failed': {
        const invoice = event.data.object as Stripe.Invoice
        const subscriptionId = invoice.subscription as string

        // Mark subscription as past_due
        await supabase
          .from('subscriptions')
          .update({
            status: 'past_due',
          })
          .eq('stripe_subscription_id', subscriptionId)

        console.log(`Payment failed for subscription ${subscriptionId}`)
        break
      }

      default:
        console.log(`Unhandled event type: ${event.type}`)
    }

    return NextResponse.json({ received: true })

  } catch (error) {
    console.error('Webhook error:', error)
    return NextResponse.json(
      { error: 'Webhook handler failed' },
      { status: 500 }
    )
  }
}
```

---

## 5. Email Alerts API (Optional)

### POST /api/alerts/send

**Sends email alerts for new high-scoring opportunities**

```typescript
// app/api/alerts/send/route.ts
import { createServiceClient } from '@/lib/supabase/api'
import { NextResponse } from 'next/server'
import { Resend } from 'resend'

const resend = new Resend(process.env.RESEND_API_KEY)

export async function POST(request: Request) {
  try {
    // Verify API key (simple authentication)
    const authHeader = request.headers.get('authorization')
    if (authHeader !== `Bearer ${process.env.API_SECRET_KEY}`) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      )
    }

    const { opportunityId } = await request.json()

    if (!opportunityId) {
      return NextResponse.json(
        { error: 'Missing opportunityId' },
        { status: 400 }
      )
    }

    const supabase = createServiceClient()

    // Get opportunity details
    const { data: opportunity, error: oppError } = await supabase
      .from('opportunities')
      .select('*')
      .eq('id', opportunityId)
      .single()

    if (oppError || !opportunity) {
      return NextResponse.json(
        { error: 'Opportunity not found' },
        { status: 404 }
      )
    }

    // Get users who have email alerts enabled
    const { data: users, error: usersError } = await supabase
      .from('users')
      .select('email')
      .eq('email_alerts_enabled', true)

    if (usersError || !users || users.length === 0) {
      return NextResponse.json({ sent: 0 })
    }

    // Send emails
    const promises = users.map(user =>
      resend.emails.send({
        from: 'RedditHarbor <alerts@redditharbor.com>',
        to: user.email,
        subject: `New High-Score Opportunity: ${opportunity.title}`,
        html: `
          <h2>New Opportunity Alert</h2>
          <p>A new high-scoring opportunity has been identified:</p>
          <h3>${opportunity.title}</h3>
          <p><strong>Score:</strong> ${opportunity.score}/100</p>
          <p><strong>Subreddit:</strong> r/${opportunity.subreddit}</p>
          <p><a href="${process.env.NEXT_PUBLIC_APP_URL}/opportunities/${opportunity.id}">
            View Full Details →
          </a></p>
        `,
      })
    )

    await Promise.all(promises)

    return NextResponse.json({ sent: users.length })

  } catch (error) {
    console.error('Email alert error:', error)
    return NextResponse.json(
      { error: 'Failed to send alerts' },
      { status: 500 }
    )
  }
}
```

---

## 6. Python Integration (Trigger from Python)

### Calling Next.js API from Python Scripts

```python
# scripts/send_alerts_for_high_scores.py
import requests
import os

def send_alert_for_opportunity(opportunity_id: str):
    """
    Call Next.js API to send email alerts for a high-scoring opportunity.
    """
    url = f"{os.getenv('NEXT_PUBLIC_APP_URL')}/api/alerts/send"
    headers = {
        "Authorization": f"Bearer {os.getenv('API_SECRET_KEY')}",
        "Content-Type": "application/json"
    }
    payload = {
        "opportunityId": opportunity_id
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        result = response.json()
        print(f"Alerts sent: {result.get('sent', 0)} users")
    except Exception as e:
        print(f"Failed to send alerts: {e}")

# Usage in your scoring script:
if opportunity_score >= 85:
    send_alert_for_opportunity(opportunity_id)
```

---

## 7. Rate Limiting Middleware (Optional)

### Add rate limiting to API routes

```typescript
// lib/rate-limit.ts
import { NextResponse } from 'next/server'

const rateLimit = new Map<string, { count: number; resetTime: number }>()

export function checkRateLimit(
  identifier: string,
  limit: number = 10,
  windowMs: number = 60000
): boolean {
  const now = Date.now()
  const record = rateLimit.get(identifier)

  if (!record || now > record.resetTime) {
    rateLimit.set(identifier, {
      count: 1,
      resetTime: now + windowMs,
    })
    return true
  }

  if (record.count >= limit) {
    return false
  }

  record.count++
  return true
}

export function rateLimitResponse() {
  return NextResponse.json(
    { error: 'Too many requests' },
    { status: 429 }
  )
}
```

**Usage in API routes:**
```typescript
import { checkRateLimit, rateLimitResponse } from '@/lib/rate-limit'

export async function GET(request: Request) {
  const ip = request.headers.get('x-forwarded-for') || 'unknown'

  if (!checkRateLimit(ip, 10, 60000)) {  // 10 requests per minute
    return rateLimitResponse()
  }

  // ... rest of your API logic
}
```

---

## 8. Error Handling Wrapper

### Reusable error handler for all API routes

```typescript
// lib/api-handler.ts
import { NextResponse } from 'next/server'
import { createClient } from '@/lib/supabase/server'

type APIHandler = (
  request: Request,
  context: { user: any; supabase: any }
) => Promise<NextResponse>

export function withAuth(handler: APIHandler) {
  return async (request: Request) => {
    try {
      const supabase = createClient()

      // Get authenticated user
      const { data: { user }, error: authError } = await supabase.auth.getUser()

      if (authError || !user) {
        return NextResponse.json(
          { error: 'Unauthorized' },
          { status: 401 }
        )
      }

      // Call the actual handler
      return await handler(request, { user, supabase })

    } catch (error) {
      console.error('API error:', error)
      return NextResponse.json(
        { error: 'Internal server error' },
        { status: 500 }
      )
    }
  }
}
```

**Usage:**
```typescript
// app/api/opportunities/route.ts
import { withAuth } from '@/lib/api-handler'

export const GET = withAuth(async (request, { user, supabase }) => {
  // No need to check auth - it's already done
  // user and supabase are available

  const { data: opportunities } = await supabase
    .from('opportunities')
    .select('*')

  return NextResponse.json(opportunities)
})
```

---

## 9. Testing API Routes

### Local testing with curl

```bash
# Test opportunities endpoint
curl http://localhost:3000/api/opportunities \
  -H "Cookie: sb-access-token=YOUR_TOKEN"

# Test checkout
curl -X POST http://localhost:3000/api/checkout \
  -H "Content-Type: application/json" \
  -H "Cookie: sb-access-token=YOUR_TOKEN" \
  -d '{"priceId":"price_xxx","tier":"pro"}'

# Test webhook (requires Stripe CLI)
stripe trigger checkout.session.completed
```

### Integration testing with Jest

```typescript
// __tests__/api/opportunities.test.ts
import { GET } from '@/app/api/opportunities/route'

describe('/api/opportunities', () => {
  it('returns unauthorized without auth', async () => {
    const request = new Request('http://localhost:3000/api/opportunities')
    const response = await GET(request)
    const data = await response.json()

    expect(response.status).toBe(401)
    expect(data.error).toBe('Unauthorized')
  })

  // Add more tests...
})
```

---

## Summary

You now have complete API routes for:
- ✅ Fetching opportunities (with tier-based limits)
- ✅ User profile and subscription management
- ✅ Stripe checkout and payment processing
- ✅ Webhook handling for subscription updates
- ✅ Email alerts (optional)
- ✅ Error handling and rate limiting

**Next Steps:**
1. Copy these files into your Next.js project
2. Update environment variables
3. Test locally
4. Deploy to Vercel
5. Test in production

---

**Document Status:** Complete
**Last Updated:** 2025-11-11

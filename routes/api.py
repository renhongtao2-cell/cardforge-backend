from fastapi import APIRouter, Header, HTTPException, Query
from fastapi.responses import JSONResponse
import os

from services.payment.stripe_service import (
    create_checkout_session,
    create_portal_session,
    get_tier_info,
    check_usage,
    consume_credit,
    verify_webhook,
)

router = APIRouter()


@router.get('/stats')
async def get_stats(x_api_key: str = Header(None)):
    """Public stats endpoint"""
    return {
        'cards_generated': 0,
        'active_users': 0,
        'plan': 'free'
    }


@router.get('/pricing')
async def get_pricing():
    """Return pricing tiers"""
    return {
        'tiers': [
            {
                'name': 'Free',
                'price': 0,
                'currency': 'USD',
                'limits': {
                    'cards_per_month': 50,
                    'max_resolution': '1200x630',
                    'custom_branding': False,
                    'api_access': False,
                },
                'features': [
                    'Basic card generation',
                    'Standard colors',
                    'PNG download',
                ]
            },
            {
                'name': 'Pro',
                'price': 9.99,
                'currency': 'USD',
                'period': 'month',
                'limits': {
                    'cards_per_month': 1000,
                    'max_resolution': '4096x4096',
                    'custom_branding': True,
                    'api_access': True,
                },
                'features': [
                    'Everything in Free',
                    'Custom colors & fonts',
                    'Batch generation',
                    'API access',
                    'No watermark',
                ]
            },
            {
                'name': 'Team',
                'price': 29.99,
                'currency': 'USD',
                'period': 'month',
                'limits': {
                    'cards_per_month': -1,
                    'max_resolution': '8192x8192',
                    'custom_branding': True,
                    'api_access': True,
                    'team_members': 5,
                },
                'features': [
                    'Everything in Pro',
                    'Unlimited cards',
                    'Priority support',
                    'Team collaboration',
                    'Brand kit',
                ]
            }
        ]
    }


@router.post('/create-checkout')
async def create_checkout(
    user_id: str = Query(..., description='Unique user identifier'),
    tier: str = Query('pro', description='Pro or Team'),
):
    """Create Stripe checkout session for subscription"""
    result = create_checkout_session(user_id, tier)
    
    if 'error' in result:
        raise HTTPException(status_code=500, detail=result['error'])
    
    return result


@router.post('/create-portal')
async def create_portal(
    customer_id: str = Query(..., description='Stripe customer ID'),
    return_url: str = Query(None),
):
    """Create Stripe billing portal session"""
    result = create_portal_session(customer_id, return_url)
    
    if 'error' in result:
        raise HTTPException(status_code=500, detail=result['error'])
    
    return result


@router.post('/webhook')
async def stripe_webhook(request_body: bytes, signature: str = Header(None, alias='stripe-signature')):
    """Handle Stripe webhook events"""
    if not verify_webhook(request_body, signature):
        raise HTTPException(status_code=400, detail='Invalid signature')
    
    # TODO: Process webhook events (checkout.completed, invoice.payment_succeeded, etc.)
    # For now, just acknowledge receipt
    return JSONResponse(status_code=200, content={'received': True})


@router.get('/usage')
async def get_usage(
    user_id: str = Query(..., description='Unique user identifier'),
    tier: str = Query('free', description='Current tier'),
):
    """Check current usage and remaining credits"""
    usage = check_usage(user_id, tier)
    return usage


@router.post('/consume')
async def consume_credit_endpoint(
    user_id: str = Query(..., description='Unique user identifier'),
    tier: str = Query('free', description='Current tier'),
):
    """Consume one credit. Returns True if allowed, False if limit exceeded."""
    allowed = consume_credit(user_id, tier)
    if not allowed:
        usage = check_usage(user_id, tier)
        raise HTTPException(
            status_code=429,
            detail='Monthly card limit exceeded',
            headers={'X-RateLimit-Remaining': '0'},
        )
    
    usage = check_usage(user_id, tier)
    return {
        'consumed': True,
        'remaining': usage['remaining'],
        'limit': usage['limit'],
    }


@router.post('/validate-key')
async def validate_api_key(x_api_key: str = Header(None)):
    """Validate an API key"""
    if not x_api_key:
        raise HTTPException(status_code=401, detail='API key required')
    
    # TODO: Replace with actual database lookup
    if x_api_key.startswith('sk_test_'):
        return {'valid': True, 'tier': 'pro', 'credits_remaining': 950}
    
    raise HTTPException(status_code=401, detail='Invalid API key')

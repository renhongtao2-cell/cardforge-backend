import stripe
import os
from pathlib import Path
from datetime import datetime

# Load .env ONCE - only set keys that aren't already set
_script_dir = Path(__file__).parent.parent.parent.resolve()
_env_path = _script_dir / '.env'

if _env_path.exists():
    for line in _env_path.read_text(encoding='utf-8').strip().splitlines():
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            key = k.strip()
            val = v.strip()
            if key and val and key not in os.environ:
                os.environ[key] = val

# Initialize Stripe
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY', '').strip()
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET', '').strip()
STRIPE_PRICE_PRO = os.getenv('STRIPE_PRICE_PRO', '').strip()
STRIPE_PRICE_TEAM = os.getenv('STRIPE_PRICE_TEAM', '').strip()
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000').strip()

if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY
else:
    print('WARNING: STRIPE_SECRET_KEY is not set. Payment features will be disabled.')

TIERS = {
    'free': {'name': 'Free', 'price': 0, 'cards_per_month': 50, 'max_resolution': '1200x630', 'custom_branding': False, 'api_access': False},
    'pro': {'name': 'Pro', 'price': 9.99, 'cards_per_month': 1000, 'max_resolution': '4096x4096', 'custom_branding': True, 'api_access': True},
    'team': {'name': 'Team', 'price': 29.99, 'cards_per_month': -1, 'max_resolution': '8192x8192', 'custom_branding': True, 'api_access': True, 'team_members': 5},
}

_credits = {}


def get_tier_info(tier_name: str) -> dict:
    return TIERS.get(tier_name, TIERS['free'])


def check_usage(user_id: str, tier_name: str = 'free') -> dict:
    monthly_limit = {'free': 50, 'pro': 1000, 'team': -1}.get(tier_name, 50)
    now = datetime.now()
    month_key = f"{now.year}-{now.month:02d}"
    if user_id not in _credits:
        _credits[user_id] = {}
    if month_key not in _credits[user_id]:
        _credits[user_id][month_key] = 0
    used = _credits[user_id][month_key]
    remaining = monthly_limit - used if monthly_limit > 0 else -1
    return {'tier': tier_name, 'used': used, 'remaining': remaining, 'limit': monthly_limit, 'month': month_key}


def consume_credit(user_id: str, tier_name: str = 'free') -> bool:
    if tier_name == 'team':
        return True
    now = datetime.now()
    month_key = f"{now.year}-{now.month:02d}"
    if user_id not in _credits:
        _credits[user_id] = {}
    if month_key not in _credits[user_id]:
        _credits[user_id][month_key] = 0
    monthly_limit = 50 if tier_name == 'free' else 1000
    if _credits[user_id][month_key] >= monthly_limit:
        return False
    _credits[user_id][month_key] += 1
    return True


def create_checkout_session(user_id: str, tier: str = 'pro') -> dict:
    if not STRIPE_SECRET_KEY:
        return {'error': 'Stripe not configured'}
    price_map = {'pro': STRIPE_PRICE_PRO, 'team': STRIPE_PRICE_TEAM}
    price_id = price_map.get(tier)
    if not price_id:
        return {'error': f'Stripe Price ID not configured for tier: {tier}'}
    try:
        session = stripe.checkout.Session.create(
            customer_email=f'{user_id}@cardforge.app',
            payment_method_types=['card'],
            line_items=[{'price': price_id, 'quantity': 1}],
            mode='subscription',
            success_url=FRONTEND_URL + '/success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=FRONTEND_URL + '/cancel',
            metadata={'user_id': user_id, 'tier': tier},
        )
        return {'checkout_url': session.url, 'session_id': session.id}
    except Exception as e:
        return {'error': str(e)}


def create_portal_session(customer_id: str, return_url: str = None) -> dict:
    if not STRIPE_SECRET_KEY:
        return {'error': 'Stripe not configured'}
    try:
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=return_url or FRONTEND_URL,
        )
        return {'portal_url': session.url}
    except Exception as e:
        return {'error': str(e)}


def verify_webhook(payload: bytes, sig_header: str) -> bool:
    if not STRIPE_WEBHOOK_SECRET:
        return False
    try:
        stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
        return True
    except stripe.error.SignatureVerificationError:
        return False
    except Exception:
        return False

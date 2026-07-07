from fastapi import APIRouter, HTTPException, Query, Header
from fastapi.responses import Response

from services.url_scraper import fetch_url_metadata
from services.card_generator import CardGenerator
from services.payment.stripe_service import consume_credit, check_usage

router = APIRouter()


@router.post('/generate')
async def generate_card(
    url: str = Query(..., description='URL to generate card for'),
    bg_color: str = Query(None, description='Background color (hex)'),
    text_color: str = Query(None, description='Text color (hex)'),
    accent_color: str = Query(None, description='Accent color (hex)'),
    custom_title: str = Query(None, description='Override title'),
    custom_description: str = Query(None, description='Override description'),
    user_id: str = Header(None, alias='X-User-ID'),
    tier: str = Header(None, alias='X-Tier'),
):
    '''Generate a beautiful preview card for any URL'''
    
    # Fetch metadata
    metadata = await fetch_url_metadata(url)
    if not metadata:
        raise HTTPException(
            status_code=400,
            detail=f'Could not fetch metadata from URL: {url}. Make sure the URL is accessible.'
        )
    
    # Check and consume credit
    user_id = user_id or 'anonymous'
    tier = tier or 'free'
    
    allowed = consume_credit(user_id, tier)
    if not allowed:
        usage = check_usage(user_id, tier)
        raise HTTPException(
            status_code=429,
            detail=f'Monthly limit exceeded ({usage["used"]}/{usage["limit"]} cards)',
        )
    
    # Generate card
    try:
        card_bytes = await CardGenerator.generate_card(
            metadata=metadata,
            bg_color=bg_color,
            text_color=text_color,
            accent_color=accent_color,
            custom_title=custom_title,
            custom_description=custom_description,
        )
        
        return Response(
            content=card_bytes,
            media_type='image/png',
            headers={
                'Content-Disposition': f'attachment; filename=cardforge_{metadata.domain}.png',
                'X-Usage-Remaining': str(check_usage(user_id, tier)['remaining']),
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/preview/{url_id}')
async def preview_card(url_id: str):
    '''Preview a previously generated card (for caching/demo)'''
    raise HTTPException(status_code=501, detail='Preview endpoint coming soon')


@router.get('/metadata')
async def get_metadata(url: str = Query(..., description='URL to fetch metadata from')):
    '''Get URL metadata without generating a card'''
    metadata = await fetch_url_metadata(url)
    if not metadata:
        raise HTTPException(
            status_code=400,
            detail=f'Could not fetch metadata from URL: {url}'
        )
    
    return {
        'title': metadata.title,
        'description': metadata.description,
        'image': metadata.image,
        'domain': metadata.domain,
        'favicon': metadata.favicon,
    }

import httpx
from bs4 import BeautifulSoup
from typing import Optional
from urllib.parse import urlparse


class URLMetadata:
    title = ''
    description = ''
    image = ''
    domain = ''
    favicon = ''


async def fetch_url_metadata(url: str) -> Optional[URLMetadata]:
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=10.0)) as client:
            headers = {
                'User-Agent': 'Mozilla/5.0 (compatible; CardForge/1.0)'
            }
            response = await client.get(url, headers=headers, follow_redirects=True)
            
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            meta = URLMetadata()
            
            # Extract title
            if soup.title and soup.title.string:
                meta.title = soup.title.string.strip()[:100]
            else:
                h1 = soup.find('h1')
                meta.title = h1.get_text().strip()[:100] if h1 else 'Untitled'
            
            # Extract description
            desc_tag = soup.find('meta', attrs={'name': 'description'})
            if not desc_tag:
                desc_tag = soup.find('meta', attrs={'property': 'og:description'})
            meta.description = desc_tag['content'][:250].strip() if desc_tag and desc_tag.get('content') else ''
            
            # Extract image
            img_tag = soup.find('meta', attrs={'property': 'og:image'})
            if img_tag and img_tag.get('content'):
                meta.image = img_tag['content']
                if not meta.image.startswith('http'):
                    base = f'{urlparse(url).scheme}://{urlparse(url).netloc}'
                    meta.image = base.rstrip('/') + meta.image
            else:
                img = soup.find('img')
                if img and img.get('src'):
                    meta.image = img['src']
                    if not meta.image.startswith('http'):
                        base = f'{urlparse(url).scheme}://{urlparse(url).netloc}'
                        meta.image = base.rstrip('/') + meta.image
            
            # Extract domain
            parsed = urlparse(url)
            meta.domain = parsed.netloc.replace('www.', '')
            
            # Extract favicon
            meta.favicon = f'https://www.google.com/s2/favicons?domain={meta.domain}&sz=32'
            
            return meta
            
    except Exception as e:
        print(f'Error fetching URL: {e}')
        return None


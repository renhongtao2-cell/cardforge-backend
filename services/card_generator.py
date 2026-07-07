from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import httpx
from typing import Optional
import os

from services.url_scraper import URLMetadata, fetch_url_metadata
from app.config import (
    CARD_WIDTH, CARD_HEIGHT, DEFAULT_BG_COLOR,
    DEFAULT_TEXT_COLOR, DEFAULT_ACCENT_COLOR
)


class CardGenerator:
    @staticmethod
    async def generate_card(
        metadata: URLMetadata,
        bg_color: str = None,
        text_color: str = None,
        accent_color: str = None,
        custom_title: str = None,
        custom_description: str = None,
    ) -> bytes:
        bg_color = bg_color or DEFAULT_BG_COLOR
        text_color = text_color or DEFAULT_TEXT_COLOR
        accent_color = accent_color or DEFAULT_ACCENT_COLOR
        
        img = Image.new('RGB', (CARD_WIDTH, CARD_HEIGHT), bg_color)
        draw = ImageDraw.Draw(img)
        
        # Try to load fonts, fallback to default
        try:
            title_font = ImageFont.truetype('arial.ttf', 48)
            desc_font = ImageFont.truetype('arial.ttf', 32)
            domain_font = ImageFont.truetype('arial.ttf', 24)
        except Exception:
            try:
                title_font = ImageFont.load_default()
                desc_font = title_font
                domain_font = title_font
            except Exception:
                title_font = ImageFont.load_default()
                desc_font = title_font
                domain_font = title_font
        
        # Draw accent bar at top
        draw.rectangle([0, 0, CARD_WIDTH, 8], fill=accent_color)
        
        # Draw domain badge
        domain_bbox = draw.textbbox((60, 40), metadata.domain, font=domain_font)
        domain_w = domain_bbox[2] - domain_bbox[0]
        draw.rounded_rectangle(
            [(60 - 10, 30), (60 + domain_w + 10, 65)],
            radius=15,
            fill=accent_color + '40',
        )
        draw.text((60, 38), metadata.domain, fill=text_color, font=domain_font)
        
        # Draw title with word wrap
        title = custom_title or metadata.title
        wrapped_title = CardGenerator._wrap_text(title, draw, title_font, CARD_WIDTH - 120)
        y = 100
        for line in wrapped_title:
            draw.text((60, y), line, fill=text_color, font=title_font)
            y += 60
        
        # Draw description with word wrap
        desc = custom_description or metadata.description
        if not desc:
            desc = 'Click to learn more'
        wrapped_desc = CardGenerator._wrap_text(desc, draw, desc_font, CARD_WIDTH - 120)
        y += 30
        for line in wrapped_desc[:4]:
            draw.text((60, y), line, fill=text_color + 'CC', font=desc_font)
            y += 45
        
        # Draw bottom bar
        draw.rectangle([0, CARD_HEIGHT - 60, CARD_WIDTH, CARD_HEIGHT], fill=accent_color)
        
        # Load and draw favicon
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                fav_resp = await client.get(metadata.favicon)
                if fav_resp.status_code == 200:
                    fav_img = Image.open(BytesIO(fav_resp.content)).resize((32, 32))
                    img.paste(fav_img, (50, CARD_HEIGHT - 50), fav_img.split()[0] if len(fav_img.split()) > 1 else None)
        except Exception:
            pass
        
        # Draw CTA text
        try:
            cta_font = ImageFont.truetype('arial.ttf', 28)
            cta_bbox = draw.textbbox((0, 0), 'Click to visit ->', font=cta_font)
            cta_w = cta_bbox[2] - cta_bbox[0]
            draw.text(
                ((CARD_WIDTH - cta_w) // 2, CARD_HEIGHT - 45),
                'Click to visit ->',
                fill='#ffffff',
                font=cta_font,
            )
        except Exception:
            pass
        
        # Save to bytes
        buffer = BytesIO()
        img.save(buffer, format='PNG', optimize=True)
        buffer.seek(0)
        
        return buffer.getvalue()
    
    @staticmethod
    def _wrap_text(text: str, draw, font, max_width: int) -> list:
        words = text.split()
        lines = []
        current_line = ''
        
        for word in words:
            test_line = f'{current_line} {word}'.strip()
            bbox = draw.textbbox((0, 0), test_line, font=font)
            if bbox[2] - bbox[0] <= max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        return lines[:5]  # Max 5 lines

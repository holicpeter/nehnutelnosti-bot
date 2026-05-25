import asyncio
import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from jinja2 import Environment, BaseLoader
from config import settings

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="sk">
<head>
  <meta charset="UTF-8">
  <style>
    body { font-family: Arial, sans-serif; background: #f4f4f4; margin: 0; padding: 20px; }
    h1 { color: #2c3e50; }
    .listing { background: #fff; border-radius: 8px; padding: 16px; margin-bottom: 16px;
               box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    .listing h2 { margin: 0 0 8px; font-size: 18px; }
    .listing h2 a { color: #2980b9; text-decoration: none; }
    .meta { color: #555; font-size: 14px; margin-bottom: 8px; }
    .price { font-size: 20px; font-weight: bold; color: #27ae60; }
    .source { display: inline-block; background: #ecf0f1; border-radius: 4px;
              padding: 2px 8px; font-size: 12px; color: #7f8c8d; margin-top: 8px; }
    .desc { color: #333; font-size: 14px; margin-top: 8px; }
    img { max-width: 100%; border-radius: 4px; margin-top: 8px; }
  </style>
</head>
<body>
  <h1>🏠 Nové inzeráty nehnuteľností ({{ count }})</h1>
  {% for l in listings %}
  <div class="listing">
    <h2><a href="{{ l.url or '#' }}">{{ l.title or 'Bez názvu' }}</a></h2>
    <div class="meta">
      📍 {{ l.location or 'N/A' }} &nbsp;|&nbsp; 📐 {{ l.area or 'N/A' }} m²
    </div>
    <div class="price">{{ l.price | int | string + ' €' if l.price else 'Cena neuvedená' }}</div>
    {% if l.description %}
    <div class="desc">{{ l.description }}</div>
    {% endif %}
    {% if l.image_url %}
    <img src="{{ l.image_url }}" alt="foto">
    {% endif %}
    <span class="source">{{ l.source or 'N/A' }}</span>
  </div>
  {% endfor %}
</body>
</html>
"""


def _render(listings: list[dict]) -> str:
    env = Environment(loader=BaseLoader())
    tmpl = env.from_string(HTML_TEMPLATE)
    return tmpl.render(listings=listings, count=len(listings))


async def send_email(listings: list[dict]) -> None:
    if not listings:
        return

    html = _render(listings)
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"[Nehnuteľnosti] {len(listings)} nových inzerátov"
    msg["From"] = settings.email_from
    msg["To"] = settings.email_to
    msg.attach(MIMEText(html, "html", "utf-8"))

    await aiosmtplib.send(
        msg,
        hostname=settings.smtp_host,
        port=settings.smtp_port,
        username=settings.smtp_user,
        password=settings.smtp_password,
        start_tls=True,
    )


def notify(listings: list[dict]) -> None:
    asyncio.run(send_email(listings))

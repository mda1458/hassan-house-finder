import os
import requests
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from supabase import create_client

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]
GMAIL_USER = os.environ["GMAIL_USER"]
GMAIL_APP_PASSWORD = os.environ["GMAIL_APP_PASSWORD"]
RECIPIENT_EMAIL = os.environ.get("RECIPIENT_EMAIL", GMAIL_USER)
GEOAPIFY_KEY = os.environ.get("GEOAPIFY_KEY", "")

API_URL = "https://akafoe.studylife.org/api/housing/db-apartments"


def get_coordinates(address):
    """Free geocoding via Nominatim (OpenStreetMap) — no API key needed"""
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {"q": address, "format": "json", "limit": 1}
        headers = {"User-Agent": "apartment-alert-bot/1.0"}
        res = requests.get(url, params=params, headers=headers, timeout=5).json()
        if res:
            return res[0]["lat"], res[0]["lon"]
    except Exception:
        pass
    return None, None


def send_email(subject, html_body):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = GMAIL_USER
    msg["To"] = RECIPIENT_EMAIL
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        smtp.send_message(msg)
    print(f"Email sent: {subject}")


def format_apartment_html(apt):
    addr = apt["address"]["full_address"]
    rent = apt["details"]["rent_range"] or f"{apt['details']['rent']} EUR"
    size = apt["details"]["size"]
    avail = apt["availability"]["available_from"]
    title = apt["title"]
    contact = apt["contact"]["email"]
    apt_id = apt["object_id"]
    furnished = "möbliert" in apt.get("description", "") or "möbliert" in apt.get("features", [])
    pets = apt["availability"]["pets_allowed"]
    wbs = apt["availability"]["wbs_required"]
    rooms = apt["details"]["rooms"]

    # Main image
    main_image = next((img["url"] for img in apt.get("images", []) if img.get("is_main")), None)
    image_html = (
        f'<img src="{main_image}" style="width:100%;max-width:560px;height:220px;object-fit:cover;display:block;" />'
        if main_image else ""
    )

    # Links
    google_maps_link = f"https://www.google.com/maps/search/?api=1&query={requests.utils.quote(addr)}"
    listing_link = f"https://akafoe.studylife.org/wohnen/wohnheime?id={apt_id}"

    # Geocode for map thumbnail
    lat, lon = get_coordinates(addr)
    map_section = ""
    if lat and lon:
        if GEOAPIFY_KEY:
            map_img_url = (
                f"https://maps.geoapify.com/v1/staticmap"
                f"?style=osm-bright&width=560&height=200"
                f"&center=lonlat:{lon},{lat}&zoom=15"
                f"&marker=lonlat:{lon},{lat};color:%23cc0000;size:medium"
                f"&apiKey={GEOAPIFY_KEY}"
            )
            map_section = f"""
            <div style="margin-top:16px;border-radius:8px;overflow:hidden;border:1px solid #ddd;">
              <a href="{google_maps_link}" target="_blank">
                <img src="{map_img_url}" style="width:100%;display:block;height:200px;object-fit:cover;" alt="Map preview" />
              </a>
            </div>
            """
        else:
            # Fallback: OpenStreetMap iframe-style link box (no API key)
            osm_link = f"https://www.openstreetmap.org/?mlat={lat}&mlon={lon}&zoom=15"
            map_section = f"""
            <div style="margin-top:16px;border-radius:8px;overflow:hidden;border:1px solid #ddd;background:#f0f4f8;padding:12px;text-align:center;">
              <a href="{osm_link}" target="_blank" style="color:#0066cc;font-size:13px;text-decoration:none;">
                🗺️ View on OpenStreetMap ({lat}, {lon})
              </a>
            </div>
            """

    return f"""
    <div style="font-family:Arial,sans-serif;max-width:560px;margin:0 auto 32px;border:1px solid #e0e0e0;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.06);">

      <!-- Apartment image -->
      {image_html}

      <div style="padding:20px;">

        <!-- Title -->
        <h2 style="margin:0 0 16px;color:#1a1a1a;font-size:17px;line-height:1.4;">{title}</h2>

        <!-- Details table -->
        <table style="width:100%;border-collapse:collapse;font-size:14px;color:#333;">
          <tr style="border-bottom:1px solid #f0f0f0;">
            <td style="padding:8px 4px;width:150px;color:#666;">📍 Address</td>
            <td style="padding:8px 4px;font-weight:500;">{addr}</td>
          </tr>
          <tr style="border-bottom:1px solid #f0f0f0;">
            <td style="padding:8px 4px;color:#666;">💶 Rent</td>
            <td style="padding:8px 4px;font-weight:500;color:#0a7c2e;">{rent}</td>
          </tr>
          <tr style="border-bottom:1px solid #f0f0f0;">
            <td style="padding:8px 4px;color:#666;">📐 Size</td>
            <td style="padding:8px 4px;">{size} m²</td>
          </tr>
          <tr style="border-bottom:1px solid #f0f0f0;">
            <td style="padding:8px 4px;color:#666;">🚪 Rooms</td>
            <td style="padding:8px 4px;">{rooms}</td>
          </tr>
          <tr style="border-bottom:1px solid #f0f0f0;">
            <td style="padding:8px 4px;color:#666;">📅 Available from</td>
            <td style="padding:8px 4px;">{avail}</td>
          </tr>
          <tr style="border-bottom:1px solid #f0f0f0;">
            <td style="padding:8px 4px;color:#666;">🪑 Furnished</td>
            <td style="padding:8px 4px;">{"✅ Yes" if furnished else "❌ No"}</td>
          </tr>
          <tr style="border-bottom:1px solid #f0f0f0;">
            <td style="padding:8px 4px;color:#666;">🐾 Pets allowed</td>
            <td style="padding:8px 4px;">{"✅ Yes" if pets else "❌ No"}</td>
          </tr>
          <tr style="border-bottom:1px solid #f0f0f0;">
            <td style="padding:8px 4px;color:#666;">📄 WBS required</td>
            <td style="padding:8px 4px;">{"⚠️ Yes" if wbs else "✅ No"}</td>
          </tr>
          <tr>
            <td style="padding:8px 4px;color:#666;">📧 Contact</td>
            <td style="padding:8px 4px;">
              <a href="mailto:{contact}" style="color:#0066cc;text-decoration:none;">{contact}</a>
            </td>
          </tr>
        </table>

        <!-- Map thumbnail -->
        {map_section}

        <!-- Action buttons -->
        <div style="margin-top:20px;display:flex;gap:8px;flex-wrap:wrap;">
          <a href="{listing_link}" target="_blank"
             style="display:inline-block;padding:10px 16px;background:#0066cc;color:#fff;text-decoration:none;border-radius:6px;font-size:13px;font-weight:bold;">
            🔗 View Listing
          </a>
          <a href="{google_maps_link}" target="_blank"
             style="display:inline-block;padding:10px 16px;background:#34a853;color:#fff;text-decoration:none;border-radius:6px;font-size:13px;font-weight:bold;">
            📍 Open in Maps
          </a>
          <a href="mailto:{contact}"
             style="display:inline-block;padding:10px 16px;background:#ea4335;color:#fff;text-decoration:none;border-radius:6px;font-size:13px;font-weight:bold;">
            📧 Contact
          </a>
        </div>

      </div>
    </div>
    """


def main():
    db = create_client(SUPABASE_URL, SUPABASE_KEY)

    response = requests.get(API_URL, timeout=10)
    apartments = response.json().get("data", [])

    existing = db.table("sent_apartments").select("id").execute()
    sent_ids = {row["id"] for row in existing.data}

    new_ones = [a for a in apartments if a["id"] not in sent_ids]

    if not new_ones:
        print("No new apartments.")
        return

    # Build one combined email for all new listings
    all_cards = "".join(format_apartment_html(apt) for apt in new_ones)
    count = len(new_ones)

    full_html = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:24px 16px;background:#f9f9f9;">

      <!-- Header -->
      <div style="background:#0066cc;border-radius:12px;padding:24px;margin-bottom:28px;text-align:center;">
        <h1 style="color:#fff;margin:0;font-size:22px;">🏠 {count} New Apartment{"s" if count > 1 else ""} Found</h1>
        <p style="color:#cce0ff;margin:8px 0 0;font-size:13px;">
          Akafoe Bochum · {len(apartments)} total listings checked
        </p>
      </div>

      <!-- Apartment cards -->
      {all_cards}

      <!-- Footer -->
      <p style="color:#aaa;font-size:11px;margin-top:32px;text-align:center;">
        This alert was sent automatically every 5 minutes via GitHub Actions.<br/>
        <a href="https://akafoe.studylife.org/wohnen/wohnheime" style="color:#aaa;">Browse all listings</a>
      </p>

    </div>
    """

    subject = f"🏠 {count} New Apartment{'s' if count > 1 else ''} Available – Akafoe Bochum"
    send_email(subject, full_html)

    # Save to DB after sending
    for apt in new_ones:
        db.table("sent_apartments").insert({
            "id": apt["id"],
            "title": apt["title"]
        }).execute()
        print(f"Saved: {apt['title']}")


if __name__ == "__main__":
    main()

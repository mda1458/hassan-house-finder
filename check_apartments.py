import os
import requests
from supabase import create_client

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]
CALLMEBOT_PHONE = os.environ["CALLMEBOT_PHONE"]   # e.g. 4917612345678
CALLMEBOT_APIKEY = os.environ["CALLMEBOT_APIKEY"]

API_URL = "https://akafoe.studylife.org/api/housing/db-apartments"

def send_whatsapp(message):
    url = "https://api.callmebot.com/whatsapp.php"
    params = {
        "phone": CALLMEBOT_PHONE,
        "text": message,
        "apikey": CALLMEBOT_APIKEY
    }
    requests.get(url, params=params)

def format_apartment(apt):
    addr = apt["address"]["full_address"]
    rent = apt["details"]["rent_range"] or f"{apt['details']['rent']} EUR"
    size = apt["details"]["size"]
    avail = apt["availability"]["available_from"]
    furnished = "✅ Furnished" if "möbliert" in apt.get("description","") or "möbliert" in apt.get("features",[]) else "🪑 Unfurnished"
    pets = "🐾 Pets OK" if apt["availability"]["pets_allowed"] else "🚫 No pets"
    contact = apt["contact"]["email"]

    return (
        f"🏠 *New Apartment Available!*\n"
        f"📍 {addr}\n"
        f"💶 {rent}\n"
        f"📐 {size} m²\n"
        f"📅 Available from: {avail}\n"
        f"{furnished} | {pets}\n"
        f"📧 {contact}"
    )

def main():
    db = create_client(SUPABASE_URL, SUPABASE_KEY)

    response = requests.get(API_URL)
    apartments = response.json().get("data", [])

    # Fetch already-sent IDs
    existing = db.table("sent_apartments").select("id").execute()
    sent_ids = {row["id"] for row in existing.data}

    new_ones = [a for a in apartments if a["id"] not in sent_ids]

    for apt in new_ones:
        message = format_apartment(apt)
        send_whatsapp(message)

        db.table("sent_apartments").insert({
            "id": apt["id"],
            "title": apt["title"]
        }).execute()

        print(f"Sent: {apt['title']}")

    if not new_ones:
        print("No new apartments.")

if __name__ == "__main__":
    main()

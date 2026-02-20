import uvicorn
from fastapi import FastAPI, Request
from datetime import datetime
import re
import os

app = FastAPI()

def clean_html(raw_html):
    """Utility to clean HTML tags and fix spacing."""
    # Replace line breaks and list tags with spaces to avoid smashing words together
    text = re.sub(r'<(br|/?li|/?ul|/?p|/?div|/?h[1-6]).*?>', ' ', raw_html, flags=re.IGNORECASE)
    # Strip all remaining tags
    text = re.sub(r'<.*?>', '', text)
    # Collapse multiple spaces into a single space
    return " ".join(text.split())

@app.post("/webhook")
async def status_webhook(request: Request):
    try:
        data = await request.json()
    except Exception:
        return {"status": "invalid json"}

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # --- Scenario A: Native Atlassian Webhook ---
    # (This is to scale to 100+ standard providers)
    if "incident" in data:
        incident = data["incident"]
        components = incident.get("components", [])
        
        affected_products = ", ".join([comp["name"] for comp in components]) if components else incident.get("name", "Unknown Service")
        
        updates = incident.get("incident_updates", [])
        status_message = updates[0].get("body", "No update body provided.") if updates else incident.get("name", "New incident.")

        print(f"[{current_time}] Product: {affected_products}")
        print(f"Status: {status_message}\n")

    # --- Scenario B: RSS-to-Webhook Bridge Fallback ---
    # (Bypasses OpenAI's disabled webhook UI tab)
    elif "title" in data:
        title = data.get("title", "Unknown Update")
        raw_description = data.get("description", "No details provided.")
        description = clean_html(raw_description)

        # Prevent double "Status:" from printing
        if description.startswith("Status:"):
            description = description.replace("Status:", "", 1).strip()
        
        # In RSS, the title usually contains the product info and status
        print(f"[{current_time}] Product/Event: {title}")
        print(f"Status: {description}\n")

    return {"status": "success"}

@app.get("/")
def health_check():
    return {"message": "Webhook listener is running."}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))

    uvicorn.run("status_tracker:app", host="0.0.0.0", port=port)



"""Simple LinkedIn RapidAPI test client using environment variables."""
import os
import http.client
import json
from dotenv import load_dotenv


# Load environment variables from .env
load_dotenv()

# Read credentials from environment
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST", "linkedin-job-search-api.p.rapidapi.com")

if not RAPIDAPI_KEY:
    raise RuntimeError("Missing RAPIDAPI_KEY. Add it to your .env file.")


def fetch_jobs(title: str = "Data Engineer", location: str = "United States", limit: int = 10, offset: int = 0):
    """Fetch jobs from LinkedIn RapidAPI and save to linkedin_jobs.json."""
    conn = http.client.HTTPSConnection(RAPIDAPI_HOST)

    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST,
    }

    endpoint = (
        f"/active-jb-24h?limit={limit}&offset={offset}"
        f"&title_filter=\"{title}\"&location_filter=\"{location}\"&description_type=text"
    )

    conn.request("GET", endpoint, headers=headers)
    res = conn.getresponse()
    data = res.read().decode("utf-8")

    # Convert string response -> JSON (dict/list)
    json_data = json.loads(data)

    # Pretty print
    print(json.dumps(json_data, indent=4))

    # Save response into a JSON file
    with open("linkedin_jobs.json", "w", encoding="utf-8") as file:
        json.dump(json_data, file, indent=4, ensure_ascii=False)

    print("\n✅ Data saved successfully in linkedin_jobs.json")


if __name__ == "__main__":
    fetch_jobs()
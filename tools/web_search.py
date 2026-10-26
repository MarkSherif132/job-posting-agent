import time
from ddgs import DDGS
from ddgs.exceptions import DDGSException

MAX_ATTEMPTS = 3
RETRY_DELAY_SECONDS = 5

def search_web(query: str, max_results: int = 3) -> str:


    results = []
    last_error = None

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            with DDGS(timeout=15) as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
            break
        except DDGSException as e:
            last_error = e
            if attempt < MAX_ATTEMPTS:
                time.sleep(RETRY_DELAY_SECONDS)
 
    if not results and last_error:
        return f"The search failed after {MAX_ATTEMPTS} tries rate limit: {last_error}"
 

 
    if not results:
        return "Not Found for this search query."
 
    lines = []
    for r in results:
        title = r.get("title", "")
        url = r.get("href", "")
        snippet = r.get("body", "")[:300]
        lines.append(f"- {title} [{url}]: {snippet}")

        return "\n".join(lines)
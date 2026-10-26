# Job Posting Agent

A Streamlit app that generates a complete job posting from a company name and a job title, using a small multi-stage LLM pipeline with live web research and guardrails for confidential inputs.

## How it works

```
Company + role + optional details
        |
        v
1. Research agent   LangChain tool-calling agent with web search (DuckDuckGo).
                    Receives only the company name and official website.
        |
        v
2. Requirements     Defines the role's requirements for this company.
                    The only stage that sees confidential details (e.g. salary),
                    used to calibrate seniority.
        |
        v
3. Writer           Writes the posting. Receives only the details marked "show".
```

## Features

- **Per-field visibility:** every detail (work mode, location, salary, experience, contract type, contact, custom fields) is marked as shown in the posting or internal only.
- **Routing, not just instructions:** internal fields are never sent to the web-search agent or the writer, so they cannot leak from stages that never saw them.
- **Leak detection:** the requirements and the posting are scanned for internal values (Arabic digits, thousand separators and spacing are normalized). On a hit, the stage is regenerated once; if it persists, a warning is shown.
- **Contact grounding:** emails and URLs must come from the user's input or from search results on the company's official domain. Anything else is removed or flagged.
- **Resilient API client:** rate-limit (429) backoff using `retry-after`, truncation detection via `finish_reason`, a cap on search calls per run, and retry when the model calls a tool that does not exist.
- **Review tabs:** posting, requirements and company research, so every claim can be traced to its source. Download as Markdown.

## Run locally

```bash
python -m venv .venv
# Windows (PowerShell): .\.venv\Scripts\Activate.ps1
# macOS/Linux:          source .venv/bin/activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and set `API_KEY` to your Groq key, then:

```bash
streamlit run app.py
```

## Limitations

- Output is a draft. Always review it before publishing, especially the "About the Company" section.
- Leak detection catches written values (for example `15,000`), not paraphrases such as "around 15k".
- Searching by name can return unrelated companies; entering the official website anchors the research to the right one, but results still vary between runs.
- The free Groq tier has a tokens-per-minute limit, so a run can take up to two minutes.

## Stack

Python, Streamlit, LangChain (`create_agent`), Groq API (`openai/gpt-oss-120b`), httpx, ddgs.

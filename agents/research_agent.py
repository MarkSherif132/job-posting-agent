from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from contact_check import official_domain, strip_unverified_contacts
from config import get_api_key
from llm_client import GROQ_BASE_URL, AGENT_MODEL_ID
from prompts import RESEARCH_ANALYST_SYSTEM
from tools.web_search import search_web
import openai

MAX_AGENT_ATTEMPTS = 3
def _make_search_tool(max_calls: int = 3, domain: str = ""):
    calls = {"n": 0}

    @tool
    def search_company_info(query: str) -> str:
        """Search the web for current, factual information about a company.
        Use this whenever you need real facts about a specific company
        (culture, mission, work environment, reputation) before writing a profile."""
        calls["n"] += 1
        if calls["n"] > max_calls:
            return "Search limit reached. Write the profile now using what you already found."
        if domain and domain not in query.lower():
            query = f"{query} {domain}"
        return search_web(query)

    return search_company_info


def _build_research_agent(domain: str = ""):
    llm = ChatOpenAI(
        model=AGENT_MODEL_ID,
        base_url=GROQ_BASE_URL,
        api_key=get_api_key(),
        temperature=0.3,
        max_tokens=1500,
    )
    return create_agent(
        model=llm,
        tools=[_make_search_tool(domain=domain)],
        system_prompt=RESEARCH_ANALYST_SYSTEM,
    )


def run_research_agent(company: str, website: str = "") -> str:
    domain = official_domain(website)
    user_message = f"Company: {company}"
    if website:
        user_message += f"\nOfficial website: {website}"

    last_error = None
    for _ in range(MAX_AGENT_ATTEMPTS):
        agent = _build_research_agent(domain)
        try:
            result = agent.invoke({
                "messages": [{"role": "user", "content": user_message}]
            })
            profile = result["messages"][-1].content
            tool_text = "\n".join(
                str(m.content) for m in result["messages"] if getattr(m, "type", "") == "tool"
            )
            return strip_unverified_contacts(profile, tool_text + "\n" + website, domain)
        except openai.BadRequestError as e:
            if "tool_use_failed" not in str(e):
                raise
            last_error = e

    raise RuntimeError(
        f"Research Agent failed after {MAX_AGENT_ATTEMPTS} attempts: {last_error}"
    )
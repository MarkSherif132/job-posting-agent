from contact_check import official_domain, strip_unverified_contacts
from dataclasses import dataclass, field

from agents.research_agent import run_research_agent
from job_details import JobDetails, format_items
from leak_check import find_leaks
from llm_client import chat_completion
from prompts import JOB_POSTING_WRITER_SYSTEM, JOB_REQUIREMENTS_SPECIALIST_SYSTEM


@dataclass
class PipelineResult:
    company_research: str
    role_requirements: str
    job_posting: str
    warnings: list[str] = field(default_factory=list)


def _run_research(company: str, details: JobDetails) -> str:
    # Stage 1: Research. This stage only looks at the company name and website, never internal details.
    return run_research_agent(company, website=details.company_website)


def _run_requirements(
    company: str, role: str, research: str, details: JobDetails, note: str = ""
) -> str:
    # Stage 2: Requirements. This is the only stage that looks at internal details (for comparison purposes).
    sections = [f"Company: {company}", f"Job role: {role}"]
    if details.visible():
        sections.append(
            "Details that WILL appear in the posting:\n" + format_items(details.visible())
        )
    if details.internal():
        sections.append(
            "INTERNAL details (never state, repeat, or hint at these in your output):\n"
            + format_items(details.internal())
        )
    sections.append(f"Company profile:\n{research}")
    if note:
        sections.append(note)

    return chat_completion(
        "\n\n".join(sections),
        system=JOB_REQUIREMENTS_SPECIALIST_SYSTEM,
        max_tokens=1200,
        temperature=0.4,
    )


def _run_writer(
    company: str,
    role: str,
    research: str,
    requirements: str,
    details: JobDetails,
    note: str = "",
) -> str:
    # Stage 3: Posting Writer. This stage only looks at visible details, never internal ones.
    sections = [f"Company: {company}", f"Job role: {role}"]
    if details.visible():
        sections.append(
            "Confirmed details to include in the posting (use exactly as given):\n"
            + format_items(details.visible())
        )
    sections.append(f"Company profile:\n{research}")
    sections.append(f"Role requirements:\n{requirements}")
    if note:
        sections.append(note)

    return chat_completion(
        "\n\n".join(sections),
        system=JOB_POSTING_WRITER_SYSTEM,
        max_tokens=2200,
        temperature=0.7,
    )


def _generate_checked(generate, details: JobDetails, stage: str) -> tuple[str, list[str]]:
    """
    Generates the text, checks it for leaks, and regenerates if necessary.
    Returns (text, list of warnings). The warnings list is empty if everything is fine.
    """
    text = generate("")
    leaks = find_leaks(text, details.internal())
    if not leaks:
        return text, []

    note = (
        "IMPORTANT: your previous output revealed these INTERNAL items: "
        + ", ".join(leaks)
        + ". Rewrite it without stating, quoting, or hinting at them."
    )
    text = generate(note)
    leaks = find_leaks(text, details.internal())
    if leaks:
        return text, [f"{stage}: Internal information revealed ({', '.join(leaks)}). Review before publishing."]
    return text, []


def run_pipeline(company: str, role: str, details: JobDetails | None = None) -> PipelineResult:
    """
    Run the three stages sequentially and return all results.
    """
    company = company.strip()
    role = role.strip()
    if not company or not role:
        raise ValueError("You must enter both the company name and job title.")
    if details is None:
        details = JobDetails()

    research = _run_research(company, details)
    requirements, req_warnings = _generate_checked(
        lambda note: _run_requirements(company, role, research, details, note),
        details,
        "Requirements",
    )
    posting, post_warnings = _generate_checked(
        lambda note: _run_writer(company, role, research, requirements, details, note),
        details,
        "Posting",
    )

    return PipelineResult(
        company_research=research,
        role_requirements=requirements,
        job_posting=posting,
        warnings=req_warnings + post_warnings,
    )
"""
نموذج تفاصيل الوظيفة: كل تفصيلة ليها قيمة وعلامة "تظهر في الإعلان ولا لأ".
"""

from dataclasses import dataclass, field


@dataclass
class DetailField:
    value: str = ""
    show: bool = False  # True = يظهر في الإعلان، False = داخلي يوجّه الموديل بس

    @property
    def filled(self) -> bool:
        return bool(self.value.strip())


# أسماء الحقول بالشكل اللي هيتكتب بيه في الـ prompts
FIELD_LABELS = {
    "work_mode": "Work mode",
    "location": "Location",
    "salary": "Salary / budget",
    "experience_years": "Years of experience",
    "contract_type": "Contract type",
    "apply_contact": "Application contact",
}


@dataclass
class JobDetails:
    work_mode: DetailField = field(default_factory=DetailField)
    location: DetailField = field(default_factory=DetailField)
    salary: DetailField = field(default_factory=DetailField)
    experience_years: DetailField = field(default_factory=DetailField)
    contract_type: DetailField = field(default_factory=DetailField)
    apply_contact: DetailField = field(default_factory=DetailField)
    company_website: str = ""
    custom: list[tuple[str, DetailField]] = field(default_factory=list)

    def _filled_items(self) -> list[tuple[str, DetailField]]:
        items = [(label, getattr(self, name)) for name, label in FIELD_LABELS.items()]
        items += self.custom
        return [(label, f) for label, f in items if f.filled]

    def visible(self) -> list[tuple[str, str]]:
        return [(label, f.value.strip()) for label, f in self._filled_items() if f.show]

    def internal(self) -> list[tuple[str, str]]:
        return [(label, f.value.strip()) for label, f in self._filled_items() if not f.show]


def format_items(items: list[tuple[str, str]]) -> str:
    return "\n".join(f"- {label}: {value}" for label, value in items)
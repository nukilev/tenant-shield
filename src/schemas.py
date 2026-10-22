from typing import Literal, List, Optional
from pydantic import BaseModel, Field


class ClauseAnalysisRequest(BaseModel):
    clause_text: str = Field(
        ...,
        min_length=10,
        description="The raw Hebrew text of a specific rental contract clause to be analyzed.",
        examples=["השוכר יפקיד ערבות בנקאית בגובה 5 חודשי שכירות."]
    )


class LegalAnalysisDetail(BaseModel):
    risk: Literal["green", "yellow", "red"] = Field(
        description="Risk classification: 'red' (illegal/void), 'yellow' (ambiguous/unfair), 'green' (valid/fair)."
    )
    summary: str = Field(
        description="A concise one-sentence summary of the clause's core implication."
    )
    legal_reasoning: str = Field(
        description="Detailed legal reasoning grounded strictly in the retrieved Israeli statutory sections."
    )
    recommendation: str = Field(
        description="Actionable strategic advice explaining what the tenant should negotiate or clarify."
    )
    suggested_revision: Optional[str] = Field(
        default=None,
        description=(
            "If risk is 'red' or 'yellow', provide an exact, legally balanced Hebrew revision of the clause "
            "ready to be inserted into the lease, protecting tenant statutory rights while remaining realistic for a landlord to accept. "
            "If risk is 'green', return null."
        )
    )
    cited_laws: str = Field(
        description="Specific statutory references (law name and section number) used for the analysis."
    )

class BatchClauseAnalysis(BaseModel):
    analyses: List[LegalAnalysisDetail] = Field(
        description="Ordered list of legal analyses corresponding to the batch of input clauses."
    )

class ClauseAnalysisResponse(BaseModel):
    clause_text: str = Field(description="The original contract clause analyzed.")
    analysis: LegalAnalysisDetail = Field(description="Structured legal evaluation from the LLM.")
    retrieved_context: str = Field(
        description="Raw statutory sections retrieved from the local ChromaDB vector store."
    )


class ContractSummaryMetrics(BaseModel):
    total_clauses: int = Field(description="Total number of clauses extracted and analyzed.")
    red_count: int = Field(description="Number of high-risk (illegal/void) clauses detected.")
    yellow_count: int = Field(description="Number of medium-risk (ambiguous) clauses detected.")
    green_count: int = Field(description="Number of compliant/standard clauses detected.")


class FullContractAnalysisResponse(BaseModel):
    filename: str = Field(description="Name of the uploaded contract document.")
    metrics: ContractSummaryMetrics = Field(description="Aggregated risk statistics for the contract.")
    results: List[ClauseAnalysisResponse] = Field(description="Clause-by-clause breakdown.")
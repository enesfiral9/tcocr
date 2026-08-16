from pydantic import BaseModel, Field


class FieldResult(BaseModel):
    value: str = ""
    raw_value: str = ""
    confidence: float = Field(0, ge=0, le=1)
    valid: bool = False


class DocumentResult(BaseModel):
    page: int
    tc_no: FieldResult = Field(default_factory=FieldResult)
    name: FieldResult = Field(default_factory=FieldResult)
    surname: FieldResult = Field(default_factory=FieldResult)
    birth_date: FieldResult = Field(default_factory=FieldResult)
    serial_no: FieldResult = Field(default_factory=FieldResult)
    overall_confidence: float = 0
    requires_review: bool = True
    failed: bool = False
    errors: list[str] = Field(default_factory=list)


class ExportRecord(BaseModel):
    page: int
    tc_no: str = ""
    name: str = ""
    surname: str = ""
    birth_date: str = ""
    serial_no: str = ""
    confidence: float = Field(0, ge=0, le=1)
    requires_review: bool = False


class ExportRequest(BaseModel):
    records: list[ExportRecord]

from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel, Field

# Entifier
class EntifierInput(BaseModel):
    text: str = Field(..., min_length=1)

class EntifierOutput(BaseModel):
    entities: List[str]

# Questor
class QuestorInput(BaseModel):
    text: str = Field(..., min_length=1)
    entities: Optional[List[str]] = None

class QuestorOutput(BaseModel):
    questions: List[str]

# Solver
class SolverInput(BaseModel):
    questions: List[str] = Field(default_factory=list)

class SolverOutput(BaseModel):
    answers: List[str]

# Integrator
class IntegratorInput(BaseModel):
    questions: List[str] = Field(default_factory=list)
    answers: List[str] = Field(default_factory=list)

class IntegratorOutput(BaseModel):
    summary: str
    result: str

# Refiner
class RefinerInput(BaseModel):
    result: str = ""

class RefinerOutput(BaseModel):
    result: str

# Rebaser
class RebaserInput(BaseModel):
    result: str = ""

class RebaserOutput(BaseModel):
    result: str
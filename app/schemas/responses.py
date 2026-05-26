from pydantic import BaseModel
from typing import Generic, TypeVar

DataT = TypeVar("DataT")


class SuccessResponse(BaseModel, Generic[DataT]):
    success: bool = True
    data: DataT


class ErrorDetail(BaseModel):
    message: str
    code: str


class ErrorResponse(BaseModel):
    success: bool = False
    error: ErrorDetail

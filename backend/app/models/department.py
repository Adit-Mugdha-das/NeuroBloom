from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
	from app.models.doctor import Doctor


class Department(SQLModel, table=True):
	"""Hospital department grouping for doctors and patient counts."""
	__tablename__ = "departments"  # type: ignore[assignment]

	id: Optional[int] = Field(default=None, primary_key=True)
	name: str = Field(index=True, unique=True)
	description: Optional[str] = Field(default=None)

	doctors: List["Doctor"] = Relationship(back_populates="department")
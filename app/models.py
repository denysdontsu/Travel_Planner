from datetime import date
from typing import List, Optional
from sqlalchemy import String, Integer, Date, ForeignKey, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class TravelProject(Base):
    __tablename__ = "travel_projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    places: Mapped[List["ProjectPlace"]] = relationship(
        "ProjectPlace",
        back_populates="project",
        cascade="all, delete-orphan"
    )

    @property
    def is_completed(self) -> bool:
        if not self.places:
            return False
        return all(place.is_visited for place in self.places)


class ProjectPlace(Base):
    __tablename__ = "project_places"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("travel_projects.id", ondelete="CASCADE"))
    external_place_id: Mapped[str] = mapped_column(String(50), index=True)
    place_name: Mapped[str] = mapped_column(String(200))
    notes: Mapped[str | None] = mapped_column(String(1000))
    is_visited: Mapped[bool] = mapped_column(default=False)

    project: Mapped["TravelProject"] = relationship("TravelProject", back_populates="places")

    __table_args__ = (
        UniqueConstraint("project_id", "external_place_id", name="uq_project_place"),
    )
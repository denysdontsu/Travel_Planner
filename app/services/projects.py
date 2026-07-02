from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas import ProjectCreate
from app.models import TravelProject, ProjectPlace
from app.services.artic_api import check_place_exists

async def create_travel_project_service(db: AsyncSession, project_in: ProjectCreate) -> TravelProject:
    """
    Create a new travel project with optional pre-validated places.

    Validates each place against the Art Institute of Chicago API before
    persisting. All places are inserted atomically with the project.

    Args:
        db: Active async database session.
        project_in: Validated input schema with project details and
            optional list of places (max 10, no duplicates).

    Returns:
        Newly created TravelProject ORM instance with places loaded.

    Raises:
        HTTPException 404: If any place ID is not found in the Art Institute API.
        SQLAlchemyError: If the database transaction fails.
    """
    validated_places = []
    if project_in.places:
        for place in project_in.places:
            external_place = await check_place_exists(place.external_place_id)
            if not external_place:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Place '{place.external_place_id}' not found in Art Institute API."
                )
            validated_places.append({
                "external_place_id": place.external_place_id,
                "place_name": external_place["title"],
                "notes": place.notes
            })

    db_project = TravelProject(
        name=project_in.name,
        description=project_in.description,
        start_date=project_in.start_date
    )
    db.add(db_project)
    await db.flush()

    for place_data in validated_places:
        db.add(ProjectPlace(
            project_id=db_project.id,
            **place_data
        ))

    await db.commit()

    stmt = select(TravelProject).where(
        TravelProject.id == db_project.id
    ).options(selectinload(TravelProject.places))

    result = await db.execute(stmt)
    return result.scalar_one()

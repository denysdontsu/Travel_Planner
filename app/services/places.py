from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ProjectPlace
from app.schemas import PlaceCreateInput
from app.services.artic_api import check_place_exists
from app.services.projects import get_project_by_id


async def add_place_to_project_service(
    db: AsyncSession,
    project_id: int,
    place_in: PlaceCreateInput
) -> ProjectPlace | None:
    """
    Validate and add a unique external artwork place to an existing travel project.

    Enforces multiple business constraints: verifies project existence, ensures the
    total number of places does not exceed 10, prevents duplicate external place IDs
    within the same project scope, and validates existence via the Art Institute API.

    Args:
        db (AsyncSession): The active database operational session.
        project_id (int): The unique primary key identifier of the target travel project.
        place_in (PlaceCreateInput): The validated input data containing the
            external place ID and user notes.

    Returns:
        Optional[ProjectPlace]: The newly created and persisted ProjectPlace ORM instance,
            or None if the target travel project does not exist.

    Raises:
        HTTPException:
            - 400 Bad Request: If the project already contains the maximum limit of 10 places.
            - 400 Bad Request: If the external place ID already exists in this project.
            - 400 Bad Request: If the external identifier cannot be validated by the ArtIC API.
            - 500 Internal Server Error: If an anomaly occurs during transaction commit.
    """
    # 1. Verify target project existence (with places eagerly loaded)
    db_project = await get_project_by_id(db, project_id)
    if not db_project:
        return None

    # 2. Enforce business rule: Strict maximum ceiling of 10 places per project
    if len(db_project.places) >= 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot add place. This travel project has already reached its maximum limit of 10 places."
        )

    # 3. Enforce business rule: Prevent duplicate external IDs within the same project
    # Cast to string to ensure safe matching against database structure
    target_external_id = str(place_in.external_place_id)
    if any(place.external_place_id == target_external_id for place in db_project.places):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Place with external ID '{target_external_id}' is already registered in this project."
        )

    # 4. Integrate external network validation: Check existence via ArtIC catalog
    external_artwork = await check_place_exists(target_external_id)
    if not external_artwork:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"External place with ID '{target_external_id}' does not exist in the Art Institute catalog."
        )

    # 5. Persist the validated record
    db_place = ProjectPlace(
        project_id=db_project.id,
        external_place_id=target_external_id,
        place_name=external_artwork["title"],
        notes=place_in.notes
    )
    db.add(db_place)
    await db.commit()
    await db.refresh(db_place)
    return db_place


async def get_project_places_service(db: AsyncSession, project_id: int) -> list[ProjectPlace] | None:
    """
    Retrieve all registered places associated with a specific travel project.

    First verifies if the parent project exists. If it is present, extracts and
    returns its internal list of places.

    Args:
        db (AsyncSession): The active database operational session.
        project_id (int): The unique primary key identifier of the parent project.

    Returns:
        Optional[List[ProjectPlace]]: A list of populated place model instances
            linked to the project, or None if the project profile does not exist.

    Raises:
        Exception: If the database execution query fails during project retrieval.
    """
    # Reuse the read function that already loads the project and its nested places
    db_project = await get_project_by_id(db, project_id)
    if not db_project:
        return None

    return list(db_project.places)



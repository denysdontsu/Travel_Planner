from asyncio import gather
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas import ProjectCreate, ProjectUpdate
from app.models import TravelProject, ProjectPlace
from app.services.artic_api import check_place_exists

async def create_travel_project_service(db: AsyncSession, project_in: ProjectCreate) -> TravelProject:
    """
    Create a new travel project with optional pre-validated places.

    Validates each place in parallel against the Art Institute of Chicago API
    before persisting. If any place is not found, returns all invalid IDs at once.
    All valid places are inserted atomically with the project.

    Args:
        db: Active async database session.
        project_in: Validated input schema with project details and
            optional list of places (max 10, no duplicates).

    Returns:
        Newly created TravelProject ORM instance with places loaded.

    Raises:
        HTTPException 404: If any place IDs are not found in the Art Institute API.
            Returns all invalid IDs in a single response.
        SQLAlchemyError: If the database transaction fails.
    """
    results = await gather(
        *[check_place_exists(place.external_place_id) for place in project_in.places]
    )

    invalid_ids = []
    for place, result in zip(project_in.places, results):
        if isinstance(result, Exception) or result is None:
            invalid_ids.append(place.external_place_id)

    if invalid_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Places not found in Art Institute API: {invalid_ids}"
        )

    validated_places = [
        {
            'external_place_id': place.external_place_id,
            'place_name': api_result['title'],
            'notes': place.notes
        } for place, api_result in zip(project_in.places, results)
    ]

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


async def get_project_by_id(db: AsyncSession, project_id: int) -> TravelProject | None:
    """
    Fetch a single travel project by its database identifier.

    Utilizes eager loading (selectinload) to efficiently pull all associated
    places in a single query execution, preventing lazy loading errors.

    Args:
        db (AsyncSession): The active database session.
        project_id (int): The unique database primary key of the project.

    Returns:
        Optional[TravelProject]: The populated database model instance if found,
            otherwise None.

    Raises:
        Exception: If the database execution query fails.
    """
    query = (
        select(TravelProject)
        .where(TravelProject.id == project_id)
        .options(selectinload(TravelProject.places))
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_all_projects(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[TravelProject]:
    """
    Retrieve a list of all travel projects with their associated places.

    Uses eager loading (selectinload) to fetch related places efficiently
    in a single database round-trip, preventing lazy evaluation errors.

    Args:
        db (AsyncSession): The active database session.
        skip (int): The number of project records to skip (for pagination).
            Defaults to 0.
        limit (int): The maximum number of project records to return.
            Defaults to 100.

    Returns:
        list[TravelProject]: A list of populated travel project model instances.

    Raises:
        Exception: If the database execution query fails.
    """
    query = (
        select(TravelProject)
        .options(selectinload(TravelProject.places))
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    return list(result.scalars().all())


async def update_travel_project_service(
    db: AsyncSession,
    project_id: int,
    project_in: ProjectUpdate
) -> TravelProject | None:
    """
    Update the metadata of an existing travel project.

    Fetches the project record by its ID, modifies its baseline attributes
    (name, description, start_date) based on the provided update schema,
    and persists the modifications into the database.

    Args:
        db (AsyncSession): The active database operational session.
        project_id (int): The unique primary key identifier of the project.
        project_in (ProjectUpdate): The validated data schema containing the
            updated attributes for the project.

    Returns:
        Optional[TravelProject]: The updated database model instance with fresh
            attributes, or None if the project does not exist.

    Raises:
        HTTPException:
            - 500 Internal Server Error: If a database mapping or execution anomaly
              occurs during the flush or commit phase.
    """
    # 1. Fetch the existing project using our defined read helper
    db_project = await get_project_by_id(db, project_id)
    if not db_project:
        return None

    # 2. Extract explicitly provided fields and update the ORM model attributes
    update_data = project_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_project, field, value)

    # 3. Commit the changes atomically
    await db.commit()

    stmt = select(TravelProject).where(
        TravelProject.id == db_project.id
    ).options(selectinload(TravelProject.places))
    result = await db.execute(stmt)

    return result.scalar_one()


async def delete_travel_project_service(db: AsyncSession, project_id: int) -> bool:
    """
    Handle the logical validation and physical deletion of a travel project.

    Enforces the core business constraint: a travel project cannot be deleted
    if any of its associated places have already been marked as visited.

    Args:
        db (AsyncSession): The active database operational session.
        project_id (int): The unique primary key identifier of the project.

    Returns:
        bool: True if the project was found and successfully deleted, False
            if the target project does not exist.

    Raises:
        HTTPException:
            - 400 Bad Request: If the project contains one or more places
              marked as visited.
            - 500 Internal Server Error: If a database mapping or processing anomaly
              occurs during execution.
    """
    # 1. Fetch the project along with its related places loaded via selectinload
    db_project = await get_project_by_id(db, project_id)
    if not db_project:
        return False

    # 2. Enforce business rule: Block deletion if any assigned place is visited
    if any(place.is_visited for place in db_project.places):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete the project because at least one place has been marked as visited."
        )

    # 3. Perform atomic deletion
    await db.delete(db_project)
    await db.commit()
    return True

from fastapi import APIRouter, status, HTTPException, Query

from app.core.database import db_dependency
from app.schemas import ProjectCreate, ProjectResponse, ProjectUpdate
from app.services.projects import create_travel_project_service, get_project_by_id, get_all_projects, \
    update_travel_project_service

router = APIRouter(prefix="/projects", tags=["Projects"])

@router.post(
    "/",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new travel project",
    description="Creates a project profile. Can optionally accept up to 10 verified external places."
)
async def create_new_project(
    project_in: ProjectCreate,
    db: db_dependency
):
    """
    Create a new travel project.

    Creates a travel project with optional places imported from the
    Art Institute of Chicago API. The endpoint delegates all business
    validation and persistence logic to the service layer.

    Args:
        project_in: Request payload containing project details and
            optional places.
        db: Active asynchronous database session.

    Returns:
        The newly created travel project.

    Raises:
        HTTPException:
            - 400 Bad Request: If the request violates business rules
              (e.g. too many places or invalid external place IDs).
            - 500 Internal Server Error: If the project cannot be
              persisted due to a database error.
            - 503 Service Unavailable: If the external Art Institute API
              is temporarily unavailable.
    """
    return await create_travel_project_service(db, project_in)


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a travel project by ID",
    description="Fetches a single travel project profile along with all its associated places."
)
async def get_project_endpoint(
    project_id: int,
    db: db_dependency
):
    """
    Expose the HTTP GET endpoint to retrieve a specific travel project.

    Queries the database via the service layer. If the project is discovered,
    it is serialized into a ProjectResponse schema; otherwise, a 404 error is raised.

    Args:
        project_id (int): The path parameter containing the unique project ID.
        db (AsyncSession): Injected database operational session dependency.

    Returns:
        ProjectResponse: A structured API response matching the project profile
            and its nested places.

    Raises:
        HTTPException:
            - 404 Not Found: If no project exists with the provided identifier.
    """
    project = await get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Travel project with ID {project_id} not found."
        )
    return project


@router.get(
    "/",
    response_model=list[ProjectResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all travel projects",
    description="Retrieves a list of all travel projects along with their associated places, supporting pagination."
)
async def get_all_projects_endpoint(
    db: db_dependency,
    skip: int = Query(default=0, ge=0, description="Number of records to skip for pagination"),
    limit: int = Query(default=100, ge=1, le=100, description="Maximum number of records to return")
) -> list[ProjectResponse]:
    """
    Expose the HTTP GET endpoint to retrieve all travel projects.

    Delegates the query execution to the consolidated service layer and
    returns a list of projects serialized into the ProjectResponse schema.

    Args:
        skip (int): Injected query parameter for pagination offset.
        limit (int): Injected query parameter for pagination limit.
        db (AsyncSession): Injected database operational session dependency.

    Returns:
        List[ProjectResponse]: A list of structured API response dictionaries
            representing travel projects.
    """
    return await get_all_projects(db, skip=skip, limit=limit) # type: ignore


@router.put(
    "/{project_id}",
    response_model=ProjectResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a travel project",
    description="Updates the primary metadata (name, description, start_date) of an existing travel project."
)
async def update_project_endpoint(
        project_id: int,
        project_in: ProjectUpdate,
        db: db_dependency
):
    """
    Expose the HTTP PUT endpoint to modify an active travel project.

    Routes the request payload down to the consolidated service layer. If the
    resource exists and updates successfully, it returns the updated profile;
    otherwise, it triggers a 404 Not Found response.

    Args:
        project_id (int): The path parameter containing the targeted project ID.
        project_in (ProjectUpdate): Injected JSON request body payload matching
            the modification requirements.
        db (AsyncSession): Injected database operational session dependency.

    Returns:
        ProjectResponse: A strictly validated API response schema tracking the
            modified project profile.

    Raises:
        HTTPException:
            - 404 Not Found: If no travel project matches the given identifier.
            - 500 Internal Server Error: Propagated directly from the internal execution layer.
    """
    updated_project = await update_travel_project_service(db, project_id, project_in)
    if not updated_project:
        raise HTTPException(status_code=404, detail=f"Travel project with ID {project_id} not found.")

    return updated_project
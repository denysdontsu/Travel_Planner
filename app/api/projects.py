from fastapi import APIRouter, status, HTTPException, Query

from app.core.database import db_dependency
from app.schemas import ProjectCreate, ProjectResponse
from app.services.projects import create_travel_project_service, get_project_by_id, get_all_projects

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
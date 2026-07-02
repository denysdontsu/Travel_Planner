from fastapi import HTTPException, status, APIRouter

from app.core.database import db_dependency
from app.schemas import PlaceResponse, PlaceCreateInput
from app.services.places import add_place_to_project_service, get_project_places_service

router = APIRouter(prefix="/projects", tags=["Projects"]) # такой роутрер

@router.post(
    "/{project_id}/places",
    response_model=PlaceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a place to an existing project",
    description="Validates and registers a unique external museum place into a specified travel project profile."
)
async def add_place_to_project_endpoint(
        project_id: int,
        place_in: PlaceCreateInput,
        db: db_dependency
):
    """
    Expose the HTTP POST endpoint to append a place to a travel project.

    Delegates structural boundary routing, limit checks, and external dependency
    validations down to the centralized project service layer.

    Args:
        project_id (int): The path parameter containing the parent project identifier.
        place_in (PlaceCreateInput): Injected JSON request body payload holding
            external parameters.
        db (AsyncSession): Injected database operational session dependency.

    Returns:
        PlaceResponse: A strictly validated API schema documenting the newly
            persisted link record.

    Raises:
        HTTPException:
            - 404 Not Found: If the parent travel project profile cannot be found.
            - 400 Bad Request: Propagated from the service if validation, duplicate,
              or capacity thresholds fail.
    """
    new_place = await add_place_to_project_service(db, project_id, place_in)
    if not new_place:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Travel project with ID {project_id} not found."
        )

    return PlaceResponse.model_validate(new_place)


@router.get(
    "/{project_id}/places",
    response_model=list[PlaceResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all places for a specific project",
    description="Retrieves the full array of verified museum places linked to the chosen travel project ID."
)
async def get_project_places_endpoint(
        project_id: int,
        db: db_dependency
):
    """
    Expose the HTTP GET endpoint to view places assigned to a travel project.

    Invokes the combined service layer to fetch records. Returns a serialized
    JSON array on success or drops a 404 error if the parent project is missing.

    Args:
        project_id (int): The path parameter indicating the parent travel project.
        db (AsyncSession): Injected database operational session dependency.

    Returns:
        List[PlaceResponse]: A list of structured place profiles assigned to the project.

    Raises:
        HTTPException:
            - 404 Not Found: If the parent travel project profile cannot be found.
    """
    places = await get_project_places_service(db, project_id)
    if places is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Travel project with ID {project_id} not found."
        )

    # Explicit conversion to satisfy static type checkers / linters completely
    return [PlaceResponse.model_validate(p) for p in places]
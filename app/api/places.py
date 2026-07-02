from fastapi import HTTPException, status, APIRouter

from app.core.database import db_dependency
from app.schemas import PlaceResponse, PlaceCreateInput
from app.services.places import add_place_to_project_service

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



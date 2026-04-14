"""
Todoist integration service.

Replicates what n8n's Todoist nodes did:
  - sync_ingredients(token, project_id, ingredients, recipe_title)
    → adds each ingredient as a task in the target Todoist project

  - get_projects(token) → list of {id, name} for the user's projects
  - verify_token(token) → True if token is valid
  - create_project(token, name) → new project id
"""
import logging

from todoist_api_python.api import TodoistAPI

logger = logging.getLogger(__name__)


def _api(token: str) -> TodoistAPI:
    return TodoistAPI(token)


def verify_token(token: str) -> bool:
    """Return True if the Todoist token is valid (makes a lightweight API call)."""
    try:
        _api(token).get_projects()
        return True
    except Exception as exc:
        logger.warning("Todoist token verification failed: %s", exc)
        return False


def get_projects(token: str) -> list[dict]:
    """Return list of {id, name} for all user projects."""
    try:
        projects = _api(token).get_projects()
        return [{"id": p.id, "name": p.name} for p in projects]
    except Exception as exc:
        logger.error("Failed to fetch Todoist projects: %s", exc)
        raise


def create_project(token: str, name: str) -> str:
    """Create a new Todoist project and return its id."""
    project = _api(token).add_project(name=name)
    return project.id


def sync_ingredients(
    token: str,
    project_id: str,
    ingredients: list[str],
    recipe_title: str = "",
) -> int:
    """
    Add each ingredient as a task in the given Todoist project.

    Returns the number of tasks successfully created.
    """
    api = _api(token)
    created = 0

    for ingredient in ingredients:
        item = ingredient.strip()
        if not item:
            continue
        try:
            api.add_task(
                content=item,
                project_id=project_id,
                description=f"From: {recipe_title}" if recipe_title else "",
            )
            created += 1
        except Exception as exc:
            # Log but continue — partial sync is better than total failure
            logger.warning("Failed to add Todoist task '%s': %s", item, exc)

    logger.info(
        "Synced %d/%d ingredients to Todoist project %s",
        created,
        len(ingredients),
        project_id,
    )
    return created

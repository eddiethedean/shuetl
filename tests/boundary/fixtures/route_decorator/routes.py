from fastapi import APIRouter

router = APIRouter()


@router.get("/duplicate")
def duplicate_route() -> dict[str, str]:
    return {"status": "invalid"}

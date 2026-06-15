from fastapi import APIRouter

router = APIRouter()

@router.get("/users-test")
def users_test():
    return {"message": "Users router working"}
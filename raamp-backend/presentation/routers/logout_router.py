from fastapi import APIRouter, Response, status

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/logout", status_code=status.HTTP_200_OK)
def logout(response: Response):
    # Remove the session cookie (assuming JWT in HttpOnly cookie)
    response.delete_cookie(key="access_token")
    return {"message": "Logged out successfully."}

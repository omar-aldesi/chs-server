from pydantic import BaseModel


class FeedbackIn(BaseModel):
    log_id: int
    user_rating: int
    user_feedback: str | None = None
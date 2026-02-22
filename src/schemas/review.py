from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ReviewCreate(BaseModel):
    """Схема для создания отзыва"""
    master_id: Optional[int] = None
    salon_id: Optional[int] = None
    appointment_id: int
    rating: int = Field(..., ge=1, le=5, description="Оценка от 1 до 5 звёзд")
    text: Optional[str] = Field(None, max_length=1000)
    
    class Config:
        json_schema_extra = {
            "example": {
                "master_id": 1,
                "appointment_id": 42,
                "rating": 5,
                "text": "Отличный мастер! Очень доволен работой."
            }
        }


class ReviewUpdate(BaseModel):
    """Схема для обновления отзыва (редактирование)"""
    rating: Optional[int] = Field(None, ge=1, le=5)
    text: Optional[str] = Field(None, max_length=1000)


class ReviewResponse(BaseModel):
    """Схема ответа с информацией об отзыве"""
    id: int
    user_id: int
    master_id: Optional[int]
    salon_id: Optional[int]
    appointment_id: int
    rating: int
    text: Optional[str]
    is_moderated: bool
    created_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True


class RatingStatsResponse(BaseModel):
    """Статистика рейтинга для мастера/салона"""
    average_rating: float
    total_reviews: int
    one_star: int
    two_star: int
    three_star: int
    four_star: int
    five_star: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "average_rating": 4.7,
                "total_reviews": 156,
                "one_star": 2,
                "two_star": 5,
                "three_star": 15,
                "four_star": 48,
                "five_star": 86
            }
        }

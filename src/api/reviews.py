from fastapi import APIRouter, Depends, Query, status

from src.core.security import get_user_from_id, get_admin_from_id
from src.core.database import get_db_session
from src.models import users as DBUser
from src.models import admins as DBAdmin
from src.services.review_service import ReviewService
from src.schemas.review import ReviewCreate, ReviewUpdate, ReviewResponse, RatingStatsResponse

from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/v1/reviews", tags=["reviews"])
admin_router = APIRouter(prefix="/admin/reviews", tags=["admin_reviews"])


async def get_review_service(session: AsyncSession = Depends(get_db_session)) -> ReviewService:
    """Создание сервиса отзывов"""
    return ReviewService(session)


@router.post(
    "/",
    response_model=ReviewResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать отзыв"
)
async def create_review(
    review_data: ReviewCreate,
    user: DBUser = Depends(get_user_from_id),
    service: ReviewService = Depends(get_review_service)
):
    """
    Создание нового отзыва.
    
    **Требования:**
    - Пользователь аутентифицирован
    - Имеет завершённое назначение в указанном салоне/у указанного мастера
    - Не оставлял отзыв на это же назначение ранее
    
    Args:
        review_data: Данные отзыва
        user: Текущий пользователь (из JWT токена)
        service: Сервис отзывов (внедряется через DI)
        
    Returns:
        ReviewResponse: Созданный отзыв
    """
    review = await service.create_review(user.id, review_data)
    return review


@router.get(
    "/",
    response_model=list[ReviewResponse],
    summary="Список отзывов"
)
async def get_reviews(
    master_id: int | None = Query(None, description="Фильтр по ID мастера"),
    salon_id: int | None = Query(None, description="Фильтр по ID салона"),
    limit: int = Query(20, ge=1, le=100, description="Количество результатов"),
    offset: int = Query(0, ge=0, description="Смещение"),
    sort_by: str = Query("created_at", description="Сортировка по полю (created_at, rating)"),
    order: str = Query("desc", description="Порядок (asc, desc)"),
    service: ReviewService = Depends(get_review_service)
):
    """
    Получение списка отзывов.
    
    **Параметры:**
    - `master_id`: Фильтр по мастеру
    - `salon_id`: Фильтр по салону
    - `sort_by`: Сортировка по полю (created_at, rating)
    - `order`: Порядок (asc, desc)
    - `limit`: Количество результатов (макс 100)
    - `offset`: Смещение для пагинации
    
    Args:
        master_id: ID мастера для фильтра
        salon_id: ID салона для фильтра
        limit: Количество результатов
        offset: Смещение
        sort_by: Поле для сортировки
        order: Порядок сортировки
        service: Сервис отзывов (внедряется через DI)
        
    Returns:
        list[ReviewResponse]: Список отзывов
    """
    reviews = await service.get_reviews(
        master_id=master_id,
        salon_id=salon_id,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        order=order
    )
    return reviews


@router.get(
    "/masters/{master_id}/rating",
    response_model=RatingStatsResponse,
    summary="Рейтинг мастера"
)
async def get_master_rating(
    master_id: int,
    service: ReviewService = Depends(get_review_service)
):
    """
    Получение статистики рейтинга мастера
    
    Args:
        master_id: ID мастера
        service: Сервис отзывов (внедряется через DI)
        
    Returns:
        RatingStatsResponse: Статистика рейтинга
    """
    stats = await service.get_rating_stats(master_id=master_id)
    return stats


@router.get(
    "/salons/{salon_id}/rating",
    response_model=RatingStatsResponse,
    summary="Рейтинг салона"
)
async def get_salon_rating(
    salon_id: int,
    service: ReviewService = Depends(get_review_service)
):
    """
    Получение статистики рейтинга салона
    
    Args:
        salon_id: ID салона
        service: Сервис отзывов (внедряется через DI)
        
    Returns:
        RatingStatsResponse: Статистика рейтинга
    """
    stats = await service.get_rating_stats(salon_id=salon_id)
    return stats


@router.delete(
    "/{review_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить отзыв"
)
async def delete_review(
    review_id: int,
    reason: str | None = Query(None, description="Причина удаления"),
    user: DBUser = Depends(get_user_from_id),
    service: ReviewService = Depends(get_review_service)
):
    """
    Удаление отзыва (только для автора).
    
    **Требования:**
    - Пользователь является автором отзыва
    
    Args:
        review_id: ID отзыва для удаления
        reason: Причина удаления (опционально)
        user: Текущий пользователь (из JWT токена)
        service: Сервис отзывов (внедряется через DI)
        
    Returns:
        None: Пустой ответ (204 No Content)
    """
    await service.delete_review(user.id, review_id, reason)
    return None


@router.put(
    "/{review_id}",
    response_model=ReviewResponse,
    summary="Обновить отзыв"
)
async def update_review(
    review_id: int,
    update_data: ReviewUpdate,
    user: DBUser = Depends(get_user_from_id),
    service: ReviewService = Depends(get_review_service)
):
    """
    Редактирование отзыва (только для автора).
    
    Args:
        review_id: ID отзыва для редактирования
        update_data: Новые данные отзыва
        user: Текущий пользователь (из JWT токена)
        service: Сервис отзывов (внедряется через DI)
        
    Returns:
        ReviewResponse: Обновлённый отзыв
    """
    review = await service.update_review(user.id, review_id, update_data)
    return review




@admin_router.get(
    "/",
    response_model=list[ReviewResponse],
    summary="Список всех отзывов (админ)"
)
async def get_all_reviews_admin(
    master_id: int | None = Query(None, description="Фильтр по мастеру"),
    salon_id: int | None = Query(None, description="Фильтр по салону"),
    is_moderated: bool | None = Query(None, description="Фильтр по модерации (True/False/None для всех)"),
    limit: int = Query(50, ge=1, le=500, description="Количество результатов"),
    offset: int = Query(0, ge=0, description="Смещение"),
    sort_by: str = Query("created_at", description="Сортировка (created_at, rating)"),
    order: str = Query("desc", description="Порядок (asc, desc)"),
    admin: DBAdmin = Depends(get_admin_from_id),
    service: ReviewService = Depends(get_review_service)
):
    """
    Получение всех отзывов для администратора.
    
    Доступно только авторизованным администраторам.
    
    Args:
        master_id: Фильтр по мастеру
        salon_id: Фильтр по салону
        is_moderated: Фильтр по статусу модерации
        limit: Количество результатов (макс 500)
        offset: Смещение для пагинации
        sort_by: Поле для сортировки
        order: Порядок сортировки
        admin: Текущий администратор
        service: Сервис отзывов
        
    Returns:
        list[ReviewResponse]: Список всех отзывов
    """
    reviews = await service.get_all_reviews_admin(
        master_id=master_id,
        salon_id=salon_id,
        is_moderated=is_moderated,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        order=order
    )
    return reviews


@admin_router.get(
    "/salon/{salon_id}",
    response_model=list[ReviewResponse],
    summary="Отзывы конкретного салона (админ)"
)
async def get_salon_reviews_admin(
    salon_id: int,
    is_moderated: bool | None = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    admin: DBAdmin = Depends(get_admin_from_id),
    service: ReviewService = Depends(get_review_service)
):
    """
    Получение отзывов конкретного салона для администратора.
    
    Args:
        salon_id: ID салона
        is_moderated: Фильтр по модерации
        limit: Количество результатов
        offset: Смещение
        admin: Текущий администратор
        service: Сервис отзывов
        
    Returns:
        list[ReviewResponse]: Список отзывов салона
    """
    reviews = await service.get_reviews(
        salon_id=salon_id,
        limit=limit,
        offset=offset
    )
    
    if is_moderated is not None:
        reviews = [r for r in reviews if r.is_moderated == is_moderated]
    
    return reviews


@admin_router.put(
    "/{review_id}/approve",
    response_model=ReviewResponse,
    summary="Одобрить отзыв"
)
async def approve_review(
    review_id: int,
    admin: DBAdmin = Depends(get_admin_from_id),
    service: ReviewService = Depends(get_review_service)
):
    """
    Одобрение отзыва модератором.
    
    Args:
        review_id: ID отзыва
        admin: Текущий администратор
        service: Сервис отзывов
        
    Returns:
        ReviewResponse: Одобренный отзыв
    """
    review = await service.approve_review(review_id)
    return review


@admin_router.put(
    "/{review_id}/reject",
    response_model=ReviewResponse,
    summary="Отклонить отзыв"
)
async def reject_review(
    review_id: int,
    reason: str = Query(..., description="Причина отклонения"),
    admin: DBAdmin = Depends(get_admin_from_id),
    service: ReviewService = Depends(get_review_service)
):
    """
    Отклонение отзыва модератором (мягкое удаление).
    
    Args:
        review_id: ID отзыва
        reason: Причина отклонения
        admin: Текущий администратор
        service: Сервис отзывов
        
    Returns:
        ReviewResponse: Отклоненный отзыв
    """
    review = await service.reject_review(review_id, reason)
    return review


@admin_router.delete(
    "/{review_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить отзыв (админ)"
)
async def delete_review_admin(
    review_id: int,
    reason: str = Query(..., description="Причина удаления"),
    admin: DBAdmin = Depends(get_admin_from_id),
    service: ReviewService = Depends(get_review_service)
):
    """
    Удаление отзыва администратором.
    
    Args:
        review_id: ID отзыва
        reason: Причина удаления
        admin: Текущий администратор
        service: Сервис отзывов
        
    Returns:
        None: Пустой ответ (204 No Content)
    """
    await service.delete_review_admin(review_id, admin.id, reason)
    return None


@admin_router.get(
    "/statistics",
    summary="Общая статистика отзывов"
)
async def get_reviews_statistics(
    admin: DBAdmin = Depends(get_admin_from_id),
    service: ReviewService = Depends(get_review_service)
):
    """
    Получение общей статистики по отзывам.
    
    Args:
        admin: Текущий администратор
        service: Сервис отзывов
        
    Returns:
        dict: Статистика отзывов
    """
    stats = await service.get_reviews_statistics()
    return stats


@admin_router.get(
    "/salon/{salon_id}/statistics",
    summary="Статистика отзывов салона"
)
async def get_salon_reviews_statistics(
    salon_id: int,
    admin: DBAdmin = Depends(get_admin_from_id),
    service: ReviewService = Depends(get_review_service)
):
    """
    Получение статистики отзывов конкретного салона.
    
    Args:
        salon_id: ID салона
        admin: Текущий администратор
        service: Сервис отзывов
        
    Returns:
        dict: Статистика отзывов салона
    """
    stats = await service.get_salon_reviews_statistics(salon_id)
    return stats

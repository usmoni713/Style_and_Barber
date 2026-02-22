from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from src.models import reviews as DBReview
from src.models import appointments as DBAppointment
from src.models import masters as DBMaster
from src.models import salons as DBSalon
from src.repository.base_repo import BaseRepository
from src.schemas.review import ReviewCreate, ReviewUpdate, RatingStatsResponse


class ReviewService:
    """Сервис для управления отзывами"""
    
    def __init__(self, session: AsyncSession):
        """
        Инициализация сервиса с сессией БД
        
        Args:
            session: Асинхронная сессия SQLAlchemy
        """
        self.session = session
        self.repo = BaseRepository(DBReview, session)
    
    async def create_review(self, user_id: int, review_data: ReviewCreate) -> DBReview:
        """
        Создание отзыва с проверкой прав доступа.
        
        Проверяет:
        1. Что пользователь имеет завершённое назначение
        2. Что назначение связано с целевым мастером/салоном
        3. Что пользователь не оставлял отзыв уже
        
        Args:
            user_id: ID пользователя-автора отзыва
            review_data: Данные отзыва (ReviewCreate)
            
        Returns:
            DBReview: Созданный отзыв
            
        Raises:
            HTTPException: Если нарушены условия создания отзыва
        """
        async with self.session.begin():
            if not review_data.master_id and not review_data.salon_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Укажите master_id или salon_id"
                )
            
            appointment = await self.session.execute(
                select(DBAppointment).where(
                    DBAppointment.id == review_data.appointment_id,
                    DBAppointment.client_id == user_id
                )
            )
            appointment = appointment.scalar_one_or_none()
            
            if not appointment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Назначение не найдено"
                )
            
            if appointment.status.value != "completed":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Отзыв можно оставить только после завершения услуги. Текущий статус: {appointment.status.value}"
                )
            
            if review_data.master_id and appointment.master_id != review_data.master_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Назначение не связано с указанным мастером"
                )
            
            if review_data.salon_id and appointment.salon_id != review_data.salon_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Назначение не связано с указанным салоном"
                )
            
            existing_review = await self.session.execute(
                select(DBReview).where(
                    DBReview.appointment_id == review_data.appointment_id,
                    DBReview.user_id == user_id
                )
            )
            
            if existing_review.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Вы уже оставили отзыв на это назначение"
                )
            
            new_review = DBReview(
                user_id=user_id,
                master_id=review_data.master_id,
                salon_id=review_data.salon_id,
                appointment_id=review_data.appointment_id,
                rating=review_data.rating,
                text=review_data.text,
                is_moderated=False
            )
            self.session.add(new_review)
            await self.session.flush()
            
        return new_review
    
    async def get_reviews(
        self,
        master_id: int | None = None,
        salon_id: int | None = None,
        limit: int = 20,
        offset: int = 0,
        sort_by: str = "created_at",
        order: str = "desc"
    ) -> list[DBReview]:
        """Получение списка отзывов с фильтрацией"""
        
        query = select(DBReview).where(DBReview.is_active == True)
        
        if master_id:
            query = query.where(DBReview.master_id == master_id)
        
        if salon_id:
            query = query.where(DBReview.salon_id == salon_id)
        
        if sort_by == "rating":
            if order.lower() == "desc":
                query = query.order_by(DBReview.rating.desc())
            else:
                query = query.order_by(DBReview.rating.asc())
        else:  # по умолчанию created_at
            if order.lower() == "desc":
                query = query.order_by(DBReview.created_at.desc())
            else:
                query = query.order_by(DBReview.created_at.asc())
        
        query = query.limit(limit).offset(offset)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_rating_stats(
        self,
        master_id: int | None = None,
        salon_id: int | None = None
    ) -> RatingStatsResponse:
        """
        Получение статистики рейтинга
        
        Args:
            master_id: ID мастера (если фильтруем по мастеру)
            salon_id: ID салона (если фильтруем по салону)
            
        Returns:
            RatingStatsResponse: Статистика рейтинга
        """
        
        query = select(DBReview).where(DBReview.is_active == True)
        
        if master_id:
            query = query.where(DBReview.master_id == master_id)
        
        if salon_id:
            query = query.where(DBReview.salon_id == salon_id)
        
        result = await self.session.execute(query)
        reviews = result.scalars().all()
        
        if not reviews:
            return RatingStatsResponse(
                average_rating=0.0,
                total_reviews=0,
                one_star=0,
                two_star=0,
                three_star=0,
                four_star=0,
                five_star=0
            )
        
        ratings = [r.rating for r in reviews]
        average = sum(ratings) / len(ratings)
        
        star_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for r in reviews:
            star_counts[r.rating] += 1
        
        return RatingStatsResponse(
            average_rating=round(average, 1),
            total_reviews=len(reviews),
            one_star=star_counts[1],
            two_star=star_counts[2],
            three_star=star_counts[3],
            four_star=star_counts[4],
            five_star=star_counts[5]
        )
    
    async def delete_review(self, user_id: int, review_id: int, reason: str | None = None) -> DBReview:
        """
        Удаление отзыва (мягкое удаление).
        Может удалять только автор отзыва.
        
        Args:
            user_id: ID пользователя (должен быть автором)
            review_id: ID отзыва
            reason: Причина удаления (опционально)
            
        Returns:
            DBReview: Удалённый отзыв
            
        Raises:
            HTTPException: Если отзыв не найден или нет прав
        """
        
        review = await self.repo.get_by_id(review_id)
        if not review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Отзыв не найден"
            )
        
        
        if review.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="У вас нет прав удалить этот отзыв"
            )
        
       
        review.is_active = False
        review.reason_for_deletion = reason or "Удалено пользователем"
        await self.session.commit()
        
        return review
    
    async def update_review(
        self,
        user_id: int,
        review_id: int,
        update_data: ReviewUpdate
    ) -> DBReview:
        """
        Обновление отзыва (редактирование).
        Только автор может редактировать свой отзыв.
        
        Args:
            user_id: ID пользователя (должен быть автором)
            review_id: ID отзыва
            update_data: Новые данные отзыва
            
        Returns:
            DBReview: Обновлённый отзыв
            
        Raises:
            HTTPException: Если отзыв не найден или нет прав
        """
        
        review = await self.repo.get_by_id(review_id)
        if not review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Отзыв не найден"
            )
        
        if review.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="У вас нет прав редактировать этот отзыв"
            )
        
        if update_data.rating is not None:
            review.rating = update_data.rating
        
        if update_data.text is not None:
            review.text = update_data.text
        
        await self.session.commit()
        return review
    
    async def get_all_reviews_admin(
        self,
        master_id: int | None = None,
        salon_id: int | None = None,
        is_moderated: bool | None = None,
        limit: int = 50,
        offset: int = 0,
        sort_by: str = "created_at",
        order: str = "desc"
    ):
        """Получение всех отзывов для администратора"""
        
        query = select(DBReview)
        
        if master_id:
            query = query.where(DBReview.master_id == master_id)
        
        if salon_id:
            query = query.where(DBReview.salon_id == salon_id)
        
        if is_moderated is not None:
            query = query.where(DBReview.is_moderated == is_moderated)
        
        sort_column = getattr(DBReview, sort_by, DBReview.created_at)
        if order.lower() == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        
        query = query.limit(limit).offset(offset)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def approve_review(self, review_id: int) -> DBReview:
        """Одобрение отзыва"""
        
        review = await self.repo.get_by_id(review_id)
        if not review:
            raise HTTPException(
                status_code=404,
                detail="Отзыв не найден"
            )
        
        review.is_moderated = True
        await self.session.commit()
        return review
    
    async def reject_review(self, review_id: int, reason: str) -> DBReview:
        """Отклонение отзыва (мягкое удаление)"""
        
        review = await self.repo.get_by_id(review_id)
        if not review:
            raise HTTPException(
                status_code=404,
                detail="Отзыв не найден"
            )
        
        review.is_active = False
        review.reason_for_deletion = reason
        await self.session.commit()
        return review
    
    async def delete_review_admin(self, review_id: int, admin_id: int, reason: str) -> DBReview:
        """Удаление отзыва администратором"""
        
        review = await self.repo.get_by_id(review_id)
        if not review:
            raise HTTPException(
                status_code=404,
                detail="Отзыв не найден"
            )
        
        review.is_active = False
        review.reason_for_deletion = f"Удалено админом {admin_id}: {reason}"
        await self.session.commit()
        return review
    
    async def get_reviews_statistics(self):
        """Получение общей статистики по отзывам"""
        
        query = select(DBReview).where(DBReview.is_active == True)
        result = await self.session.execute(query)
        reviews = result.scalars().all()
        
        total_reviews = len(reviews)
        if total_reviews == 0:
            return {
                "total_reviews": 0,
                "average_rating": 0.0,
                "moderated_reviews": 0,
                "unmoderated_reviews": 0,
                "ratings_distribution": {
                    "one_star": 0,
                    "two_star": 0,
                    "three_star": 0,
                    "four_star": 0,
                    "five_star": 0
                }
            }
        
        ratings = [r.rating for r in reviews]
        average_rating = sum(ratings) / len(ratings)
        
        moderated_count = len([r for r in reviews if r.is_moderated])
        unmoderated_count = total_reviews - moderated_count
        
        star_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for r in reviews:
            star_counts[r.rating] += 1
        
        return {
            "total_reviews": total_reviews,
            "average_rating": round(average_rating, 1),
            "moderated_reviews": moderated_count,
            "unmoderated_reviews": unmoderated_count,
            "ratings_distribution": {
                "one_star": star_counts[1],
                "two_star": star_counts[2],
                "three_star": star_counts[3],
                "four_star": star_counts[4],
                "five_star": star_counts[5]
            }
        }
    
    async def get_salon_reviews_statistics(self, salon_id: int):
        """Получение статистики отзывов конкретного салона"""
        
        query = select(DBReview).where(
            (DBReview.salon_id == salon_id) & (DBReview.is_active == True)
        )
        result = await self.session.execute(query)
        reviews = result.scalars().all()
        
        total_reviews = len(reviews)
        if total_reviews == 0:
            return {
                "salon_id": salon_id,
                "total_reviews": 0,
                "average_rating": 0.0,
                "moderated_reviews": 0,
                "unmoderated_reviews": 0,
                "ratings_distribution": {
                    "one_star": 0,
                    "two_star": 0,
                    "three_star": 0,
                    "four_star": 0,
                    "five_star": 0
                }
            }
        
        ratings = [r.rating for r in reviews]
        average_rating = sum(ratings) / len(ratings)
        
        moderated_count = len([r for r in reviews if r.is_moderated])
        unmoderated_count = total_reviews - moderated_count
        
        star_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for r in reviews:
            star_counts[r.rating] += 1
        
        return {
            "salon_id": salon_id,
            "total_reviews": total_reviews,
            "average_rating": round(average_rating, 1),
            "moderated_reviews": moderated_count,
            "unmoderated_reviews": unmoderated_count,
            "ratings_distribution": {
                "one_star": star_counts[1],
                "two_star": star_counts[2],
                "three_star": star_counts[3],
                "four_star": star_counts[4],
                "five_star": star_counts[5]
            }
        }

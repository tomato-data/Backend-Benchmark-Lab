from fastapi import APIRouter, Depends
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.connection import get_db
from src.infrastructure.database.models import UserWideModel, AuthorModel, PostModel
from src.presentation.schemas.aggregation import (
    CountComparisonResponse,
    CountryStatsResponse,
    AuthorStatsResponse,
)


router = APIRouter(prefix="/aggregation", tags=["aggregation"])


# ============================================
# A. 단순 집계 비교: COUNT(*) vs COUNT(id) vs COUNT(DISTINCT)
# ============================================
@router.get("/count/orm", response_model=CountComparisonResponse)
async def count_comparison_orm(db: AsyncSession = Depends(get_db)):
    """
    ORM을 사용한 COUNT 비교
    - COUNT(*): 전체 행 수
    - COUNT(id): NULL 제외 행 수 (id는 NOT NULL이므로 동일)
    - COUNT(DISTINCT status): 고유 status 수
    """
    # COUNT(*)
    result_star = await db.execute(select(func.count()).select_from(UserWideModel))
    count_star = result_star.scalar() or 0

    # COUNT(id)
    result_id = await db.execute(select(func.count(UserWideModel.id)))
    count_id = result_id.scalar() or 0

    # COUNT(DISTINCT status)
    result_distinct = await db.execute(
        select(func.count(func.distinct(UserWideModel.status)))
    )
    count_distinct = result_distinct.scalar() or 0

    return CountComparisonResponse(
        count_star=count_star,
        count_id=count_id,
        count_distinct_status=count_distinct,
    )


@router.get("/count/raw", response_model=CountComparisonResponse)
async def count_comparison_raw(db: AsyncSession = Depends(get_db)):
    """
    Raw SQL을 사용한 COUNT 비교
    """
    query = text("""
        SELECT
            COUNT(*) as count_star,
            COUNT(id) as count_id,
            COUNT(DISTINCT status) as count_distinct_status
        FROM users_wide
    """)
    result = await db.execute(query)
    row = result.fetchone()

    if row is None:
        return CountComparisonResponse(
            count_star=0,
            count_id=0,
            count_distinct_status=0,
        )

    return CountComparisonResponse(
        count_star=row.count_star,
        count_id=row.count_id,
        count_distinct_status=row.count_distinct_status,
    )


# ============================================
# B. GROUP BY 집계: 국가별 통계
# ============================================
@router.get("/stats/country/orm", response_model=list[CountryStatsResponse])
async def country_stats_orm(
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
):
    """
    ORM을 사용한 국가별 통계
    - GROUP BY country
    - COUNT, SUM, AVG
    """
    query = (
        select(
            UserWideModel.country,
            func.count(UserWideModel.id).label("user_count"),
            func.sum(UserWideModel.login_count).label("total_logins"),
            func.avg(UserWideModel.login_count).label("avg_logins"),
        )
        .group_by(UserWideModel.country)
        .order_by(func.count(UserWideModel.id).desc())
        .limit(limit)
    )

    result = await db.execute(query)
    rows = result.all()

    return [
        CountryStatsResponse(
            country=row.country or "",
            user_count=row.user_count,
            total_logins=row.total_logins or 0,
            avg_logins=float(row.avg_logins or 0),
        )
        for row in rows
    ]


@router.get("/stats/country/raw", response_model=list[CountryStatsResponse])
async def country_stats_raw(
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
):
    """
    Raw SQL을 사용한 국가별 통계
    """
    query = text("""
        SELECT
            country,
            COUNT(id) as user_count,
            SUM(login_count) as total_logins,
            AVG(login_count) as avg_logins
        FROM users_wide
        GROUP BY country
        ORDER BY user_count DESC
        LIMIT :limit
    """)

    result = await db.execute(query, {"limit": limit})
    rows = result.all()

    return [
        CountryStatsResponse(
            country=row.country or "",
            user_count=row.user_count,
            total_logins=row.total_logins or 0,
            avg_logins=float(row.avg_logins or 0),
        )
        for row in rows
    ]


# ============================================
# C. 다중 테이블 집계: 작가별 게시글 통계
# ============================================
@router.get("/stats/author/orm", response_model=list[AuthorStatsResponse])
async def author_stats_orm(
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
):
    """
    ORM을 사용한 작가별 게시글 통계 (JOIN + GROUP BY)
    """
    query = (
        select(
            AuthorModel.id.label("author_id"),
            AuthorModel.name.label("author_name"),
            func.count(PostModel.id).label("post_count"),
            func.sum(PostModel.view_count).label("total_views"),
            func.avg(PostModel.view_count).label("avg_views"),
        )
        .join(PostModel, AuthorModel.id == PostModel.author_id)
        .group_by(AuthorModel.id, AuthorModel.name)
        .order_by(func.count(PostModel.id).desc())
        .limit(limit)
    )

    result = await db.execute(query)
    rows = result.all()

    return [
        AuthorStatsResponse(
            author_id=row.author_id,
            author_name=row.author_name,
            post_count=row.post_count,
            total_views=row.total_views or 0,
            avg_views=float(row.avg_views or 0),
        )
        for row in rows
    ]


@router.get("/stats/author/raw", response_model=list[AuthorStatsResponse])
async def author_stats_raw(
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
):
    """
    Raw SQL을 사용한 작가별 게시글 통계
    """
    query = text("""
        SELECT
            a.id as author_id,
            a.name as author_name,
            COUNT(p.id) as post_count,
            SUM(p.view_count) as total_views,
            AVG(p.view_count) as avg_views
        FROM authors a
        JOIN posts p ON a.id = p.author_id
        GROUP BY a.id, a.name
        ORDER BY post_count DESC
        LIMIT :limit
    """)
    result = await db.execute(query, {"limit": limit})
    rows = result.all()

    return [
        AuthorStatsResponse(
            author_id=row.author_id,
            author_name=row.author_name,
            post_count=row.post_count,
            total_views=row.total_views or 0,
            avg_views=float(row.avg_views or 0),
        )
        for row in rows
    ]

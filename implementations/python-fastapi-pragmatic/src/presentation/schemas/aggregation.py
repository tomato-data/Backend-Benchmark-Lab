from pydantic import BaseModel


# ============================================
# A. 단순 집계 결과
# ============================================
class SimpleCountResponse(BaseModel):
    """COUNT 결과"""

    count: int


class CountComparisonResponse(BaseModel):
    """COUNT 방식별 비교 결과"""

    count_star: int  # COUNT(*)
    count_id: int  # COUNT(id)
    count_distinct_status: int  # COUNT(DISTINCT status)


# ============================================
# B. GROUP BY 집계 결과
# ============================================
class CountryStatsResponse(BaseModel):
    """국가별 통계"""

    country: str
    user_count: int
    total_logins: int
    avg_logins: float


class StatusStatsResponse(BaseModel):
    """상태별 통계"""

    status: str
    user_count: int


# ============================================
# C. 다중 테이블 집계 결과 (authors + posts)
# ============================================
class AuthorStatsResponse(BaseModel):
    """작가별 게시글 통계"""

    author_id: int
    author_name: str
    post_count: int
    total_views: int
    avg_views: float

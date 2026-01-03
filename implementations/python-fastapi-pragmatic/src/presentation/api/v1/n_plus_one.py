from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.connection import get_db
from src.infrastructure.database.models import AuthorModel, PostModel
from src.presentation.schemas.n_plus_one import AuthorWithPostsResponse


router = APIRouter(prefix="/n-plus-one", tags=["n-plus-one"])


@router.get("/lazy", response_model=list[AuthorWithPostsResponse])
async def get_authors_lazy(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """
    N+1 문제 발생 (Lazy Loading 시뮬레이션)
    - 1번: SELECT * FROM authors
    - N번: 각 author마다 SELECT * FROM posts WHERE author_id = ?
    """
    # 1. Authors 조회
    authors_query = select(AuthorModel).limit(limit)
    result = await db.execute(authors_query)
    authors = result.scalars().all()

    # 2. 각 author마다 개별 posts 쿼리 (N+1 발생!) + dict 변환
    response = []
    for author in authors:
        posts_query = select(PostModel).where(PostModel.author_id == author.id)
        posts_result = await db.execute(posts_query)
        posts = posts_result.scalars().all()

        response.append({
            "id": author.id,
            "name": author.name,
            "email": author.email,
            "bio": author.bio,
            "created_at": author.created_at,
            "posts": [
                {
                    "id": p.id,
                    "title": p.title,
                    "content": p.content,
                    "view_count": p.view_count,
                    "created_at": p.created_at,
                }
                for p in posts
            ],
        })

    return response


@router.get("/eager", response_model=list[AuthorWithPostsResponse])
async def get_authors_eager(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """
    Eager Loading (joinedload) - 1번의 JOIN 쿼리
    - SELECT authors.*, posts.* FROM authors LEFT JOIN posts ON ...
    """
    query = select(AuthorModel).options(joinedload(AuthorModel.posts)).limit(limit)
    result = await db.execute(query)
    authors = result.unique().scalars().all()
    return authors


@router.get("/subquery", response_model=list[AuthorWithPostsResponse])
async def get_authors_subquery(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """
    Subquery Loading (selectinload) - 2번의 쿼리
    - 1번: SELECT * FROM authors
    - 2번: SELECT * FROM posts WHERE author_id IN (...)
    """
    query = select(AuthorModel).options(selectinload(AuthorModel.posts)).limit(limit)
    result = await db.execute(query)
    authors = result.scalars().all()
    return authors

from typing import Any, Generic, TypeVar
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import Session
from app.database import get_db
from app.security import allow_roles, current_user

ModelT = TypeVar("ModelT")
InT = TypeVar("InT", bound=BaseModel)


def serialize(row: Any) -> dict[str, Any]:
    return {column.key: getattr(row, column.key) for column in inspect(row).mapper.column_attrs}


def create_crud_router(model: type[ModelT], schema: type[InT], id_name: str, prefix: str, search_column: str | None = None) -> APIRouter:
    router = APIRouter(prefix=prefix, tags=[prefix.removeprefix("/")])
    id_col = getattr(model, id_name)

    @router.get("")
    def list_rows(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), search: str | None = None,
                  db: Session = Depends(get_db), _=Depends(current_user)):
        query = select(model)
        if search and search_column:
            query = query.where(getattr(model, search_column).ilike(f"%{search}%"))
        total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
        rows = db.scalars(query.order_by(id_col.desc()).offset((page - 1) * page_size).limit(page_size)).all()
        return {"items": [serialize(row) for row in rows], "total": total, "page": page, "page_size": page_size}

    @router.get("/{row_id}")
    def get_row(row_id: int, db: Session = Depends(get_db), _=Depends(current_user)):
        row = db.get(model, row_id)
        if not row:
            raise HTTPException(404, "Record not found")
        return serialize(row)

    @router.post("", status_code=201)
    def create_row(payload: schema, db: Session = Depends(get_db), _=Depends(allow_roles("admin", "fleet_manager"))):
        row = model(**payload.model_dump())
        try:
            db.add(row)
            db.commit()
            db.refresh(row)
            return serialize(row)
        except IntegrityError as exc:
            db.rollback()
            raise HTTPException(409, "Database constraint prevented this record") from exc

    @router.put("/{row_id}")
    def update_row(row_id: int, payload: schema, db: Session = Depends(get_db), _=Depends(allow_roles("admin", "fleet_manager"))):
        row = db.get(model, row_id)
        if not row:
            raise HTTPException(404, "Record not found")
        for key, value in payload.model_dump().items():
            setattr(row, key, value)
        try:
            db.commit()
            db.refresh(row)
            return serialize(row)
        except IntegrityError as exc:
            db.rollback()
            raise HTTPException(409, "Database constraint prevented this update") from exc

    @router.delete("/{row_id}", status_code=204)
    def delete_row(row_id: int, db: Session = Depends(get_db), _=Depends(allow_roles("admin"))):
        row = db.get(model, row_id)
        if not row:
            raise HTTPException(404, "Record not found")
        try:
            db.delete(row)
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise HTTPException(409, "Cannot delete a record referenced by fleet history") from exc

    return router

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app import categorization, models, schemas
from app.deps import DB, CurrentUser, canonical_category, get_owned_or_404

router = APIRouter(prefix="/rules", tags=["categorisation rules"])

# Expenses a new rule may re-categorise: never ones the user or their bank labelled.
OVERRIDABLE_SOURCES = ("none", "default", "model")


def _ensure_unique_keyword(db: DB, user: models.User, keyword: str, exclude_id: int | None = None) -> None:
    query = select(models.CategoryRule.id).where(
        models.CategoryRule.user_id == user.id, models.CategoryRule.keyword == keyword
    )
    if exclude_id is not None:
        query = query.where(models.CategoryRule.id != exclude_id)
    if db.scalar(query) is not None:
        raise HTTPException(status_code=409, detail=f"You already have a rule for '{keyword}'")


@router.get("", response_model=list[schemas.RuleOut])
def list_rules(db: DB, user: CurrentUser):
    return db.scalars(
        select(models.CategoryRule)
        .where(models.CategoryRule.user_id == user.id)
        .order_by(models.CategoryRule.keyword)
    ).all()


@router.get("/defaults", response_model=list[schemas.DefaultRule])
def list_default_rules(user: CurrentUser):
    """Built-in merchant keywords used when no rule of yours or learned pattern matches."""
    return [{"keyword": k, "category": c} for k, c in sorted(categorization.DEFAULT_RULES.items())]


@router.post("", response_model=schemas.RuleCreated, status_code=status.HTTP_201_CREATED)
def create_rule(payload: schemas.RuleCreate, db: DB, user: CurrentUser):
    _ensure_unique_keyword(db, user, payload.keyword)
    category = canonical_category(db, user, payload.category)
    rule = models.CategoryRule(user_id=user.id, keyword=payload.keyword, category=category)
    db.add(rule)

    applied = 0
    if payload.apply_to_existing:
        candidates = db.scalars(
            select(models.Expense).where(
                models.Expense.user_id == user.id,
                models.Expense.description.is_not(None),
                models.Expense.category_source.in_(OVERRIDABLE_SOURCES),
            )
        )
        for expense in candidates:
            if categorization.match_keyword(expense.description, {rule.keyword: category}):
                expense.category = category
                expense.category_source = "rule"
                applied += 1

    db.commit()
    return {"id": rule.id, "keyword": rule.keyword, "category": rule.category, "applied": applied}


@router.put("/{rule_id}", response_model=schemas.RuleOut)
def update_rule(rule_id: int, payload: schemas.RuleIn, db: DB, user: CurrentUser):
    rule = get_owned_or_404(db, models.CategoryRule, rule_id, user)
    _ensure_unique_keyword(db, user, payload.keyword, exclude_id=rule.id)
    rule.keyword = payload.keyword
    rule.category = canonical_category(db, user, payload.category)
    db.commit()
    return rule


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_rule(rule_id: int, db: DB, user: CurrentUser):
    db.delete(get_owned_or_404(db, models.CategoryRule, rule_id, user))
    db.commit()

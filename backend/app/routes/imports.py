from dataclasses import asdict

from fastapi import APIRouter, HTTPException, UploadFile
from sqlalchemy import select

from app import csv_import, models, schemas
from app.deps import DB, CategoryLookup, CurrentUser, load_categorizer

router = APIRouter(prefix="/imports", tags=["imports"])

MAX_FILE_BYTES = 2 * 1024 * 1024


def _bad_file(error: csv_import.CSVImportError) -> HTTPException:
    return HTTPException(status_code=400, detail=str(error))


@router.post("/parse", response_model=schemas.ParsedFile)
async def parse_file(file: UploadFile, user: CurrentUser):
    """Step 1: read the uploaded CSV and suggest which column is which."""
    content = await file.read(MAX_FILE_BYTES + 1)
    if len(content) > MAX_FILE_BYTES:
        raise HTTPException(status_code=413, detail="Files can be at most 2 MB.")
    try:
        parsed = csv_import.parse_csv(content)
    except csv_import.CSVImportError as error:
        raise _bad_file(error) from error
    return {
        "headers": parsed.headers,
        "rows": parsed.rows,
        "suggested_mapping": csv_import.suggest_mapping(parsed),
    }


@router.post("/preview", response_model=schemas.PreviewResponse)
def preview(payload: schemas.PreviewRequest, db: DB, user: CurrentUser):
    """Step 2: apply the confirmed mapping, categorise, and flag rows that are already recorded."""
    mapping = csv_import.ColumnMapping(**payload.mapping.model_dump())
    width = max((len(r) for r in payload.rows), default=0)
    try:
        csv_import.validate_mapping(mapping, width)
    except csv_import.CSVImportError as error:
        raise _bad_file(error) from error

    extraction = csv_import.extract_transactions(payload.rows, mapping)
    transactions = extraction.transactions

    existing = []
    if transactions:
        existing = db.execute(
            select(models.Expense.date, models.Expense.amount, models.Expense.description).where(
                models.Expense.user_id == user.id,
                models.Expense.date >= min(t.date for t in transactions),
                models.Expense.date <= max(t.date for t in transactions),
            )
        ).all()
    duplicates = csv_import.find_duplicates(transactions, existing)

    categories = CategoryLookup(db, user)
    categorizer = load_categorizer(db, user)
    preview_rows = []
    for transaction, duplicate in zip(transactions, duplicates, strict=True):
        if transaction.category:
            category, source, confidence = categories.canonical(transaction.category), "file", None
        else:
            suggestion = categorizer.suggest(transaction.description)
            category = categories.canonical(suggestion.category)
            source, confidence = suggestion.source, suggestion.confidence
        preview_rows.append(
            {
                **asdict(transaction),
                "category": category,
                "category_source": source,
                "confidence": confidence,
                "duplicate": duplicate,
            }
        )
    return {"transactions": preview_rows, "skipped": [asdict(s) for s in extraction.skipped]}


@router.post("/commit", response_model=schemas.ImportResult, status_code=201)
def commit(payload: schemas.ImportRequest, db: DB, user: CurrentUser):
    """Step 3: save the transactions the user kept (all or nothing)."""
    categories = CategoryLookup(db, user)
    for item in payload.transactions:
        db.add(
            models.Expense(
                user_id=user.id,
                amount=item.amount,
                category=categories.canonical(item.category),
                date=item.date,
                description=item.description,
                category_source=item.category_source,
            )
        )
    db.commit()
    return {"imported": len(payload.transactions)}

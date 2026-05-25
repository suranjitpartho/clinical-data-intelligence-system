import csv
import io
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import text
from app.db.base import SessionLocal
from app.schemas.query import ExportRequest
from app.services.refinement_utils import apply_data_refinement
from app.agent.exceptions import InvalidQueryError

router = APIRouter(tags=["export"])


# Download query results as a CSV file
@router.post("/export-csv")
async def export_csv(request: ExportRequest):
    if not request.sql or not request.sql.strip().upper().startswith(("SELECT", "WITH")):
        raise InvalidQueryError("Invalid SQL query for export")

    def generate_csv():
        db = SessionLocal()
        try:
            result = db.execute(text(request.sql))
            raw_data = [dict(row._mapping) for row in result]
            refined_data, refined_metadata, refinement_log = apply_data_refinement(
                raw_data, {"total_count": len(raw_data)}
            )
            if not refined_data:
                output = io.StringIO()
                writer = csv.writer(output)
                writer.writerow(["No results after refinement"])
                yield output.getvalue()
                return

            keys = list(refined_data[0].keys())
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(keys)
            yield output.getvalue()
            output.seek(0)
            output.truncate(0)

            for row in refined_data:
                writer.writerow([row.get(k, "") for k in keys])
                yield output.getvalue()
                output.seek(0)
                output.truncate(0)
        except Exception as e:
            print(f"Export Error: {e}")
        finally:
            db.close()

    return StreamingResponse(
        generate_csv(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=clinical_intelligence_export.csv"},
    )

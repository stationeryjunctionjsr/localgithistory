import os
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill

from app.utils.logger import logger

# Find .env in the backend directory
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
env_path = os.path.join(base_dir, ".env")
load_dotenv(env_path)


class ReportService:
    def __init__(self):
        pass

    async def _read_tracking_data(self, start_date: Optional[datetime] = None, limit: int = 50000) -> List[Any]:
        """Read tracking events from the MySQL tracking table with a safety limit."""
        try:
            from app.db.storage_factory import get_storage
            storage = get_storage("tracking")
            query = {}
            if start_date:
                query["timestamp"] = {"$gte": start_date.isoformat()}
            records = await storage.findAll(query, limit=limit)
            return records if records else []
        except Exception as e:
            logger.error("Error reading tracking data from MySQL: %s", str(e), exc_info=True)
            return []

    async def generate_daily_search_report(self, date: datetime = None) -> str:
        """
        Generates an Excel report for search keywords and conversions for a specific date.
        Defaults to yesterday if no date is provided.
        """
        if date is None:
            date = datetime.now() - timedelta(days=1)

        target_date_str = date.strftime("%Y-%m-%d")
        start_date = datetime.combine(date, datetime.min.time())
        
        events = await self._read_tracking_data(start_date=start_date, limit=100000)

        # Filter events for the exact target date (since we used >= start_date)
        day_events = [e for e in events if (e.timestamp or "").startswith(target_date_str)]

        # Separate search events and conversion events
        search_events = [e for e in day_events if e.type == "product_search"]
        conversion_events = [e for e in day_events if e.type in ["cart_add", "wishlist_add"]]

        report_data = []

        for search in search_events:
            session_id = search.session_id
            search_term = search.searchTerm or ""
            results_count = search.resultsCount or 0
            product_ids = search.product_ids or []
            search_time = search.timestamp

            added_to_cart = False
            added_to_wishlist = False

            if session_id:
                for conv in conversion_events:
                    if conv.session_id == session_id and (conv.timestamp or "") >= (search_time or ""):
                        prod_id = conv.product_id
                        if prod_id in product_ids:
                            if conv.type == "cart_add":
                                added_to_cart = True
                            elif conv.type == "wishlist_add":
                                added_to_wishlist = True

            report_data.append(
                {
                    "Search Text": search_term,
                    "Results Count": results_count,
                    "Added to Cart": "Yes" if added_to_cart else "No",
                    "Added to Wishlist": "Yes" if added_to_wishlist else "No",
                    "Timestamp": search_time,
                }
            )

        # Generate Excel
        wb = Workbook()
        ws = wb.active
        ws.title = f"Search Report {target_date_str}"

        # Headers
        headers = ["Search Text", "Results Count", "Added to Cart", "Added to Wishlist", "Timestamp"]
        ws.append(headers)

        # Formatting headers
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="1A4D33", end_color="1A4D33", fill_type="solid")
        for cell in ws[1]:
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center")

        # Add data
        for row in report_data:
            ws.append(
                [
                    row["Search Text"],
                    row["Results Count"],
                    row["Added to Cart"],
                    row["Added to Wishlist"],
                    row["Timestamp"],
                ]
            )

        # Auto-adjust column width
        for col in ws.columns:
            max_length = 0
            column = col[0].column_letter
            for cell in col:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except Exception:
                    continue
            ws.column_dimensions[column].width = max_length + 2

        # Save to temp file
        report_dir = "backend/app/reports"
        if not os.path.exists(report_dir):
            report_dir = "app/reports"
            if not os.path.exists(report_dir):
                os.makedirs(report_dir, exist_ok=True)

        report_path = os.path.abspath(os.path.join(report_dir, f"search_report_{target_date_str}.xlsx"))
        wb.save(report_path)

        return report_path


report_service = ReportService()

import json
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List

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
        # JSON file-based tracking data read is disabled — Oracle is the only supported backend.
        # self.tracking_file = os.path.join("backend", "app", "data", "tracking.json")
        # if not os.path.exists(self.tracking_file):
        #     # Fallback if running from backend directory
        #     self.tracking_file = os.path.join("app", "data", "tracking.json")
        pass

    def _read_tracking_data(self) -> List[Dict[str, Any]]:
        # JSON file-based tracking data read is disabled — tracking data is stored in Oracle.
        # if not os.path.exists(self.tracking_file):
        #     return []
        # try:
        #     with open(self.tracking_file, "r") as f:
        #         return json.load(f)
        # except Exception as e:
        #     logger.error("Error reading tracking data: %s", str(e), exc_info=True)
        #     return []
        return []  # Tracking data is now in Oracle; implement DB read if needed.

    def generate_daily_search_report(self, date: datetime = None) -> str:
        """
        Generates an Excel report for search keywords and conversions for a specific date.
        Defaults to yesterday if no date is provided.
        """
        if date is None:
            date = datetime.now() - timedelta(days=1)

        target_date_str = date.strftime("%Y-%m-%d")
        events = self._read_tracking_data()

        # Filter events for the target date
        day_events = [e for e in events if e.get("timestamp", "").startswith(target_date_str)]

        # Separate search events and conversion events
        search_events = [e for e in day_events if e.get("type") == "product_search"]
        conversion_events = [e for e in day_events if e.get("type") in ["cart_add", "wishlist_add"]]

        # Aggregate data by search term/session
        # A simple approach: for each search, check if a conversion happened in the same session later that day
        # for one of the products in the search results.

        report_data = []

        for search in search_events:
            session_id = search.get("sessionId")
            search_term = search.get("searchTerm", "")
            results_count = search.get("resultsCount", 0)
            product_ids = search.get("productIds", [])
            search_time = search.get("timestamp")

            added_to_cart = False
            added_to_wishlist = False

            if session_id:
                # Find conversions in the same session after the search
                for conv in conversion_events:
                    if conv.get("sessionId") == session_id and conv.get("timestamp") >= search_time:
                        prod_id = conv.get("productId")
                        # Check if this product was in the search results
                        if prod_id in product_ids:
                            if conv.get("type") == "cart_add":
                                added_to_cart = True
                            elif conv.get("type") == "wishlist_add":
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
            # Fallback
            report_dir = "app/reports"
            if not os.path.exists(report_dir):
                os.makedirs(report_dir, exist_ok=True)

        report_path = os.path.abspath(os.path.join(report_dir, f"search_report_{target_date_str}.xlsx"))
        wb.save(report_path)

        return report_path


report_service = ReportService()

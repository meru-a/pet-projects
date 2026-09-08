"""Render the checked-in Power BI PDF pages as README-ready PNG screenshots.

Run from the project root:
    .\\documentation-deliverables\\.venv\\Scripts\\python.exe documentation-deliverables\\render_dashboard_screens.py
"""
from pathlib import Path
import pymupdf

OUT = Path(__file__).parent / "assets" / "dashboard-screens"
PDF = Path(__file__).parent.parent / "Power BI Report Screens.pdf"
NAMES = [
    "01-overview.png", "02-funnel-analysis.png", "03-cohort-retention.png",
    "04-customer-segmentation.png", "05-product-performance.png",
    "06-reviews-and-sentiment.png", "07-ab-testing.png",
]

if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    document = pymupdf.open(PDF)
    if len(document) != len(NAMES):
        raise ValueError(f"Expected {len(NAMES)} PDF pages; found {len(document)}")
    for page, name in zip(document, NAMES):
        page.get_pixmap(matrix=pymupdf.Matrix(1.5, 1.5), alpha=False).save(OUT / name)
    print(f"Rendered {len(NAMES)} dashboard screenshots to {OUT}")

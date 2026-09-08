"""Generate evidence-based project documentation from the repository's checked-in assets.

Run from the project root:
    .\\documentation-deliverables\\.venv\\Scripts\\python.exe documentation-deliverables\\generate_deliverables.py
"""
from pathlib import Path
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.section import WD_SECTION
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

OUT = Path(__file__).parent

README = r'''# Ecommerce Product Analytics

An analytics portfolio project that models ecommerce behavioral and transactional data in Snowflake, explores it with Snowpark Python notebooks, and presents the results in a Power BI Project (`.pbip`). The checked-in repository documents the analytical design; raw source data and executed query outputs are not included.

## What the project covers

| Workstream | Purpose | Main assets |
|---|---|---|
| Data transformation | Builds event, session, user activity, customer value, product performance, and retention datasets. | `snowflake-sql-scripts/` |
| Advanced analysis | Examines funnel progression, cohort retention, customer segmentation, product/review performance, and a separate advertising experiment. | `python-advanced-analysis/` |
| Reporting | Defines an editable Power BI semantic model and seven-page report. | `pbi-dashboards/Dashboards.pbip` |
| Presentation evidence | Provides exported report screens. | `Power BI Report Screens.pdf` |

## Repository layout

```text
ecommerce-product-analytics/
├── snowflake-sql-scripts/          # Snowflake SQL transformation sequence
├── python-advanced-analysis/       # Snowpark Python notebooks
├── pbi-dashboards/                 # Power BI Project, report, and semantic model
├── Power BI Report Screens.pdf      # Exported dashboard screens
└── documentation-deliverables/     # This README, generation script, local venv, Word report
```

## Data model and transformation flow

The SQL scripts refer to the `PRODUCT_ANALYTICS` database and use source objects in `RAW_EVENTS`. They should be executed in numeric order after the source tables are available.

```text
RAW_EVENTS.EVENTS + RAW_EVENTS.SESSIONS ──► FCT_EVENTS / FCT_SESSIONS
RAW_EVENTS.CUSTOMERS_CLEAN + FCT_SESSIONS ─► FCT_USER_ACTIVITY ─► DIM_USER
RAW_EVENTS.ORDERS + ORDER_ITEMS + DIM_USER ─► FCT_CUSTOMER_VALUE
RAW_EVENTS.PRODUCTS + EVENTS + ORDERS + ORDER_ITEMS ─► PRODUCT_PERFORMANCE
DIM_USER + FCT_USER_ACTIVITY ─► USER_RETENTION
```

### SQL assets

1. `01_fct_events.sql` joins events to sessions to add customer and session attributes.
2. `02_fct_sessions.sql` aggregates events to session grain, including funnel counts, flags, duration, and purchase-event revenue.
3. `03_ft_user_activity.sql` aggregates session activity to a customer-day dataset and adds signup/cohort attributes.
4. `04_dim_users.sql` produces one customer record with first activity, first purchase, and activation timing.
5. `05_fct_customer_value.sql` calculates orders, items, revenue, average order value, purchase dates, recency, and 30-/90-day revenue.
6. `06_product_performance.sql` combines product engagement, product-session funnel rates, units, and revenue.
7. `07_user_retention.sql` calculates retained users and retention rate by signup cohort and days since signup.

## Analyses and confirmed findings

The notebooks connect through Snowpark (`get_active_session`) and expect the Snowflake objects named in the SQL layer.

### Funnel

The funnel notebook reports 67.9% progression from page view to add-to-cart, 55.1% from add-to-cart to checkout, and 74.8% from checkout to purchase. The documented largest drop-off is therefore add-to-cart to checkout. These figures are notebook-reported results; the underlying data are not included here for independent recalculation.

### Retention, segmentation, and product performance

The project provides cohort-retention analysis at D1, D7, D14, and D30; RFM scoring plus four-cluster K-means segmentation; and product, review, rating, and sentiment exploration. The repository does not retain numerical result tables for these workstreams, so this documentation does not state unverified rankings, rates, or segment sizes.

### A/B test: separate demonstration dataset

`05-ab-testing.ipynb` explicitly uses a Kaggle advertising-effectiveness dataset because the ecommerce dataset lacks experiment data. Its notebook reports control conversion of approximately 3.2%, treatment conversion of approximately 6.66%, a 3.43 percentage-point lift, and p < 0.001. It also reports no statistically significant evidence that the treatment effect varies by ad count (p = 0.705) or exposure days (p = 0.387). This result is illustrative and must not be treated as ecommerce-store performance.

## Power BI report

Open `pbi-dashboards/Dashboards.pbip` in Power BI Desktop. The semantic model defines measures for orders, customers, revenue, product revenue, units sold, average session duration, review count/rating/sentiment, retention, and A/B conversion. The report contains seven configured pages.

## Important implementation checks before refresh

- `03_ft_user_activity.sql` references `SESSION_REVENUE`, whereas `02_fct_sessions.sql` outputs `PURCHASE_EVENT_REVENUE`. Reconcile this column name before executing the sequence as written.
- The customer-value recency measure is calculated relative to 31 December 2025, a fixed reference date that should be updated or parameterized for a current refresh.
- The report measure named `Conversion` uses `SUM(FCT_EVENTS[CUSTOMER_ID])`. Customer IDs are identifiers, not counts; validate or replace this calculation before using it as a business KPI.
- The report measure `ProdNetRevenue` sums `GROSS_PRODUCT_REVENUE`, despite its name. Validate the intended metric labeling.

## Running the notebooks

1. Load the raw source tables referenced by the SQL scripts into Snowflake.
2. Run the SQL scripts in sequence, resolving the implementation checks above.
3. Run the notebooks in a Snowflake/Snowpark environment with an active session and the required Python packages (pandas, matplotlib, scikit-learn, statsmodels; optional Snowflake ML components for the sentiment exploration).
4. Open the `.pbip` project and refresh only after validating mappings and measures.

## Documentation deliverables

This folder contains an isolated `.venv`, `requirements.txt`, and `generate_deliverables.py`. Regenerate both this README and the Word report with:

```powershell
.\documentation-deliverables\.venv\Scripts\python.exe .\documentation-deliverables\generate_deliverables.py
```

The companion report, `Ecommerce_Product_Analytics_Final_Report.docx`, gives an executive-ready, evidence-qualified summary, priorities, and recommendations.
'''

def shade(cell, color):
    props = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:fill'), color)
    props.append(shd)

def set_cell_text(cell, text, bold=False, color=None):
    cell.text = text
    run = cell.paragraphs[0].runs[0]
    run.bold = bold
    if color:
        run.font.color.rgb = RGBColor.from_string(color)
    run.font.size = Pt(9)

def add_table(doc, headers, rows, widths=None):
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = 'Light Shading Accent 1'
    for idx, header in enumerate(headers):
        set_cell_text(table.rows[0].cells[idx], header, True, 'FFFFFF')
        shade(table.rows[0].cells[idx], '17365D')
    for row in rows:
        cells = table.add_row().cells
        for idx, value in enumerate(row):
            set_cell_text(cells[idx], str(value))
    if widths:
        for row in table.rows:
            for idx, width in enumerate(widths):
                row.cells[idx].width = Inches(width)
    doc.add_paragraph()
    return table

def bullet(doc, text, level=0):
    doc.add_paragraph(text, style='List Bullet' if level == 0 else 'List Bullet 2')

def heading(doc, text, level=1):
    p = doc.add_heading(text, level)
    for run in p.runs:
        run.font.color.rgb = RGBColor(23, 54, 93)
    return p

def build_report():
    doc = Document()
    sec = doc.sections[0]
    sec.top_margin, sec.bottom_margin = Inches(.65), Inches(.65)
    sec.left_margin, sec.right_margin = Inches(.72), Inches(.72)
    doc.styles['Normal'].font.name = 'Aptos'
    doc.styles['Normal'].font.size = Pt(10)

    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run('Ecommerce Product Analytics'); r.bold = True; r.font.size = Pt(28); r.font.color.rgb = RGBColor(23, 54, 93)
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run('Final project report | Executive evidence and recommendations'); r.italic = True; r.font.size = Pt(13)
    doc.add_paragraph('Scope: checked-in Snowflake SQL, Snowpark notebooks, Power BI project definition, and seven exported Power BI report screens. Prepared 9 September 2026.', style='Subtitle')
    doc.add_paragraph('Decision statement', style='Heading 2')
    doc.add_paragraph('The largest observable funnel loss is from page view to add to cart. Focus conversion diagnosis and testing on that entry point; in parallel, protect the concentrated value of Champions and K-means Cluster 0, and build a targeted reactivation program for Hibernating customers.')

    heading(doc, '1. Executive summary')
    add_table(doc, ['Verified finding', 'Implication'], [
        ('$4.84m revenue, 33,580 orders, 20,000 customers, and $144.0 average order value are displayed for 2020–2025.', 'The report provides a clear six-year commercial baseline.'),
        ('Only 26.5% of 539,343 page-view events progress to add-to-cart; checkout-to-purchase is 74.8%.', 'The largest visible conversion opportunity is upstream of checkout.'),
        ('Champions are 3,178 customers (15.9%) and contribute $1.73m (35.8%) of revenue.', 'Protecting high-value customers is a material revenue-retention priority.'),
        ('Hibernating customers are 5,133 (25.7%) but contribute $69.8k (1.4%) of revenue.', 'A large low-value pool is suitable for disciplined, low-cost reactivation tests.'),
        ('The report displays 8.9% D0 retention, declining to 4.1% at D7 and 1.1% at D28.', 'Early lifecycle engagement is the retention priority.')
    ], [2.65, 3.8])

    heading(doc, '2. Evidence base and metric interpretation')
    doc.add_paragraph('All quantitative findings in this report are transcribed from the checked-in Power BI report screens, with definitions supported by the accompanying SQL, notebook, and semantic-model assets. The screen filters are set to 1 January 2020–31 December 2025 unless noted. Revenue is displayed in USD.')
    doc.add_paragraph('The funnel screen displays event counts: 539,343 page views, 143,126 add-to-carts, 44,909 checkouts, and 33,580 purchases. The Python funnel notebook separately describes session-level progression. The two views should not be compared as identical measures because their denominators differ.')
    add_table(doc, ['Asset', 'Verified role'], [
        ('Snowflake SQL (7 scripts)', 'Builds event/session, customer value, product performance, and retention datasets.'),
        ('Python notebooks (5)', 'Contains funnel, cohort, RFM/K-means, product/review, and external A/B analyses.'),
        ('Power BI report screens (7)', 'Provides the numerical business findings summarized below.'),
        ('Local NLTK sentiment output', 'Per the project owner, local NLTK generated the sentiment values presented in the report screen.')
    ], [2.1, 4.35])

    heading(doc, '3. Commercial findings and insights')
    heading(doc, 'Funnel: improve product-to-cart progression first', 2)
    add_table(doc, ['Stage', 'Displayed count', 'Progression from prior stage'], [
        ('Page view', '539,343', '—'), ('Add to cart', '143,126', '26.5%'),
        ('Checkout', '44,909', '31.4%'), ('Purchase', '33,580', '74.8%')
    ], [2.1, 1.75, 2.6])
    doc.add_paragraph('Overall displayed conversion from page view to purchase is 6.22%. Device conversion is tightly clustered—mobile 6.23%, desktop 6.22%, tablet 6.14%—so the screen does not point to a device-specific priority. Paid is the highest displayed source at 6.36%, versus organic at 6.16%; the 0.20 percentage-point spread is modest. The largest actionable diagnostic is therefore the product-page-to-cart journey, not a broad device/channel redesign.')

    heading(doc, 'Customer value: a small set of segments carries disproportionate value', 2)
    add_table(doc, ['RFM segment', 'Customers', 'Revenue', 'Avg. orders', 'Interpretation'], [
        ('Champions', '3,178', '$1,731,102', '3.34', '15.9% of customers and 35.8% of revenue.'),
        ('Can’t Lose Them', '1,283', '$628,354', '2.71', 'High-value reactivation/protection opportunity.'),
        ('Loyal Customers', '2,834', '$885,756', '2.00', 'Strong base for retention and referral initiatives.'),
        ('At Risk', '2,149', '$448,226', '1.70', 'Prioritize targeted recovery tests.'),
        ('Hibernating', '5,133', '$69,761', '0.27', '25.7% of customers but 1.4% of revenue.'),
        ('Lost', '702', '$176,934', '1.00', 'Use low-cost win-back only.')
    ], [1.2, .78, 1.1, .78, 2.6])
    doc.add_paragraph('The K-means view corroborates concentration: Cluster 0 contains 5,812 customers (29.1%) and $3.06m revenue (63.4%) with 3.16 average orders. Cluster 1 contains 3,906 customers (19.5%) but only $3,930 revenue and 0.04 average orders. The cluster labels are algorithm outputs, so the RFM segment names are more suitable for customer-facing activation rules.')

    heading(doc, 'Retention: intervene in the first week', 2)
    add_table(doc, ['Days since signup', 'Displayed retention'], [('0', '8.9%'), ('7', '4.1%'), ('14', '2.0%'), ('21', '1.1%'), ('28', '1.1%')], [2.2, 2.2])
    doc.add_paragraph('Retention more than halves between day 0 and day 7, and reaches 1.1% by day 21. This pattern supports a first-week onboarding and second-purchase intervention rather than relying on late-stage win-back alone. Cohort-level values vary substantially on the screen; they should be interpreted with cohort size and maturity before changing investment by cohort.')

    heading(doc, 'Product and category portfolio: scale the top three while protecting margin', 2)
    doc.add_paragraph('The product page displays 1,197 products, $4,835,608 net product revenue, 77,106 units sold, and $42.3 average margin. Home & Kitchen ($840,737), Sports ($832,350), and Fashion ($824,739) account for $2.50m, or 51.6%, of displayed revenue. Electronics ($692,866), Beauty ($692,312), Toys ($569,153), and Books ($383,451) make up the balance. The screen’s rating-versus-conversion plot is descriptive; it does not establish a causal relationship.')

    heading(doc, 'Customer feedback: favorable aggregate signal, with focused issue mining needed', 2)
    doc.add_paragraph('The reviews screen displays 10,780 records, a 3.9/5 average rating, 89.1% positive sentiment, and 10.9% negative sentiment. Ratings of 4 and 5 total 7,620 reviews (70.7%). Positive TF-IDF terms include “overall,” “okay,” “value,” “money,” and “recommend”; negative terms include “quality,” “great,” “disappointed,” and “buy.” Use the negative terms as inputs to qualitative review coding by product/category, not as root-cause proof by themselves.')

    heading(doc, 'A/B analysis: methodological evidence only', 2)
    doc.add_paragraph('The A/B page explicitly labels its dataset as unrelated to the other report pages. It shows 12,053 treatment users and 7,947 PSA users; conversion is 6.66% versus 3.23%, a 3.43 percentage-point absolute lift and 106.01% relative lift (z = -10.59; p < 0.001). The page reports no statistically significant variation in treatment effectiveness by ad exposure. This is a valid demonstration of the testing approach, not evidence to deploy the same intervention in this ecommerce dataset.')

    heading(doc, '4. Recommended action plan')
    add_table(doc, ['Horizon', 'Actions', 'Success measure'], [
        ('0–30 days', 'Audit high-traffic product pages and cart-entry events; test product information, value framing, stock/price clarity, and cart calls-to-action.', 'Increase page-view-to-cart progression from its 26.5% baseline without reducing checkout completion.'),
        ('0–30 days', 'Create RFM journeys: benefits/early access for Champions, loyalty/referral for Loyal customers, and controlled win-back for Can’t Lose Them and At Risk.', 'Incremental repeat orders and revenue by segment versus holdout.'),
        ('30–60 days', 'Deploy first-week lifecycle messages and a second-purchase trigger; tailor content from product/review insight.', 'Improve D7 and D28 retention against the displayed 4.1% and 1.1% baselines.'),
        ('30–90 days', 'Prioritize assortment, merchandising, and availability reviews for the top-three revenue categories; investigate negative-review themes at SKU/category level.', 'Revenue, margin, conversion, and sentiment guardrails by category.'),
        ('Ongoing', 'Use store-specific, pre-registered A/B tests with a primary metric, sample-size plan, and guardrails.', 'Adopt only changes with statistically and commercially credible incremental impact.')
    ], [1.25, 3.8, 1.35])

    heading(doc, '5. Appendix: model and scope')
    doc.add_paragraph('Raw event, session, customer, order, order-item, product, and review objects feed the Snowflake analytics layer. The model includes FCT_EVENTS, FCT_SESSIONS, FCT_USER_ACTIVITY, DIM_USER, FCT_CUSTOMER_VALUE, PRODUCT_PERFORMANCE, USER_RETENTION, FCT_CUSTOMER_SEGMENTS, and review-sentiment data. Customer IDs and gross-USD/revenue field choices follow the project’s stated metric design. Per the project owner, a local NLTK workflow supplies the sentiment results used in the dashboard; that local code is not included in the checked-in notebook.')
    doc.add_paragraph('This report does not infer causes from descriptive results. Recommendations are testable hypotheses anchored to observed funnel, retention, segment, product, and feedback patterns.')

    footer = doc.sections[0].footer.paragraphs[0]; footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer.add_run('Ecommerce Product Analytics | Final project report | Dashboard evidence')
    doc.save(OUT / 'Ecommerce_Product_Analytics_Final_Report_Updated.docx')

if __name__ == '__main__':
    build_report()
    print('Generated Ecommerce_Product_Analytics_Final_Report_Updated.docx')

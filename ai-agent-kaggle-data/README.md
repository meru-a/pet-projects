# Customer Marketing Executive Analysis

An executive-style customer segmentation and campaign-targeting analysis built from the Kaggle Customer Personality Analysis dataset. The project converts a tab-delimited customer-marketing dataset into a three-slide PowerPoint narrative and a companion PDF, with recommendations framed as testable commercial actions.

## Business question

Which customer groups should receive priority marketing investment, and how should the business tailor its offer and channel approach?

## Key findings

The final deck uses 2,216 customers with usable income data from 2,240 source records. Spending refers to the dataset's prior-two-year category-spend fields and is presented in euros in the final deck.

- The top-spend quartile contains 555 customers with total category spend of at least €1,048 and contributes 61.5% of historical category spend.
- Wine and meat account for 80% of the top-spender basket, supporting premium wine-and-meat bundle hypotheses.
- The latest-campaign response rate is 15.0% across the analysis population.
- The priority audience—top-spend customers with prior campaign acceptance—contains 249 customers (11% of the base), has a 47.4% latest-campaign response rate, and averages €1,623 historical spend.
- High-value customers are omnichannel; the deck reports 5.9 average catalogue purchases for the top-spend group versus 1.6 for the rest of the base.

These are descriptive patterns, not causal effects. The source file does not provide offer-exposure, campaign-cost, or product-margin data; the recommended actions should therefore be validated with randomized holdouts and incremental-profit measurement.

## Deliverables

| File | Description |
|---|---|
| [Final PowerPoint](Customer_Marketing_Executive_Analysis_final.pptx) | Three-slide executive presentation with findings, target audience, and action plan. |
| [Final PDF](Customer_Marketing_Executive_Analysis_final.pdf) | Portable version of the final presentation. |
| [Dataset description](about-dataset.md) | Source-field definitions and analytical target. |
| [Source data](data/marketing_campaign.csv) | Local tab-delimited Kaggle dataset copy. |

## Analytical approach

1. Load the customer-marketing data and retain records with usable income values.
2. Sum six product-category spend fields to calculate historical customer spend.
3. Define the top-spend quartile using the 75th percentile of total category spend.
4. Combine spend tier with historical campaign acceptance to define priority audiences.
5. Compare response rate, historical spend, product mix, and purchase-channel usage across groups.
6. Translate descriptive insights into controlled marketing-test recommendations.

## Recommended actions in the deck

- Protect the 249 high-spend prior accepters with a premium wine-and-meat bundle, measured against a holdout on incremental profit.
- Test a lighter premium offer with the remaining 306 top spenders who have no recorded prior acceptance.
- Use catalogue-led creative with store follow-up for high-value customers, then measure channel-level profit and repeat purchase.

## Repository structure

```text
ai-agent-kaggle-data/
├── data/
│   └── marketing_campaign.csv
├── archived-scripts/                 # Superseded deck-development iterations
│   ├── build_deck.py
│   ├── revise_deck.py
│   └── add_profile_to_deck.py
├── about-dataset.md
├── build_redesigned_deck.py         # Active, standalone deck generator
├── Customer_Marketing_Executive_Analysis_final.pptx
├── Customer_Marketing_Executive_Analysis_final.pdf
└── README.md
```

## Reproducing or adapting the deck

The generation scripts use Python's standard library and `python-pptx`.

```powershell
python -m pip install python-pptx
python build_redesigned_deck.py
```

`build_redesigned_deck.py` is the active standalone script: it reads the local dataset and creates the redesigned presentation. Earlier deck-development iterations are retained in `archive scripts/` for reference and are not part of the current reproduction path.

## Limitations

- The analysis is based on historical, observational customer data and cannot demonstrate campaign incrementality.
- The source describes prior two-year customer spend and purchase history; it does not provide campaign costs, offer exposure, or product-margin fields.
- Segment thresholds and target rules are analytical heuristics. They should be revalidated if the data period, offer strategy, or customer base changes.

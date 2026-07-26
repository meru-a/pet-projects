import csv
from pathlib import Path
from statistics import mean

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor

ROOT = Path(__file__).parent
OUT = ROOT / "Customer_Marketing_Executive_Analysis.pptx"

# Consulting-style palette
NAVY = RGBColor(15, 39, 71)
BLUE = RGBColor(32, 104, 170)
TEAL = RGBColor(26, 150, 136)
GOLD = RGBColor(233, 162, 45)
INK = RGBColor(40, 52, 66)
MUTED = RGBColor(105, 119, 135)
LIGHT = RGBColor(242, 246, 250)
PALE_BLUE = RGBColor(228, 240, 249)
WHITE = RGBColor(255, 255, 255)
RED = RGBColor(196, 75, 76)

with open(ROOT / "data" / "marketing_campaign.csv", newline="", encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f, delimiter="\t"))
if len(rows[0]) == 1:  # defensive fallback for a comma-delimited copy
    with open(ROOT / "data" / "marketing_campaign.csv", newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

num_cols = ["Income", "Recency", "MntWines", "MntFruits", "MntMeatProducts", "MntFishProducts", "MntSweetProducts", "MntGoldProds", "NumDealsPurchases", "NumWebPurchases", "NumCatalogPurchases", "NumStorePurchases", "NumWebVisitsMonth", "Response", "AcceptedCmp1", "AcceptedCmp2", "AcceptedCmp3", "AcceptedCmp4", "AcceptedCmp5", "Kidhome", "Teenhome"]
data = []
for r in rows:
    try:
        d = {k: float(r[k]) for k in num_cols}
    except (ValueError, KeyError):
        continue
    d["total"] = sum(d[k] for k in ["MntWines", "MntFruits", "MntMeatProducts", "MntFishProducts", "MntSweetProducts", "MntGoldProds"])
    d["prior_accept"] = int(sum(d[k] for k in ["AcceptedCmp1", "AcceptedCmp2", "AcceptedCmp3", "AcceptedCmp4", "AcceptedCmp5"]) > 0)
    data.append(d)

def q(values, p):
    v = sorted(values); i = (len(v)-1)*p; lo=int(i); hi=min(lo+1,len(v)-1)
    return v[lo] + (v[hi]-v[lo])*(i-lo)

income_q = [q([d['Income'] for d in data], p) for p in (.25,.5,.75)]
spend_q = [q([d['total'] for d in data], p) for p in (.25,.5,.75)]
for d in data:
    d['income_band'] = sum(d['Income'] > x for x in income_q)
    d['spend_band'] = sum(d['total'] > x for x in spend_q)

n=len(data)
response=sum(d['Response'] for d in data)/n
prior=[d for d in data if d['prior_accept']]
no_prior=[d for d in data if not d['prior_accept']]
prior_resp=mean(d['Response'] for d in prior)
no_prior_rate=mean(d['Response'] for d in no_prior)
top=[d for d in data if d['spend_band']==3]
top_share=sum(d['total'] for d in top)/sum(d['total'] for d in data)
top_response=mean(d['Response'] for d in top)
top_income=[d for d in data if d['income_band']==3]
channel_names=["Web", "Catalog", "Store"]
channel_vals=[mean(d['NumWebPurchases'] for d in data), mean(d['NumCatalogPurchases'] for d in data), mean(d['NumStorePurchases'] for d in data)]
product_names=["Wine", "Meat", "Gold", "Fish", "Fruits", "Sweets"]
product_keys=["MntWines","MntMeatProducts","MntGoldProds","MntFishProducts","MntFruits","MntSweetProducts"]
product_vals=[mean(d[k] for d in data) for k in product_keys]
resp_by_spend=[mean(d['Response'] for d in data if d['spend_band']==i) for i in range(4)]
revenue_by_spend=[sum(d['total'] for d in data if d['spend_band']==i) for i in range(4)]
web_high=[d for d in data if d['NumWebVisitsMonth'] >= 7]
web_gap=mean(d['NumWebVisitsMonth'] for d in data)/mean(d['NumWebPurchases'] for d in data)

prs=Presentation(); prs.slide_width=Inches(13.333); prs.slide_height=Inches(7.5)
blank=prs.slide_layouts[6]

def box(slide,x,y,w,h,fill=WHITE,line=None,radius=False):
    sh=slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    sh.fill.solid(); sh.fill.fore_color.rgb=fill
    sh.line.color.rgb=line or fill
    return sh
def text(slide, s, x,y,w,h, size=12, color=INK, bold=False, font="Aptos", align=None, valign=MSO_ANCHOR.TOP):
    tb=slide.shapes.add_textbox(Inches(x),Inches(y),Inches(w),Inches(h)); tf=tb.text_frame; tf.clear(); tf.word_wrap=True; tf.vertical_anchor=valign
    p=tf.paragraphs[0]; p.text=s; p.font.name=font; p.font.size=Pt(size); p.font.bold=bold; p.font.color.rgb=color
    if align: p.alignment=align
    tf.margin_left=tf.margin_right=Pt(0); tf.margin_top=tf.margin_bottom=Pt(0)
    return tb
def title(slide, kicker, headline, subtitle):
    text(slide,kicker.upper(),0.55,0.28,8,0.22,9,TEAL,True)
    text(slide,headline,0.55,0.55,12.1,0.48,23,NAVY,True)
    text(slide,subtitle,0.55,1.10,12,0.27,10,MUTED)
    box(slide,0.55,1.47,12.2,0.025,TEAL)
def footer(slide, page):
    text(slide,"Source: Kaggle Customer Personality Analysis; n = {:,} complete-income customers; spending and purchase history cover the prior 2 years.".format(n),.55,7.17,10.8,.16,7,MUTED)
    text(slide,str(page),12.35,7.15,.35,.16,8,MUTED,True,align=PP_ALIGN.RIGHT)
def add_chart(slide, cats, vals, x,y,w,h, title_text, color=BLUE, chart_type=XL_CHART_TYPE.BAR_CLUSTERED, percent=False):
    cd=CategoryChartData(); cd.categories=cats; cd.add_series("", vals)
    chart=slide.shapes.add_chart(chart_type, Inches(x), Inches(y), Inches(w), Inches(h), cd).chart
    chart.has_legend=False; chart.has_title=True; chart.chart_title.text_frame.text=title_text
    chart.chart_title.text_frame.paragraphs[0].font.size=Pt(10); chart.chart_title.text_frame.paragraphs[0].font.bold=True; chart.chart_title.text_frame.paragraphs[0].font.color.rgb=NAVY
    chart.value_axis.has_major_gridlines=True; chart.value_axis.major_gridlines.format.line.color.rgb=RGBColor(220,226,233)
    chart.value_axis.tick_labels.font.size=Pt(8); chart.category_axis.tick_labels.font.size=Pt(8)
    chart.category_axis.tick_labels.font.color.rgb=MUTED; chart.value_axis.tick_labels.font.color.rgb=MUTED
    if percent: chart.value_axis.tick_labels.number_format="0%"; chart.value_axis.maximum_scale=0.40
    chart.series[0].format.fill.solid(); chart.series[0].format.fill.fore_color.rgb=color
    chart.series[0].format.line.color.rgb=color
    chart.plots[0].has_data_labels=True; dl=chart.plots[0].data_labels; dl.position=XL_LABEL_POSITION.OUTSIDE_END; dl.font.size=Pt(8); dl.number_format="0%" if percent else "0"
    return chart
def notes(slide, s):
    try:
        tf=slide.notes_slide.notes_text_frame; tf.text=s
    except Exception:
        pass

# Slide 1
s=prs.slides.add_slide(blank); box(s,0,0,13.333,7.5,LIGHT); title(s,"Executive snapshot","The growth agenda is precision: protect high-value buyers and re-activate proven responders","Customer Personality Analysis | spend, channel and campaign behavior | analysis of 2,216 usable customer records")
kpis=[("{:.0%}".format(top_share),"of total spend from the top spend quartile"),("{:.1%}".format(response),"latest campaign response rate"),("{:.1f}×".format(web_gap),"web visits per web purchase")]
for i,(big,lab) in enumerate(kpis):
    x=.55+i*2.05; box(s,x,1.78,1.8,.9,WHITE,None,True); text(s,big,x+.12,1.91,1.56,.32,22,[TEAL,GOLD,BLUE][i],True); text(s,lab,x+.12,2.29,1.55,.25,8,MUTED)
add_chart(s,product_names,product_vals,6.95,1.72,5.72,2.25,"Average spend per customer by product (€)",TEAL)
text(s,"Interpretation: Wine contributes €304/customer—over half of category spend—making it the clearest premium-product anchor.",6.98,4.00,5.55,.28,9,INK,False)
box(s,.55,3.08,5.88,3.68,WHITE,None,True); text(s,"Five findings that matter",.8,3.34,3.4,.25,13,NAVY,True)
insights=[
    "1  Concentration: the top 25% of spenders generate {:.0%} of all category spend.".format(top_share),
    "2  Campaign memory: previous accepters respond at {:.1%} vs {:.1%} for everyone else ({:.1f}×).".format(prior_resp,no_prior_rate,prior_resp/no_prior_rate),
    "3  Product mix: wine is {:.0%} of average customer spend; meat is the second-largest basket.".format(product_vals[0]/sum(product_vals)),
    "4  Channel reality: stores lead at {:.1f} purchases/customer vs {:.1f} online.".format(channel_vals[2],channel_vals[0]),
    "5  Digital friction: customers make {:.1f} monthly web visits for each web purchase.".format(web_gap),
]
for i,v in enumerate(insights): text(s,v,.82,3.83+i*.49,5.3,.37,10,INK)
footer(s,1); notes(s,"The data points to a more selective commercial model. Spend is heavily concentrated, while historic campaign acceptance is the strongest observable signal of near-term response. The opportunity is to allocate offer investment to proven responders and protect the premium wine-led base.")

# Slide 2
s=prs.slides.add_slide(blank); box(s,0,0,13.333,7.5,LIGHT); title(s,"Opportunity sizing","Response rises with customer value—but historical acceptance is the decisive targeting filter","The broad base responds weakly; a behavior-led audience can materially improve campaign efficiency.")
add_chart(s,["Q1\nlowest","Q2","Q3","Q4\nhighest"],resp_by_spend,.55,1.78,5.7,3.0,"Latest campaign response rate by total-spend quartile",BLUE,percent=True)
text(s,"Interpretation: response climbs from {:.1%} in the lowest-spend quartile to {:.1%} in the highest, supporting value-tiered offers.".format(resp_by_spend[0],resp_by_spend[3]),.6,4.92,5.55,.30,9,INK)
box(s,6.58,1.78,6.16,3.44,WHITE,None,True); text(s,"Prior acceptance creates a high-propensity micro-audience",6.9,2.05,5.1,.25,13,NAVY,True)
metrics=[("{:.1%}".format(prior_resp),"latest response among prior accepters"),("{:.1%}".format(no_prior_rate),"latest response without prior acceptance"),("{:.1f}×".format(prior_resp/no_prior_rate),"propensity lift from acceptance history")]
for i,(a,b) in enumerate(metrics):
    x=6.92+i*1.82; box(s,x,2.58,1.58,1.1,PALE_BLUE if i!=2 else RGBColor(252,242,218),None,True); text(s,a,x+.1,2.76,1.35,.29,20,TEAL if i!=2 else GOLD,True,align=PP_ALIGN.CENTER); text(s,b,x+.12,3.17,1.32,.30,8,MUTED,align=PP_ALIGN.CENTER)
text(s,"Interpretation: acceptance history identifies a compact group that is {:.1f}× more likely to respond—ideal for the first wave of outreach.".format(prior_resp/no_prior_rate),6.92,4.25,5.35,.42,9,INK)
box(s,.55,5.54,12.18,1.17,NAVY,None,True); text(s,"Targeting implication",.82,5.78,1.55,.20,10,RGBColor(173,214,238),True); text(s,"Prioritize customers with both high spend and an accepted prior campaign; use value-tiered wine offers, then suppress low-propensity contacts from expensive channels.",.82,6.08,11.25,.27,12,WHITE,True)
footer(s,2); notes(s,"Response is not uniform across the file: high-spend customers are more responsive, and prior acceptance creates a much stronger lift. This supports a two-step targeting rule: first filter to known responders, then tailor the offer and contact investment by customer value.")

# Slide 3
s=prs.slides.add_slide(blank); box(s,0,0,13.333,7.5,LIGHT); title(s,"Action plan","Turn customer behavior into three testable moves—while improving the data needed for next-best-action modeling","Recommended 90-day agenda | quantify incrementality, not just response")
add_chart(s,channel_names,channel_vals,.55,1.73,4.25,2.55,"Average purchases per customer by channel",GOLD)
text(s,"Interpretation: stores remain the dominant purchase channel ({:.1f}/customer), so digital growth should augment—not abruptly replace—the store experience.".format(channel_vals[2]),.60,4.48,4.1,.42,9,INK)
box(s,5.05,1.73,7.68,3.20,WHITE,None,True); text(s,"Three data-backed actions",5.35,1.98,3.2,.25,14,NAVY,True)
actions=[
    ("01","Launch a premium retention wave","Target top-spend customers with curated wine bundles and a controlled holdout; this quartile carries {:.0%} of spend.".format(top_share)),
    ("02","Exploit campaign memory","Make prior acceptance the first targeting gate; its {:.1f}× response lift warrants richer contact investment.".format(prior_resp/no_prior_rate)),
    ("03","Convert browsing into baskets","Trigger site-visit abandonment and store-to-web offers; {:.1f} visits per web purchase signals digital conversion friction.".format(web_gap)),
]
for i,(num,head,body) in enumerate(actions):
    y=2.43+i*.75; box(s,5.36,y,.42,.42,[TEAL,BLUE,GOLD][i],None,True); text(s,num,5.36,y+.10,.42,.14,8,WHITE,True,align=PP_ALIGN.CENTER); text(s,head,5.95,y,3.4,.20,10,INK,True); text(s,body,5.95,y+.25,6.25,.32,8,MUTED)
box(s,.55,5.30,12.18,1.38,WHITE,None,True); text(s,"Limitations & next step",.82,5.56,2.3,.22,12,NAVY,True)
text(s,"Observed associations—not causal lift; no campaign cost, margin, exposure, offer, or time-series transaction detail. Next: run randomized holdouts and train a response/uplift model using recency, spend mix, channel behavior and acceptance history; assess profit, not opens or response alone.",.82,5.92,11.3,.42,10,INK)
footer(s,3); notes(s,"I recommend three practical tests rather than a single broad rollout: premium retention, response-history targeting, and digital conversion triggers. The file is rich for segmentation but cannot establish incremental profit, so each action should include a holdout and profitability measurement. With campaign-exposure and margin data, the next step is a response or uplift model.")

prs.save(OUT)
print(f"Created {OUT}")
print(f"n={n}; response={response:.4f}; top_share={top_share:.4f}; prior={prior_resp:.4f}; nonprior={no_prior_rate:.4f}; web_gap={web_gap:.3f}")

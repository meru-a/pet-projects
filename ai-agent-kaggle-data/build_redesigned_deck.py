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
OUT = ROOT / "Customer_Marketing_Executive_Analysis_redesigned.pptx"

NAVY = RGBColor(13, 35, 63); TEAL = RGBColor(0, 135, 125); BLUE = RGBColor(35, 100, 185)
GOLD = RGBColor(221, 150, 30); ORANGE = RGBColor(231, 111, 45); INK = RGBColor(38, 48, 61)
MUTED = RGBColor(95, 108, 123); LIGHT = RGBColor(244, 247, 250); PALE = RGBColor(229, 240, 247)
WHITE = RGBColor(255,255,255); LINE = RGBColor(216,224,232); PALE_GOLD = RGBColor(252,243,222)

prod = ["MntWines", "MntFruits", "MntMeatProducts", "MntFishProducts", "MntSweetProducts", "MntGoldProds"]
accept = ["AcceptedCmp1", "AcceptedCmp2", "AcceptedCmp3", "AcceptedCmp4", "AcceptedCmp5"]
with open(ROOT / "data" / "marketing_campaign.csv", encoding="utf-8-sig", newline="") as f:
    raw = list(csv.DictReader(f, delimiter="\t"))
rows = []
for x in raw:
    try:
        d = {k: float(x[k]) for k in prod + accept + ["Income", "Response", "NumWebPurchases", "NumCatalogPurchases", "NumStorePurchases", "Kidhome", "Teenhome"]}
    except (ValueError, KeyError):
        continue
    d["education"] = x["Education"]
    d["spend"] = sum(d[k] for k in prod)
    d["prior"] = any(d[k] == 1 for k in accept)
    rows.append(d)

def percentile(v, p):
    v = sorted(v); i = (len(v)-1)*p; lo = int(i); hi = min(lo+1, len(v)-1)
    return v[lo] + (v[hi]-v[lo])*(i-lo)
cutoff = percentile([d["spend"] for d in rows], .75)
top = [d for d in rows if d["spend"] >= cutoff]
other = [d for d in rows if d["spend"] < cutoff]
groups = {
    ("Top spend", "Prior accepted"): [d for d in rows if d["spend"] >= cutoff and d["prior"]],
    ("Top spend", "No prior acceptance"): [d for d in rows if d["spend"] >= cutoff and not d["prior"]],
    ("Other customers", "Prior accepted"): [d for d in rows if d["spend"] < cutoff and d["prior"]],
    ("Other customers", "No prior acceptance"): [d for d in rows if d["spend"] < cutoff and not d["prior"]],
}
def av(g, key): return mean(d[key] for d in g)
def pct(g, test): return sum(test(d) for d in g)/len(g)
total_spend = sum(d["spend"] for d in rows)
share_spend = sum(d["spend"] for d in top)/total_spend
degree_share = pct(top, lambda d: d["education"] in {"Graduation", "Master", "PhD"})
child_share = pct(top, lambda d: d["Kidhome"]+d["Teenhome"] > 0)
top_basket = av(top, "MntWines") + av(top, "MntMeatProducts")

prs = Presentation(); prs.slide_width = Inches(13.333); prs.slide_height = Inches(7.5); blank = prs.slide_layouts[6]

def shape(slide, x,y,w,h, fill, rounded=False, line=None):
    sh = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if rounded else MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    sh.fill.solid(); sh.fill.fore_color.rgb = fill; sh.line.color.rgb = line or fill
    return sh
def txt(slide, value,x,y,w,h,size=12,color=INK,bold=False,align=None):
    sh=slide.shapes.add_textbox(Inches(x),Inches(y),Inches(w),Inches(h)); tf=sh.text_frame; tf.clear(); tf.word_wrap=True; tf.vertical_anchor=MSO_ANCHOR.TOP
    tf.margin_left=tf.margin_right=tf.margin_top=tf.margin_bottom=Pt(0)
    p=tf.paragraphs[0]; p.text=value; p.font.name="Aptos"; p.font.size=Pt(size); p.font.bold=bold; p.font.color.rgb=color
    if align is not None: p.alignment=align
    return sh
def header(slide, section, headline, sub):
    txt(slide, section.upper(), .55,.25,4,.18,9,TEAL,True)
    txt(slide, headline,.55,.52,12.15,.42,23,NAVY,True)
    txt(slide, sub,.55,1.04,12,.22,10,MUTED)
    shape(slide,.55,1.42,12.2,.025,TEAL)
def footer(slide,page):
    txt(slide,"Source: Kaggle Customer Personality Analysis. n = {:,} customers with usable income data; spending is reported for the prior two years.".format(len(rows)),.55,7.16,11,.14,7,MUTED)
    txt(slide,str(page),12.35,7.14,.3,.14,8,MUTED,True,PP_ALIGN.RIGHT)
def note(slide, value):
    slide.notes_slide.notes_text_frame.text=value
def bar_chart(slide, cats, series, x,y,w,h,title,percent=False):
    cd=CategoryChartData(); cd.categories=cats
    for name, vals in series: cd.add_series(name, vals)
    chart=slide.shapes.add_chart(XL_CHART_TYPE.BAR_CLUSTERED, Inches(x),Inches(y),Inches(w),Inches(h),cd).chart
    chart.has_title=True; chart.chart_title.text_frame.text=title
    p=chart.chart_title.text_frame.paragraphs[0]; p.font.name="Aptos"; p.font.size=Pt(10); p.font.bold=True; p.font.color.rgb=NAVY
    chart.has_legend=True; chart.legend.include_in_layout=False; chart.legend.position=2; chart.legend.font.size=Pt(8)
    chart.value_axis.has_major_gridlines=True; chart.value_axis.major_gridlines.format.line.color.rgb=LINE
    chart.value_axis.tick_labels.font.size=Pt(8); chart.category_axis.tick_labels.font.size=Pt(8)
    if percent: chart.value_axis.tick_labels.number_format="0%"
    colors=[TEAL, NAVY]
    for i,ser in enumerate(chart.series):
        ser.format.fill.solid(); ser.format.fill.fore_color.rgb=colors[i]; ser.format.line.color.rgb=colors[i]
    chart.plots[0].has_data_labels = True
    labels = chart.plots[0].data_labels
    labels.position = XL_LABEL_POSITION.OUTSIDE_END
    labels.font.size = Pt(8)
    labels.number_format = "0%" if percent else "0"
    return chart

# Slide 1 — value pool
s=prs.slides.add_slide(blank); shape(s,0,0,13.333,7.5,LIGHT); header(s,"1 | Value pool","Customer value is concentrated—and it is built around a premium wine-and-meat basket","Start with the customers who matter most: the top-spend quartile accounts for most historical spend.")
# dataset strip
shape(s,.55,1.65,12.18,.52,WHITE,True)
for i,(a,b) in enumerate([(f"{len(rows):,}","customers"),("2 years","of spend history"),("6","product categories"),("3","purchase channels"),("15.0%","latest-campaign response")]):
    x=.80+i*2.38; txt(s,a,x,1.76,1.05,.17,13,NAVY,True); txt(s,b,x+1.05,1.78,1.12,.14,8,MUTED)
# left concentration
shape(s,.55,2.45,3.35,3.70,NAVY,True)
txt(s,"TOP-SPEND QUARTILE",.84,2.76,2.3,.18,10,RGBColor(170,211,235),True)
txt(s,"{:.1%}".format(share_spend),.84,3.10,2.4,.48,33,WHITE,True)
txt(s,"of all historical category spend",.84,3.66,2.55,.20,11,WHITE,True)
shape(s,.84,4.14,2.68,.012,RGBColor(80,116,146))
txt(s,"555 customers  |  spend ≥ €{:,.0f}".format(cutoff),.84,4.39,2.50,.20,10,RGBColor(211,225,236),True)
txt(s,"Average basket: €{:,.0f}\nvs €{:,.0f} for all other customers".format(av(top,"spend"),av(other,"spend")),.84,4.79,2.30,.55,12,WHITE,True)
txt(s,"The top quarter generates nearly two-thirds of spend; broad, uniform outreach would dilute investment.",.84,5.62,2.50,.35,9,RGBColor(211,225,236))
# product visual right
product_labels=["Wine","Meat","Fish","Gold","Sweets","Fruits"]
order=["MntWines","MntMeatProducts","MntFishProducts","MntGoldProds","MntSweetProducts","MntFruits"]
bar_chart(s,product_labels,[("Top-spend quartile",[av(top,k) for k in order]),("Other customers",[av(other,k) for k in order])],4.25,2.45,8.48,3.25,"Average product spend per customer (€)")
shape(s,4.25,5.92,8.48,.55,PALE,True)
txt(s,"Wine (€{:.0f}) and meat (€{:.0f}) make up {:.0%} of the top-spender basket—lead with premium bundles, not gold-product discounts.".format(av(top,"MntWines"),av(top,"MntMeatProducts"),top_basket/av(top,"spend")),4.52,6.10,7.95,.20,10,INK,True)
footer(s,1); note(s,"Customer value is sharply concentrated: 555 customers, effectively the top spending quartile, generate 61.5% of category spend. Their basket is premium and focused—wine and meat account for 80% of it. This is the value pool to protect first, with bundles that match its observed buying behavior.")

# Slide 2 — target
s=prs.slides.add_slide(blank); shape(s,0,0,13.333,7.5,LIGHT); header(s,"2 | Priority audience","A small 11% audience combines high value with demonstrated campaign propensity","Prior campaign acceptance and spend together create a clear first-wave target.")
txt(s,"LATEST-CAMPAIGN RESPONSE RATE",.65,1.73,3.2,.18,10,TEAL,True)
txt(s,"Prior campaign acceptance",3.72,1.75,4.1,.18,10,NAVY,True,PP_ALIGN.CENTER)
txt(s,"No prior campaign acceptance",8.36,1.75,3.6,.18,10,NAVY,True,PP_ALIGN.CENTER)
txt(s,"SPEND\nTIER",.62,2.47,.72,.38,9,MUTED,True,PP_ALIGN.CENTER)
cells=[
    ("Top-spend\nquartile", "Prior accepted", 1.45,2.05, ("Top spend","Prior accepted"), TEAL),
    ("", "No prior acceptance", 6.73,2.05, ("Top spend","No prior acceptance"), RGBColor(67,121,184)),
    ("Other\ncustomers", "Prior accepted", 1.45,4.10, ("Other customers","Prior accepted"), RGBColor(92,143,156)),
    ("", "No prior acceptance", 6.73,4.10, ("Other customers","No prior acceptance"), RGBColor(182,194,205)),
]
for row_label, col_label, x,y,key,color in cells:
    if row_label: txt(s,row_label,.62,y+.54,.75,.42,10,NAVY,True,PP_ALIGN.CENTER)
    g=groups[key]; shape(s,x,y,4.72,1.62,color,True)
    txt(s,"{:,.0f} customers  |  {:.0%} of base".format(len(g),len(g)/len(rows)),x+.25,y+.22,3.9,.18,9,WHITE,True)
    txt(s,"{:.1%}".format(av(g,"Response")),x+.25,y+.51,1.7,.40,25,WHITE,True)
    txt(s,"latest response rate",x+.25,y+.96,2.1,.16,9,WHITE)
    txt(s,"€{:,.0f}\navg. spend".format(av(g,"spend")),x+3.30,y+.58,1.1,.42,12,WHITE,True,PP_ALIGN.RIGHT)
# priority callout
shape(s,1.45,3.64,10.0,.28,PALE_GOLD,True)
txt(s,"Priority: 249 top-spend prior accepters deliver a 47.4% response rate and €1,623 average spend.",1.70,3.71,9.5,.15,9.5,INK,True,PP_ALIGN.CENTER)
# profile strip
shape(s,11.77,2.05,.96,3.67,NAVY,True)
txt(s,"PRIORITY\nAUDIENCE",11.90,2.40,.68,.40,9,RGBColor(181,217,236),True,PP_ALIGN.CENTER)
txt(s,"11%",11.89,3.10,.70,.30,19,WHITE,True,PP_ALIGN.CENTER)
txt(s,"of base",11.91,3.42,.66,.15,8,WHITE,False,PP_ALIGN.CENTER)
txt(s,"47.4%\nresponse",11.88,4.04,.72,.37,14,WHITE,True,PP_ALIGN.CENTER)
txt(s,"€1.6k\nspend",11.88,4.76,.72,.37,14,WHITE,True,PP_ALIGN.CENTER)
shape(s,.55,6.08,12.18,.61,WHITE,True)
txt(s,"WHO THEY ARE",.82,6.25,1.12,.16,9,TEAL,True)
txt(s,"€75.2k average income  |  92.6% have Graduation, Master’s or PhD education  |  33.3% have children/teens at home",2.03,6.24,6.15,.18,9.5,INK,True)
txt(s,"WHAT THEY BUY",8.46,6.25,1.20,.16,9,TEAL,True)
txt(s,"Wine + meat = 80% of basket",9.75,6.24,2.55,.18,9.5,INK,True)
footer(s,2); note(s,"The most valuable audience is not simply high spenders or former responders alone. It is the overlap: 249 customers—11% of the database—with 47.4% latest-campaign response and €1,623 average spend. They are affluent, highly educated, and have a wine-and-meat-led basket, so use that profile to shape premium creative.")

# Slide 3 — actions
s=prs.slides.add_slide(blank); shape(s,0,0,13.333,7.5,LIGHT); header(s,"3 | Action plan","Use premium offers and the right channel—then prove incremental profit","Three tests turn the observed customer signals into a measurable commercial program.")
bar_chart(s,["Store","Catalogue","Web"],[("Top-spend quartile",[av(top,"NumStorePurchases"),av(top,"NumCatalogPurchases"),av(top,"NumWebPurchases")]),("Other customers",[av(other,"NumStorePurchases"),av(other,"NumCatalogPurchases"),av(other,"NumWebPurchases")])],.55,1.73,4.65,3.15,"Average purchases per customer by channel")
shape(s,.55,5.09,4.65,.55,PALE,True)
txt(s,"High-value customers use all channels; catalogue usage is 3.7× higher than the rest of the base (5.9 vs 1.6 purchases).",.80,5.25,4.12,.20,9.3,INK,True)
txt(s,"90-DAY TEST AGENDA",5.58,1.76,3,.18,10,TEAL,True)
actions=[
    ("01","Protect the priority 249","Lead with a premium wine-and-meat bundle for top-spend prior accepters.","Measure: incremental profit vs holdout","47.4% response"),
    ("02","Retain the remaining top spenders","Test a lighter premium offer for the 306 high-spend customers without prior acceptance.","Measure: incremental response and spend","16.0% response"),
    ("03","Orchestrate channels","Use catalogue-led creative with store follow-up for high-value customers.","Measure: channel-level profit and repeat purchase","5.9 catalogue buys"),
]
for i,(num,head,body,measure,metric) in enumerate(actions):
    y=2.15+i*1.12; shape(s,5.58,y,.48,.48,[TEAL,BLUE,GOLD][i],True); txt(s,num,5.58,y+.14,.48,.13,9,WHITE,True,PP_ALIGN.CENTER)
    txt(s,head,6.25,y,3.85,.18,11,NAVY,True); txt(s,body,6.25,y+.26,4.15,.32,9,MUTED)
    shape(s,10.60,y+.02,1.95,.70,WHITE,True); txt(s,metric,10.73,y+.15,1.68,.18,10,[TEAL,BLUE,GOLD][i],True,PP_ALIGN.CENTER); txt(s,measure,10.70,y+.41,1.74,.16,7.5,MUTED,False,PP_ALIGN.CENTER)
shape(s,.55,5.98,12.18,.72,NAVY,True)
txt(s,"LIMITATIONS & NEXT STEP",.82,6.20,2.1,.16,9,RGBColor(181,217,236),True)
txt(s,"The file shows patterns, not causal impact: it lacks offer exposure, campaign cost and product-margin data. Run randomized holdouts, evaluate incremental profit, then build a response/uplift model using spend, recency, channel and campaign-history signals.",2.98,6.12,9.20,.34,9.5,WHITE)
footer(s,3); note(s,"The action plan is designed as three controlled tests rather than a broad rollout. Start with the top-spend prior accepters, use a lighter approach for the remaining high-value group, and match the channel plan to their omnichannel behavior. The current data demonstrates associations, so success should be incremental profit measured through randomized holdouts.")

prs.save(OUT)
print(f"Created {OUT}")
print(f"n={len(rows)}, cutoff={cutoff}, top_n={len(top)}, top_share={share_spend:.6f}, priority={len(groups[('Top spend','Prior accepted')])}")

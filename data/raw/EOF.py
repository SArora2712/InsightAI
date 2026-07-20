
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

doc = SimpleDocTemplate("data/raw/q3_sales_report.pdf", pagesize=letter)
styles = getSampleStyleSheet()
story = []

def add(style, text):
    story.append(Paragraph(text, styles[style]))
    story.append(Spacer(1, 0.15*inch))

# --- Page 1: Executive Summary + Regional ---
add("Title", "Q3 2026 Sales Performance Report — InsightAI Demo Corp")
add("Heading2", "Executive Summary")
add("Normal", "Q3 revenue reached $4.2M, a 12% increase quarter-over-quarter. Growth was driven primarily by the Enterprise segment, which grew 18%, while the SMB segment grew only 3%. Customer churn in the SMB segment rose to 6.5%, up from 4.1% in Q2, raising concerns about retention in that channel.")
add("Heading2", "Regional Breakdown")
add("Normal", "North America accounted for 58% of total revenue ($2.44M), EMEA for 27% ($1.13M), and APAC for 15% ($0.63M). APAC showed the fastest growth rate at 24% QoQ, though off a smaller base. EMEA growth slowed to 4% QoQ, attributed by the regional team to a stronger Euro impacting deal conversion timing.")
story.append(PageBreak())

# --- Page 2: Marketing + Product ---
add("Heading2", "Marketing Spend Analysis")
add("Normal", "Marketing spend in Q3 totaled $410,000, representing 9.8% of revenue. The Enterprise outbound campaign delivered a 3.2x return on ad spend, while the SMB paid social campaign underperformed at 1.1x ROAS. Leadership is evaluating reallocating SMB budget toward the Enterprise channel in Q4.")
add("Heading2", "Product Usage Trends")
add("Normal", "Weekly active usage among Enterprise accounts grew 22% QoQ, driven largely by adoption of the new reporting module released in August. SMB weekly active usage was flat, growing only 1% QoQ, despite the same feature release being available to all tiers.")
story.append(PageBreak())

# --- Page 3: Risks + Outlook ---
add("Heading2", "Risks and Watch Items")
add("Normal", "The rise in SMB churn coincides with a support ticket backlog that grew from an average 2-day response time to 5 days during Q3. Customer success leadership has flagged this as a likely contributing factor, though it has not yet been formally validated against churn data.")
add("Normal", "A secondary risk factor is pricing: the SMB tier has not had a price adjustment in 18 months, while Enterprise pricing was revised in Q2. Some SMB churn exit surveys cite competitor pricing as a factor, though sample size on these surveys remains small.")
add("Heading2", "Q4 Outlook")
add("Normal", "Leadership guidance for Q4 targets $4.6M in revenue, assuming continued Enterprise momentum and stabilization of SMB churn following planned support staffing increases in October. The Enterprise pipeline entering Q4 stands at $2.1M in qualified opportunities, up from $1.7M entering Q3.")

doc.build(story)
print("3-page sample PDF regenerated.")

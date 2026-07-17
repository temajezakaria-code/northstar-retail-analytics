"""
Generates static PNG mockups of the 4 Power BI dashboard pages using matplotlib,
so the dashboard designs exist as real, downloadable image files (not just an
interactive in-chat widget or a written spec).
"""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

OUT = "/home/claude/northstar-retail-analytics/outputs"
plt.rcParams["figure.dpi"] = 130
NAVY, TEAL, ORANGE, GREY, PURPLE, PINK, GREEN, AMBER, RED = \
    "#1f3b57","#2a9d8f","#e76f51","#6c757d","#4a3aa7","#d55181","#2e7d32","#eda100","#c0392b"

def kpi_card(ax, label, value, sub, color=NAVY):
    ax.set_xlim(0,1); ax.set_ylim(0,1); ax.axis("off")
    ax.add_patch(mpatches.FancyBboxPatch((0.03,0.08), 0.94, 0.84, boxstyle="round,pad=0.02,rounding_size=0.04",
                                          linewidth=0.8, edgecolor="#dddddd", facecolor="#f7f7f5"))
    ax.text(0.1, 0.72, label, fontsize=10, color="#666", va="top")
    ax.text(0.1, 0.42, value, fontsize=19, fontweight="bold", color="#111", va="top")
    ax.text(0.1, 0.2, sub, fontsize=9, color=color, va="top")

# =========================================================================
# PAGE 1 — EXECUTIVE SUMMARY
# =========================================================================
fig = plt.figure(figsize=(13, 7.5))
fig.suptitle("NorthStar Retail Group — Executive Summary", fontsize=15, fontweight="bold", x=0.02, ha="left", y=0.98)
gs = fig.add_gridspec(3, 4, height_ratios=[1, 2, 2], hspace=0.55, wspace=0.35, top=0.90, bottom=0.06, left=0.05, right=0.97)

kpis = [("Total Revenue","$31.1M","▲ 11.5% YoY"), ("Gross Profit","$13.3M","42.7% margin"),
        ("Growth Rate","+11.5%","3rd straight year"), ("Active Customers","5,911","$4,341 median LTV")]
for i,(l,v,s) in enumerate(kpis):
    ax = fig.add_subplot(gs[0,i]); kpi_card(ax,l,v,s, TEAL)

ax1 = fig.add_subplot(gs[1:,0:3])
months = ['23-01','23-04','23-07','23-10','24-01','24-04','24-07','24-10','25-01','25-04','25-07','25-10','25-12']
rev = [495,690,460,1470,580,830,470,1800,650,890,590,1720,1900]
ax1.plot(months, rev, color=NAVY, linewidth=2.2, marker="o", markersize=4)
ax1.fill_between(months, rev, color=NAVY, alpha=0.08)
ax1.set_title("Monthly Revenue Trend (2023–2025)", fontsize=11, fontweight="bold", loc="left")
ax1.set_ylabel("Revenue ($K)"); ax1.tick_params(axis='x', rotation=40)
ax1.spines[['top','right']].set_visible(False)

ax2 = fig.add_subplot(gs[1:,3])
regions = ["West","Southwest","Midwest","South","Northeast"]
vals = [20.9,20.6,19.7,19.4,18.9]
ax2.barh(regions, vals, color=NAVY)
ax2.set_title("Revenue by Region", fontsize=11, fontweight="bold", loc="left")
ax2.set_xlabel("% of Total Revenue")
ax2.spines[['top','right']].set_visible(False)
ax2.invert_yaxis()

plt.savefig(f"{OUT}/dashboard1_executive_summary.png", bbox_inches="tight")
plt.close()
print("Saved dashboard1_executive_summary.png")

# =========================================================================
# PAGE 2 — SALES DASHBOARD
# =========================================================================
fig = plt.figure(figsize=(13, 8))
fig.suptitle("NorthStar Retail Group — Sales Dashboard", fontsize=15, fontweight="bold", x=0.02, ha="left", y=0.98)
gs = fig.add_gridspec(2, 2, height_ratios=[1,1], hspace=0.45, wspace=0.3, top=0.90, bottom=0.08, left=0.06, right=0.97)

ax1 = fig.add_subplot(gs[0,0])
prods = ["Urbanox Laptop","Vantek Tablet X","Nexa Smart Watch","HomeCraft Air Fryer Pro","Aurora 4K TV"]
prodvals = [1.24,1.24,1.05,0.98,0.91]
ax1.barh(prods, prodvals, color=PURPLE)
ax1.set_title("Top 5 Products by Revenue", fontsize=11, fontweight="bold", loc="left")
ax1.set_xlabel("Revenue ($M)"); ax1.invert_yaxis(); ax1.spines[['top','right']].set_visible(False)

ax2 = fig.add_subplot(gs[0,1])
cats = ["Electronics","Home Appliances","Furniture","Outdoor & Garden","Kitchenware","Home Decor"]
catvals = [51.4,18.2,12.6,8.4,5.8,3.6]
ax2.barh(cats, catvals, color=TEAL)
ax2.set_title("Revenue Share by Category", fontsize=11, fontweight="bold", loc="left")
ax2.set_xlabel("% of Total Revenue"); ax2.invert_yaxis(); ax2.spines[['top','right']].set_visible(False)

ax3 = fig.add_subplot(gs[1,:])
region_rev = [6.5,6.4,6.1,6.0,5.9]
cum_pct = [20.9,41.8,61.5,80.9,100]
ax3.bar(regions, region_rev, color=ORANGE)
ax3.set_ylabel("Revenue ($M)")
ax3b = ax3.twinx()
ax3b.plot(regions, cum_pct, color=NAVY, marker="o", linewidth=2)
ax3b.set_ylabel("Cumulative % of Revenue"); ax3b.set_ylim(0,110)
ax3.set_title("Regional Revenue Concentration (Pareto View)", fontsize=11, fontweight="bold", loc="left")
ax3.spines[['top']].set_visible(False)

plt.savefig(f"{OUT}/dashboard2_sales.png", bbox_inches="tight")
plt.close()
print("Saved dashboard2_sales.png")

# =========================================================================
# PAGE 3 — CUSTOMER DASHBOARD
# =========================================================================
fig = plt.figure(figsize=(13, 8.5))
fig.suptitle("NorthStar Retail Group — Customer Dashboard", fontsize=15, fontweight="bold", x=0.02, ha="left", y=0.98)
gs = fig.add_gridspec(2, 2, height_ratios=[1,1.1], hspace=0.5, wspace=0.35, top=0.90, bottom=0.07, left=0.06, right=0.97)

ax1 = fig.add_subplot(gs[0,0])
seg_labels = ["Needs Attention","New / Promising","Champions","At Risk (High Value)","Lost / Dormant"]
seg_vals = [38,27,15,12,8]
seg_colors = [AMBER, GREEN, NAVY, RED, GREY]
wedges, texts, autotexts = ax1.pie(seg_vals, labels=seg_labels, autopct="%1.0f%%", colors=seg_colors,
                                     wedgeprops=dict(width=0.45), pctdistance=0.78, textprops={"fontsize":9})
ax1.set_title("Customer Segments (RFM)", fontsize=11, fontweight="bold", loc="left")

ax2 = fig.add_subplot(gs[0,1])
channels = ["In-Store Signup","Referral","Paid Social","Direct","Email Campaign","Organic Search","Affiliate"]
clv = [5440,5404,5351,5245,5228,5146,5138]
ax2.barh(channels, clv, color=PINK)
ax2.set_title("Lifetime Value by Acquisition Channel", fontsize=11, fontweight="bold", loc="left")
ax2.set_xlabel("Avg. Customer Lifetime Value ($)"); ax2.invert_yaxis()
ax2.set_xlim(4900, 5550); ax2.spines[['top','right']].set_visible(False)

ax3 = fig.add_subplot(gs[1,:])
cohort_labels = ["Jan-23","Jul-23","Jan-24","Jul-24","Jan-25"]
cohort_data = np.array([
    [100,11,10,11,10,10],
    [100,10,11,9,10,11],
    [100,11,9,10,11,9],
    [100,9,10,10,9,10],
    [100,10,10,9,10,np.nan],
])
im = ax3.imshow(cohort_data, cmap="Blues", vmin=0, vmax=100, aspect="auto")
ax3.set_xticks(range(6)); ax3.set_xticklabels(["M0","M1","M2","M3","M4","M5"])
ax3.set_yticks(range(5)); ax3.set_yticklabels(cohort_labels)
for i in range(5):
    for j in range(6):
        v = cohort_data[i,j]
        if not np.isnan(v):
            ax3.text(j, i, f"{int(v)}%", ha="center", va="center",
                      color="white" if v>60 else "#0C447C", fontsize=9, fontweight="bold")
ax3.set_title("Retention by Monthly Cohort (% still active)", fontsize=11, fontweight="bold", loc="left")

plt.savefig(f"{OUT}/dashboard3_customer.png", bbox_inches="tight")
plt.close()
print("Saved dashboard3_customer.png")

# =========================================================================
# PAGE 4 — OPERATIONS DASHBOARD
# =========================================================================
fig = plt.figure(figsize=(13, 7.5))
fig.suptitle("NorthStar Retail Group — Operations Dashboard", fontsize=15, fontweight="bold", x=0.02, ha="left", y=0.98)
gs = fig.add_gridspec(3, 3, height_ratios=[0.7,1.3,1.3], hspace=0.6, wspace=0.35, top=0.90, bottom=0.06, left=0.05, right=0.97)

ops_kpis = [("Total Orders","37,925",""), ("Cancel/Refund Rate","33.3%","industry avg ~20-25%"), ("Peak Day Lift","+30%","Fri/Sat vs. midweek")]
for i,(l,v,s) in enumerate(ops_kpis):
    ax = fig.add_subplot(gs[0,i]); kpi_card(ax,l,v,s, ORANGE)

ax1 = fig.add_subplot(gs[1:,0:2])
days = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
dowvals = [3338,3313,3309,3316,4273,4338,3401]
bar_colors = [NAVY if v < 4000 else ORANGE for v in dowvals]
ax1.bar(days, dowvals, color=bar_colors)
ax1.set_title("Order Volume by Day of Week", fontsize=11, fontweight="bold", loc="left")
ax1.set_ylabel("Completed Orders"); ax1.spines[['top','right']].set_visible(False)

ax2 = fig.add_subplot(gs[1,2])
status_labels = ["Completed","Cancelled","Refunded"]
status_vals = [66.7,16.9,16.4]
ax2.pie(status_vals, labels=status_labels, autopct="%1.0f%%", colors=[GREEN,AMBER,RED],
        wedgeprops=dict(width=0.45), textprops={"fontsize":8})
ax2.set_title("Order Status Breakdown", fontsize=10, fontweight="bold", loc="left")

ax3 = fig.add_subplot(gs[2,2])
methods = ["Credit Card","PayPal","BNPL","Debit Card","Gift Card"]
prate = [34.0,34.0,33.4,32.9,32.3]
ax3.barh(methods, prate, color=PINK)
ax3.set_xlim(0,40)
ax3.set_title("Cancel/Refund Rate by Payment", fontsize=10, fontweight="bold", loc="left")
ax3.set_xlabel("% problem rate"); ax3.invert_yaxis(); ax3.spines[['top','right']].set_visible(False)

plt.savefig(f"{OUT}/dashboard4_operations.png", bbox_inches="tight")
plt.close()
print("Saved dashboard4_operations.png")

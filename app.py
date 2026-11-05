"""Lebanon vs the world on tobacco - MSBA 325 team project dashboard (Streamlit).

Data
  WHO Global Health Observatory, tobacco use estimates (2026 release): adults 15+, age-standardised,
  2000-2025 plus 2030 projection; Global Youth Tobacco Survey (ages 13-15); smoke-free law compliance.
  IHME Global Burden of Disease 2023: tobacco-attributable deaths in Lebanon (key figures).
Design: built phone-first. Controls sit inline above each chart (no sidebar), charts are touch-safe
(no drag-zoom that would trap page scrolling) and every view has a table or text equivalent.
"""
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ----------------------------------------------------------------------------- settings
SURVEY_URL = ""   # paste the Google Form link here; the button appears automatically
BLOG_URL = ""     # paste the blog post link here

DATA = Path(__file__).parent / "data"
LEB, WORLD, OTHER, CONTEXT = "#eb6834", "#2a78d6", "#8f8d86", "#d6d4cd"
INK, INK2, MUTED, GRID = "#0b0b0b", "#52514e", "#898781", "#e9e8e2"
FONT = "Inter, system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif"
PLOT_CONFIG = {"displayModeBar": False, "scrollZoom": False, "doubleClick": False, "responsive": True}
SEXES = {"Everyone": "Both sexes", "Men": "Men", "Women": "Women"}
OBS_LAST = 2023  # last year with survey-based estimates; later years are WHO projections

st.set_page_config(page_title="Lebanon vs the world: tobacco", page_icon="🌍", layout="centered")

st.markdown(
    """
    <style>
      .block-container {padding-top: 2.2rem; padding-bottom: 3rem;}
      .eyebrow {font-size: 0.78rem; letter-spacing: .06em; text-transform: uppercase; color: #898781; margin-bottom: .2rem;}
      .bigidea {font-size: 1.08rem; line-height: 1.55; color: #262624;}
      .note {font-size: .86rem; color: #52514e; line-height: 1.5;}
      .takeaway {border-left: 3px solid #eb6834; padding: .35rem 0 .35rem .8rem; margin: .4rem 0 .8rem 0; font-size: 1rem;}
      div[data-testid="stMetricValue"] {font-size: 1.75rem;}
      button[data-baseweb="tab"] p {font-size: .95rem;}
      @media (max-width: 640px) {
        .block-container {padding-left: 1rem; padding-right: 1rem; padding-top: 1.2rem;}
        h1 {font-size: 1.75rem !important;}
        div[data-testid="stMetricValue"] {font-size: 1.5rem;}
      }
    </style>
    """,
    unsafe_allow_html=True,
)


# ----------------------------------------------------------------------------- data
@st.cache_data
def load():
    p = pd.read_csv(DATA / "who_adult_prevalence.csv")
    y = pd.read_csv(DATA / "who_youth_13_15.csv")
    pol = pd.read_csv(DATA / "who_smokefree_policy.csv")
    u = pd.read_csv(DATA / "who_users.csv")
    g = pd.read_csv(DATA / "ihme_gbd2023_lebanon_key_figures.csv")
    return p, y, pol, u, g


P, Y, POL, U, G = load()
YEARS = sorted(P.year.unique())
NAMES = P[P.level == "Country"].drop_duplicates("iso3").set_index("iso3").country.sort_values()


def series(iso, ind="tobacco_use", sex="Both sexes"):
    d = P[(P.iso3 == iso) & (P.indicator == ind) & (P.sex == sex)].sort_values("year")
    return d.set_index("year")


def countries(ind, sex, year):
    d = P[(P.level == "Country") & (P.indicator == ind) & (P.sex == sex) & (P.year == year)]
    return d.set_index("iso3").value.dropna()


def rank_of(s, iso):
    return int(s.rank(method="min", ascending=False)[iso])


def ordinal(n):
    suffix = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def base_layout(fig, height, legend=True, ytitle=None, ysuffix="%"):
    fig.update_layout(
        height=height, margin=dict(l=8, r=12, t=36 if legend else 12, b=8),
        font=dict(family=FONT, size=13, color=INK2), paper_bgcolor="white", plot_bgcolor="white",
        dragmode=False, hovermode="x unified", showlegend=legend,
        legend=dict(orientation="h", yanchor="bottom", y=1.0, x=0, font=dict(size=12), bgcolor="rgba(0,0,0,0)"),
        hoverlabel=dict(font=dict(family=FONT, size=13)),
    )
    fig.update_xaxes(showgrid=False, linecolor="#c3c2b7", ticks="outside", ticklen=6, tickcolor="rgba(0,0,0,0)",
                     fixedrange=True, automargin=True,
                     tickfont=dict(color=MUTED, size=12))
    fig.update_yaxes(gridcolor=GRID, zeroline=False, ticksuffix=ysuffix, title=ytitle, fixedrange=True, automargin=True,
                     tickfont=dict(color=MUTED, size=12))
    return fig


def show(fig):
    st.plotly_chart(fig, width="stretch", config=PLOT_CONFIG, theme=None)


def line_with_projection(fig, s, name, color, width=2.5, show_ci=False, label_end=True):
    """Observed years solid, WHO projections (after 2023) dotted; optional uncertainty band."""
    obs, prj = s[s.index <= OBS_LAST], s[s.index >= OBS_LAST]
    if show_ci and s["low"].notna().any():
        fig.add_trace(go.Scatter(x=list(s.index) + list(s.index[::-1]), y=list(s["high"]) + list(s["low"][::-1]),
                                 fill="toself", fillcolor=color, opacity=0.12, line=dict(width=0),
                                 hoverinfo="skip", showlegend=False))
    fig.add_trace(go.Scatter(x=obs.index, y=obs.value, name=name, mode="lines", line=dict(color=color, width=width),
                             legendgroup=name, hovertemplate="%{y:.1f}%"))
    fig.add_trace(go.Scatter(x=prj.index, y=prj.value, name=f"{name} (projected)", mode="lines",
                             line=dict(color=color, width=width * 0.8, dash="dot"), legendgroup=name,
                             showlegend=False, hovertemplate="%{y:.1f}% (projected)"))
    if label_end:
        fig.add_trace(go.Scatter(x=[OBS_LAST], y=[obs.value.iloc[-1]], mode="markers",
                                 marker=dict(color=color, size=9, line=dict(color="white", width=2)),
                                 hoverinfo="skip", showlegend=False))


# ----------------------------------------------------------------------------- headline numbers
T23 = countries("tobacco_use", "Both sexes", 2023)
T00 = countries("tobacco_use", "Both sexes", 2000)
leb = series("LBN")
wld = series("GLOBAL")
users = U[(U.iso3 == "LBN") & (U.indicator == "tobacco_users") & (U.sex == "Both sexes")].set_index("year").users
deaths = G[G.measure == "tobacco_attributable_deaths"].set_index("year").value

st.markdown('<div class="eyebrow">MSBA 325 · Data visualization project · AUB</div>', unsafe_allow_html=True)
st.title("Lebanon is smoking against the tide")
st.markdown(
    f'<p class="bigidea">Since 2000 the world has cut tobacco use from {wld.value[2000]:.0f}% to {wld.value[2023]:.0f}% of adults. '
    f"Lebanon went the other way, to <b>{leb.value[2023]:.1f}%</b>, the {ordinal(rank_of(T23, 'LBN'))} highest of "
    f"{len(T23)} countries. Much of the rise is <b>argileh</b>, especially among women and teens. "
    "Explore the numbers below, then decide whether argileh really is the 'lighter' option.</p>",
    unsafe_allow_html=True,
)

c1, c2 = st.columns(2)
c1.metric("Adults who use tobacco, 2023", f"{leb.value[2023]:.1f}%",
          f"{leb.value[2023] - leb.value[2000]:+.1f} points since 2000", delta_color="inverse", border=True,
          help="WHO estimate, adults 15+, age-standardised. World: "
               f"{wld.value[2023]:.1f}% ({wld.value[2023] - wld.value[2000]:+.1f} points).")
c2.metric("World rank", f"{ordinal(rank_of(T23, 'LBN'))} of {len(T23)}", f"from {ordinal(rank_of(T00, 'LBN'))} in 2000",
          delta_color="inverse", border=True,
          help="Rank among 167 countries with WHO estimates (1 = highest tobacco use).")
c3, c4 = st.columns(2)
c3.metric("People in Lebanon who use tobacco", f"{users[2023] / 1e6:.2f} million",
          f"{(users[2023] - users[2000]) / 1e6:+.2f} million since 2000", delta_color="inverse", border=True,
          help="WHO estimate of current tobacco users aged 15+.")
c4.metric("Deaths caused by tobacco, 2023", f"{deaths[2023]:,.0f}",
          f"{deaths[2023] / deaths[1990]:.1f} times 1990", delta_color="inverse", border=True,
          help=f"About {deaths[2023] / 365:.0f} deaths a day. IHME Global Burden of Disease 2023.")

tabs = st.tabs(["The trend", "The rank", "Beyond cigarettes", "Teens", "The cost", "Explore"])

# ----------------------------------------------------------------------------- 1. the trend
with tabs[0]:
    st.subheader("The world cut back. Lebanon did not.")
    who = st.segmented_control("Show", list(SEXES), default="Everyone", key="trend_sex", required=True)
    sex = SEXES[who]
    default_cmp = []
    picks = st.multiselect("Compare Lebanon with up to 5 countries", options=[i for i in NAMES.index if i != "LBN"],
                           default=default_cmp, format_func=lambda i: NAMES[i], max_selections=5,
                           placeholder="Add a country, e.g. Jordan or France")
    show_ci = st.toggle("Show WHO uncertainty range", value=False,
                        help="WHO's 95% uncertainty interval. Lebanon's is wide because few national surveys exist.")
    fig = go.Figure()
    for iso in picks:
        s = series(iso, sex=sex)
        if len(s):
            line_with_projection(fig, s, NAMES[iso], OTHER, width=1.8, label_end=False)
    line_with_projection(fig, series("GLOBAL", sex=sex), "World", WORLD, width=2.4, show_ci=show_ci)
    line_with_projection(fig, series("LBN", sex=sex), "Lebanon", LEB, width=3.2, show_ci=show_ci)
    fig.add_vrect(x0=OBS_LAST, x1=2030, fillcolor="#f4f3ef", line_width=0, layer="below")
    fig.add_annotation(x=2026.5, y=0, yanchor="bottom", text="WHO projection", showarrow=False,
                       font=dict(size=11, color=MUTED))
    base_layout(fig, 420)
    fig.update_yaxes(rangemode="tozero")
    show(fig)
    l_s, w_s = series("LBN", sex=sex).value, series("GLOBAL", sex=sex).value
    grp = {"Both sexes": "adults", "Men": "men", "Women": "women"}[sex]
    st.markdown(
        f'<div class="takeaway">Among {grp}, tobacco use in Lebanon went from <b>{l_s[2000]:.1f}%</b> in 2000 to '
        f"<b>{l_s[2023]:.1f}%</b> in 2023. Worldwide it fell from {w_s[2000]:.1f}% to {w_s[2023]:.1f}%.</div>",
        unsafe_allow_html=True)
    if sex == "Women":
        st.markdown(f'<p class="note">Women in Lebanon ({l_s[2023]:.1f}%) now use tobacco more than men worldwide '
                    f"({series('GLOBAL', sex='Men').value[2023]:.1f}%).</p>", unsafe_allow_html=True)
    ch = (countries("tobacco_use", sex, 2023) - countries("tobacco_use", sex, 2000)).dropna()
    st.markdown(f'<p class="note">Between 2000 and 2023, tobacco use among {grp} went <b>down</b> in {int((ch < 0).sum())} '
                f"of {len(ch)} countries. Lebanon's change ({ch['LBN']:+.1f} points) was "
                + ("the largest rise in the world." if rank_of(ch, 'LBN') == 1 else f"the {ordinal(rank_of(ch, 'LBN'))} largest rise in the world.")
                + "</p>", unsafe_allow_html=True)

# ----------------------------------------------------------------------------- 2. the rank
with tabs[1]:
    st.subheader("From 63rd to 2nd in the world")
    col_a, col_b = st.columns([3, 2])
    year = col_a.select_slider("Year", options=YEARS, value=2023, key="rank_year",
                               help="2024 onward are WHO projections.")
    who_r = col_b.segmented_control("Show", list(SEXES), default="Everyone", key="rank_sex", required=True)
    sex_r = SEXES[who_r]
    vals = countries("tobacco_use", sex_r, year)
    order = vals.sort_values(ascending=False)
    top = order.head(12)
    lr = rank_of(vals, "LBN")
    if "LBN" not in top.index:
        top = pd.concat([top, order.loc[["LBN"]]])
    labels = [f"{NAMES[i]}  ({ordinal(rank_of(vals, i))})" if i == "LBN" and lr > 12 else NAMES[i] for i in top.index]
    fig = go.Figure(go.Bar(
        x=top.values, y=labels, orientation="h",
        marker=dict(color=[LEB if i == "LBN" else "#b4b2aa" for i in top.index]),
        text=[f"{v:.1f}%" for v in top.values], textposition="outside", cliponaxis=False,
        hovertemplate="%{y}: %{x:.1f}%<extra></extra>"))
    w_val = series("GLOBAL", sex=sex_r).value.get(year)
    if w_val is not None:
        fig.add_vline(x=w_val, line=dict(color=WORLD, width=2))
        fig.add_annotation(x=w_val, y=1.0, yref="paper", yanchor="bottom", xanchor="left", text=f" World {w_val:.1f}%",
                           showarrow=False, font=dict(size=11, color=INK2))
    base_layout(fig, 34 * len(top) + 70, legend=False)
    fig.update_layout(hovermode="closest", bargap=0.35, margin=dict(l=8, r=48, t=28, b=8), barcornerradius=4)
    fig.update_yaxes(autorange="reversed", gridcolor="rgba(0,0,0,0)", ticksuffix="", tickfont=dict(size=12.5))
    fig.update_xaxes(showgrid=True, gridcolor=GRID, ticksuffix="%", range=[0, max(top.max() * 1.18, 10)])
    show(fig)
    proj = " (WHO projection)" if year > OBS_LAST else ""
    st.markdown(f'<div class="takeaway">In {year}{proj}, Lebanon ranked <b>{ordinal(lr)}</b> of {len(vals)} countries '
                f"({vals['LBN']:.1f}%).</div>", unsafe_allow_html=True)

    st.markdown("**Lebanon's world rank over time**")
    ranks = pd.Series({yr: rank_of(countries("tobacco_use", sex_r, yr), "LBN") for yr in YEARS})
    pos = {YEARS[0]: "middle right", OBS_LAST: "bottom center", YEARS[-1]: "bottom left"}
    fig = go.Figure(go.Scatter(x=ranks.index, y=ranks.values, mode="lines+markers+text", cliponaxis=False,
                               line=dict(color=LEB, width=3), marker=dict(size=8, color=LEB, line=dict(color="white", width=2)),
                               text=[f"  {ordinal(int(r))}  " if yr in pos else "" for yr, r in ranks.items()],
                               textposition=[pos.get(yr, "top center") for yr in ranks.index],
                               textfont=dict(size=12.5, color=INK),
                               hovertemplate="%{x}: ranked %{y}<extra></extra>"))
    base_layout(fig, 260, legend=False, ysuffix="")
    top_rank = int(ranks.max())
    fig.update_yaxes(range=[top_rank + 8, -6], tickvals=[1] + list(range(20, top_rank + 8, 20)),
                     title="world rank (1 = highest)", title_font=dict(size=12))
    fig.update_layout(hovermode="closest")
    show(fig)

# ----------------------------------------------------------------------------- 3. beyond cigarettes
with tabs[2]:
    st.subheader("Cigarettes are only part of the story")
    who_c = st.segmented_control("Show", list(SEXES), default="Everyone", key="cig_sex", required=True)
    sex_c = SEXES[who_c]
    t_s, c_s = series("LBN", "tobacco_use", sex_c), series("LBN", "cigarette_smoking", sex_c)
    obs_t, obs_c = t_s[t_s.index <= OBS_LAST].value, c_s[c_s.index <= OBS_LAST].value
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=obs_c.index, y=obs_c.values, name="Smoke cigarettes", mode="lines",
                             line=dict(color="#8f8d86", width=2.4), hovertemplate="%{y:.1f}%"))
    fig.add_trace(go.Scatter(x=obs_t.index, y=obs_t.values, name="Use any tobacco", mode="lines",
                             line=dict(color=LEB, width=3), fill="tonexty", fillcolor="rgba(235,104,52,0.16)",
                             hovertemplate="%{y:.1f}%"))
    gap23 = obs_t[OBS_LAST] - obs_c[OBS_LAST]
    fig.add_annotation(x=2010, y=(obs_t[2010] + obs_c[2010]) / 2, text="only other tobacco,<br>mostly argileh",
                       showarrow=False, font=dict(size=12, color="#9c3a12"))
    base_layout(fig, 380)
    fig.update_yaxes(rangemode="tozero")
    show(fig)
    grp_c = {"Both sexes": "Lebanese tobacco users", "Men": "Lebanese men who use tobacco",
             "Women": "Lebanese women who use tobacco"}[sex_c]
    st.markdown(f'<div class="takeaway">In 2023, <b>{gap23 / obs_t[OBS_LAST] * 100:.0f}%</b> of {grp_c} did not smoke '
                f"cigarettes at all ({gap23:.1f} of {obs_t[OBS_LAST]:.1f} points). A cigarette-only campaign "
                "would miss them.</div>", unsafe_allow_html=True)

    st.markdown("**Where is smoked tobacco other than cigarettes most common? (2023)**")
    gap = (countries("tobacco_smoking", sex_c, 2023) - countries("cigarette_smoking", sex_c, 2023)).dropna()
    gtop = gap.sort_values(ascending=False).head(10)
    if "LBN" not in gtop.index:
        gtop = pd.concat([gtop, gap.loc[["LBN"]]])
    fig = go.Figure(go.Bar(x=gtop.values, y=[NAMES[i] for i in gtop.index], orientation="h",
                           marker=dict(color=[LEB if i == "LBN" else "#b4b2aa" for i in gtop.index]),
                           text=[f"{v:.1f}" for v in gtop.values], textposition="outside", cliponaxis=False,
                           hovertemplate="%{y}: %{x:.1f} points<extra></extra>"))
    base_layout(fig, 34 * len(gtop) + 50, legend=False, ysuffix="")
    fig.update_layout(hovermode="closest", bargap=0.35, margin=dict(l=8, r=40, t=8, b=8), barcornerradius=4)
    fig.update_yaxes(autorange="reversed", gridcolor="rgba(0,0,0,0)", tickfont=dict(size=12.5))
    fig.update_xaxes(showgrid=True, gridcolor=GRID, title="percentage points",
                     title_font=dict(size=11.5), range=[0, gtop.max() * 1.2])
    show(fig)
    st.markdown(f'<p class="note">Lebanon ranks <b>{ordinal(rank_of(gap, "LBN"))}</b> of {len(gap)} countries on this gap. '
                "WHO does not publish argileh separately for adults, so the gap is the closest measure: in Lebanon, "
                "smokeless tobacco is negligible and the main non-cigarette product is the waterpipe.</p>",
                unsafe_allow_html=True)

# ----------------------------------------------------------------------------- 4. teens
with tabs[3]:
    st.subheader("It starts at school age")
    yl = Y[Y.sex == "Both sexes"].sort_values("year").groupby(["indicator", "iso3"]).tail(1)
    tu = yl[yl.indicator == "tobacco_use"].set_index("iso3")
    cg = yl[yl.indicator == "cigarette_smoking"].set_index("iso3")
    both = tu[["country", "year", "value", "who_region"]].join(cg[["value"]].rename(columns={"value": "cig"}), how="inner")
    view = st.segmented_control("Compare with", ["Eastern Mediterranean", "Top 15 worldwide"],
                                default="Eastern Mediterranean", key="teen_view", required=True)
    d = both[both.who_region == "EMR"] if view == "Eastern Mediterranean" else both.sort_values("value", ascending=False).head(15)
    d = d.sort_values("value", ascending=True)
    fig = go.Figure()
    for iso, r in d.iterrows():
        col = LEB if iso == "LBN" else "#b4b2aa"
        fig.add_trace(go.Scatter(x=[r.cig, r.value], y=[f"{r.country} ({r.year})"] * 2, mode="lines",
                                 line=dict(color=col, width=3), hoverinfo="skip", showlegend=False))
    lab = [f"{r.country} ({r.year})" for _, r in d.iterrows()]
    fig.add_trace(go.Scatter(x=d.cig, y=lab, mode="markers", name="Smoke cigarettes",
                             marker=dict(size=10, color="white", line=dict(color="#6f6d66", width=2)),
                             hovertemplate="%{y}<br>cigarettes: %{x:.1f}%<extra></extra>"))
    fig.add_trace(go.Scatter(x=d.value, y=lab, mode="markers", name="Use any tobacco",
                             marker=dict(size=11, color=[LEB if i == "LBN" else "#6f6d66" for i in d.index],
                                         line=dict(color="white", width=1.5)),
                             hovertemplate="%{y}<br>any tobacco: %{x:.1f}%<extra></extra>"))
    base_layout(fig, 28 * len(d) + 80)
    fig.update_layout(hovermode="closest")
    fig.update_yaxes(gridcolor="rgba(0,0,0,0)", ticksuffix="", tickfont=dict(size=11.5))
    fig.update_xaxes(showgrid=True, gridcolor=GRID, ticksuffix="%", rangemode="tozero",
                     title="% of 13-15-year-olds", title_font=dict(size=11.5))
    show(fig)
    lt = both.loc["LBN"]
    st.markdown(f'<div class="takeaway">In Lebanon\'s {lt.year} school survey, <b>{lt.value:.1f}%</b> of 13-15-year-olds used '
                f"tobacco but only {lt.cig:.1f}% smoked cigarettes: about {round((lt.value - lt.cig) / lt.value * 3)} in 3 young users "
                "used something else, mostly argileh.</div>", unsafe_allow_html=True)
    st.markdown(f'<p class="note">That is the highest teen tobacco use in the Eastern Mediterranean and the '
                f"{ordinal(rank_of(tu.value, 'LBN'))} highest of {len(tu)} countries with data. In the earlier 2011 survey, "
                "about 38% of 13-15-year-olds reported using a waterpipe (MoPH and WHO, Epi-Monitor, 2017), and an analysis of "
                "60 countries' school surveys found Lebanon's teen waterpipe use the highest of all (Yang, Jawad and Filippidis, "
                "2018). Survey years differ between countries, so read close ranks with care.</p>", unsafe_allow_html=True)

# ----------------------------------------------------------------------------- 5. the cost
with tabs[4]:
    st.subheader("What it costs in lives")
    dr = G[G.measure == "tobacco_attributable_death_rate_age_std"].pivot(index="location", columns="year", values="value")
    share = G[G.measure == "share_of_all_deaths_attributable_to_tobacco"].set_index("year").value
    m1, m2 = st.columns(2)
    m1.metric("Deaths caused by tobacco, 2023", f"{deaths[2023]:,.0f}", f"about {deaths[2023] / 365:.0f} a day",
              delta_color="off", delta_arrow="off", border=True)
    m2.metric("Share of all deaths in Lebanon", f"{share[2023]:.1f}%", f"{share[2023] - share[1990]:+.1f} points since 1990",
              delta_color="inverse", border=True)
    fig = go.Figure()
    for loc, col, name, w in [("Global", WORLD, "World", 2.6), ("Lebanon", LEB, "Lebanon", 3.4)]:
        fig.add_trace(go.Scatter(x=["1990", "2023"], y=[dr.loc[loc, 1990], dr.loc[loc, 2023]], name=name,
                                 mode="lines+markers+text", line=dict(color=col, width=w),
                                 marker=dict(size=10, color=col, line=dict(color="white", width=2)),
                                 text=[f"{dr.loc[loc, 1990]:.0f}", f"{dr.loc[loc, 2023]:.0f}"],
                                 textposition=["middle left", "top right" if loc == "Lebanon" else "bottom right"],
                                 textfont=dict(size=13, color=INK), cliponaxis=False,
                                 hovertemplate=f"{name}: %{{y:.0f}} per 100,000<extra></extra>"))
    base_layout(fig, 340, ysuffix="")
    fig.update_layout(hovermode="closest")
    fig.update_xaxes(type="category", range=[-0.4, 1.4])
    fig.update_yaxes(rangemode="tozero", title="deaths per 100,000 (age-standardised)", title_font=dict(size=11.5))
    show(fig)
    st.markdown(f'<div class="takeaway">Tobacco\'s death rate in Lebanon rose from {dr.loc["Lebanon", 1990]:.0f} to '
                f"{dr.loc['Lebanon', 2023]:.0f} per 100,000 while the world's fell from {dr.loc['Global', 1990]:.0f} to "
                f"{dr.loc['Global', 2023]:.0f}. Lebanon is now above the world.</div>", unsafe_allow_html=True)

    cause = G[G.measure == "deaths_by_cause"].set_index("note").value
    cause = pd.concat([cause, pd.Series({"Other causes": deaths[2023] - cause.sum()})])
    short = {"Ischemic heart disease": "Heart disease", "Tracheal, bronchus and lung cancer": "Lung cancer",
             "Chronic obstructive pulmonary disease": "COPD (lung disease)", "Ischemic stroke": "Stroke"}
    st.markdown("**Which diseases? Tobacco deaths in Lebanon, 2023**")
    fig = go.Figure(go.Bar(x=cause.values, y=[short.get(i, i) for i in cause.index], orientation="h",
                           marker=dict(color=[LEB] * 4 + ["#b4b2aa"]), text=[f"{v:,.0f}" for v in cause.values],
                           textposition="outside", cliponaxis=False, hovertemplate="%{y}: %{x:,.0f} deaths<extra></extra>"))
    base_layout(fig, 250, legend=False, ysuffix="")
    fig.update_layout(hovermode="closest", bargap=0.35, margin=dict(l=8, r=48, t=8, b=8), barcornerradius=4)
    fig.update_yaxes(autorange="reversed", gridcolor="rgba(0,0,0,0)", tickfont=dict(size=12.5))
    fig.update_xaxes(showgrid=True, gridcolor=GRID, range=[0, cause.max() * 1.22])
    show(fig)
    age = G[G.measure == "deaths_by_age"].set_index("note").value
    st.markdown(f'<p class="note"><b>{(age["Ages 50-69"] + age["Ages 70+"]) / deaths[2023] * 100:.0f}%</b> of these deaths are in '
                "people aged 50 and over. Tobacco kills decades after people start, so today's record use shapes the "
                "death toll of the 2040s and 2050s.</p>", unsafe_allow_html=True)
    st.caption("Source: IHME Global Burden of Disease 2023 (risk factor: tobacco, both sexes), key figures extracted "
               "with the GBD Results Tool. 'Other causes' is the remainder of the 2023 total.")

# ----------------------------------------------------------------------------- 6. explore
with tabs[5]:
    st.subheader("Explore every country")
    ind_label = st.segmented_control("Measure", ["Any tobacco", "Cigarettes", "Other smoked tobacco"],
                                     default="Any tobacco", key="ex_ind", required=True)
    col_a, col_b = st.columns([3, 2])
    year_e = col_a.select_slider("Year", options=YEARS, value=2023, key="ex_year")
    sex_e = SEXES[col_b.segmented_control("Show", list(SEXES), default="Everyone", key="ex_sex", required=True)]
    if ind_label == "Other smoked tobacco":
        vals_e = (countries("tobacco_smoking", sex_e, year_e) - countries("cigarette_smoking", sex_e, year_e)).dropna().clip(lower=0)
        unit = "points"
    else:
        vals_e = countries("tobacco_use" if ind_label == "Any tobacco" else "cigarette_smoking", sex_e, year_e)
        unit = "%"
    fig = go.Figure(go.Choropleth(
        locations=vals_e.index, z=vals_e.values, text=[NAMES.get(i, i) for i in vals_e.index],
        colorscale=[[0, "#fdf0e9"], [0.5, "#f19468"], [1, "#9c3a12"]], marker_line_color="white", marker_line_width=0.4,
        colorbar=dict(title=dict(text=unit, side="top"), thickness=10, len=0.6, orientation="h", y=-0.12, x=0.5),
        hovertemplate="%{text}: %{z:.1f}" + ("%" if unit == "%" else " points") + "<extra></extra>"))
    fig.update_geos(showframe=False, showcoastlines=False, projection_type="natural earth", bgcolor="white",
                    lataxis_range=[-58, 85], showcountries=False)
    fig.update_layout(height=380, margin=dict(l=0, r=0, t=0, b=40), dragmode=False, font=dict(family=FONT, size=12),
                      geo=dict(fitbounds=False))
    show(fig)
    st.caption("Tap a country to see its value. Countries in white have no WHO estimate. "
               + ("2024 onward are WHO projections." if year_e > OBS_LAST else ""))
    table = pd.DataFrame({"Country": [NAMES.get(i, i) for i in vals_e.index], "Value": vals_e.values.round(1)})
    table["Rank"] = table["Value"].rank(method="min", ascending=False).astype(int)
    table = table.sort_values("Rank")
    with st.expander("See the table"):
        st.dataframe(table, hide_index=True, height=320,
                     column_config={"Value": st.column_config.NumberColumn(f"Value ({unit})", format="%.1f")})
        st.download_button("Download this table (CSV)", table.to_csv(index=False).encode(),
                           file_name=f"tobacco_{ind_label.lower().replace(' ', '_')}_{year_e}.csv", mime="text/csv")

# ----------------------------------------------------------------------------- what you can do / about
st.divider()
st.subheader("What you can do")
comp = POL[(POL.indicator == "P_compl_all_sfe") & (POL.iso3 == "LBN")].value
st.markdown(
    "1. **Drop the 'argileh is lighter' idea.** WHO's tobacco regulation advisers estimate that a typical one-hour "
    "waterpipe session means inhaling 100 to 200 times the smoke volume of a single cigarette. The water does not filter out "
    "the toxicants.\n"
    "2. **Choose smoke-free places and say so.** Lebanon's Law 174 (2011) bans smoking indoors in restaurants, cafés and pubs, "
    f"but WHO scores compliance at only **{comp.iloc[0]:.0f} out of 10** (2022).\n"
    "3. **Share this page** with one friend who thinks argileh doesn't count."
)
if SURVEY_URL:
    st.link_button("Tell us what you think (2-minute survey)", SURVEY_URL, type="primary")
if BLOG_URL:
    st.link_button("Read the full story on our blog", BLOG_URL)

with st.expander("About the data and this dashboard"):
    st.markdown(
        "- **Adult tobacco use, cigarette smoking and tobacco smoking:** WHO Global Health Observatory, tobacco use estimates "
        "(2026 release), adults 15+, age-standardised. 2024, 2025 and 2030 are WHO projections. Lebanon's latest national "
        "survey in the WHO series is from 2023. 'Other smoked tobacco' is tobacco smoking minus cigarette smoking.\n"
        "- **Teens:** Global Youth Tobacco Survey via WHO GHO, ages 13-15, latest survey per country.\n"
        "- **Deaths:** IHME Global Burden of Disease 2023, risk factor tobacco, key figures extracted with the GBD Results Tool.\n"
        "- **Smoke-free law compliance:** WHO GHO, overall compliance score 0-10, 2022.\n"
        "- **Ranks** are among the 167 countries with WHO estimates; ties share the higher rank. Country names follow WHO, "
        "shortened in a few cases.\n"
        "- **Caveat:** WHO's uncertainty range for Lebanon is wide (switch it on in 'The trend'), because few national "
        f"surveys exist. Even its low end for 2023 ({leb.low[2023]:.1f}%) is far above the high end of the world's "
        f"({wld.high[2023]:.1f}%)."
    )
    st.caption("MSBA 325 Data Visualization and Communication, Olayan School of Business, American University of Beirut, Fall 2026.")

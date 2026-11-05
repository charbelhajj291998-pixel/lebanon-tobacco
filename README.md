# Lebanon is smoking against the tide

Interactive dashboard for the MSBA 325 (Data Visualization and Communication) team project, Olayan School of Business, AUB, Fall 2026.

Since 2000 the world has cut adult tobacco use from 33% to 20%. Lebanon went the other way, to 46.3% in 2023, the 2nd highest of 167 countries. Much of the rise is argileh (waterpipe), especially among women and teens.

## What's inside
| Tab | Question it answers |
|---|---|
| The trend | How has tobacco use in Lebanon changed since 2000, compared with the world and any country you pick? |
| The rank | Where does Lebanon rank, in any year from 2000 to 2030, for men, women or everyone? |
| Beyond cigarettes | How much of Lebanon's tobacco use is not cigarettes (mostly argileh)? |
| Teens | How common is tobacco use among 13-15-year-olds in Lebanon and the region? |
| The cost | How many deaths does tobacco cause in Lebanon, and from which diseases? |
| Explore | A world map and a downloadable table for every country |

## Data
- **WHO Global Health Observatory**, tobacco use estimates (2026 release): current tobacco use, tobacco smoking and cigarette smoking, adults 15+, age-standardised, 2000-2025 plus 2030 projections; number of users. API: https://ghoapi.azureedge.net/api/
- **Global Youth Tobacco Survey** (ages 13-15), via WHO GHO.
- **WHO GHO** smoke-free law compliance score (2022).
- **IHME Global Burden of Disease 2023**: tobacco-attributable deaths in Lebanon (key figures, GBD Results Tool).

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy (free)
Push this folder to a public GitHub repository, then go to https://share.streamlit.io, choose **Create app**, pick the repository and set the main file to `app.py`.

To embed the dashboard in a blog post, use the app URL with `?embed=true` added at the end.

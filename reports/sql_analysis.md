# World Cup 2026 Analytics: SQL Analysis

## 1. Dataset Overview

The database contains **49,520 international matches** from **1872-11-30** to **2026-07-19**. It covers **337 teams**, **201 tournaments**, and **269 host countries**.

| Metric | Value |
| --- | --- |
| Matches | 49,520 |
| Date range | 1872-11-30 to 2026-07-19 |
| Unique teams | 337 |
| Tournaments | 201 |
| Host countries | 269 |

This is a large historical football dataset: it spans more than 150 years, covers both competitive and friendly football, and is broad enough for long-run trend analysis rather than just tournament-specific reporting.

---

## 2. Football Through Time

The year-by-year SQL output shows a dramatic expansion in the volume of international football. Early history contains only a handful of matches per year, while the modern era regularly exceeds 900 matches per year and peaked at **1231 matches in 2024**.

| Year | Matches | Average total goals |
| --- | --- | --- |
| 1872 | 1 | 0.00 |
| 1900 | 6 | 3.50 |
| 1950 | 135 | 4.29 |
| 1975 | 397 | 3.04 |
| 2000 | 1040 | 2.83 |
| 2010 | 863 | 2.59 |
| 2020 | 347 | 2.44 |
| 2024 | 1231 | 2.64 |
| 2026 | 423 | 2.87 |

Key trend points:

- The long-run direction is clearly upward: from **1 match in 1872** to **1,231 matches in 2024**.
- Match volume accelerated especially after the mid-20th century, and the modern international calendar is much denser than the early historical period.
- Scoring was much more volatile and generally higher in the earliest decades, when annual averages often exceeded 4 goals per match on very small samples.
- In the modern era, scoring is much more stable and usually stays around **2.5 to 3.0 goals per match**.
- Within the post-1950 period, the highest average total goals came in **1954 (4.33)**, while one of the lowest modern scoring points was **1988 (2.22)**.

Conclusion: the number of international matches has grown strongly over time, while average scoring has generally settled into a narrower modern range after the high-scoring and much smaller early era.

---

## 3. Home Advantage

| Venue type | Matches | Home wins | Draws | Away wins | Home win % | Draw % | Away win % |
| --- | --- | --- | --- | --- | --- | --- | --- |
| neutral | 13156 | 5811 | 2949 | 4396 | 44.17 | 22.42 | 33.41 |
| non_neutral | 36364 | 18454 | 8309 | 9601 | 50.75 | 22.85 | 26.40 |

Analytical conclusion:

- In **non-neutral matches**, the home team wins **50.75%** of the time.
- In **neutral matches**, the home team still wins more often than it loses, but the rate falls to **44.17%**.
- Away wins rise from **26.40%** in non-neutral games to **33.41%** on neutral fields.
- Draw rates are very similar in both environments: **22.85%** vs **22.42%**.

This is strong evidence of home advantage in the dataset. The difference is not subtle: moving from non-neutral to neutral conditions reduces home-win share by more than 6 percentage points and makes outcomes visibly more balanced.

---

## 4. Most Successful Teams

Ranking below is based on total wins, with win rate and goal difference used as secondary ordering signals.

| Team | Matches | Wins | Draws | Losses | Goals For | Goals Against | Goal Diff | Win Rate % |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Brazil | 1064 | 675 | 217 | 172 | 2315 | 961 | 1354 | 63.44 |
| England | 1098 | 631 | 259 | 208 | 2401 | 1053 | 1348 | 57.47 |
| Germany | 1035 | 601 | 214 | 220 | 2331 | 1203 | 1128 | 58.07 |
| Argentina | 1077 | 599 | 257 | 221 | 2047 | 1083 | 964 | 55.62 |
| Sweden | 1105 | 542 | 234 | 329 | 2178 | 1431 | 747 | 49.05 |
| South Korea | 1010 | 539 | 252 | 219 | 1794 | 917 | 877 | 53.37 |
| Mexico | 1008 | 518 | 231 | 259 | 1777 | 1057 | 720 | 51.39 |
| France | 943 | 483 | 195 | 265 | 1735 | 1219 | 516 | 51.22 |
| Italy | 893 | 477 | 243 | 173 | 1565 | 876 | 689 | 53.42 |
| Hungary | 1006 | 472 | 222 | 312 | 2011 | 1483 | 528 | 46.92 |
| Spain | 791 | 468 | 183 | 140 | 1616 | 704 | 912 | 59.17 |
| Netherlands | 883 | 455 | 200 | 228 | 1852 | 1081 | 771 | 51.53 |
| Uruguay | 973 | 428 | 242 | 303 | 1537 | 1182 | 355 | 43.99 |
| Scotland | 854 | 403 | 182 | 269 | 1455 | 1054 | 401 | 47.19 |
| Denmark | 874 | 402 | 185 | 287 | 1587 | 1173 | 414 | 46.00 |
| Japan | 794 | 391 | 167 | 236 | 1451 | 915 | 536 | 49.24 |
| Russia | 749 | 385 | 197 | 167 | 1301 | 735 | 566 | 51.40 |
| Belgium | 859 | 385 | 183 | 291 | 1564 | 1297 | 267 | 44.82 |
| Poland | 892 | 384 | 225 | 283 | 1499 | 1201 | 298 | 43.05 |
| Egypt | 761 | 380 | 188 | 193 | 1233 | 773 | 460 | 49.93 |

Analytical takeaway:

- **Brazil** leads the dataset by total wins and also has the strongest combination of win rate and goal difference among the very high-volume teams.
- **England, Germany, and Argentina** form the next tier: all have massive sample sizes and excellent win profiles.
- Teams such as **Sweden, Mexico, South Korea, and Hungary** rank highly because of both long histories and very large match counts.
- This ranking is intentionally based only on historical match outcomes from the table and does not rely on external rating systems.

---

## 5. Highest Scoring Teams

Minimum filter: **100 matches**.

| Team | Matches | Goals For | Goals Against | Avg Goals For | Avg Goals Against |
| --- | --- | --- | --- | --- | --- |
| Jersey | 235 | 645 | 285 | 2.745 | 1.213 |
| Tahiti | 242 | 657 | 371 | 2.715 | 1.533 |
| New Caledonia | 265 | 698 | 369 | 2.634 | 1.392 |
| Guernsey | 240 | 616 | 313 | 2.567 | 1.304 |
| Fiji | 268 | 608 | 439 | 2.269 | 1.638 |
| Germany | 1035 | 2331 | 1203 | 2.252 | 1.162 |
| England | 1098 | 2401 | 1053 | 2.187 | 0.959 |
| Brazil | 1064 | 2315 | 961 | 2.176 | 0.903 |
| Papua New Guinea | 155 | 336 | 312 | 2.168 | 2.013 |
| Solomon Islands | 214 | 462 | 421 | 2.159 | 1.967 |
| Netherlands | 883 | 1852 | 1081 | 2.097 | 1.224 |
| Spain | 791 | 1616 | 704 | 2.043 | 0.890 |
| Australia | 585 | 1170 | 622 | 2.000 | 1.063 |
| Hungary | 1006 | 2011 | 1483 | 1.999 | 1.474 |
| Sweden | 1105 | 2178 | 1431 | 1.971 | 1.295 |
| Yugoslavia | 483 | 942 | 756 | 1.950 | 1.565 |
| Argentina | 1077 | 2047 | 1083 | 1.901 | 1.006 |
| Czechoslovakia | 520 | 984 | 721 | 1.892 | 1.387 |
| Iran | 615 | 1158 | 486 | 1.883 | 0.790 |
| Vanuatu | 214 | 403 | 460 | 1.883 | 2.150 |

Interpretation:

- The highest-scoring list is not the same as the ?most successful? list. It rewards teams that score heavily per match, not necessarily the teams with the most wins overall.
- Some smaller football ecosystems such as **Jersey, Tahiti, New Caledonia, and Guernsey** rank very highly on scoring rate.
- Among globally prominent long-history teams, **Germany, England, Brazil, the Netherlands, Spain, and Argentina** combine strong scoring rates with very large match volumes.

---

## 6. Biggest Wins

| Date | Home Team | Away Team | Home | Away | Goal Diff | Winner | Loser | Winner Side | Tournament |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2001-04-11 | Australia | American Samoa | 31 | 0 | 31 | Australia | American Samoa | home | FIFA World Cup qualification |
| 1971-09-13 | Tahiti | Cook Islands | 30 | 0 | 30 | Tahiti | Cook Islands | home | South Pacific Games |
| 1979-08-30 | Fiji | Kiribati | 24 | 0 | 24 | Fiji | Kiribati | home | South Pacific Games |
| 2001-04-09 | Australia | Tonga | 22 | 0 | 22 | Australia | Tonga | home | FIFA World Cup qualification |
| 2013-06-24 | Provence | Tibet | 22 | 0 | 22 | Provence | Tibet | home | International Tournament of Peoples, Cultures and Tribes |
| 1966-04-03 | Libya | Oman | 21 | 0 | 21 | Libya | Oman | home | Arab Cup |
| 2005-03-11 | Guam | North Korea | 0 | 21 | 21 | North Korea | Guam | away | EAFF Championship |
| 2013-06-23 | Quebec | Tibet | 21 | 0 | 21 | Quebec | Tibet | home | International Tournament of Peoples, Cultures and Tribes |
| 2006-11-24 | SГЎpmi | Monaco | 21 | 1 | 20 | SГЎpmi | Monaco | home | Viva World Cup |
| 1987-12-15 | American Samoa | Papua New Guinea | 0 | 20 | 20 | Papua New Guinea | American Samoa | away | South Pacific Games |
| 2000-02-14 | Kuwait | Bhutan | 20 | 0 | 20 | Kuwait | Bhutan | home | AFC Asian Cup qualification |
| 2003-06-30 | Sark | Isle of Wight | 0 | 20 | 20 | Isle of Wight | Sark | away | Island Games |
| 2014-06-01 | Darfur | Padania | 0 | 20 | 20 | Padania | Darfur | away | CONIFA World Football Cup |
| 1997-05-13 | Kazakhstan | Guam | 20 | 1 | 19 | Kazakhstan | Guam | home | East Asian Games |
| 1983-08-22 | Niue | Papua New Guinea | 0 | 19 | 19 | Papua New Guinea | Niue | away | South Pacific Games |
| 2000-01-26 | China | Guam | 19 | 0 | 19 | China | Guam | home | AFC Asian Cup qualification |
| 2000-11-24 | Iran | Guam | 19 | 0 | 19 | Iran | Guam | home | FIFA World Cup qualification |
| 2003-06-29 | Gibraltar | Sark | 19 | 0 | 19 | Gibraltar | Sark | home | Island Games |
| 2014-06-02 | Darfur | South Ossetia | 0 | 19 | 19 | South Ossetia | Darfur | away | CONIFA World Football Cup |
| 1963-09-06 | Solomon Islands | Tahiti | 0 | 18 | 18 | Tahiti | Solomon Islands | away | South Pacific Games |

These results should not be ?fixed? or removed automatically. The table shows that the most extreme scorelines are concentrated in qualification or regional tournaments and are historically plausible as lopsided matches between very unequal opponents.

---

## 7. Tournament Analysis

Top tournaments by number of matches, restricted to competitions with at least 50 matches.

| Tournament | Matches | Avg Total Goals | Avg Goal Difference |
| --- | --- | --- | --- |
| Friendly | 18387 | 2.87 | 1.54 |
| FIFA World Cup qualification | 8771 | 2.89 | 1.87 |
| UEFA Euro qualification | 2824 | 2.83 | 1.82 |
| African Cup of Nations qualification | 2327 | 2.42 | 1.45 |
| FIFA World Cup | 1068 | 2.84 | 1.50 |
| Copa AmГ©rica | 869 | 3.14 | 1.82 |
| African Cup of Nations | 845 | 2.38 | 1.19 |
| AFC Asian Cup qualification | 829 | 3.29 | 2.33 |
| UEFA Nations League | 658 | 2.51 | 1.38 |
| CECAFA Cup | 620 | 2.51 | 1.46 |
| CFU Caribbean Cup qualification | 606 | 3.51 | 2.16 |
| Merdeka Tournament | 599 | 3.27 | 1.75 |
| British Home Championship | 523 | 3.52 | 1.93 |
| CONCACAF Nations League | 422 | 3.19 | 1.94 |
| AFC Asian Cup | 421 | 2.66 | 1.48 |
| Gold Cup | 420 | 2.81 | 1.63 |
| Gulf Cup | 410 | 2.51 | 1.44 |
| Island Games | 394 | 3.98 | 2.51 |
| UEFA Euro | 388 | 2.44 | 1.22 |
| Asian Games | 368 | 3.32 | 2.08 |

Key observations:

- **Friendly** matches dominate the dataset by volume, far ahead of any single competitive tournament.
- **FIFA World Cup qualification** is the largest competitive block in the data.
- Some regional competitions and qualification tournaments, such as **CFU Caribbean Cup qualification**, **AFC Asian Cup qualification**, and the **Island Games**, are relatively high-scoring and have wider average margins.
- Major final tournaments like the **FIFA World Cup**, **UEFA Euro**, and **African Cup of Nations** tend to have lower average goal differences, which fits the expectation of more balanced opposition.

---

## 8. Data Quality

The dataset contains exactly **9 matches** where one side scored more than 20 goals.

| Date | Home Team | Away Team | Home | Away | Tournament | City | Country | Max Side Score | Total Goals |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2001-04-11 | Australia | American Samoa | 31 | 0 | FIFA World Cup qualification | Coffs Harbour | Australia | 31 | 31 |
| 1971-09-13 | Tahiti | Cook Islands | 30 | 0 | South Pacific Games | Papeete | Tahiti | 30 | 30 |
| 1979-08-30 | Fiji | Kiribati | 24 | 0 | South Pacific Games | Nausori | Fiji | 24 | 24 |
| 2001-04-09 | Australia | Tonga | 22 | 0 | FIFA World Cup qualification | Coffs Harbour | Australia | 22 | 22 |
| 2013-06-24 | Provence | Tibet | 22 | 0 | International Tournament of Peoples, Cultures and Tribes | Marseille | France | 22 | 22 |
| 2006-11-24 | SГЎpmi | Monaco | 21 | 1 | Viva World Cup | HyГЁres | France | 21 | 22 |
| 1966-04-03 | Libya | Oman | 21 | 0 | Arab Cup | Baghdad | Iraq | 21 | 21 |
| 2005-03-11 | Guam | North Korea | 0 | 21 | EAFF Championship | Taipei | Taiwan | 21 | 21 |
| 2013-06-23 | Quebec | Tibet | 21 | 0 | International Tournament of Peoples, Cultures and Tribes | Marseille | France | 21 | 21 |

Assessment:

- These rows are **extreme but rare**: 9 matches out of 49,520 total matches.
- They are not isolated technical fragments: they have valid dates, identifiable teams, tournaments, and structured score values.
- They cluster in qualifiers, regional games, and alternative competitions, which makes them look more like **real historical outliers** than parser failures.
- At the same time, the table contains some **text encoding artifacts** in categorical fields, for example garbled characters in a few team, city, and tournament names. That is a separate quality issue from the score values.
- Based only on the database, the safest conclusion is: these 9 results should be treated as **plausible historical outliers that merit manual verification**, not as automatic errors.

Nothing was deleted or corrected.

---

## 9. Interesting Facts

- **Oldest recorded match:** 1872-11-30. Scotland 0:0 England.
- **Most recent recorded match:** 2026-07-19. Spain 1:0 Argentina.
- **Most active year:** 2024. 1231 matches.
- **Highest-scoring year (50+ matches):** 1912. 5.06 goals per match across 53 matches.
- **Tournament with most matches:** Friendly. 18387 matches.
- **Country hosting the most matches:** United States. 1585 matches.
- **Most frequent host city:** Kuala Lumpur. 745 matches.
- **Biggest home win:** 31-goal margin. 2001-04-11: Australia 31:0 American Samoa.
- **Biggest away win:** 21-goal margin. 2005-03-11: Guam 0:21 North Korea.
- **Highest-scoring single match:** 31 total goals. 2001-04-11: Australia 31:0 American Samoa.
- **Most common scoreline:** 1:0. 5106 matches.


---

## 10. Executive Summary

This project assembled a production-like analytical pipeline around a historical database of **49,520 international football matches** spanning **1872 to 2026**. The final SQL analysis shows three clear patterns.

First, international football expanded enormously over time. The dataset begins with isolated matches in the nineteenth century and grows into a modern calendar with more than one thousand matches in peak years. Second, there is clear evidence of **home advantage**: non-neutral home teams win materially more often than away teams, while neutral venues produce more balanced outcomes. Third, long-run team performance is highly concentrated: a small group of historically dominant teams ? led by Brazil, England, Germany, and Argentina ? combine large match volumes with strong win rates and goal differences.

Tournament structure also matters. Friendlies and qualification matches dominate the database by volume, while major final tournaments are generally tighter and less one-sided. At the same time, the dataset preserves rare but important outliers, including a small number of matches with scores above 20. These should not be removed automatically; they are part of the historical record, although some rows indicate text-encoding issues in categorical labels that should be reviewed before any public presentation layer is built.

Overall, the SQL stage is now strong enough to support substantive football analysis directly from PostgreSQL. The database is large, historically broad, internally consistent on core match fields, and already capable of answering meaningful business-style questions about scale, competition structure, home advantage, and long-run team performance.

"""P7: build market_events.csv and inversion_regimes.csv from data/raw/market/*.csv and meeting_master.csv.
uv run python scripts/20_build_market_panel.py [--selftest-only]
ISOLATION (plan 1.3): this script reads NO stance/index file (sentence_stance.csv, stance_index.csv, ...) and computes no correlation
or regression between rates and stance. Units: yields in % in the raw files; dY*, dUST*, d_i are in bp.
Alignment: Y_t is the value on the meeting date t (a Korean trading day); Y_prev the previous Korean trading day (ECOS dates).
  us_prev_bday(t) = latest US business day STRICTLY BEFORE t (US close of t-1 precedes the Korean session of t); dUST_lag is that day's
  change from the previous US observation. bok_rate = rate in the ECOS daily series on t; bok_rate_prev = rate on calendar day t-1.
  Spread_lag = bok_rate_prev - fed upper target (as of t-1, carried forward); D_inv = 1[Spread_lag < 0].
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

RAW = Path("data/raw/market")
INTERIM = Path("data/interim")
META = Path("data/metadata")


def read_series(name):
    df = pd.read_csv(RAW / f"{name}.csv", parse_dates=["date"])
    s = df.set_index("date")["value"].sort_index()
    assert s.index.is_unique and s.notna().all(), name
    return s


def us_prev_bday(t, us_dates):
    """Latest date in us_dates (US business days with an observation) strictly before t; None if there is none."""
    i = us_dates.searchsorted(t, side="left")
    return us_dates[i - 1] if i > 0 else None


def prev_obs(d, dates):
    i = dates.searchsorted(d, side="left")
    return dates[i - 1] if i > 0 else None


def selftest():
    idx = pd.DatetimeIndex(pd.to_datetime(["2010-11-24", "2010-11-26", "2010-11-29", "2024-01-05", "2024-01-09"]))
    assert us_prev_bday(pd.Timestamp("2010-11-26"), idx) == pd.Timestamp("2010-11-24")  # day after Thanksgiving (11-25 closed) -> Wed
    assert us_prev_bday(pd.Timestamp("2010-11-29"), idx) == pd.Timestamp("2010-11-26")  # Monday meeting -> previous Friday
    assert us_prev_bday(pd.Timestamp("2024-01-09"), idx) == pd.Timestamp("2024-01-05")  # Tuesday after a gap -> Friday
    assert us_prev_bday(pd.Timestamp("2010-11-24"), idx) is None
    print("selftest ok: Monday meeting, post-holiday meeting, series start")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest-only", action="store_true")
    ap.add_argument("--master", default=str(META / "meeting_master.csv"))
    ap.add_argument("--ko-release", default=str(META / "ko_release_dates.csv"))
    ap.add_argument("--out-events", default=str(INTERIM / "market_events.csv"))
    ap.add_argument("--out-regimes", default=str(INTERIM / "inversion_regimes.csv"))
    ap.add_argument("--out-checks", default=str(INTERIM / "market_checks.txt"))
    args = ap.parse_args()
    selftest()
    if args.selftest_only:
        return
    log = []

    def say(*a):
        line = " ".join(str(x) for x in a)
        print(line)
        log.append(line)

    mm = pd.read_csv(args.master, encoding="utf-8-sig", parse_dates=["meeting_date"])
    reg = mm[mm["regular"] == 1].sort_values("meeting_date").reset_index(drop=True)
    y3, y10 = read_series("ecos_ktb3y"), read_series("ecos_ktb10y")
    br = read_series("ecos_base_rate")
    u2, u10, fed = read_series("fred_dgs2"), read_series("fred_dgs10"), read_series("fred_dfedtaru")
    kr_days = y3.index
    assert kr_days.equals(y10.index), "3y and 10y trading-day calendars differ"
    us_days = u2.index.intersection(u10.index)  # a day counts only if both DGS2 and DGS10 were observed
    last = reg["meeting_date"].max()
    for nm, s_ in (('base rate', br), ('fed target', fed), ('KTB', y3), ('DGS', u2)):
        assert s_.index.max() >= last, f"{nm} series ends before the last meeting {last.date()}"

    rows, missing = [], []
    for t in reg["meeting_date"]:
        r = {"meeting_date": t.strftime("%Y-%m-%d")}
        if t not in kr_days:
            missing.append((r["meeting_date"], "meeting date is not a Korean trading day in ECOS KTB series"))
            rows.append(r)
            continue
        p = prev_obs(t, kr_days)
        r.update(prev_trading_day=p.strftime("%Y-%m-%d"), Y3=y3[t], Y3_prev=y3[p], dY3=round((y3[t] - y3[p]) * 100, 4),
                 Y10=y10[t], Y10_prev=y10[p], dY10=round((y10[t] - y10[p]) * 100, 4))
        ub = us_prev_bday(t, us_days)
        ubp = prev_obs(ub, us_days) if ub is not None else None
        assert ub is not None and ubp is not None, f"no US business day before {t.date()}"
        r.update(us_prev_bday=ub.strftime("%Y-%m-%d"), dUST2_lag=round((u2[ub] - u2[ubp]) * 100, 4),
                 dUST10_lag=round((u10[ub] - u10[ubp]) * 100, 4))
        d1 = t - pd.Timedelta(days=1)
        r.update(bok_rate=br.asof(t), bok_rate_prev=br.asof(d1), fed_upper_lag=fed.asof(d1))
        assert not any(pd.isna(r[k]) for k in ("bok_rate", "bok_rate_prev", "fed_upper_lag")), f"missing rate input at {t.date()}"
        r["d_i"] = round((r["bok_rate"] - r["bok_rate_prev"]) * 100, 4)
        r["spread_lag"] = round(r["bok_rate_prev"] - r["fed_upper_lag"], 4)
        r["D_inv"] = int(r["spread_lag"] < 0)
        r["D_freq"] = int(t.year >= 2017)
        rows.append(r)
    ev = pd.DataFrame(rows)
    cols = ["meeting_date", "Y3", "Y3_prev", "dY3", "Y10", "Y10_prev", "dY10", "dUST2_lag", "dUST10_lag", "bok_rate", "bok_rate_prev",
            "d_i", "fed_upper_lag", "spread_lag", "D_inv", "D_freq", "prev_trading_day", "us_prev_bday"]
    ev = ev[cols]
    ev.to_csv(args.out_events, index=False)

    say("== completeness (regular meetings:", len(reg), ") ==")
    for c in ("dY3", "dY10", "d_i", "dUST2_lag", "dUST10_lag", "spread_lag"):
        say(f"missing {c}: {int(ev[c].isna().sum())}")
    for m in missing:
        say("MISSING reason:", *m)

    say("\n== D_freq vs meeting_master.freq_regime ==")
    j = ev.merge(reg[["meeting_date", "freq_regime"]].assign(meeting_date=lambda d: d["meeting_date"].dt.strftime("%Y-%m-%d")), on="meeting_date")
    say("D_freq==freq_regime for all:", bool((j["D_freq"] == j["freq_regime"]).all()), "| D_freq counts:", j["D_freq"].value_counts().sort_index().to_dict(),
        "| master counts:", reg["freq_regime"].value_counts().sort_index().to_dict())

    say("\n== base-rate change timing (all changes in the ECOS daily series since 2009-12) ==")
    chg = br.diff()[lambda x: x.abs() > 1e-9].dropna()
    alld = pd.to_datetime(mm["meeting_date"])
    for d, v in chg.items():
        near = [(m, int(r)) for m, r in zip(alld, mm["regular"]) if abs((m - d).days) <= 3]
        tag = ", ".join(f"meeting {m.date()} regular={r} offset(change-meeting)={(d - m).days}" for m, r in near) or "NO MEETING within 3 days"
        if not any(off == 0 and rr == 1 for (m, rr), off in zip(near, [(d - m).days for m, _ in near])):
            say(f"change {d.date()} {v * 100:+.0f}bp -> {tag}")
    n_same = sum(1 for d in chg.index if d in set(reg["meeting_date"]))
    say(f"changes on a regular-meeting date: {n_same} of {len(chg)} (lines above list the exceptions)")
    em = mm[mm["regular"] == 0]
    for _, e in em.iterrows():
        i0 = br.asof(e["meeting_date"] - pd.Timedelta(days=1))
        say(f"emergency meeting {e['meeting_date'].date()}: rate day-before {i0}, same day {br.asof(e['meeting_date'])}, next day {br.asof(e['meeting_date'] + pd.Timedelta(days=1))}")
        nxt = reg[reg["meeting_date"] > e["meeting_date"]].iloc[0]["meeting_date"]
        row = ev[ev["meeting_date"] == nxt.strftime("%Y-%m-%d")].iloc[0]
        say(f"  next regular meeting {nxt.date()}: bok_rate_prev={row['bok_rate_prev']} bok_rate={row['bok_rate']} d_i={row['d_i']} (emergency change not mixed in iff d_i==0 here)")
    nz = ev[ev["d_i"].notna() & (ev["d_i"] != 0)][["meeting_date", "d_i"]]
    say(f"\nmeetings with d_i != 0: {len(nz)}; distribution:", nz["d_i"].value_counts().sort_index().to_dict())

    say("\n== inversion regimes ==")
    daily = pd.DataFrame({"br": br, "fed": fed}).dropna()
    daily = daily.reindex(pd.date_range(daily.index.min(), daily.index.max())).ffill()
    daily["spread"] = daily["br"] - daily["fed"]
    neg = daily["spread"] < 0
    run = (neg != neg.shift()).cumsum()
    cal = [(g.index.min(), g.index.max()) for _, g in daily[neg].groupby(run[neg])]
    ev_d = ev.assign(d=pd.to_datetime(ev["meeting_date"]))
    reg_rows, grp = [], (ev_d["D_inv"] != ev_d["D_inv"].shift()).cumsum()
    for k, (_, g) in enumerate(ev_d[ev_d["D_inv"] == 1].groupby(grp[ev_d["D_inv"] == 1]), start=1):
        s, e = g["d"].min(), g["d"].max()
        c = [x for x in cal if x[0] <= e - pd.Timedelta(days=1) and x[1] >= s - pd.Timedelta(days=1)]
        reg_rows.append({"regime_id": k, "start_date": s.strftime("%Y-%m-%d"), "end_date": e.strftime("%Y-%m-%d"), "n_meetings": len(g),
                         "first_neg_day": c[0][0].strftime("%Y-%m-%d") if c else "", "last_neg_day": c[-1][1].strftime("%Y-%m-%d") if c else "",
                         "last_neg_day_censored_by_data_end": bool(c and c[-1][1] == daily.index.max())})
    rg = pd.DataFrame(reg_rows)
    rg.to_csv(args.out_regimes, index=False)
    say(rg.to_string(index=False))
    say("total D_inv=1 meetings:", int(ev["D_inv"].sum()), "of", len(ev))
    say("(proposal estimate: 3rd ~16 meetings 2018-03..2020-02, 4th ~34 meetings 2022-07..present)")

    say("\n== ko_release_dates: Korean business-day check ==")
    ko = pd.read_csv(args.ko_release, encoding="utf-8-sig", parse_dates=["meeting_date", "ko_release_date"])
    bad = ko[~ko["ko_release_date"].isin(kr_days)]
    say(f"{len(ko)} release dates; in ECOS Korean trading-day calendar: {len(ko) - len(bad)}; not in it: {len(bad)}")
    for _, b in bad.iterrows():
        say("  not a trading day:", b["ko_release_date"].date(), b["ko_release_date"].day_name(), "(meeting", b["meeting_date"].date(), ")")
    say("meeting_master 1:1 with ko_release (dates after 2023-04):", sorted(set(ko["meeting_date"])) == sorted(set(reg[reg["meeting_date"] >= "2023-04-01"]["meeting_date"])))
    Path(args.out_checks).write_text("\n".join(log) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

"""تجميع حركات كل موظف: أول بصمة = دخول، آخر بصمة = خروج في نفس اليوم (مع دعم الشيفت المسائي)."""
import calendar
from dataclasses import dataclass
from datetime import datetime, date, time, timedelta

from .constants import WORK_DAYS_PER_REST


@dataclass
class Cfg:
    night_start_hour: int = 15      # أول بصمة بعد هذه الساعة = بداية شيفت مسائي
    night_end_hour: int = 12        # بصمة الخروج المسائي يجب أن تكون قبل هذه الساعة من اليوم التالي
    max_span_hours: int = 16        # أقصى مدة للشيفت الواحد
    min_minutes: int = 30           # أقل فارق بين الدخول والخروج (غيره يعتبر تكرار بصمة)


@dataclass
class Day:
    day: date
    in_dt: datetime
    out_dt: datetime = None
    night: bool = False

    @property
    def hours(self):
        if self.out_dt is None:
            return 0.0
        return (self.out_dt - self.in_dt).total_seconds() / 3600.0

    @property
    def note(self):
        n = []
        if self.night:
            n.append("مسائي")
        if self.out_dt is None:
            n.append("بصمة ناقصة")
        return " - ".join(n)


def _day_record(d, plist, cfg):
    plist = sorted(plist)
    first, last = plist[0], plist[-1]
    if (last - first) < timedelta(minutes=cfg.min_minutes):
        return Day(d, first, None)
    return Day(d, first, last)


def _day_mode(ps, cfg):
    by = {}
    for p in ps:
        by.setdefault(p.date(), []).append(p)
    return {d: _day_record(d, pl, cfg) for d, pl in by.items()}


def _night_pairs(ps, cfg):
    by = {}
    for p in ps:
        by.setdefault(p.date(), []).append(p)
    pairs = 0
    for d, pl in by.items():
        first = min(pl)
        if first.hour < cfg.night_start_hour:
            continue
        limit = min(first + timedelta(hours=cfg.max_span_hours),
                    datetime.combine(d + timedelta(days=1), time(cfg.night_end_hour)))
        if any(first + timedelta(minutes=cfg.min_minutes) <= p <= limit for p in ps):
            pairs += 1
    return pairs, len(by)


def detect_mode(ps, cfg=None):
    cfg = cfg or Cfg()
    pairs, ndays = _night_pairs(ps, cfg)
    return "night" if ndays and pairs >= 2 and pairs >= 0.5 * ndays else "day"


def _night_mode(ps, cfg):
    ps = sorted(ps)
    used = [False] * len(ps)
    days = {}
    for d in sorted({p.date() for p in ps}):
        idx = [i for i, p in enumerate(ps) if p.date() == d and not used[i]]
        if not idx:
            continue
        start = next((i for i in idx if ps[i].hour >= cfg.night_start_hour), None)
        if start is None:
            days[d] = _day_record(d, [ps[i] for i in idx], cfg)
            for i in idx:
                used[i] = True
            continue
        s = ps[start]
        limit = min(s + timedelta(hours=cfg.max_span_hours),
                    datetime.combine(d + timedelta(days=1), time(cfg.night_end_hour)))
        cand = [i for i in range(start, len(ps)) if ps[i] <= limit and not used[i]]
        outs = [i for i in cand if ps[i] - s >= timedelta(minutes=cfg.min_minutes)]
        out = ps[outs[-1]] if outs else None
        for i in cand:
            used[i] = True
        for i in idx:
            if i < start:
                used[i] = True
        days[d] = Day(d, s, out, night=out is not None and out.date() != d)
    return days


def build_days(punches, mode="auto", cfg=None):
    cfg = cfg or Cfg()
    ps = sorted(set(punches))
    if not ps:
        return {}
    if mode == "auto":
        mode = detect_mode(ps, cfg)
    return _night_mode(ps, cfg) if mode == "night" else _day_mode(ps, cfg)


@dataclass
class Summary:
    month_days: int = 30
    present: int = 0
    rest: int = 0
    remaining: int = 0
    complete_days: int = 0
    total_hours: float = 0.0
    avg_hours: float = 0.0
    ot_hours: float = 0.0
    short_hours: float = 0.0


def month_days_of(ym):
    y, m = int(ym[:4]), int(ym[5:7])
    return calendar.monthrange(y, m)[1]


def summarize(days, ym, req_hours, grace_min):
    md = month_days_of(ym)
    y, m = int(ym[:4]), int(ym[5:7])
    mine = [d for d in days.values() if d.day.year == y and d.day.month == m]
    s = Summary(month_days=md)
    s.present = len(mine)
    s.rest = min(s.present // WORK_DAYS_PER_REST, md - s.present)
    s.remaining = md - s.present - s.rest
    ot = sh = 0.0
    for d in mine:
        if d.out_dt is None:
            continue
        s.complete_days += 1
        s.total_hours += d.hours
        diff = (d.hours - req_hours) * 60.0
        if diff > grace_min:
            ot += diff
        elif diff < -grace_min:
            sh += -diff
    s.avg_hours = s.total_hours / s.complete_days if s.complete_days else 0.0
    s.ot_hours = ot / 60.0
    s.short_hours = sh / 60.0
    return s

"""تجميع حركات كل موظف: صباحي (أول بصمة دخول وآخر بصمة خروج في نفس اليوم) أو مسائي (يمتد لليوم التالي)."""
import calendar
from dataclasses import dataclass
from datetime import datetime, date, time, timedelta

from .constants import WORK_DAYS_PER_REST


@dataclass
class Cfg:
    split_hour: int = 12            # الشيفت المسائي: قبل هذه الساعة = بصمة خروج لليوم السابق، بعدها = بصمة دخول
    detect_hour: int = 6            # للكشف التلقائي: بصمة بين 00:00 وهذه الساعة تدل على شيفت مسائي
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


def _by_date(ps):
    by = {}
    for p in ps:
        by.setdefault(p.date(), []).append(p)
    return by


def detect_mode(ps, cfg=None):
    """الموظف مسائي لو بصماته بعد منتصف الليل (00:00 - detect_hour) متكررة في نصف أيامه على الأقل.
    بصمة بعد منتصف الليل لا يمكن أن تكون دخول، فهي خروج شيفت اليوم السابق."""
    cfg = cfg or Cfg()
    by = _by_date(ps)
    early = sum(1 for pl in by.values() if any(p.hour < cfg.detect_hour for p in pl))
    return "night" if early >= 2 and early >= 0.5 * len(by) else "day"


def _night_mode(ps, cfg):
    """يوم العمل = تاريخ بصمة الدخول.
    الدخول = أول بصمة بعد الساعة 12 ظهراً في اليوم.
    الخروج = آخر بصمة قبل الساعة 12 ظهراً في اليوم التالي.
    بصمات الصباح تخص شيفت اليوم السابق ولا تُحسب كدخول."""
    by = _by_date(sorted(ps))
    dates = sorted(by)
    days, claimed = {}, set()
    one_day = timedelta(days=1)
    for d in dates:
        eve = [p for p in by[d] if p.hour >= cfg.split_hour]
        if not eve:
            continue
        s = eve[0]
        morning = [p for p in by.get(d + one_day, []) if p.hour < cfg.split_hour]
        out = morning[-1] if morning and morning[-1] - s >= timedelta(minutes=cfg.min_minutes) else None
        days[d] = Day(d, s, out, night=True)
        if morning:
            claimed.add(d + one_day)
    # بصمات صباحية لا يقابلها دخول في اليوم السابق
    for d in dates:
        if d in days or d in claimed or d == dates[0]:
            continue   # أول يوم في البيانات: خروج شيفت آخر الشهر السابق، يُهمل
        days[d] = Day(d, by[d][0], None)
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

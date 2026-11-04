def calculate(emp, s):
    """emp: dict بيانات الموظف للشهر، s: Summary. يرجع dict بكل بنود المرتب."""
    md = s.month_days
    salary = float(emp.get("salary") or 0)
    allowances = float(emp.get("allowances") or 0)
    penalties = float(emp.get("penalties") or 0)
    insurance = float(emp.get("insurance") or 0)
    advance = float(emp.get("advance") or 0)
    req = float(emp.get("req_hours") or 10) or 10.0
    rate = float(emp.get("ot_rate") or 1.0)
    leave = max(0, min(int(emp.get("leave_days") or 0), s.remaining))
    absent = s.remaining - leave

    daily = salary / md if md else 0.0
    hourly = daily / req
    ot_manual = emp.get("ot_manual")
    ot_hours = float(ot_manual) if ot_manual not in (None, "") else s.ot_hours
    ot_pay = ot_hours * hourly * rate
    absence_ded = absent * daily
    leave_ded = 0.0 if emp.get("leave_paid", 1) else leave * daily
    short_ded = s.short_hours * hourly if emp.get("deduct_short") else 0.0

    gross = salary + allowances + ot_pay
    total_ded = absence_ded + leave_ded + short_ded + penalties + insurance + advance
    net = gross - total_ded
    r = lambda x: round(x + 1e-9, 2)
    return {
        "salary": r(salary), "allowances": r(allowances), "penalties": r(penalties),
        "insurance": r(insurance), "advance": r(advance), "leave": leave, "absent": absent,
        "daily": r(daily), "hourly": r(hourly), "ot_hours": round(ot_hours, 2), "ot_pay": r(ot_pay),
        "absence_ded": r(absence_ded), "leave_ded": r(leave_ded), "short_ded": r(short_ded),
        "gross": r(gross), "total_ded": r(total_ded), "net": r(net),
    }

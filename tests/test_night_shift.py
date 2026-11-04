import os, sys, unittest
from datetime import datetime, date
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from aswaq_hr.attendance import build_days, detect_mode, summarize


def dt(d, hm):
    return datetime(2026, 10, d, int(hm[:2]), int(hm[3:]))


class NightShift(unittest.TestCase):
    def test_user_example_auto(self):
        # دخول 1 الساعة 18:00 - خروج 2 الساعة 04:00 - دخول 2 الساعة 18:00 - خروج 3 الساعة 04:00
        ps = [dt(1, "18:00"), dt(2, "04:00"), dt(2, "18:00"), dt(3, "04:00")]
        self.assertEqual(detect_mode(ps), "night")
        days = build_days(ps)
        self.assertEqual(sorted(days), [date(2026, 10, 1), date(2026, 10, 2)])
        self.assertAlmostEqual(days[date(2026, 10, 1)].hours, 10)
        self.assertEqual(days[date(2026, 10, 1)].in_dt, dt(1, "18:00"))
        self.assertEqual(days[date(2026, 10, 1)].out_dt, dt(2, "04:00"))
        self.assertAlmostEqual(days[date(2026, 10, 2)].hours, 10)

    def test_20_to_11(self):
        days = build_days([dt(5, "20:00"), dt(6, "11:00")], "night")
        self.assertAlmostEqual(days[date(2026, 10, 5)].hours, 15)

    def test_duplicates_and_orphan_first_morning(self):
        ps = [dt(1, "03:50"),                      # خروج شيفت الشهر السابق: يُهمل
              dt(1, "18:00"), dt(1, "18:02"),      # تكرار دخول
              dt(2, "03:00"), dt(2, "04:05"),      # آخر بصمة صباحية هي الخروج
              dt(2, "18:10")]                      # دخول بدون خروج
        days = build_days(ps, "night")
        self.assertEqual(sorted(days), [date(2026, 10, 1), date(2026, 10, 2)])
        self.assertEqual(days[date(2026, 10, 1)].in_dt, dt(1, "18:00"))
        self.assertEqual(days[date(2026, 10, 1)].out_dt, dt(2, "04:05"))
        self.assertIsNone(days[date(2026, 10, 2)].out_dt)
        self.assertIn("بصمة ناقصة", days[date(2026, 10, 2)].note)

    def test_month_summary_counts_each_shift_once(self):
        ps = []
        for d in range(1, 11):
            ps += [dt(d, "18:00"), dt(d + 1, "04:00")] if d < 10 else [dt(d, "18:00"), dt(11, "04:00")]
        s = summarize(build_days(ps), "2026-10", 10, 20)
        self.assertEqual(s.present, 10)
        self.assertAlmostEqual(s.total_hours, 100)
        self.assertAlmostEqual(s.ot_hours, 0)

    def test_day_worker_unchanged(self):
        ps = [dt(1, "08:00"), dt(1, "18:00"), dt(2, "08:30"), dt(2, "17:30")]
        self.assertEqual(detect_mode(ps), "day")
        days = build_days(ps)
        self.assertAlmostEqual(days[date(2026, 10, 1)].hours, 10)
        self.assertAlmostEqual(days[date(2026, 10, 2)].hours, 9)

    def test_day_worker_single_late_punch_not_night(self):
        ps = [dt(1, "08:00"), dt(1, "18:00"), dt(2, "00:30"), dt(2, "08:00"), dt(2, "18:00"),
              dt(3, "08:00"), dt(3, "18:00"), dt(4, "08:00"), dt(4, "18:00")]
        self.assertEqual(detect_mode(ps), "day")


if __name__ == "__main__":
    unittest.main()

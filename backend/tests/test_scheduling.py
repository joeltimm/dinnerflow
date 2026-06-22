"""Phase 3: per-user meal-plan delivery time + timezone (tasks.send_all_meal_plans)."""
from datetime import datetime

from tasks import send_all_meal_plans
from tests.conftest import seed_user

NOW = "2026-06-24T14:30:00+00:00"  # a Wednesday, 14:30 UTC
WEEKDAY = datetime.fromisoformat(NOW).isoweekday()


def _set_schedule(db, uid, *, tz="UTC", hour=14, minute=30, days=(WEEKDAY,)):
    with db.cursor() as cur:
        cur.execute(
            "UPDATE users SET timezone_name = %s, meal_plan_hour = %s, "
            "meal_plan_minute = %s, email_days = %s WHERE id = %s",
            (tz, hour, minute, list(days), uid),
        )


def test_enqueues_at_local_time_once_per_day(db, mocker):
    delay = mocker.patch("tasks.send_meal_plan_for_user.delay")
    uid = seed_user(db, email="tz@example.com", email_consent=True)
    _set_schedule(db, uid)

    send_all_meal_plans(now_iso=NOW)
    delay.assert_called_once()
    assert delay.call_args[0][0] == uid

    # A second tick in the same local day must not re-send (last_meal_plan_sent_at guard).
    send_all_meal_plans(now_iso=NOW)
    delay.assert_called_once()


def test_skips_when_minute_does_not_match(db, mocker):
    delay = mocker.patch("tasks.send_meal_plan_for_user.delay")
    uid = seed_user(db, email="tz2@example.com", email_consent=True)
    _set_schedule(db, uid, minute=31)  # user wants 14:31, tick is 14:30

    send_all_meal_plans(now_iso=NOW)
    delay.assert_not_called()


def test_skips_when_weekday_not_selected(db, mocker):
    delay = mocker.patch("tasks.send_meal_plan_for_user.delay")
    uid = seed_user(db, email="tz3@example.com", email_consent=True)
    other_day = (WEEKDAY % 7) + 1
    _set_schedule(db, uid, days=(other_day,))

    send_all_meal_plans(now_iso=NOW)
    delay.assert_not_called()


def test_respects_user_timezone(db, mocker):
    """A user in a different zone gets mail at their own local 14:30, not UTC 14:30."""
    delay = mocker.patch("tasks.send_meal_plan_for_user.delay")
    uid = seed_user(db, email="ny@example.com", email_consent=True)
    # 14:30 America/New_York == 18:30 UTC, so the 14:30 UTC tick should NOT fire.
    _set_schedule(db, uid, tz="America/New_York")

    send_all_meal_plans(now_iso=NOW)
    delay.assert_not_called()


def test_skips_unconsented_user(db, mocker):
    delay = mocker.patch("tasks.send_meal_plan_for_user.delay")
    uid = seed_user(db, email="noconsent@example.com", email_consent=False)
    _set_schedule(db, uid)

    send_all_meal_plans(now_iso=NOW)
    delay.assert_not_called()

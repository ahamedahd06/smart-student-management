"""Chart data for admin/lecturer analytics — real DB when available."""
from __future__ import annotations

from catalog import PROGRAMMES
from database import get_connection

# When no `students.course` rows yet: same names as registration (max five bars).
_FALLBACK_MODULES: tuple[str, ...] = tuple(PROGRAMMES)


def module_programme_attendance_chart(max_n: int = 5) -> dict[str, float]:
    """Average `students.attendance_rate` grouped by `course` (programme name), top `max_n` by headcount."""
    max_n = max(1, min(8, max_n))
    with get_connection() as c:
        rows = c.execute(
            """
            SELECT course AS label, AVG(COALESCE(attendance_rate, 0)) AS pct, COUNT(*) AS n
            FROM students
            WHERE course IS NOT NULL AND TRIM(course) != ''
            GROUP BY course
            ORDER BY n DESC, label
            LIMIT ?
            """,
            (max_n,),
        ).fetchall()
    if rows:
        return {str(r["label"]): round(float(r["pct"] or 0), 1) for r in rows}
    demo = [86.0, 91.0, 84.0, 88.0, 83.0]
    names = list(_FALLBACK_MODULES[:max_n])
    return {names[i]: demo[i] for i in range(len(names))}


def emotion_sentiment_chart() -> dict[str, int]:
    """Counts from emotion_logs (else attendance_records) mapped to Positive / Neutral / Negative."""

    def bump(row_em: str | None, counts: dict[str, int]) -> None:
        if not row_em:
            return
        e = row_em.lower().strip()
        if e == "happy":
            counts["Positive"] += 1
        elif e in ("angry", "sad"):
            counts["Negative"] += 1
        else:
            counts["Neutral"] += 1

    counts = {"Positive": 0, "Neutral": 0, "Negative": 0}
    with get_connection() as c:
        rows = c.execute(
            "SELECT emotion FROM emotion_logs WHERE emotion IS NOT NULL AND TRIM(emotion) != ''"
        ).fetchall()
        if not rows:
            rows = c.execute(
                "SELECT emotion FROM attendance_records WHERE emotion IS NOT NULL AND TRIM(emotion) != ''"
            ).fetchall()
    for r in rows:
        em = (r["emotion"] or "").strip()
        if em.lower() == "no_face":
            continue
        bump(r["emotion"], counts)
    if sum(counts.values()) == 0:
        return {"Positive": 8, "Neutral": 4, "Negative": 2}
    return counts


def weekly_checkin_trend(max_points: int = 5) -> dict[str, list[float | int]]:
    """Last N calendar weeks: attendance % and distinct alert rows (rough proxy)."""
    max_points = max(2, min(12, max_points))
    with get_connection() as c:
        att_rows = c.execute(
            """
            SELECT strftime('%Y-%W', check_in_time) AS wk,
                   SUM(CASE WHEN status = 'present' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS pct
            FROM attendance_records
            WHERE check_in_time IS NOT NULL AND TRIM(check_in_time) != ''
            GROUP BY wk
            ORDER BY wk DESC
            LIMIT ?
            """,
            (max_points,),
        ).fetchall()
    att_rows = list(reversed(att_rows))
    if att_rows:
        labels = [f"Week {i+1}" for i in range(len(att_rows))]
        pcts = [round(float(r["pct"] or 0), 1) for r in att_rows]
        with get_connection() as c:
            alert_counts: list[int] = []
            for r in att_rows:
                wk = r["wk"]
                n = c.execute(
                    "SELECT COUNT(*) AS c FROM retention_alerts WHERE strftime('%Y-%W', created_at) = ?",
                    (wk,),
                ).fetchone()["c"]
                alert_counts.append(int(n or 0))
        return {"Attendance %": pcts, "Alerts": alert_counts}

    return {"Attendance %": [88.0, 86.0, 90.0, 84.0, 89.0][:max_points], "Alerts": [2, 4, 3, 5, 2][:max_points]}

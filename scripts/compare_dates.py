#!/usr/bin/env python3
"""Calculate comparison periods for Yizhilan analysis without network access.

Relative-period modes default to Gregorian year-over-year comparisons. Period-over-period
comparisons require an explicit period-over-period mode.
"""

from __future__ import annotations

import argparse
import calendar
import json
from dataclasses import dataclass
from datetime import date, timedelta


# The lunar conversion tables and conversion algorithm in this file are adapted
# from wolfhong/LunarCalendar:
# https://github.com/wolfhong/LunarCalendar
#
# MIT License
#
# Copyright (c) 2018 wolfhong
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


LUNAR_MONTH_DAYS = (
    1887,
    0x1694, 0x16AA, 0x4AD5, 0xAB6, 0xC4B7, 0x4AE, 0xA56, 0xB52A,
    0x1D2A, 0xD54, 0x75AA, 0x156A, 0x1096D, 0x95C, 0x14AE, 0xAA4D,
    0x1A4C, 0x1B2A, 0x8D55, 0xAD4, 0x135A, 0x495D, 0x95C, 0xD49B,
    0x149A, 0x1A4A, 0xBAA5, 0x16A8, 0x1AD4, 0x52DA, 0x12B6, 0xE937,
    0x92E, 0x1496, 0xB64B, 0xD4A, 0xDA8, 0x95B5, 0x56C, 0x12AE,
    0x492F, 0x92E, 0xCC96, 0x1A94, 0x1D4A, 0xADA9, 0xB5A, 0x56C,
    0x726E, 0x125C, 0xF92D, 0x192A, 0x1A94, 0xDB4A, 0x16AA, 0xAD4,
    0x955B, 0x4BA, 0x125A, 0x592B, 0x152A, 0xF695, 0xD94, 0x16AA,
    0xAAB5, 0x9B4, 0x14B6, 0x6A57, 0xA56, 0x1152A, 0x1D2A, 0xD54,
    0xD5AA, 0x156A, 0x96C, 0x94AE, 0x14AE, 0xA4C, 0x7D26, 0x1B2A,
    0xEB55, 0xAD4, 0x12DA, 0xA95D, 0x95A, 0x149A, 0x9A4D, 0x1A4A,
    0x11AA5, 0x16A8, 0x16D4, 0xD2DA, 0x12B6, 0x936, 0x9497,
    0x1496, 0x1564B, 0xD4A, 0xDA8, 0xD5B4, 0x156C, 0x12AE,
    0xA92F, 0x92E, 0xC96, 0x6D4A, 0x1D4A, 0x10D65, 0xB58, 0x156C,
    0xB26D, 0x125C, 0x192C, 0x9A95, 0x1A94, 0x1B4A, 0x4B55, 0xAD4,
    0xF55B, 0x4BA, 0x125A, 0xB92B, 0x152A, 0x1694, 0x96AA, 0x15AA,
    0x12AB5, 0x974, 0x14B6, 0xCA57, 0xA56, 0x1526, 0x8E95, 0xD54,
    0x15AA, 0x49B5, 0x96C, 0xD4AE, 0x149C, 0x1A4C, 0xBD26, 0x1AA6,
    0xB54, 0x6D6A, 0x12DA, 0x1695D, 0x95A, 0x149A, 0xDA4B, 0x1A4A,
    0x1AA4, 0xBB54, 0x16B4, 0xADA, 0x495B, 0x936, 0xF497, 0x1496,
    0x154A, 0xB6A5, 0xDA4, 0x15B4, 0x6AB6, 0x126E, 0x1092F, 0x92E,
    0xC96, 0xCD4A, 0x1D4A, 0xD64, 0x956C, 0x155C, 0x125C, 0x792E,
    0x192C, 0xFA95, 0x1A94, 0x1B4A, 0xAB55, 0xAD4, 0x14DA, 0x8A5D,
    0xA5A, 0x1152B, 0x152A, 0x1694, 0xD6AA, 0x15AA, 0xAB4, 0x94BA,
    0x14B6, 0xA56, 0x7527, 0xD26, 0xEE53, 0xD54, 0x15AA, 0xA9B5,
    0x96C, 0x14AE, 0x8A4E, 0x1A4C, 0x11D26, 0x1AA4, 0x1B54,
    0xCD6A, 0xADA, 0x95C, 0x949D, 0x149A, 0x1A2A, 0x5B25, 0x1AA4,
    0xFB52, 0x16B4, 0xABA, 0xA95B, 0x936, 0x1496, 0x9A4B, 0x154A,
    0x136A5, 0xDA4, 0x15AC,
)

SOLAR_NEW_YEAR = (
    1887,
    0xEC04C, 0xEC23F, 0xEC435, 0xEC649, 0xEC83E, 0xECA51, 0xECC46,
    0xECE3A, 0xED04D, 0xED242, 0xED436, 0xED64A, 0xED83F, 0xEDA53,
    0xEDC48, 0xEDE3D, 0xEE050, 0xEE244, 0xEE439, 0xEE64D, 0xEE842,
    0xEEA36, 0xEEC4A, 0xEEE3E, 0xEF052, 0xEF246, 0xEF43A, 0xEF64E,
    0xEF843, 0xEFA37, 0xEFC4B, 0xEFE41, 0xF0054, 0xF0248, 0xF043C,
    0xF0650, 0xF0845, 0xF0A38, 0xF0C4D, 0xF0E42, 0xF1037, 0xF124A,
    0xF143E, 0xF1651, 0xF1846, 0xF1A3A, 0xF1C4E, 0xF1E44, 0xF2038,
    0xF224B, 0xF243F, 0xF2653, 0xF2848, 0xF2A3B, 0xF2C4F, 0xF2E45,
    0xF3039, 0xF324D, 0xF3442, 0xF3636, 0xF384A, 0xF3A3D, 0xF3C51,
    0xF3E46, 0xF403B, 0xF424E, 0xF4443, 0xF4638, 0xF484C, 0xF4A3F,
    0xF4C52, 0xF4E48, 0xF503C, 0xF524F, 0xF5445, 0xF5639, 0xF584D,
    0xF5A42, 0xF5C35, 0xF5E49, 0xF603E, 0xF6251, 0xF6446, 0xF663B,
    0xF684F, 0xF6A43, 0xF6C37, 0xF6E4B, 0xF703F, 0xF7252, 0xF7447,
    0xF763C, 0xF7850, 0xF7A45, 0xF7C39, 0xF7E4D, 0xF8042, 0xF8254,
    0xF8449, 0xF863D, 0xF8851, 0xF8A46, 0xF8C3B, 0xF8E4F, 0xF9044,
    0xF9237, 0xF944A, 0xF963F, 0xF9853, 0xF9A47, 0xF9C3C, 0xF9E50,
    0xFA045, 0xFA238, 0xFA44C, 0xFA641, 0xFA836, 0xFAA49, 0xFAC3D,
    0xFAE52, 0xFB047, 0xFB23A, 0xFB44E, 0xFB643, 0xFB837, 0xFBA4A,
    0xFBC3F, 0xFBE53, 0xFC048, 0xFC23C, 0xFC450, 0xFC645, 0xFC839,
    0xFCA4C, 0xFCC41, 0xFCE36, 0xFD04A, 0xFD23D, 0xFD451, 0xFD646,
    0xFD83A, 0xFDA4D, 0xFDC43, 0xFDE37, 0xFE04B, 0xFE23F, 0xFE453,
    0xFE648, 0xFE83C, 0xFEA4F, 0xFEC44, 0xFEE38, 0xFF04C, 0xFF241,
    0xFF436, 0xFF64A, 0xFF83E, 0xFFA51, 0xFFC46, 0xFFE3A, 0x10004E,
    0x100242, 0x100437, 0x10064B, 0x100841, 0x100A53, 0x100C48,
    0x100E3C, 0x10104F, 0x101244, 0x101438, 0x10164C, 0x101842,
    0x101A35, 0x101C49, 0x101E3D, 0x102051, 0x102245, 0x10243A,
    0x10264E, 0x102843, 0x102A37, 0x102C4B, 0x102E3F, 0x103053,
    0x103247, 0x10343B, 0x10364F, 0x103845, 0x103A38, 0x103C4C,
    0x103E42, 0x104036, 0x104249, 0x10443D, 0x104651, 0x104846,
    0x104A3A, 0x104C4E, 0x104E43, 0x105038, 0x10524A, 0x10543E,
    0x105652, 0x105847, 0x105A3B, 0x105C4F, 0x105E45, 0x106039,
    0x10624C, 0x106441, 0x106635, 0x106849, 0x106A3D, 0x106C51,
    0x106E47, 0x10703C, 0x10724F, 0x107444, 0x107638, 0x10784C,
    0x107A3F, 0x107C53, 0x107E48,
)

MIN_SUPPORTED = date(1900, 1, 31)
MAX_SUPPORTED = date(2100, 12, 31)


@dataclass(frozen=True)
class LunarDate:
    year: int
    month: int
    day: int
    is_leap_month: bool = False


class AlignmentNeeded(Exception):
    def __init__(self, issue: str, message: str, details: dict | None = None):
        super().__init__(message)
        self.issue = issue
        self.message = message
        self.details = details or {}


def get_bit_int(data: int, length: int, shift: int) -> int:
    return (data & (((1 << length) - 1) << shift)) >> shift


def solar_to_int(year: int, month: int, day: int) -> int:
    adjusted_month = (month + 9) % 12
    adjusted_year = year - adjusted_month // 10
    return (
        365 * adjusted_year
        + adjusted_year // 4
        - adjusted_year // 100
        + adjusted_year // 400
        + (adjusted_month * 306 + 5) // 10
        + day
        - 1
    )


def solar_from_int(value: int) -> date:
    year = (10000 * value + 14780) // 3652425
    day_of_year = value - (
        365 * year + year // 4 - year // 100 + year // 400
    )
    if day_of_year < 0:
        year -= 1
        day_of_year = value - (
            365 * year + year // 4 - year // 100 + year // 400
        )
    month_index = (100 * day_of_year + 52) // 3060
    month = (month_index + 2) % 12 + 1
    year += (month_index + 2) // 12
    day = day_of_year - (month_index * 306 + 5) // 10 + 1
    return date(year, month, day)


def validate_solar(value: date) -> None:
    if not MIN_SUPPORTED <= value <= MAX_SUPPORTED:
        raise ValueError(
            f"date {value.isoformat()} is outside the supported lunar range "
            f"{MIN_SUPPORTED.isoformat()} to {MAX_SUPPORTED.isoformat()}"
        )


def lunar_year_data(year: int) -> int:
    index = year - LUNAR_MONTH_DAYS[0]
    if index <= 0 or index >= len(LUNAR_MONTH_DAYS):
        raise ValueError(f"lunar year {year} is outside the conversion table")
    return LUNAR_MONTH_DAYS[index]


def lunar_month_length(value: LunarDate) -> int:
    if not 1 <= value.month <= 12:
        raise ValueError(f"invalid lunar month: {value.month}")
    year_data = lunar_year_data(value.year)
    leap_month = get_bit_int(year_data, 4, 13)
    if value.is_leap_month and leap_month != value.month:
        raise AlignmentNeeded(
            "missing_leap_month",
            (
                f"农历 {value.year} 年没有闰 {value.month} 月，"
                "需要用户确认农历同比对齐方式。"
            ),
            {
                "lunar_year": value.year,
                "month": value.month,
                "requested_leap_month": True,
                "actual_leap_month": leap_month or None,
            },
        )

    if value.is_leap_month:
        sequence_index = leap_month
    elif leap_month == 0 or value.month <= leap_month:
        sequence_index = value.month - 1
    else:
        sequence_index = value.month
    return 30 if get_bit_int(year_data, 1, 12 - sequence_index) else 29


def lunar_to_solar(value: LunarDate) -> date:
    month_days = lunar_month_length(value)
    if not 1 <= value.day <= month_days:
        raise AlignmentNeeded(
            "missing_lunar_day",
            (
                f"农历 {value.year} 年"
                f"{'闰' if value.is_leap_month else ''}{value.month} 月"
                f"没有第 {value.day} 日，需要用户确认对齐方式。"
            ),
            {
                "lunar_year": value.year,
                "month": value.month,
                "day": value.day,
                "is_leap_month": value.is_leap_month,
                "month_days": month_days,
            },
        )

    year_data = lunar_year_data(value.year)
    leap_month = get_bit_int(year_data, 4, 13)
    if value.is_leap_month:
        months_before = leap_month
    elif leap_month == 0 or value.month <= leap_month:
        months_before = value.month - 1
    else:
        months_before = value.month

    offset = 0
    for index in range(months_before):
        offset += 30 if get_bit_int(year_data, 1, 12 - index) else 29
    offset += value.day

    new_year_data = SOLAR_NEW_YEAR[value.year - SOLAR_NEW_YEAR[0]]
    new_year = get_bit_int(new_year_data, 12, 9)
    new_month = get_bit_int(new_year_data, 4, 5)
    new_day = get_bit_int(new_year_data, 5, 0)
    result = solar_from_int(
        solar_to_int(new_year, new_month, new_day) + offset - 1
    )
    validate_solar(result)
    return result


def solar_to_lunar(value: date) -> LunarDate:
    validate_solar(value)
    index = value.year - SOLAR_NEW_YEAR[0]
    packed_date = (value.year << 9) | (value.month << 5) | value.day
    if SOLAR_NEW_YEAR[index] > packed_date:
        index -= 1

    new_year_data = SOLAR_NEW_YEAR[index]
    new_year = get_bit_int(new_year_data, 12, 9)
    new_month = get_bit_int(new_year_data, 4, 5)
    new_day = get_bit_int(new_year_data, 5, 0)
    offset = solar_to_int(value.year, value.month, value.day) - solar_to_int(
        new_year, new_month, new_day
    )

    year_data = LUNAR_MONTH_DAYS[index]
    leap_month = get_bit_int(year_data, 4, 13)
    lunar_year = index + SOLAR_NEW_YEAR[0]
    lunar_sequence_month = 1
    offset += 1

    for sequence_index in range(13):
        month_days = (
            30 if get_bit_int(year_data, 1, 12 - sequence_index) else 29
        )
        if offset > month_days:
            lunar_sequence_month += 1
            offset -= month_days
        else:
            break

    lunar_month = lunar_sequence_month
    is_leap = False
    if leap_month and lunar_sequence_month > leap_month:
        lunar_month = lunar_sequence_month - 1
        is_leap = lunar_sequence_month == leap_month + 1
    return LunarDate(
        year=lunar_year,
        month=lunar_month,
        day=int(offset),
        is_leap_month=is_leap,
    )


def parse_date(raw_value: str) -> date:
    try:
        return date.fromisoformat(raw_value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"invalid ISO date {raw_value!r}; expected YYYY-MM-DD"
        ) from exc


def period_payload(start: date, end: date) -> dict:
    return {
        "start": start.isoformat(),
        "end": end.isoformat(),
        "days": (end - start).days + 1,
    }


def lunar_payload(value: LunarDate) -> dict:
    return {
        "year": value.year,
        "month": value.month,
        "day": value.day,
        "is_leap_month": value.is_leap_month,
    }


def shift_month(value: date, months: int, policy: str) -> tuple[date, list[str]]:
    absolute_month = value.year * 12 + value.month - 1 + months
    target_year, zero_based_month = divmod(absolute_month, 12)
    target_month = zero_based_month + 1
    target_last_day = calendar.monthrange(target_year, target_month)[1]
    if value.day > target_last_day:
        clamped = date(target_year, target_month, target_last_day)
        if policy == "ask":
            raise AlignmentNeeded(
                "missing_month_day",
                (
                    f"{value.isoformat()} 向前移动后没有同日；"
                    "请用户选择月末对齐或明确等长对比区间。"
                ),
                {
                    "source": value.isoformat(),
                    "target_year": target_year,
                    "target_month": target_month,
                    "month_end_candidate": clamped.isoformat(),
                    "options": [
                        "月末对齐：使用目标月最后一天",
                        "等长周期：由用户明确对比区间",
                    ],
                },
            )
        return clamped, [
            (
                f"{value.isoformat()} 在目标月份无同日，"
                f"已按月末对齐到 {clamped.isoformat()}。"
            )
        ]
    return date(target_year, target_month, value.day), []


def shift_month_period(
    start: date, end: date, months: int, policy: str
) -> tuple[date, date, list[str]]:
    shifted_start, start_notes = shift_month(start, months, policy)
    shifted_end, end_notes = shift_month(end, months, policy)
    return shifted_start, shifted_end, start_notes + end_notes


def month_bounds(value: date) -> tuple[date, date]:
    first = value.replace(day=1)
    last = value.replace(day=calendar.monthrange(value.year, value.month)[1])
    return first, last


def is_full_calendar_month(start: date, end: date) -> bool:
    first, last = month_bounds(start)
    return start == first and end == last


def previous_full_month(start: date) -> tuple[date, date]:
    previous_end = start.replace(day=1) - timedelta(days=1)
    return previous_end.replace(day=1), previous_end


def quarter_bounds(value: date) -> tuple[date, date]:
    first_month = ((value.month - 1) // 3) * 3 + 1
    first = date(value.year, first_month, 1)
    last_month = first_month + 2
    last = date(
        value.year,
        last_month,
        calendar.monthrange(value.year, last_month)[1],
    )
    return first, last


def is_full_calendar_quarter(start: date, end: date) -> bool:
    first, last = quarter_bounds(start)
    return start == first and end == last


def previous_full_quarter(start: date) -> tuple[date, date]:
    previous_end = quarter_bounds(start)[0] - timedelta(days=1)
    return quarter_bounds(previous_end)


def shift_year(value: date) -> tuple[date, list[str]]:
    try:
        return value.replace(year=value.year - 1), []
    except ValueError:
        if value.month == 2 and value.day == 29:
            fallback = date(value.year - 1, 2, 28)
            return fallback, [
                (
                    f"{value.isoformat()} 在上一年无同日，"
                    f"已按规则对齐到 {fallback.isoformat()}。"
                )
            ]
        raise


def gregorian_comparison(
    mode: str, start: date, end: date, month_end_policy: str
) -> dict:
    notes: list[str] = []
    if mode == "previous-period":
        period_days = (end - start).days + 1
        comparison_end = start - timedelta(days=1)
        comparison_start = comparison_end - timedelta(days=period_days - 1)
        rule = "普通环比：对比紧邻本期之前的等长自然日区间"
    elif mode == "day-over-day":
        if start != end:
            raise ValueError(
                "日环比只接受单个日期；明确日期区间只说环比时使用 previous-period"
            )
        comparison_start = start - timedelta(days=1)
        comparison_end = comparison_start
        rule = "日环比：对比前一自然日"
    elif mode == "week-over-week":
        comparison_start = start - timedelta(days=7)
        comparison_end = end - timedelta(days=7)
        rule = "周环比：对比上一自然周的相同星期范围"
    elif mode in ("month-over-month", "current-month-over-month"):
        if mode == "month-over-month" and is_full_calendar_month(start, end):
            comparison_start, comparison_end = previous_full_month(start)
        else:
            comparison_start, comparison_end, notes = shift_month_period(
                start, end, -1, month_end_policy
            )
        rule = "月环比：对比上一个自然月同期"
    elif mode in ("quarter-over-quarter", "current-quarter-over-quarter"):
        if mode == "quarter-over-quarter" and is_full_calendar_quarter(start, end):
            comparison_start, comparison_end = previous_full_quarter(start)
        else:
            comparison_start, comparison_end, notes = shift_month_period(
                start, end, -3, month_end_policy
            )
        rule = "季度环比：对比上一个自然季度同期"
    elif mode == "year-over-year":
        comparison_start, start_notes = shift_year(start)
        comparison_end, end_notes = shift_year(end)
        notes = start_notes + end_notes
        rule = "公历同比：对比上一年相同公历日期"
    else:
        raise ValueError(f"unsupported Gregorian comparison mode: {mode}")

    if mode in {
        "month-over-month",
        "current-month-over-month",
        "quarter-over-quarter",
        "current-quarter-over-quarter",
    }:
        current_days = (end - start).days + 1
        comparison_days = (comparison_end - comparison_start).days + 1
        if current_days != comparison_days:
            notes.append(
                "自然周期同期按月序和日号对齐；"
                f"本期 {current_days} 天，对比期 {comparison_days} 天。"
            )

    notes = list(dict.fromkeys(notes))
    return {
        "status": "ok",
        "mode": mode,
        "rule": rule,
        "current": period_payload(start, end),
        "comparison": period_payload(comparison_start, comparison_end),
        "notes": notes,
    }


def lunar_year_over_year(start: date, end: date) -> dict:
    current_start_lunar = solar_to_lunar(start)
    current_end_lunar = solar_to_lunar(end)
    previous_start_lunar = LunarDate(
        current_start_lunar.year - 1,
        current_start_lunar.month,
        current_start_lunar.day,
        current_start_lunar.is_leap_month,
    )
    previous_end_lunar = LunarDate(
        current_end_lunar.year - 1,
        current_end_lunar.month,
        current_end_lunar.day,
        current_end_lunar.is_leap_month,
    )
    comparison_start = lunar_to_solar(previous_start_lunar)
    comparison_end = lunar_to_solar(previous_end_lunar)
    if comparison_start > comparison_end:
        raise AlignmentNeeded(
            "lunar_range_order",
            "换算后的农历同比区间顺序异常，需要用户确认边界。",
            {
                "comparison_start": comparison_start.isoformat(),
                "comparison_end": comparison_end.isoformat(),
            },
        )

    return {
        "status": "ok",
        "mode": "lunar-year-over-year",
        "rule": "农历同比：上一农历年相同农历月日，再换算为公历",
        "current": period_payload(start, end),
        "current_lunar": {
            "start": lunar_payload(current_start_lunar),
            "end": lunar_payload(current_end_lunar),
        },
        "comparison": period_payload(comparison_start, comparison_end),
        "comparison_lunar": {
            "start": lunar_payload(previous_start_lunar),
            "end": lunar_payload(previous_end_lunar),
        },
        "notes": [
            "实际查询和回答应同时展示本期与对比期的公历日期。"
        ],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Calculate Gregorian or lunar comparison periods."
    )
    parser.add_argument(
        "--mode",
        required=True,
        choices=(
            "previous-period",
            "day-over-day",
            "week-over-week",
            "month-over-month",
            "quarter-over-quarter",
            "current-week",
            "current-week-over-week",
            "current-month",
            "current-month-over-month",
            "current-quarter",
            "current-quarter-over-quarter",
            "recent-days",
            "recent-days-over-previous-period",
            "year-over-year",
            "lunar-year-over-year",
        ),
        help=(
            "current-week/current-month/current-quarter/recent-days 默认公历同比；"
            "使用 previous-period 或明确的日/周/月/季度环比模式计算环比。"
        ),
    )
    parser.add_argument("--start", type=parse_date)
    parser.add_argument(
        "--end",
        type=parse_date,
        help="Inclusive end date; defaults to the start date.",
    )
    parser.add_argument(
        "--as-of",
        type=parse_date,
        help="Reference date for current-* and recent-days modes.",
    )
    parser.add_argument(
        "--days",
        type=int,
        help="Number of complete days for recent-days.",
    )
    parser.add_argument(
        "--month-end-policy",
        choices=("ask", "clamp"),
        default="ask",
        help="For missing target dates, ask by default or clamp to month end.",
    )
    parser.add_argument(
        "--alignment-confirmed",
        action="store_true",
        help="Required with --month-end-policy clamp after explicit user approval.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    relative_modes = {
        "current-week",
        "current-week-over-week",
        "current-month",
        "current-month-over-month",
        "current-quarter",
        "current-quarter-over-quarter",
        "recent-days",
        "recent-days-over-previous-period",
    }
    recent_modes = {
        "recent-days",
        "recent-days-over-previous-period",
    }
    month_alignment_modes = {
        "month-over-month",
        "quarter-over-quarter",
        "current-month-over-month",
        "current-quarter-over-quarter",
    }

    if args.month_end_policy == "clamp" and args.mode not in month_alignment_modes:
        parser.error("--month-end-policy clamp 只适用于月环比或季度环比")
    if args.alignment_confirmed and args.month_end_policy != "clamp":
        parser.error("--alignment-confirmed 必须与 --month-end-policy clamp 同时使用")
    if args.month_end_policy == "clamp" and not args.alignment_confirmed:
        result = {
            "status": "error",
            "mode": args.mode,
            "issue": "confirmation_required",
            "message": (
                "--month-end-policy clamp 只能在用户明确选择月末对齐后使用；"
                "请同时传入 --alignment-confirmed。"
            ),
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2

    requested_mode = args.mode
    if requested_mode in relative_modes:
        if args.start is not None or args.end is not None:
            parser.error(f"{requested_mode} 使用 --as-of，不接受 --start/--end")
        if args.as_of is None:
            parser.error(f"{requested_mode} 必须提供 --as-of")

        if requested_mode in {"current-week", "current-week-over-week"}:
            if args.days is not None:
                parser.error("--days 只适用于 recent-days")
            current_start = args.as_of - timedelta(days=args.as_of.weekday())
            current_end = args.as_of
            calculation_mode = (
                "year-over-year"
                if requested_mode == "current-week"
                else "week-over-week"
            )
        elif requested_mode in {"current-month", "current-month-over-month"}:
            if args.days is not None:
                parser.error("--days 只适用于 recent-days")
            current_start = args.as_of.replace(day=1)
            current_end = args.as_of
            calculation_mode = (
                "year-over-year"
                if requested_mode == "current-month"
                else "current-month-over-month"
            )
        elif requested_mode in {"current-quarter", "current-quarter-over-quarter"}:
            if args.days is not None:
                parser.error("--days 只适用于 recent-days")
            current_start = quarter_bounds(args.as_of)[0]
            current_end = args.as_of
            calculation_mode = (
                "year-over-year"
                if requested_mode == "current-quarter"
                else "current-quarter-over-quarter"
            )
        else:
            if args.days is None or args.days <= 0:
                parser.error("recent-days 必须提供正整数 --days")
            current_end = args.as_of - timedelta(days=1)
            current_start = current_end - timedelta(days=args.days - 1)
            calculation_mode = (
                "year-over-year"
                if requested_mode == "recent-days"
                else "previous-period"
            )
    else:
        if args.start is None:
            parser.error(f"{requested_mode} 必须提供 --start")
        if args.as_of is not None or args.days is not None:
            parser.error("--as-of/--days 只适用于 current-* 或 recent-days")
        current_start = args.start
        current_end = args.end or args.start
        calculation_mode = requested_mode

    if current_end < current_start:
        parser.error("--end must not be earlier than --start")

    try:
        if calculation_mode == "lunar-year-over-year":
            result = lunar_year_over_year(current_start, current_end)
        else:
            result = gregorian_comparison(
                calculation_mode,
                current_start,
                current_end,
                args.month_end_policy,
            )
        result["mode"] = requested_mode
        if requested_mode in relative_modes:
            result["reference_date"] = args.as_of.isoformat()
        if requested_mode in recent_modes:
            if requested_mode == "recent-days":
                result["rule"] = (
                    f"近 {args.days} 天默认公历同比：今天之前的 {args.days} 个完整自然日，"
                    "对比上一年相同公历日期区间"
                )
            else:
                result["rule"] = (
                    f"近 {args.days} 天环比：今天之前的 {args.days} 个完整自然日，"
                    f"对比其之前的 {args.days} 个完整自然日"
                )
            result["requested_days"] = args.days
    except AlignmentNeeded as exc:
        result = {
            "status": "needs_confirmation",
            "mode": requested_mode,
            "current": period_payload(current_start, current_end),
            "issue": exc.issue,
            "message": exc.message,
            "details": exc.details,
        }
    except ValueError as exc:
        result = {
            "status": "error",
            "mode": requested_mode,
            "message": str(exc),
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

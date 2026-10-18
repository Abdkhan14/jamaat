// Thursday 2026-10-08 at noon ET (UTC-4) — not a Friday, after Zuhr iqamah
export const FIXED_THURSDAY_NOON = new Date('2026-10-08T16:00:00Z')

// Friday 2026-10-09 at noon ET — Jummah day
export const FIXED_FRIDAY_NOON = new Date('2026-10-09T16:00:00Z')

// Fajr iqamah is 06:00 local. 05:45 ET = before iqamah → Available
export const BEFORE_FAJR_IQAMAH = new Date('2026-10-08T09:45:00Z')  // 05:45 ET

// 06:04 ET = within 3-min grace → still Available
export const WITHIN_FAJR_GRACE = new Date('2026-10-08T10:04:00Z')  // 06:04 ET

// 06:05 ET = past grace → Finished
export const AFTER_FAJR_GRACE = new Date('2026-10-08T10:05:00Z')  // 06:05 ET

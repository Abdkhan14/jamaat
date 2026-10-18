import type { PrayerTimes } from '../../types'

const BASE_PRAYER_TIMES: PrayerTimes['prayer_times'] = {
  mosque_name: 'Test Mosque',
  date: '2026-10-05',
  fajr_start: '05:00:00',
  fajr_iqamah: '06:00:00',
  zuhr_start: null,
  zuhr_iqamah: '13:30:00',
  asr_start: null,
  asr_iqamah: '18:00:00',
  maghrib_start: null,
  maghrib_iqamah: '20:00:00',
  isha_start: null,
  isha_iqamah: '22:00:00',
  jummah1_start: '13:00:00',
  jummah1_iqamah: '13:30:00',
  jummah2_start: null,
  jummah2_iqamah: '14:30:00',
  jummah3_start: null,
  jummah3_iqamah: null,
  updated_at: '2026-10-05T03:00:00+00:00',
}

export const mosqueFull: PrayerTimes = {
  name: 'Test Mosque',
  address: '123 Test St, Scarborough, ON',
  website: 'https://example.com',
  latitude: 43.7,
  longitude: -79.3,
  prayer_times: BASE_PRAYER_TIMES,
}

export const mosqueMaghribNull: PrayerTimes = {
  ...mosqueFull,
  name: 'Maghrib Mosque',
  prayer_times: { ...BASE_PRAYER_TIMES, mosque_name: 'Maghrib Mosque', maghrib_iqamah: null },
}

export const prayerTimesList: PrayerTimes[] = [
  mosqueFull,
  { ...mosqueFull, name: 'Second Mosque', prayer_times: { ...BASE_PRAYER_TIMES, mosque_name: 'Second Mosque' } },
]

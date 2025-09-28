const PRAYERS = [
  'fajr',
  'zuhr',
  'asr',
  'maghrib',
  'isha',
  'jummah1',
  'jummah2',
  'jummah3'
] as const;

export type PrayerName = typeof PRAYERS[number];

export type PrayerTimes = {
  address: string;
  latitude: number;
  longitude: number;
  name: string;
  website: string;
  prayer_times: {
    asr_iqamah: string | null;
    asr_start: string | null;
    date: string;
    fajr_iqamah: string | null;
    fajr_start: string | null;
    isha_iqamah: string | null;
    isha_start: string | null;
    jummah1_iqamah: string | null;
    jummah1_start: string | null;
    jummah2_iqamah: string | null;
    jummah2_start: string | null;
    jummah3_iqamah: string | null;
    jummah3_start: string | null;
    maghrib_iqamah: string | null;
    maghrib_start: string | null;
    mosque_name: string;
    updated_at: string;
    zuhr_iqamah: string | null;
    zuhr_start: string | null;
  };
};

type PrayerTimeKeysMap = {
    [P in PrayerName]: {
      start: keyof PrayerTimes["prayer_times"];
      iqamah: keyof PrayerTimes["prayer_times"];
    };
};
  
export const PRAYER_TIME_KEYS: PrayerTimeKeysMap = {
    fajr:    { start: "fajr_start",    iqamah: "fajr_iqamah" },
    zuhr:    { start: "zuhr_start",    iqamah: "zuhr_iqamah" },
    asr:     { start: "asr_start",     iqamah: "asr_iqamah" },
    maghrib: { start: "maghrib_start", iqamah: "maghrib_iqamah" },
    isha:    { start: "isha_start",    iqamah: "isha_iqamah" },
    jummah1: { start: "jummah1_start", iqamah: "jummah1_iqamah" },
    jummah2: { start: "jummah2_start", iqamah: "jummah2_iqamah" },
    jummah3: { start: "jummah3_start", iqamah: "jummah3_iqamah" },
};
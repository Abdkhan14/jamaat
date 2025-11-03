export enum Prayer {
  FAJR = 'fajr',
  ZUHR = 'zuhr',
  ASR = 'asr',
  MAGHRIB = 'maghrib',
  ISHA = 'isha',
  JUMMAH1 = 'jummah1',
  JUMMAH2 = 'jummah2',
  JUMMAH3 = 'jummah3'
}

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

export const PRAYER_TIME_KEYS: Record<Prayer, { start: keyof PrayerTimes["prayer_times"]; iqamah: keyof PrayerTimes["prayer_times"] }> = {
    [Prayer.FAJR] :    { start: "fajr_start",    iqamah: "fajr_iqamah" },
    [Prayer.ZUHR] :    { start: "zuhr_start",    iqamah: "zuhr_iqamah" },
    [Prayer.ASR] :     { start: "asr_start",     iqamah: "asr_iqamah" },
    [Prayer.MAGHRIB] : { start: "maghrib_start", iqamah: "maghrib_iqamah" },
    [Prayer.ISHA] :    { start: "isha_start",    iqamah: "isha_iqamah" },
    [Prayer.JUMMAH1] : { start: "jummah1_start", iqamah: "jummah1_iqamah" },
    [Prayer.JUMMAH2] : { start: "jummah2_start", iqamah: "jummah2_iqamah" },
    [Prayer.JUMMAH3] : { start: "jummah3_start", iqamah: "jummah3_iqamah" },
};
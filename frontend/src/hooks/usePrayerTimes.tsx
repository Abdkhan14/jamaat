import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import type { PrayerTimes } from '../types';

const fetchPrayerTimes = async (): Promise<PrayerTimes[]> => {
  const response = await axios.get<PrayerTimes[]>('http://127.0.0.1:5000/prayer-times');
  return response.data;
};

export const usePrayerTimes = () => {
  return useQuery({
    queryKey: ['prayerTimes'],
    queryFn: fetchPrayerTimes,
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes (formerly cacheTime)
  });
};

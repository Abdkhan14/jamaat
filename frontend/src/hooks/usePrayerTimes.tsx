import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import type { PrayerTimes } from '../types';
import { API_URL } from '../config';

const fetchPrayerTimes = async (): Promise<PrayerTimes[]> => {
  const response = await axios.get<PrayerTimes[]>(`${API_URL}/prayer-times`);
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

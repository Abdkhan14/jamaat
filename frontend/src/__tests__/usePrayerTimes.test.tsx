import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { ReactNode } from 'react'
import { usePrayerTimes } from '../hooks/usePrayerTimes'
import { prayerTimesList } from './fixtures/prayerTimes'

vi.mock('axios')
import axios from 'axios'
const mockedAxios = vi.mocked(axios, true)

function wrapper({ children }: { children: ReactNode }) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>
}

beforeEach(() => { vi.resetAllMocks() })

describe('usePrayerTimes', () => {
  it('returns mosque list on success', async () => {
    mockedAxios.get.mockResolvedValueOnce({ data: prayerTimesList })
    const { result } = renderHook(() => usePrayerTimes(), { wrapper })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toEqual(prayerTimesList)
  })

  it('exposes error when request fails', async () => {
    mockedAxios.get.mockRejectedValueOnce(new Error('Network Error'))
    const { result } = renderHook(() => usePrayerTimes(), { wrapper })
    await waitFor(() => expect(result.current.isError).toBe(true))
  })
})

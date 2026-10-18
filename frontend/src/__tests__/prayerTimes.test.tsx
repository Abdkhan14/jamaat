import { describe, it, expect } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import { renderWithProviders } from './utils/renderWithProviders'
import { PrayerTimes } from '../prayerTimes'
import { mosqueFull, mosqueMaghribNull, prayerTimesList } from './fixtures/prayerTimes'
import {
  FIXED_THURSDAY_NOON,
  FIXED_FRIDAY_NOON,
  BEFORE_FAJR_IQAMAH,
  AFTER_FAJR_GRACE,
} from './fixtures/clock'
import type { UseQueryResult } from '@tanstack/react-query'
import type { PrayerTimes as PrayerTimesType } from '../types'

function makeResult(overrides: Partial<UseQueryResult<PrayerTimesType[], Error>>): UseQueryResult<PrayerTimesType[], Error> {
  return {
    data: undefined,
    isLoading: false,
    isError: false,
    error: null,
    status: 'success',
    isSuccess: true,
    isPending: false,
    isFetching: false,
    isFetched: true,
    isFetchedAfterMount: true,
    isRefetching: false,
    isLoadingError: false,
    isRefetchError: false,
    isPlaceholderData: false,
    isStale: false,
    dataUpdatedAt: 0,
    errorUpdatedAt: 0,
    failureCount: 0,
    failureReason: null,
    fetchStatus: 'idle',
    refetch: async () => ({ data: undefined } as unknown as ReturnType<UseQueryResult<PrayerTimesType[], Error>['refetch']>),
    ...overrides,
  } as UseQueryResult<PrayerTimesType[], Error>
}

describe('PrayerTimes', () => {
  it('shows loading terminal while loading', async () => {
    renderWithProviders(
      <PrayerTimes currentTime={FIXED_THURSDAY_NOON} prayerTimesResult={makeResult({ isLoading: true, status: 'pending', isPending: true })} />
    )
    // LoadingTerminal reveals lines progressively with a 600ms timer
    await waitFor(() => expect(screen.getByText(/GET \/prayer-times/i)).toBeInTheDocument(), { timeout: 3000 })
  })

  it('shows error alert on failure', () => {
    renderWithProviders(
      <PrayerTimes currentTime={FIXED_THURSDAY_NOON} prayerTimesResult={makeResult({ isError: true, status: 'error', error: new Error('fail') })} />
    )
    expect(screen.getByText(/Failed to load/i)).toBeInTheDocument()
  })

  it('shows empty state when data is empty', () => {
    renderWithProviders(
      <PrayerTimes currentTime={FIXED_THURSDAY_NOON} prayerTimesResult={makeResult({ data: [] })} />
    )
    expect(screen.getByText(/No prayer times yet/i)).toBeInTheDocument()
  })

  it('renders a card per mosque', () => {
    renderWithProviders(
      <PrayerTimes currentTime={FIXED_THURSDAY_NOON} prayerTimesResult={makeResult({ data: prayerTimesList })} />
    )
    expect(screen.getByText('Test Mosque')).toBeInTheDocument()
    expect(screen.getByText('Second Mosque')).toBeInTheDocument()
  })

  it('formats 24h times as 12h', () => {
    renderWithProviders(
      <PrayerTimes currentTime={FIXED_THURSDAY_NOON} prayerTimesResult={makeResult({ data: [mosqueFull] })} />
    )
    // fajr_start is "05:00:00" → "5:00 AM"
    expect(screen.getByText('5:00 AM')).toBeInTheDocument()
  })

  it('shows None for missing times and Sunset for missing Maghrib', () => {
    renderWithProviders(
      <PrayerTimes currentTime={FIXED_THURSDAY_NOON} prayerTimesResult={makeResult({ data: [mosqueMaghribNull] })} />
    )
    expect(screen.getByText('Sunset')).toBeInTheDocument()
  })

  it('marks prayer Available before iqamah plus grace', () => {
    renderWithProviders(
      <PrayerTimes currentTime={BEFORE_FAJR_IQAMAH} prayerTimesResult={makeResult({ data: [mosqueFull] })} />
    )
    const availableItems = screen.getAllByText('Available')
    expect(availableItems.length).toBeGreaterThan(0)
  })

  it('marks fajr Finished after the 3-minute grace', () => {
    renderWithProviders(
      <PrayerTimes currentTime={AFTER_FAJR_GRACE} prayerTimesResult={makeResult({ data: [mosqueFull] })} />
    )
    const finishedItems = screen.getAllByText('Finished')
    expect(finishedItems.length).toBeGreaterThan(0)
  })

  it('shows Jummah as None on non-Fridays', () => {
    renderWithProviders(
      <PrayerTimes currentTime={FIXED_THURSDAY_NOON} prayerTimesResult={makeResult({ data: [mosqueFull] })} />
    )
    const noneItems = screen.getAllByText('None')
    expect(noneItems.length).toBeGreaterThan(0)
  })

  it('computes Jummah status on Fridays', () => {
    renderWithProviders(
      <PrayerTimes currentTime={FIXED_FRIDAY_NOON} prayerTimesResult={makeResult({ data: [mosqueFull] })} />
    )
    // On a Friday after Jummah1 iqamah (13:30) at noon (12:00 ET), jummah1 is Available
    expect(screen.getAllByText('Available').length).toBeGreaterThan(0)
  })

  it('shows Updated At with ET', () => {
    renderWithProviders(
      <PrayerTimes currentTime={FIXED_THURSDAY_NOON} prayerTimesResult={makeResult({ data: [mosqueFull] })} />
    )
    expect(screen.getByText(/ET/)).toBeInTheDocument()
  })
})

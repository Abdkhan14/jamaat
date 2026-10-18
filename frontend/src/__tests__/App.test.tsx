import { describe, it, expect, vi } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import { renderWithProviders } from './utils/renderWithProviders'
import { prayerTimesList } from './fixtures/prayerTimes'

vi.mock('@vercel/analytics/react', () => ({ Analytics: () => null }))
vi.mock('axios')
import axios from 'axios'
const mockedAxios = vi.mocked(axios, true)

describe('App', () => {
  it('renders the mosque list after fetch', async () => {
    mockedAxios.get.mockResolvedValueOnce({ data: prayerTimesList })
    const { default: App } = await import('../App')
    renderWithProviders(<App />)
    await waitFor(() => expect(screen.getByText('Test Mosque')).toBeInTheDocument())
  })
})

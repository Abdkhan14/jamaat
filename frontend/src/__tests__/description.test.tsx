import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { renderWithProviders } from './utils/renderWithProviders'
import { Description } from '../components/description'

vi.mock('axios')
import axios from 'axios'
const mockedAxios = vi.mocked(axios, true)

beforeEach(() => { vi.resetAllMocks() })

async function openModal() {
  await userEvent.click(screen.getByText('Submit a request'))
}

describe('Description', () => {
  it('posts name and info, shows success toast, and closes modal', async () => {
    mockedAxios.post.mockResolvedValueOnce({ data: { ok: true } })

    renderWithProviders(<Description />)
    await openModal()

    await userEvent.type(screen.getByLabelText(/Mosque Name/i), 'Test Mosque')
    await userEvent.type(screen.getByLabelText(/Additional Information/i), 'Some details')
    await userEvent.click(screen.getByText('Submit Request'))

    await waitFor(() => expect(screen.getByText(/Request submitted successfully/i)).toBeInTheDocument())
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('shows error toast when submission fails', async () => {
    mockedAxios.post.mockRejectedValueOnce(new Error('Server error'))

    renderWithProviders(<Description />)
    await openModal()

    await userEvent.type(screen.getByLabelText(/Mosque Name/i), 'Test Mosque')
    await userEvent.click(screen.getByText('Submit Request'))

    await waitFor(() => expect(screen.getByText(/Submission failed/i)).toBeInTheDocument())
  })

  it('disables buttons while submitting', async () => {
    let resolve!: () => void
    mockedAxios.post.mockReturnValueOnce(new Promise((r) => { resolve = () => r({ data: { ok: true } }) }))

    renderWithProviders(<Description />)
    await openModal()

    await userEvent.type(screen.getByLabelText(/Mosque Name/i), 'Test Mosque')
    await userEvent.click(screen.getByText('Submit Request'))

    expect(screen.getByText(/Cancel/i).closest('button')).toBeDisabled()

    resolve()
    await waitFor(() => expect(screen.getByText(/Request submitted successfully/i)).toBeInTheDocument())
  })
})

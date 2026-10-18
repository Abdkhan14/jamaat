import { describe, it, expect, vi, afterEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useCurrentTime } from '../hooks/useCurrentTime'

afterEach(() => vi.useRealTimers())

describe('useCurrentTime', () => {
  it('updates after the interval', () => {
    vi.useFakeTimers()
    const { result } = renderHook(() => useCurrentTime(60_000))
    const initial = result.current

    act(() => { vi.advanceTimersByTime(60_000) })

    expect(result.current.getTime()).toBeGreaterThan(initial.getTime())
  })
})

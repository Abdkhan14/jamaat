import { http, HttpResponse } from 'msw'
import { prayerTimesList } from '../fixtures/prayerTimes'

const API_URL = 'http://localhost:5000'

export const handlers = [
  http.get(`${API_URL}/prayer-times`, () => HttpResponse.json(prayerTimesList)),

  http.post(`${API_URL}/mosque-request`, () =>
    HttpResponse.json({ ok: true }, { status: 201 })
  ),
]

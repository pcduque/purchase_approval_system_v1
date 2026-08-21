import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import RequestsPage from './RequestsPage'
import { listRequests } from '../api/api'

vi.mock('../api/api', () => ({
  listRequests: vi.fn(),
}))

function renderPage() {
  render(
    <MemoryRouter>
      <RequestsPage />
    </MemoryRouter>,
  )
}

describe('RequestsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('muestra solicitudes', async () => {
    listRequests.mockResolvedValue([
      {
        request_id: 'request-1',
        title: 'Compra de computador',
        requester_name: 'Pablo Duque',
        amount: 5000000,
        status: 'PENDING',
        created_at: '2026-08-20T10:00:00+00:00',
      },
    ])

    renderPage()

    expect(await screen.findByText('Compra de computador')).toBeInTheDocument()
    expect(screen.getByText('Pablo Duque')).toBeInTheDocument()
    expect(screen.getByText('PENDING')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Ver detalle' })).toHaveAttribute(
      'href',
      '/requests/request-1',
    )
  })

  it('muestra estado vacio', async () => {
    listRequests.mockResolvedValue([])

    renderPage()

    await waitFor(() => {
      expect(screen.getByText('No hay solicitudes creadas.')).toBeInTheDocument()
    })
  })
})

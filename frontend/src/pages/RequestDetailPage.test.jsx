import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import RequestDetailPage from './RequestDetailPage'
import { getRequest } from '../api/api'

vi.mock('../api/api', () => ({
  getEvidenceUrl: (requestId) => `http://127.0.0.1:8000/api/requests/${requestId}/evidence.pdf`,
  getRequest: vi.fn(),
}))

function renderPage(requestId = 'request-1') {
  render(
    <MemoryRouter initialEntries={[`/requests/${requestId}`]}>
      <Routes>
        <Route path="/requests/:requestId" element={<RequestDetailPage />} />
      </Routes>
    </MemoryRouter>,
  )
}

function requestDetail(status = 'PENDING') {
  return {
    request_id: 'request-1',
    title: 'Compra de computador',
    description: 'Computador para desarrollo',
    amount: 5000000,
    requester_name: 'Pablo Duque',
    status,
    created_at: '2026-08-20T10:00:00+00:00',
    approvers: [
      {
        name: 'Juan Perez',
        email: 'juan@example.com',
        status: 'SIGNED',
        signed_at: '2026-08-20T10:10:00+00:00',
      },
      { name: 'Maria Lopez', email: 'maria@example.com', status: 'PENDING' },
      { name: 'Carlos Ruiz', email: 'carlos@example.com', status: 'PENDING' },
    ],
  }
}

describe('RequestDetailPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('muestra detalle', async () => {
    getRequest.mockResolvedValue(requestDetail())

    renderPage()

    expect(await screen.findByText('Compra de computador')).toBeInTheDocument()
    expect(screen.getByText('Computador para desarrollo')).toBeInTheDocument()
    expect(screen.getByText('Pablo Duque')).toBeInTheDocument()
  })

  it('muestra approvals', async () => {
    getRequest.mockResolvedValue(requestDetail())

    renderPage()

    expect(await screen.findByText('Juan Perez')).toBeInTheDocument()
    expect(screen.getByText('juan@example.com')).toBeInTheDocument()
    expect(screen.getByText('Firmado: 2026-08-20T10:10:00+00:00')).toBeInTheDocument()
  })

  it('muestra boton PDF solo cuando status es COMPLETED', async () => {
    getRequest.mockResolvedValue(requestDetail('COMPLETED'))

    renderPage()

    expect(await screen.findByRole('link', { name: 'Descargar evidencia PDF' })).toHaveAttribute(
      'href',
      'http://127.0.0.1:8000/api/requests/request-1/evidence.pdf',
    )
  })

  it('oculta boton PDF cuando status no es COMPLETED', async () => {
    getRequest.mockResolvedValue(requestDetail('PENDING'))

    renderPage()

    expect(await screen.findByText('Compra de computador')).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: 'Descargar evidencia PDF' })).not.toBeInTheDocument()
  })
})

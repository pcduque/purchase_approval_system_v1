import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import CreateRequestPage from './CreateRequestPage'
import { createRequest } from '../api/api'

const navigate = vi.fn()

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => navigate,
  }
})

vi.mock('../api/api', () => ({
  createRequest: vi.fn(),
}))

function renderPage() {
  render(
    <MemoryRouter>
      <CreateRequestPage />
    </MemoryRouter>,
  )
}

function fillValidForm() {
  fireEvent.change(screen.getByLabelText('Titulo'), {
    target: { value: 'Compra de computadores' },
  })
  fireEvent.change(screen.getByLabelText('Descripcion'), {
    target: { value: 'Compra de equipos para desarrollo' },
  })
  fireEvent.change(screen.getByLabelText('Monto'), {
    target: { value: '8500000' },
  })
  fireEvent.change(screen.getByLabelText('Solicitante'), {
    target: { value: 'Pablo Duque' },
  })

  const nameInputs = screen.getAllByLabelText('Nombre')
  const emailInputs = screen.getAllByLabelText('Email')

  fireEvent.change(nameInputs[0], { target: { value: 'Juan Perez' } })
  fireEvent.change(emailInputs[0], { target: { value: 'juan@example.com' } })
  fireEvent.change(nameInputs[1], { target: { value: 'Maria Lopez' } })
  fireEvent.change(emailInputs[1], { target: { value: 'maria@example.com' } })
  fireEvent.change(nameInputs[2], { target: { value: 'Carlos Ruiz' } })
  fireEvent.change(emailInputs[2], { target: { value: 'carlos@example.com' } })
}

describe('CreateRequestPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('envia los datos correctos', async () => {
    createRequest.mockResolvedValue({ request_id: 'request-1' })
    renderPage()

    fillValidForm()
    fireEvent.click(screen.getByRole('button', { name: 'Crear solicitud' }))

    await waitFor(() => {
      expect(createRequest).toHaveBeenCalledWith({
        title: 'Compra de computadores',
        description: 'Compra de equipos para desarrollo',
        amount: 8500000,
        requester_name: 'Pablo Duque',
        approvers: [
          { name: 'Juan Perez', email: 'juan@example.com' },
          { name: 'Maria Lopez', email: 'maria@example.com' },
          { name: 'Carlos Ruiz', email: 'carlos@example.com' },
        ],
      })
    })
    expect(navigate).toHaveBeenCalledWith('/requests/request-1')
  })

  it('exige amount mayor que 0', async () => {
    renderPage()

    fillValidForm()
    fireEvent.change(screen.getByLabelText('Monto'), {
      target: { value: '0' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Crear solicitud' }))

    expect(await screen.findByText('El monto debe ser mayor que 0.')).toBeInTheDocument()
    expect(createRequest).not.toHaveBeenCalled()
  })

  it('contiene exactamente 3 aprobadores', () => {
    renderPage()

    expect(screen.getByText('Aprobador 1')).toBeInTheDocument()
    expect(screen.getByText('Aprobador 2')).toBeInTheDocument()
    expect(screen.getByText('Aprobador 3')).toBeInTheDocument()
    expect(screen.getAllByLabelText('Nombre')).toHaveLength(3)
    expect(screen.getAllByLabelText('Email')).toHaveLength(3)
  })
})

import { StrictMode } from 'react'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import ApprovalPage from './ApprovalPage'
import {
  approveApproval,
  getApprovalDetail,
  rejectApproval,
  startApproval,
  validateApprovalOtp,
} from '../api/api'

vi.mock('../api/api', () => ({
  approveApproval: vi.fn(),
  getApprovalDetail: vi.fn(),
  rejectApproval: vi.fn(),
  startApproval: vi.fn(),
  validateApprovalOtp: vi.fn(),
}))

const validPath = '/approve?solicitud_id=request-1&approver_token=token-1'
const approvalPayload = {
  request_id: 'request-1',
  approver_token: 'token-1',
}

function approvalDetail(status = 'PENDING') {
  return {
    request_id: 'request-1',
    title: 'Compra de computador',
    description: 'Computador para desarrollo',
    amount: 5000000,
    requester_name: 'Pablo Duque',
    status,
    created_at: '2026-08-20T10:00:00+00:00',
  }
}

function renderPage(path = validPath, withStrictMode = false) {
  const page = (
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/approve" element={<ApprovalPage />} />
      </Routes>
    </MemoryRouter>
  )

  render(withStrictMode ? <StrictMode>{page}</StrictMode> : page)
}

async function reachOtpForm() {
  renderPage()
  expect(await screen.findByText('Ingresa tu codigo OTP')).toBeInTheDocument()
}

async function reachDetail() {
  await reachOtpForm()
  fireEvent.change(screen.getByLabelText('Codigo OTP'), {
    target: { value: '123456' },
  })
  fireEvent.click(screen.getByRole('button', { name: 'Validar codigo' }))
  expect(await screen.findByText('Compra de computador')).toBeInTheDocument()
}

describe('ApprovalPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    startApproval.mockResolvedValue({ message: 'OTP generated', expires_in_seconds: 180 })
    validateApprovalOtp.mockResolvedValue({ message: 'OTP validated', ...approvalPayload })
    getApprovalDetail.mockResolvedValue(approvalDetail())
    approveApproval.mockResolvedValue({ message: 'Approved', ...approvalPayload, status: 'SIGNED' })
    rejectApproval.mockResolvedValue({ message: 'Rejected', ...approvalPayload, status: 'REJECTED' })
  })

  it('muestra error cuando falta solicitud_id', async () => {
    renderPage('/approve?approver_token=token-1')

    expect(await screen.findByText('Enlace de aprobacion invalido.')).toBeInTheDocument()
    expect(startApproval).not.toHaveBeenCalled()
  })

  it('muestra error cuando falta approver_token', async () => {
    renderPage('/approve?solicitud_id=request-1')

    expect(await screen.findByText('Enlace de aprobacion invalido.')).toBeInTheDocument()
    expect(startApproval).not.toHaveBeenCalled()
  })

  it('al abrir link valido llama start', async () => {
    renderPage()

    await waitFor(() => {
      expect(startApproval).toHaveBeenCalledWith(approvalPayload)
    })
  })

  it('ejecuta start una sola vez en StrictMode', async () => {
    renderPage(validPath, true)

    await waitFor(() => {
      expect(startApproval).toHaveBeenCalledTimes(1)
    })
  })

  it('start exitoso muestra formulario OTP', async () => {
    await reachOtpForm()

    expect(screen.getByLabelText('Codigo OTP')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Validar codigo' })).toBeInTheDocument()
  })

  it('OTP incorrecto muestra error', async () => {
    validateApprovalOtp.mockRejectedValue(new Error('Invalid or expired OTP'))
    await reachOtpForm()

    fireEvent.change(screen.getByLabelText('Codigo OTP'), {
      target: { value: '000000' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Validar codigo' }))

    expect(await screen.findByText('OTP incorrecto o expirado.')).toBeInTheDocument()
  })

  it('OTP correcto consulta detail', async () => {
    await reachOtpForm()

    fireEvent.change(screen.getByLabelText('Codigo OTP'), {
      target: { value: '123456' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Validar codigo' }))

    await waitFor(() => {
      expect(getApprovalDetail).toHaveBeenCalledWith('request-1', 'token-1')
    })
  })

  it('muestra detail correctamente', async () => {
    await reachDetail()

    expect(screen.getByText('Computador para desarrollo')).toBeInTheDocument()
    expect(screen.getByText('5.000.000')).toBeInTheDocument()
    expect(screen.getByText('Pablo Duque')).toBeInTheDocument()
  })

  it('boton Aprobar llama endpoint correcto', async () => {
    await reachDetail()

    fireEvent.click(screen.getByRole('button', { name: 'Aprobar' }))

    await waitFor(() => {
      expect(approveApproval).toHaveBeenCalledWith(approvalPayload)
    })
  })

  it('approve exitoso muestra SIGNED', async () => {
    await reachDetail()

    fireEvent.click(screen.getByRole('button', { name: 'Aprobar' }))

    expect(await screen.findByText('Aprobacion registrada correctamente.')).toBeInTheDocument()
    expect(screen.getByText('Estado: SIGNED')).toBeInTheDocument()
  })

  it('boton Rechazar llama endpoint correcto', async () => {
    await reachDetail()

    fireEvent.click(screen.getByRole('button', { name: 'Rechazar' }))

    await waitFor(() => {
      expect(rejectApproval).toHaveBeenCalledWith(approvalPayload)
    })
  })

  it('reject exitoso muestra REJECTED', async () => {
    await reachDetail()

    fireEvent.click(screen.getByRole('button', { name: 'Rechazar' }))

    expect(await screen.findByText('Solicitud rechazada.')).toBeInTheDocument()
    expect(screen.getByText('Estado: REJECTED')).toBeInTheDocument()
  })

  it('despues de decision los botones desaparecen', async () => {
    await reachDetail()

    fireEvent.click(screen.getByRole('button', { name: 'Aprobar' }))
    expect(await screen.findByText('Estado: SIGNED')).toBeInTheDocument()

    expect(screen.queryByRole('button', { name: 'Aprobar' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Rechazar' })).not.toBeInTheDocument()
  })

  it('muestra error cuando la request ya fue rechazada', async () => {
    startApproval.mockRejectedValue(new Error('Request is already rejected'))

    renderPage()

    expect(
      await screen.findByText('Esta solicitud ya fue rechazada y no admite mas decisiones.'),
    ).toBeInTheDocument()
  })
})

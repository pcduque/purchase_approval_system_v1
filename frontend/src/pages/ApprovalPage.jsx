import { useEffect, useRef, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import {
  approveApproval,
  getApprovalDetail,
  rejectApproval,
  startApproval,
  validateApprovalOtp,
} from '../api/api'

const STATES = {
  INITIALIZING: 'INITIALIZING',
  WAITING_OTP: 'WAITING_OTP',
  LOADING_DETAIL: 'LOADING_DETAIL',
  READY_FOR_DECISION: 'READY_FOR_DECISION',
  SIGNED: 'SIGNED',
  REJECTED: 'REJECTED',
  ERROR: 'ERROR',
}

function getFriendlyError(error) {
  const message = error instanceof Error ? error.message : String(error)

  if (message.includes('Request is already rejected')) {
    return 'Esta solicitud ya fue rechazada y no admite mas decisiones.'
  }

  if (message.includes('Approval is not pending')) {
    return 'Esta aprobacion ya fue procesada.'
  }

  if (message.includes('Approval not found')) {
    return 'Aprobacion inexistente.'
  }

  if (message.includes('OTP flow has not started')) {
    return 'El flujo OTP no ha sido iniciado.'
  }

  if (message.includes('Invalid or expired OTP')) {
    return 'OTP incorrecto o expirado.'
  }

  if (message.includes('OTP has not been validated')) {
    return 'Primero debes validar el OTP.'
  }

  return message || 'No se pudo completar la solicitud.'
}

function Detail({ detail }) {
  return (
    <>
      <div className="detail-header">
        <div>
          <h2>{detail.title}</h2>
          <p>{detail.description}</p>
        </div>
        <span className={`status ${detail.status?.toLowerCase()}`}>{detail.status}</span>
      </div>
      <dl className="detail-grid">
        <div>
          <dt>Monto</dt>
          <dd>{Number(detail.amount).toLocaleString('es-CO')}</dd>
        </div>
        <div>
          <dt>Solicitante</dt>
          <dd>{detail.requester_name}</dd>
        </div>
        <div>
          <dt>Fecha de creacion</dt>
          <dd>{detail.created_at}</dd>
        </div>
        {detail.approver_name && (
          <div>
            <dt>Aprobador</dt>
            <dd>{detail.approver_name}</dd>
          </div>
        )}
        {detail.approver_email && (
          <div>
            <dt>Email aprobador</dt>
            <dd>{detail.approver_email}</dd>
          </div>
        )}
      </dl>
    </>
  )
}

function ApprovalPage() {
  const [searchParams] = useSearchParams()
  const requestId = searchParams.get('solicitud_id')
  const approverToken = searchParams.get('approver_token')
  const hasValidLink = Boolean(requestId && approverToken)
  const hasStartedRef = useRef(false)
  const [pageState, setPageState] = useState(hasValidLink ? STATES.INITIALIZING : STATES.ERROR)
  const [errorMessage, setErrorMessage] = useState(
    hasValidLink ? '' : 'Enlace de aprobacion invalido.',
  )
  const [otpError, setOtpError] = useState('')
  const [otp, setOtp] = useState('')
  const [detail, setDetail] = useState(null)
  const [isSubmittingDecision, setIsSubmittingDecision] = useState(false)

  useEffect(() => {
    if (!hasValidLink) {
      return
    }

    if (hasStartedRef.current) {
      return
    }

    hasStartedRef.current = true
    startApproval({
      request_id: requestId,
      approver_token: approverToken,
    })
      .then(() => {
        setPageState(STATES.WAITING_OTP)
      })
      .catch((error) => {
        setErrorMessage(getFriendlyError(error))
        setPageState(STATES.ERROR)
      })
  }, [hasValidLink, requestId, approverToken])

  async function handleValidateOtp(event) {
    event.preventDefault()
    setOtpError('')
    setErrorMessage('')

    try {
      setPageState(STATES.LOADING_DETAIL)
      await validateApprovalOtp({
        request_id: requestId,
        approver_token: approverToken,
        otp,
      })
      const approvalDetail = await getApprovalDetail(requestId, approverToken)
      setDetail(approvalDetail)
      setPageState(STATES.READY_FOR_DECISION)
    } catch (error) {
      const message = getFriendlyError(error)
      if (message.includes('OTP')) {
        setOtpError(message)
        setPageState(STATES.WAITING_OTP)
        return
      }

      setErrorMessage(message)
      setPageState(STATES.ERROR)
    }
  }

  async function handleDecision(decision) {
    setErrorMessage('')
    setIsSubmittingDecision(true)

    try {
      const action = decision === STATES.SIGNED ? approveApproval : rejectApproval
      await action({
        request_id: requestId,
        approver_token: approverToken,
      })
      setPageState(decision)
    } catch (error) {
      setErrorMessage(getFriendlyError(error))
      setPageState(STATES.ERROR)
    } finally {
      setIsSubmittingDecision(false)
    }
  }

  return (
    <section className="page-section approval-page">
      <Link className="back-link" to="/">
        Volver a solicitudes
      </Link>

      <div className="section-heading">
        <div>
          <p className="eyebrow">Solicitud de aprobacion</p>
          <h2>Flujo del aprobador</h2>
        </div>
      </div>

      {pageState === STATES.INITIALIZING && (
        <p className="state-message">Preparando aprobacion...</p>
      )}

      {pageState === STATES.WAITING_OTP && (
        <form className="form approval-card" onSubmit={handleValidateOtp}>
          <div>
            <h3>Ingresa tu codigo OTP</h3>
            <p>Ingresa el codigo OTP enviado a tu correo.</p>
            <p>El codigo es valido durante 3 minutos.</p>
          </div>
          <label>
            Codigo OTP
            <input
              autoComplete="one-time-code"
              inputMode="numeric"
              onChange={(event) => setOtp(event.target.value)}
              value={otp}
            />
          </label>
          {otpError && <p className="error-message">{otpError}</p>}
          <button className="button primary" disabled={!otp.trim()} type="submit">
            Validar codigo
          </button>
        </form>
      )}

      {pageState === STATES.LOADING_DETAIL && (
        <p className="state-message">Validando codigo y cargando detalle...</p>
      )}

      {pageState === STATES.READY_FOR_DECISION && detail && (
        <section className="approval-decision">
          <Detail detail={detail} />
          <div className="decision-actions">
            <button
              className="button primary"
              disabled={isSubmittingDecision}
              onClick={() => handleDecision(STATES.SIGNED)}
              type="button"
            >
              Aprobar
            </button>
            <button
              className="button danger"
              disabled={isSubmittingDecision}
              onClick={() => handleDecision(STATES.REJECTED)}
              type="button"
            >
              Rechazar
            </button>
          </div>
        </section>
      )}

      {pageState === STATES.SIGNED && (
        <div className="success-message">
          <p>Aprobacion registrada correctamente.</p>
          <p>Estado: SIGNED</p>
        </div>
      )}

      {pageState === STATES.REJECTED && (
        <div className="error-message">
          <p>Solicitud rechazada.</p>
          <p>Estado: REJECTED</p>
        </div>
      )}

      {pageState === STATES.ERROR && <p className="error-message">{errorMessage}</p>}
    </section>
  )
}

export default ApprovalPage

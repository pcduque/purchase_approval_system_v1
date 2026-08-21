import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { getEvidenceUrl, getRequest } from '../api/api'

function RequestDetailPage() {
  const { requestId } = useParams()
  const [request, setRequest] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let isMounted = true

    async function loadRequest() {
      try {
        const data = await getRequest(requestId)
        if (isMounted) {
          setRequest(data)
        }
      } catch (err) {
        if (isMounted) {
          setError(err.message)
        }
      } finally {
        if (isMounted) {
          setLoading(false)
        }
      }
    }

    loadRequest()

    return () => {
      isMounted = false
    }
  }, [requestId])

  if (loading) {
    return <p className="state-message">Cargando detalle...</p>
  }

  if (error) {
    return <p className="error-message">{error}</p>
  }

  if (!request) {
    return <p className="state-message">Solicitud no encontrada.</p>
  }

  return (
    <section className="page-section">
      <Link className="back-link" to="/">
        Volver a solicitudes
      </Link>

      <div className="detail-header">
        <div>
          <h2>{request.title}</h2>
          <p>{request.description}</p>
        </div>
        <span className={`status ${request.status.toLowerCase()}`}>
          {request.status}
        </span>
      </div>

      <dl className="detail-grid">
        <div>
          <dt>Monto</dt>
          <dd>{Number(request.amount).toLocaleString()}</dd>
        </div>
        <div>
          <dt>Solicitante</dt>
          <dd>{request.requester_name}</dd>
        </div>
        <div>
          <dt>Fecha de creacion</dt>
          <dd>{request.created_at}</dd>
        </div>
      </dl>

      {request.status === 'COMPLETED' && (
        <a className="button primary" href={getEvidenceUrl(request.request_id)}>
          Descargar evidencia PDF
        </a>
      )}

      <section className="approvals-section">
        <h3>Aprobadores</h3>
        <div className="approvals-list">
          {request.approvers.map((approver) => (
            <article className="approval-card" key={approver.email}>
              <div>
                <h4>{approver.name}</h4>
                <p>{approver.email}</p>
              </div>
              <span className={`status ${approver.status.toLowerCase()}`}>
                {approver.status}
              </span>
              {approver.signed_at && <p>Firmado: {approver.signed_at}</p>}
              {approver.rejected_at && <p>Rechazado: {approver.rejected_at}</p>}
            </article>
          ))}
        </div>
      </section>
    </section>
  )
}

export default RequestDetailPage

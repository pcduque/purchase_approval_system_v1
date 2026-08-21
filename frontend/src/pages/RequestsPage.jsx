import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { listRequests } from '../api/api'

function RequestsPage() {
  const [requests, setRequests] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let isMounted = true

    async function loadRequests() {
      try {
        const data = await listRequests()
        if (isMounted) {
          setRequests(data)
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

    loadRequests()

    return () => {
      isMounted = false
    }
  }, [])

  if (loading) {
    return <p className="state-message">Cargando solicitudes...</p>
  }

  if (error) {
    return <p className="error-message">{error}</p>
  }

  return (
    <section className="page-section">
      <div className="section-heading">
        <h2>Solicitudes</h2>
        <Link className="button primary" to="/requests/new">
          Nueva solicitud
        </Link>
      </div>

      {requests.length === 0 ? (
        <p className="state-message">No hay solicitudes creadas.</p>
      ) : (
        <div className="request-list">
          {requests.map((request) => (
            <article className="request-card" key={request.request_id}>
              <div>
                <h3>{request.title}</h3>
                <p>{request.requester_name}</p>
              </div>
              <div className="request-meta">
                <span>{Number(request.amount).toLocaleString()}</span>
                <span className={`status ${request.status.toLowerCase()}`}>
                  {request.status}
                </span>
                <span>{request.created_at}</span>
              </div>
              <Link className="button secondary" to={`/requests/${request.request_id}`}>
                Ver detalle
              </Link>
            </article>
          ))}
        </div>
      )}
    </section>
  )
}

export default RequestsPage

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { createRequest } from '../api/api'

const initialApprovers = [
  { name: '', email: '' },
  { name: '', email: '' },
  { name: '', email: '' },
]

function CreateRequestPage() {
  const navigate = useNavigate()
  const [form, setForm] = useState({
    title: '',
    description: '',
    amount: '',
    requester_name: '',
    approvers: initialApprovers,
  })
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [submitting, setSubmitting] = useState(false)

  function updateField(event) {
    const { name, value } = event.target
    setForm((current) => ({ ...current, [name]: value }))
  }

  function updateApprover(index, field, value) {
    setForm((current) => ({
      ...current,
      approvers: current.approvers.map((approver, currentIndex) =>
        currentIndex === index ? { ...approver, [field]: value } : approver,
      ),
    }))
  }

  function validateForm() {
    if (!form.title.trim() || !form.description.trim() || !form.requester_name.trim()) {
      return 'Completa los campos obligatorios.'
    }
    if (Number(form.amount) <= 0) {
      return 'El monto debe ser mayor que 0.'
    }
    if (form.approvers.length !== 3) {
      return 'Deben existir exactamente 3 aprobadores.'
    }
    if (form.approvers.some((approver) => !approver.name.trim() || !approver.email.trim())) {
      return 'Completa los datos de los 3 aprobadores.'
    }
    return ''
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')
    setSuccess('')

    const validationError = validateForm()
    if (validationError) {
      setError(validationError)
      return
    }

    setSubmitting(true)
    try {
      const payload = {
        ...form,
        amount: Number(form.amount),
        approvers: form.approvers.map((approver) => ({
          name: approver.name,
          email: approver.email,
        })),
      }
      const createdRequest = await createRequest(payload)
      setSuccess('Solicitud creada correctamente')
      navigate(`/requests/${createdRequest.request_id}`)
    } catch (err) {
      setError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <section className="page-section">
      <div className="section-heading">
        <h2>Nueva solicitud</h2>
        <p>Registra la compra y los tres aprobadores requeridos.</p>
      </div>

      <form className="form" onSubmit={handleSubmit}>
        <label>
          Titulo
          <input name="title" value={form.title} onChange={updateField} />
        </label>
        <label>
          Descripcion
          <textarea name="description" value={form.description} onChange={updateField} />
        </label>
        <label>
          Monto
          <input name="amount" type="number" value={form.amount} onChange={updateField} />
        </label>
        <label>
          Solicitante
          <input
            name="requester_name"
            value={form.requester_name}
            onChange={updateField}
          />
        </label>

        <div className="approvers-grid">
          {form.approvers.map((approver, index) => (
            <fieldset key={index}>
              <legend>Aprobador {index + 1}</legend>
              <label>
                Nombre
                <input
                  value={approver.name}
                  onChange={(event) => updateApprover(index, 'name', event.target.value)}
                />
              </label>
              <label>
                Email
                <input
                  type="email"
                  value={approver.email}
                  onChange={(event) => updateApprover(index, 'email', event.target.value)}
                />
              </label>
            </fieldset>
          ))}
        </div>

        {error && <p className="error-message">{error}</p>}
        {success && <p className="success-message">{success}</p>}

        <button className="button primary" type="submit" disabled={submitting}>
          {submitting ? 'Creando...' : 'Crear solicitud'}
        </button>
      </form>
    </section>
  )
}

export default CreateRequestPage

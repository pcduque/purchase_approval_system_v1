import { describe, expect, it } from 'vitest'
import { getEvidenceUrl } from './api'

describe('api client', () => {
  it('construye la URL de evidencia con la base configurada', () => {
    expect(getEvidenceUrl('request-1')).toBe(
      'https://i2ecy353md.execute-api.us-east-2.amazonaws.com/default/api/requests/request-1/evidence.pdf',
    )
  })
})

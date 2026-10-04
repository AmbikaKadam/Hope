// API service layer - the ONLY file that knows how to talk to the FastAPI backend.
// Components call these functions instead of using fetch() directly.

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export class ApiError extends Error {
  constructor(message, status = 0, fieldErrors = {}) {
    super(message)
    this.status = status // HTTP status (0 = server could not be reached)
    this.fieldErrors = fieldErrors // e.g. { phone: 'Enter a valid 10-digit mobile number' }
  }
}

// The backend uses snake_case (Python style); the React prototype uses camelCase.
const toCamel = (key) => key.replace(/_([a-z])/g, (_, letter) => letter.toUpperCase())
const toSnake = (key) => key.replace(/[A-Z]/g, (letter) => `_${letter.toLowerCase()}`)

// ---------------------------------------------------------------- HTTP helper
async function request(path, options = {}) {
  let response
  try {
    response = await fetch(`${API_BASE}${path}`, { headers: { 'Content-Type': 'application/json' }, ...options })
  } catch {
    throw new ApiError(`Cannot reach the server. Please make sure the backend is running at ${API_BASE}.`)
  }
  const data = await response.json().catch(() => null)
  if (!response.ok) {
    const fieldErrors = {}
    for (const item of data?.errors || []) fieldErrors[toCamel(item.field)] = item.message
    const message = typeof data?.detail === 'string' ? data.detail : `Something went wrong (error ${response.status}).`
    throw new ApiError(message, response.status, fieldErrors)
  }
  return data
}

// ---------------------------------------------------------------- data conversion
// Fields the beneficiary form can send to the backend.
const FIELDS = ['name', 'age', 'gender', 'phone', 'email', 'dob', 'address', 'city', 'state', 'emergency', 'govIdType', 'govIdNumber', 'marital', 'occupation', 'familyMembers', 'income', 'education', 'primaryNeed', 'secondaryNeeds', 'needDescription', 'urgency', 'program', 'registrationDate', 'assignedStaff', 'assessment', 'status']
const NUMBER_FIELDS = ['age', 'familyMembers', 'income']
const DEFAULTS = { urgency: 'Medium', status: 'Active' }

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

/** '2026-09-24' or an ISO timestamp -> '24 Sep 2026' (the format the prototype displays). */
export function fmtDate(value) {
  if (!value) return ''
  const date = value.length === 10 ? new Date(`${value}T00:00:00`) : new Date(value)
  if (Number.isNaN(date.getTime())) return ''
  return `${String(date.getDate()).padStart(2, '0')} ${MONTHS[date.getMonth()]} ${date.getFullYear()}`
}

/** ISO timestamp -> '10 min ago', 'Yesterday', ... */
export function timeAgo(value) {
  const seconds = Math.max(0, (Date.now() - new Date(value).getTime()) / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)
  if (minutes < 1) return 'Just now'
  if (minutes < 60) return `${minutes} min ago`
  if (hours < 24) return `${hours} hour${hours > 1 ? 's' : ''} ago`
  if (days < 2) return 'Yesterday'
  if (days < 30) return `${days} days ago`
  return fmtDate(value)
}

/** Backend record (snake_case) -> object the existing React components already understand. */
export function fromApi(record) {
  const person = {}
  for (const [key, value] of Object.entries(record)) person[toCamel(key)] = value ?? '' // null -> '' like the prototype
  return {
    ...person,
    dobISO: person.dob, // raw dates are kept for the edit form's <input type="date">
    registrationDateISO: person.registrationDate,
    dob: person.dob ? fmtDate(person.dob) : '',
    registrationDate: fmtDate(person.registrationDate),
    lastActivity: fmtDate(person.updatedAt),
    // These belong to other modules and are NOT stored in the database yet,
    // so they start empty and only live in the browser for the current session.
    services: [],
    followUps: [],
    documents: [],
    progress: ['Beneficiary registered'],
  }
}

/** A record from fromApi() -> plain form values (with ISO dates), ready for toPayload(). */
export const recordToFormValues = (person) => ({ ...person, dob: person.dobISO, registrationDate: person.registrationDateISO })

/** Form values (camelCase strings) -> JSON body for the backend (snake_case, numbers, nulls). */
export function toPayload(values) {
  const payload = {}
  for (const key of FIELDS) {
    let value = values[key]
    if (typeof value === 'string') value = value.trim()
    if (value === '' || value === undefined || value === null) value = DEFAULTS[key] ?? null
    if (value !== null && NUMBER_FIELDS.includes(key)) value = Number(value)
    payload[toSnake(key)] = value
  }
  return payload
}

// ---------------------------------------------------------------- validation (mirrors the backend rules)
const cleanPhone = (value) => {
  const digits = value.replace(/[\s-]/g, '')
  return digits.startsWith('+91') ? digits.slice(3) : digits
}
const isPhone = (value) => /^[6-9]\d{9}$/.test(cleanPhone(value))
const isEmail = (value) => /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(value)

/** Returns an object like { name: 'Full name is required' }. Empty object = form is valid. */
export function validateBeneficiary(values) {
  const errors = {}
  const text = (key) => String(values[key] ?? '').trim()
  const today = new Date().toISOString().slice(0, 10)

  if (!text('name')) errors.name = 'Full name is required'
  else if (text('name').length < 2) errors.name = 'Name must be at least 2 characters'

  if (!text('age')) errors.age = 'Age is required'
  else if (!/^\d+$/.test(text('age')) || Number(text('age')) > 120) errors.age = 'Enter a whole number between 0 and 120'

  if (!text('gender')) errors.gender = 'Please select a gender'

  if (!text('phone')) errors.phone = 'Phone number is required'
  else if (!isPhone(text('phone'))) errors.phone = 'Enter a valid 10-digit mobile number'

  if (!text('city')) errors.city = 'City is required'
  else if (text('city').length < 2) errors.city = 'City must be at least 2 characters'

  if (text('emergency') && !isPhone(text('emergency'))) errors.emergency = 'Enter a valid 10-digit mobile number'
  if (text('email') && !isEmail(text('email'))) errors.email = 'Enter a valid email address'
  for (const key of ['familyMembers', 'income']) {
    if (text(key) && !/^\d+$/.test(text(key))) errors[key] = 'Enter a whole number (0 or more)'
  }
  for (const key of ['dob', 'registrationDate']) {
    if (text(key) > today) errors[key] = 'Date cannot be in the future'
  }
  return errors
}

// ---------------------------------------------------------------- API calls
export const listBeneficiaries = async () => (await request('/api/beneficiaries?limit=1000')).map(fromApi)
export const getBeneficiary = async (id) => fromApi(await request(`/api/beneficiaries/${id}`))
export const createBeneficiary = async (values) =>
  fromApi(await request('/api/beneficiaries', { method: 'POST', body: JSON.stringify(toPayload(values)) }))
export const updateBeneficiary = async (id, values) =>
  fromApi(await request(`/api/beneficiaries/${id}`, { method: 'PUT', body: JSON.stringify(toPayload(values)) }))
export const deactivateBeneficiary = async (id) => fromApi(await request(`/api/beneficiaries/${id}`, { method: 'DELETE' }))
export const getStatistics = () => request('/api/dashboard/statistics')

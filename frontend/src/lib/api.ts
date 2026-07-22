export type ApiStatus = 'ok'

export interface PermissionUser {
  id: number
  username: string
  nombre_completo: string
  correo: string
  permisos: string[]
}

export interface Area {
  id: number
  nombre: string
  descripcion: string | null
  activo: boolean
}

export interface CatalogItem extends Area {
  codigo?: string
  area_id?: number
  proceso_id?: number
  cargo_id?: number
  maquina_id?: number | null
  tipo_puesto?: 'operador' | 'ayudante' | 'manual'
}

export interface PersonItem {
  id: number
  codigo: string
  documento: string
  nombres: string
  apellidos: string
  correo: string | null
  activo: boolean
  usuario_id?: number | null
}

export interface WorkerItem {
  id: number
  codigo: string
  documento: string
  nombres: string
  apellidos: string
  activo: boolean
}

export interface WorkerDetail {
  trabajador: WorkerItem
  asignacion_laboral: { cargo_id: number; area_id: number; turno_id: number } | null
  supervisor: { supervisor_id: number } | null
  puestos: CatalogItem[]
}

export interface EvaluationDetailItem {
  id: number
  evaluacion_id: number
  requisito_id: number
  nivel_obtenido: number
  nivel_minimo: number
  aprobado: boolean
  observaciones: string | null
}

export interface EvaluationItem {
  id: number
  trabajador_id: number
  evaluador_id: number | null
  supervisor_id: number | null
  usuario_ejecutor_id: number | null
  puesto_id: number
  fecha: string
  estado: 'borrador' | 'completada' | 'anulada'
  observaciones: string | null
  detalles: EvaluationDetailItem[]
}

export interface ImportIssue { hoja: string; fila: number; error?: string; advertencia?: string }

export interface ChecklistCompetency {
  requisito_id: number
  competencia_id: number
  competencia: string
  nivel_minimo: number
}

export interface ChecklistActivity {
  actividad_id: number
  actividad: string
  competencias: ChecklistCompetency[]
}

export interface UserItem {
  id: number
  username: string
  correo: string
  nombre_completo: string
  activo: boolean
  roles: RoleItem[]
}

export interface PermissionItem {
  id: number
  codigo: string
  nombre: string
  descripcion: string | null
  modulo: string
  accion: string
  sistema: boolean
  activo: boolean
}

export interface RoleItem {
  id: number
  nombre: string
  descripcion: string | null
  sistema: boolean
  activo: boolean
  permisos: PermissionItem[]
}

interface HealthResponse {
  status: ApiStatus
  database: 'connected'
}

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

function authHeaders(): HeadersInit {
  const token = localStorage.getItem('mc_access_token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  let response: Response
  try {
    response = await fetch(`${API_URL}${path}`, {
      ...options,
      headers: { ...authHeaders(), ...options.headers },
    })
  } catch {
    throw new Error(`No se pudo conectar con la API en ${API_URL}. Verifique que el backend esté iniciado.`)
  }
  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as { detail?: string } | null
    throw new Error(body?.detail ?? `La API respondió con el estado ${response.status}`)
  }
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

export async function getHealth(signal?: AbortSignal): Promise<HealthResponse> {
  const response = await fetch(`${API_URL}/api/health`, { signal })

  if (!response.ok) {
    throw new Error(`La API respondió con el estado ${response.status}`)
  }

  return response.json() as Promise<HealthResponse>
}

export async function login(username: string, password: string): Promise<string> {
  const response = await fetch(`${API_URL}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  })
  if (!response.ok) throw new Error('Usuario o contraseña inválidos')
  const data = (await response.json()) as { access_token: string }
  return data.access_token
}

export async function getCurrentUser(): Promise<PermissionUser> {
  const response = await fetch(`${API_URL}/api/auth/me`, { headers: authHeaders() })
  if (!response.ok) throw new Error('Sesión expirada')
  return response.json() as Promise<PermissionUser>
}

export async function getAreas(): Promise<Area[]> {
  const response = await fetch(`${API_URL}/api/areas`, { headers: authHeaders() })
  if (!response.ok) throw new Error('No se pudieron cargar las áreas')
  return response.json() as Promise<Area[]>
}

export async function createArea(nombre: string, descripcion: string): Promise<Area> {
  const response = await fetch(`${API_URL}/api/areas`, {
    method: 'POST',
    headers: { ...authHeaders(), 'Content-Type': 'application/json' },
    body: JSON.stringify({ nombre, descripcion }),
  })
  if (!response.ok) throw new Error('No se pudo crear el área')
  return response.json() as Promise<Area>
}

export async function listCatalog(path: string): Promise<CatalogItem[]> {
  return request<CatalogItem[]>(`/api/${path}`)
}

export async function saveCatalog(
  path: string,
  data: Record<string, unknown>,
  id?: number,
): Promise<CatalogItem> {
  return request<CatalogItem>(`/api/${path}${id ? `/${id}` : ''}`, {
    method: id ? 'PATCH' : 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
}

export async function deactivateCatalog(path: string, id: number): Promise<void> {
  return request<void>(`/api/${path}/${id}`, { method: 'DELETE' })
}

export async function activateCatalog(path: string, id: number): Promise<CatalogItem> {
  return request<CatalogItem>(`/api/${path}/${id}/activar`, { method: 'POST' })
}

export async function listPeople(path: 'supervisores' | 'evaluadores'): Promise<PersonItem[]> {
  return request<PersonItem[]>(`/api/${path}`)
}

export async function savePerson(
  path: 'supervisores' | 'evaluadores',
  data: Record<string, unknown>,
  id?: number,
): Promise<PersonItem> {
  return request<PersonItem>(`/api/${path}${id ? `/${id}` : ''}`, {
    method: id ? 'PATCH' : 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
}

export async function activatePerson(path: 'supervisores' | 'evaluadores', id: number): Promise<PersonItem> {
  return request<PersonItem>(`/api/${path}/${id}/activar`, { method: 'POST' })
}

export async function deactivatePerson(path: 'supervisores' | 'evaluadores', id: number): Promise<void> {
  await request(`/api/${path}/${id}`, { method: 'DELETE' })
}

export async function linkPersonUser(path: 'supervisores' | 'evaluadores', id: number, usuarioId: number): Promise<void> {
  await request(`/api/${path}/${id}/usuario`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ usuario_id: usuarioId }),
  })
}

export async function listUsers(): Promise<UserItem[]> {
  return request<UserItem[]>('/api/usuarios')
}

export async function saveUser(data: Record<string, unknown>, id?: number): Promise<UserItem> {
  return request<UserItem>(`/api/usuarios${id ? `/${id}` : ''}`, {
    method: id ? 'PATCH' : 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
}

export async function activateUser(id: number): Promise<UserItem> { return request<UserItem>(`/api/usuarios/${id}/activar`, { method: 'POST' }) }
export async function deactivateUser(id: number): Promise<void> { await request(`/api/usuarios/${id}`, { method: 'DELETE' }) }
export async function resetUserPassword(id: number, newPassword: string): Promise<void> { await request(`/api/usuarios/${id}/reset-password`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ new_password: newPassword }) }) }

export async function listRoles(): Promise<RoleItem[]> {
  return request<RoleItem[]>('/api/roles')
}

export async function saveRole(data: Record<string, unknown>, id?: number): Promise<RoleItem> {
  return request<RoleItem>(`/api/roles${id ? `/${id}` : ''}`, {
    method: id ? 'PATCH' : 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
}

export async function activateRole(id: number): Promise<RoleItem> { return request<RoleItem>(`/api/roles/${id}/activar`, { method: 'POST' }) }
export async function deactivateRole(id: number): Promise<void> { await request(`/api/roles/${id}`, { method: 'DELETE' }) }

export async function listPermissions(): Promise<PermissionItem[]> {
  return request<PermissionItem[]>('/api/permisos')
}

export async function savePermission(data: Record<string, unknown>, id?: number): Promise<PermissionItem> {
  return request<PermissionItem>(`/api/permisos${id ? `/${id}` : ''}`, {
    method: id ? 'PATCH' : 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
}

export async function assignPositionActivity(positionId: number, activityId: number): Promise<void> {
  return request<void>(`/api/puestos/${positionId}/actividades`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ actividad_id: activityId }),
  })
}

export async function assignPositionMachine(positionId: number, machineId: number): Promise<void> {
  return request<void>(`/api/puestos/${positionId}/maquinas`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ maquina_id: machineId, fecha_inicio: new Date().toISOString().slice(0, 10) }),
  })
}

export async function assignMachineProcess(machineId: number, processId: number): Promise<void> {
  return request<void>(`/api/maquinas/${machineId}/proceso`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ proceso_id: processId, fecha_inicio: new Date().toISOString().slice(0, 10) }),
  })
}

export async function addPositionRequirement(positionId: number, data: Record<string, unknown>): Promise<void> {
  return request<void>(`/api/puestos/${positionId}/requisitos`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data),
  })
}

export async function listWorkers(filters: { buscar?: string; area_id?: string; supervisor_id?: string; puesto_id?: string } = {}): Promise<WorkerItem[]> {
  const params = new URLSearchParams()
  Object.entries(filters).forEach(([key, value]) => { if (value) params.set(key, value) })
  return request<WorkerItem[]>(`/api/trabajadores${params.size ? `?${params}` : ''}`)
}

export async function createCompleteWorker(data: Record<string, unknown>): Promise<WorkerItem> {
  return request<WorkerItem>('/api/trabajadores/registro-completo', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) })
}

export async function updateCompleteWorker(id: number, data: Record<string, unknown>): Promise<WorkerItem> {
  return request<WorkerItem>(`/api/trabajadores/${id}/registro`, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) })
}

export async function getWorkerDetail(id: number): Promise<WorkerDetail> { return request<WorkerDetail>(`/api/trabajadores/${id}/detalle`) }

export async function getPositionChecklist(id: number): Promise<{ puesto_id: number; actividades: ChecklistActivity[] }> { return request(`/api/puestos/${id}/checklist`) }

export async function createEvaluation(data: Record<string, unknown>): Promise<EvaluationItem> {
  return request<EvaluationItem>('/api/evaluaciones', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) })
}

export async function listEvaluations(trabajadorId?: number): Promise<EvaluationItem[]> {
  return request<EvaluationItem[]>(`/api/evaluaciones${trabajadorId ? `?trabajador_id=${trabajadorId}` : ''}`)
}

export async function downloadImportTemplate(): Promise<Blob> {
  const response = await fetch(`${API_URL}/api/importaciones/plantilla`, { headers: authHeaders() })
  if (!response.ok) throw new Error('No se pudo descargar la plantilla')
  return response.blob()
}

export async function validateImport(file: File): Promise<{ valido: boolean; errores: ImportIssue[]; advertencias: ImportIssue[]; resumen: Record<string, Record<string, number>> }> {
  const form = new FormData(); form.append('archivo', file)
  return request('/api/importaciones/validar', { method: 'POST', body: form })
}

export async function executeImport(file: File, skipExisting: boolean): Promise<{ resumen: Record<string, Record<string, number>> }> {
  const form = new FormData(); form.append('archivo', file)
  return request(`/api/importaciones/ejecutar?omitir_existentes=${skipExisting}`, { method: 'POST', body: form })
}

export async function getEvaluation(id: number): Promise<EvaluationItem> {
  return request<EvaluationItem>(`/api/evaluaciones/${id}`)
}

export async function updateEvaluation(id: number, data: Record<string, unknown>): Promise<EvaluationItem> {
  return request<EvaluationItem>(`/api/evaluaciones/${id}`, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) })
}

export async function cancelEvaluation(id: number): Promise<EvaluationItem> {
  return request<EvaluationItem>(`/api/evaluaciones/${id}/anular`, { method: 'POST' })
}

export async function completeEvaluation(id: number): Promise<void> {
  await request(`/api/evaluaciones/${id}/completar`, { method: 'POST' })
}

export async function saveWorker(data: Record<string, unknown>): Promise<WorkerItem> {
  return request<WorkerItem>('/api/trabajadores', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) })
}

export async function assignWorkerSupervisor(workerId: number, supervisorId: number): Promise<void> {
  return request<void>(`/api/trabajadores/${workerId}/supervisor`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ supervisor_id: supervisorId, fecha_inicio: new Date().toISOString().slice(0, 10) }) })
}

export async function assignWorkerPosition(workerId: number, positionId: number): Promise<void> {
  return request<void>(`/api/trabajadores/${workerId}/puestos`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ puesto_id: positionId, fecha_inicio: new Date().toISOString().slice(0, 10) }) })
}

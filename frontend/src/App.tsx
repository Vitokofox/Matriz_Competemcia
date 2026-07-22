import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import './App.css'
import {
  getCurrentUser,
  getHealth,
  login,
  listEvaluations,
  listWorkers,
  type EvaluationItem,
  type ApiStatus,
  type PermissionUser,
} from './lib/api'
import { ConfigurationPage } from './features/configuration/ConfigurationPage'
import { WorkersPage } from './features/process/WorkersPage'
import { WorkerDetailPage } from './features/process/WorkerDetailPage'
import { EvaluationsPage } from './features/process/EvaluationsPage'
import { AppShell, type AppSection, type ConnectionState } from './layouts/AppShell'

type SessionConnectionState = ApiStatus | 'checking' | 'offline'

function App() {
  const [user, setUser] = useState<PermissionUser | null>(null)
  const [checkingSession, setCheckingSession] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('mc_access_token')
    if (!token) {
      setCheckingSession(false)
      return
    }
    getCurrentUser()
      .then(setUser)
      .catch(() => localStorage.removeItem('mc_access_token'))
      .finally(() => setCheckingSession(false))
  }, [])

  if (checkingSession) return <div className="loading-screen">Cargando sesión...</div>
  if (!user) return <LoginScreen onLogin={setUser} />
  return <AuthenticatedApp user={user} onLogout={() => setUser(null)} />
}

function LoginScreen({ onLogin }: { onLogin: (user: PermissionUser) => void }) {
  const [username, setUsername] = useState('admin')
  const [password, setPassword] = useState('Cambiar123!')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function submit(event: FormEvent) {
    event.preventDefault()
    setLoading(true)
    setError('')
    try {
      const token = await login(username, password)
      localStorage.setItem('mc_access_token', token)
      onLogin(await getCurrentUser())
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'No se pudo iniciar sesión')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="auth-layout">
      <section className="auth-intro">
        <span className="brand-mark">MC</span>
        <p className="eyebrow">Matriz de Competencias</p>
        <h1>El talento visible mueve mejor la operación.</h1>
        <p>Administra capacidades, evaluaciones y disponibilidad desde un solo lugar.</p>
      </section>
      <form className="login-card" onSubmit={submit}>
        <p className="eyebrow">Acceso seguro</p>
        <h2>Iniciar sesión</h2>
        <label>Usuario<input value={username} onChange={(event) => setUsername(event.target.value)} /></label>
        <label>Contraseña<input type="password" value={password} onChange={(event) => setPassword(event.target.value)} /></label>
        {error && <p className="form-error">{error}</p>}
        <button className="primary-action" disabled={loading}>{loading ? 'Ingresando...' : 'Entrar'} <span>→</span></button>
        <small>Cuenta inicial de desarrollo: admin</small>
      </form>
    </main>
  )
}

function AuthenticatedApp({ user, onLogout }: { user: PermissionUser; onLogout: () => void }) {
  const [connection, setConnection] = useState<SessionConnectionState>('checking')
  const [section, setSection] = useState<AppSection>('overview')
  const [workerId, setWorkerId] = useState<number | null>(null)

  useEffect(() => {
    getHealth().then(() => setConnection('ok')).catch(() => setConnection('offline'))
  }, [])

  function logout() {
    localStorage.removeItem('mc_access_token')
    onLogout()
  }

  return <AppShell user={user} section={section} connection={connection as ConnectionState} onSectionChange={(next) => { if (next === 'workers') setWorkerId(null); setSection(next) }} onLogout={logout}>{section === 'configuration' ? <ConfigurationPage /> : section === 'workers' ? workerId ? <WorkerDetailPage workerId={workerId} onBack={() => setWorkerId(null)} /> : <WorkersPage onOpenDetail={setWorkerId} /> : section === 'evaluations' ? <EvaluationsPage /> : <Overview />}</AppShell>
}

function Overview() {
  const [evaluations, setEvaluations] = useState<EvaluationItem[]>([]); const [workerItems, setWorkerItems] = useState<Awaited<ReturnType<typeof listWorkers>>>([]); const [error, setError] = useState('')
  useEffect(() => { void Promise.all([listEvaluations(), listWorkers()]).then(([items, loadedWorkers]) => { setEvaluations(items); setWorkerItems(loadedWorkers) }).catch((reason: unknown) => setError(reason instanceof Error ? reason.message : 'No se pudo cargar el resumen')) }, [])
  const workers = workerItems.filter((item) => item.activo).length
  const completed = evaluations.filter((item) => item.estado === 'completada'); const drafts = evaluations.filter((item) => item.estado === 'borrador'); const approved = completed.flatMap((item) => item.detalles); const approvalRate = approved.length ? Math.round(approved.filter((item) => item.aprobado).length / approved.length * 100) : 0
  return <div className="overview-page"><div className="process-heading"><div><p className="eyebrow">Vista general</p><h2>Resumen operativo</h2></div><span>Actualizado ahora</span></div>{error && <p className="form-error">{error}</p>}<div className="summary-cards"><article><span>Trabajadores activos</span><strong>{workers}</strong></article><article><span>Evaluaciones completadas</span><strong>{completed.length}</strong></article><article><span>Borradores</span><strong>{drafts.length}</strong></article><article><span>Aprobación global</span><strong>{approvalRate}%</strong></article></div><section className="recent-evaluations"><div className="panel-heading"><div><p className="eyebrow">Actividad reciente</p><h3>Últimas evaluaciones</h3></div><span>{evaluations.length} total</span></div>{evaluations.slice(0, 5).map((item) => <div className="recent-row" key={item.id}><strong>{workerItems.find((worker) => worker.id === item.trabajador_id)?.nombres ?? `Evaluación #${item.id}`}</strong><span>{item.fecha}</span><span className={`status-pill status-${item.estado}`}>{item.estado}</span><span>{item.detalles.filter((detail) => detail.aprobado).length}/{item.detalles.length} aprobadas</span></div>)}{!evaluations.length && <p className="table-empty">Aún no hay evaluaciones registradas.</p>}</section></div>
}

export default App

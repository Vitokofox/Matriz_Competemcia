import { useEffect, useState } from 'react'
import { completeTrainingActivity, createTrainingPlan, listCatalog, listTrainingPlans, listWorkers, rescheduleTrainingActivity, type CatalogItem, type TrainingPlan, type WorkerItem } from '../../lib/api'
import { addCalendarDays, formatDate, parseLatinDate, todayLocalDate } from '../../lib/dates'

export function TrainingPlansPage() {
  const [plans, setPlans] = useState<TrainingPlan[]>([])
  const [workers, setWorkers] = useState<WorkerItem[]>([])
  const [positions, setPositions] = useState<CatalogItem[]>([])
  const [activities, setActivities] = useState<CatalogItem[]>([])
  const [workerId, setWorkerId] = useState('')
  const [positionId, setPositionId] = useState('')
  const [selectedActivities, setSelectedActivities] = useState<number[]>([])
  const [planType, setPlanType] = useState<'manual' | 'nuevo_puesto' | 'reemplazo'>('manual')
  const [startDate, setStartDate] = useState(todayLocalDate())
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [reportPlan, setReportPlan] = useState<TrainingPlan | null>(null)

  async function load() {
    try {
      const [loadedPlans, loadedWorkers, loadedPositions, loadedActivities] = await Promise.all([listTrainingPlans(), listWorkers(), listCatalog('puestos'), listCatalog('actividades')])
      setPlans(loadedPlans); setWorkers(loadedWorkers); setPositions(loadedPositions); setActivities(loadedActivities)
    } catch (reason) { setError(message(reason)) }
  }
  useEffect(() => { void load() }, [])

  async function create() {
    if (!workerId || !positionId || !selectedActivities.length) { setError('Seleccione trabajador, puesto y al menos una actividad'); return }
    try {
      await createTrainingPlan({ trabajador_id: Number(workerId), puesto_id: Number(positionId), tipo: planType, fecha_inicio: startDate, actividades: selectedActivities.map((id, index) => ({ actividad_id: id, fecha_programada: addDays(startDate, index) })) })
      setNotice('Plan creado correctamente'); setSelectedActivities([]); await load()
    } catch (reason) { setError(message(reason)) }
  }
  async function complete(planId: number, activityId: number) { try { await completeTrainingActivity(planId, activityId); await load() } catch (reason) { setError(message(reason)) } }
  async function reschedule(planId: number, activityId: number) { const entered = window.prompt('Nueva fecha (DD/MM/AAAA)'); if (!entered) return; const date = parseLatinDate(entered); if (!date) { setError('Ingrese una fecha válida en formato DD/MM/AAAA'); return } try { await rescheduleTrainingActivity(planId, activityId, date); setNotice('Actividad reprogramada'); await load() } catch (reason) { setError(message(reason)) } }

  return <div className="training-page"><div className="panel-heading"><div><p className="eyebrow">Seguimiento operativo</p><h2>Planes de capacitación</h2></div><span>{plans.length} planes</span></div>{error && <p className="form-error">{error}</p>}{notice && <p className="success-message">{notice}</p>}<section className="training-create"><h3>Nuevo plan</h3><div className="form-line"><select value={workerId} onChange={(event) => setWorkerId(event.target.value)}><option value="">Trabajador</option>{workers.map((worker) => <option key={worker.id} value={worker.id}>{worker.codigo} · {worker.nombres} {worker.apellidos}</option>)}</select><select value={positionId} onChange={(event) => setPositionId(event.target.value)}><option value="">Puesto</option>{positions.map((position) => <option key={position.id} value={position.id}>{position.codigo ?? 'AUTO'} · {position.nombre}</option>)}</select><select value={planType} onChange={(event) => setPlanType(event.target.value as typeof planType)}><option value="manual">Plan manual</option><option value="nuevo_puesto">Nuevo puesto</option><option value="reemplazo">Reemplazo</option></select><input type="date" value={startDate} onChange={(event) => setStartDate(event.target.value)} /></div><div className="training-activity-picker">{activities.map((activity) => <label key={activity.id}><input type="checkbox" checked={selectedActivities.includes(activity.id)} onChange={() => setSelectedActivities((current) => current.includes(activity.id) ? current.filter((id) => id !== activity.id) : [...current, activity.id])} /> {activity.nombre}</label>)}</div><button className="primary-action" onClick={() => void create()}>Crear plan <span>→</span></button></section><div className="training-plans">{plans.map((plan) => <article className="training-plan" key={plan.id}><div className="training-plan-heading"><div><p className="eyebrow">{plan.tipo === 'reevaluacion' ? 'Reevaluación' : 'Plan operativo'} · Plan #{plan.id}</p><h3>{workerName(plan.trabajador_id, workers)} · {positionName(plan.puesto_id, positions)}</h3></div><span className={`status-pill status-${plan.estado}`}>{plan.estado}</span></div>{plan.motivo && <p>{plan.motivo}</p>}<div className="training-gantt">{plan.actividades.map((activity) => { const reschedules = Number(Boolean(activity.fecha_reprogramacion_1)) + Number(Boolean(activity.fecha_reprogramacion_2)); return <div className="training-gantt-row" key={activity.id}><strong>{activityName(activity.actividad_id, activities)}</strong><div className="gantt-track"><span className={`gantt-bar gantt-${activity.estado}`} style={{ width: `${Math.max(14, (reschedules + 1) * 28)}%` }} /></div><small>{formatDate(activity.fecha_reprogramacion_2 || activity.fecha_reprogramacion_1 || activity.fecha_programada)}</small><div className="row-actions">{activity.estado !== 'completada' && <><button onClick={() => void complete(plan.id, activity.id)}>Completar</button><button onClick={() => void reschedule(plan.id, activity.id)}>Reprogramar</button></>}<button onClick={() => setReportPlan(plan)}>Reporte</button></div></div> })}</div></article>)}{!plans.length && <p className="table-empty">No hay planes de capacitación.</p>}</div>{reportPlan && <TrainingReport plan={reportPlan} workers={workers} positions={positions} activities={activities} onClose={() => setReportPlan(null)} />}</div>
}

function TrainingReport({ plan, workers, positions, activities, onClose }: { plan: TrainingPlan; workers: WorkerItem[]; positions: CatalogItem[]; activities: CatalogItem[]; onClose: () => void }) {
  const text = `Plan de capacitación #${plan.id}\nTrabajador: ${workerName(plan.trabajador_id, workers)}\nPuesto: ${positionName(plan.puesto_id, positions)}\nEstado: ${plan.estado}\n\n${plan.actividades.map((item) => `${activityName(item.actividad_id, activities)}: ${formatDate(item.fecha_reprogramacion_2 || item.fecha_reprogramacion_1 || item.fecha_programada)} - ${item.estado}`).join('\n')}`
  async function share() { if (navigator.share) await navigator.share({ title: `Plan de capacitación #${plan.id}`, text }); else window.print() }
  return <div className="report-modal training-report-modal" role="dialog" aria-modal="true"><div className="report-card"><div className="report-actions"><button className="secondary-action" onClick={() => window.print()}>Imprimir / PDF</button><button className="primary-action" onClick={() => void share()}>Compartir</button><button className="back-link" onClick={onClose}>Cerrar</button></div><article className="evaluation-report"><p className="eyebrow">Seguimiento de capacitación</p><h2>Gantt del plan #{plan.id}</h2><p><strong>Trabajador:</strong> {workerName(plan.trabajador_id, workers)}</p><p><strong>Puesto:</strong> {positionName(plan.puesto_id, positions)}</p><p><strong>Estado:</strong> {plan.estado}</p><div className="training-gantt">{plan.actividades.map((item) => <div className="training-gantt-row" key={item.id}><strong>{activityName(item.actividad_id, activities)}</strong><div className="gantt-track"><span className={`gantt-bar gantt-${item.estado}`} style={{ width: '70%' }} /></div><small>{formatDate(item.fecha_reprogramacion_2 || item.fecha_reprogramacion_1 || item.fecha_programada)}</small></div>)}</div><footer className="report-footer">Documento de seguimiento y cumplimiento</footer></article></div></div>
}

function workerName(id: number, workers: WorkerItem[]) { const item = workers.find((worker) => worker.id === id); return item ? `${item.codigo} · ${item.nombres} ${item.apellidos}` : `Trabajador #${id}` }
function positionName(id: number, positions: CatalogItem[]) { return positions.find((position) => position.id === id)?.nombre ?? `Puesto #${id}` }
function activityName(id: number, activities: CatalogItem[]) { return activities.find((activity) => activity.id === id)?.nombre ?? `Actividad #${id}` }
function addDays(value: string, days: number) { return addCalendarDays(value, days) }
function message(reason: unknown) { return reason instanceof Error ? reason.message : 'No se pudo cargar el seguimiento' }

import { useEffect, useState } from 'react'
import { getWorkerDetail, type WorkerDetail } from '../../lib/api'
import { EvaluationPage } from './EvaluationPage'

export function WorkerDetailPage({ workerId, onBack }: { workerId: number; onBack: () => void }) {
  const [detail, setDetail] = useState<WorkerDetail | null>(null)
  const [evaluationPosition, setEvaluationPosition] = useState<number | null>(null)
  const [error, setError] = useState('')

  useEffect(() => { void getWorkerDetail(workerId).then(setDetail).catch((reason: unknown) => setError(message(reason))) }, [workerId])
  if (evaluationPosition && detail) return <EvaluationPage worker={detail.trabajador} positionId={evaluationPosition} onBack={() => setEvaluationPosition(null)} />
  if (error) return <div className="form-error">{error}</div>
  if (!detail) return <div className="loading-screen">Cargando trabajador...</div>

  return <div className="worker-detail-page"><button className="back-link" onClick={onBack}>← Volver al listado</button><div className="process-heading"><div><p className="eyebrow">Detalle del trabajador</p><h2>{detail.trabajador.nombres} {detail.trabajador.apellidos}</h2></div><span>{detail.trabajador.codigo}</span></div><section className="worker-summary detail-summary"><p><strong>Documento:</strong> {detail.trabajador.documento}</p><p><strong>Estado:</strong> {detail.trabajador.activo ? 'Activo' : 'Inactivo'}</p><p><strong>Supervisor:</strong> {detail.supervisor ? 'Asignado' : 'Sin supervisor'}</p><p><strong>Asignación laboral:</strong> {detail.asignacion_laboral ? 'Activa' : 'Sin asignación'}</p></section><section className="associated-positions"><p className="eyebrow">Puestos asociados</p>{detail.puestos.map((position) => <article key={position.id}><div><strong>{position.codigo ?? 'AUTO'} · {position.nombre}</strong><small>Seleccione el puesto para abrir su evaluación</small></div><button onClick={() => setEvaluationPosition(position.id)}>Evaluar puesto</button></article>)}{!detail.puestos.length && <p>El trabajador no tiene puestos asignados.</p>}</section></div>
}

function message(reason: unknown) { return reason instanceof Error ? reason.message : 'No se pudo cargar el detalle' }

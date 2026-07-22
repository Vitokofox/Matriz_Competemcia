import { useEffect, useState } from 'react'
import { completeEvaluation, createEvaluation, getPositionChecklist, type ChecklistActivity, type WorkerItem } from '../../lib/api'

export function EvaluationPage({ worker, positionId, onBack }: { worker: WorkerItem; positionId: number; onBack: () => void }) {
  const [activities, setActivities] = useState<ChecklistActivity[]>([])
  const [scores, setScores] = useState<Record<number, number>>({})
  const [observations, setObservations] = useState('')
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  useEffect(() => { void getPositionChecklist(positionId).then((data) => setActivities(data.actividades)).catch((reason: unknown) => setError(message(reason))) }, [positionId])
  const requirements = activities.flatMap((activity) => activity.competencias)
  async function submit(complete: boolean) {
    if (requirements.some((item) => !scores[item.requisito_id])) { setError('Debe registrar una nota para todas las competencias'); return }
    try {
      const evaluation = await createEvaluation({ trabajador_id: worker.id, puesto_id: positionId, fecha: new Date().toISOString().slice(0, 10), observaciones: observations, detalles: requirements.map((item) => ({ requisito_id: item.requisito_id, nivel_obtenido: scores[item.requisito_id] })) })
      if (complete) await completeEvaluation(evaluation.id)
      setNotice(complete ? 'Evaluación completada correctamente' : 'Borrador guardado')
    } catch (reason) { setError(message(reason)) }
  }
  return <div className="evaluation-page"><button className="back-link" onClick={onBack}>← Volver a trabajadores</button><div className="process-heading"><div><p className="eyebrow">Checklist de evaluación</p><h2>{worker.nombres} {worker.apellidos}</h2></div><span>{requirements.length} competencias</span></div>{error && <p className="form-error">{error}</p>}{notice && <p className="success-message">{notice}</p>}{activities.map((activity) => <section className="checklist-activity" key={activity.actividad_id}><h3>{activity.actividad}</h3>{activity.competencias.map((competency) => <div className="checklist-row" key={competency.requisito_id}><div><strong>{competency.competencia}</strong><small>Nivel mínimo: {competency.nivel_minimo}</small></div><select value={scores[competency.requisito_id] ?? ''} onChange={(event) => setScores({ ...scores, [competency.requisito_id]: Number(event.target.value) })}><option value="">Nota</option>{[1, 2, 3, 4, 5].map((level) => <option key={level} value={level}>{level}</option>)}</select><span className={scores[competency.requisito_id] >= competency.nivel_minimo ? 'check-approved' : 'check-pending'}>{scores[competency.requisito_id] ? scores[competency.requisito_id] >= competency.nivel_minimo ? 'Aprobado' : 'No aprobado' : 'Pendiente'}</span></div>)}</section>)}<textarea className="evaluation-notes" placeholder="Observaciones generales" value={observations} onChange={(event) => setObservations(event.target.value)} /><div className="evaluation-actions"><button className="secondary-action" onClick={() => void submit(false)}>Guardar borrador</button><button className="primary-action" onClick={() => void submit(true)}>Completar evaluación <span>→</span></button></div></div>
}

function message(reason: unknown) { return reason instanceof Error ? reason.message : 'No se pudo cargar el checklist' }

import { useEffect, useState } from 'react'
import { completeEvaluation, createEvaluation, getPositionChecklist, type ChecklistActivity, type EvaluationItem, type WorkerItem } from '../../lib/api'

export function EvaluationPage({ worker, positionId, positionName, onBack }: { worker: WorkerItem; positionId: number; positionName: string; onBack: () => void }) {
  const [activities, setActivities] = useState<ChecklistActivity[]>([])
  const [scores, setScores] = useState<Record<number, number>>({})
  const [observations, setObservations] = useState('')
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [completedEvaluation, setCompletedEvaluation] = useState<EvaluationItem | null>(null)

  useEffect(() => { void getPositionChecklist(positionId).then((data) => setActivities(data.actividades)).catch((reason: unknown) => setError(message(reason))) }, [positionId])
  const requirements = activities.flatMap((activity) => activity.competencias)

  async function submit(complete: boolean) {
    setError('')
    if (requirements.some((item) => !scores[item.requisito_id])) { setError('Debe registrar una nota para todas las competencias'); return }
    try {
      const evaluation = await createEvaluation({ trabajador_id: worker.id, puesto_id: positionId, fecha: new Date().toISOString().slice(0, 10), observaciones: observations, detalles: requirements.map((item) => ({ requisito_id: item.requisito_id, nivel_obtenido: scores[item.requisito_id] })) })
      if (complete) {
        setCompletedEvaluation(await completeEvaluation(evaluation.id))
        setNotice('Evaluación completada correctamente')
      } else setNotice('Borrador guardado')
    } catch (reason) { setError(message(reason)) }
  }

  return <div className="evaluation-page"><button className="back-link" onClick={onBack}>← Volver a trabajadores</button><div className="process-heading"><div><p className="eyebrow">Checklist de evaluación</p><h2>{worker.nombres} {worker.apellidos}</h2></div><span>{requirements.length} competencias</span></div>{error && <p className="form-error">{error}</p>}{notice && <p className="success-message">{notice}</p>}{activities.map((activity) => <section className="checklist-activity" key={activity.actividad_id}><h3>{activity.actividad}</h3>{activity.competencias.map((competency) => <div className="checklist-row" key={competency.requisito_id}><div><strong>{competency.competencia}</strong><small>Nivel mínimo: {competency.nivel_minimo}</small></div><select disabled={Boolean(completedEvaluation)} value={scores[competency.requisito_id] ?? ''} onChange={(event) => setScores({ ...scores, [competency.requisito_id]: Number(event.target.value) })}><option value="">Nota</option>{[1, 2, 3, 4, 5].map((level) => <option key={level} value={level}>{level}</option>)}</select><span className={scores[competency.requisito_id] >= competency.nivel_minimo ? 'check-approved' : 'check-pending'}>{scores[competency.requisito_id] ? scores[competency.requisito_id] >= competency.nivel_minimo ? 'Aprobado' : 'No aprobado' : 'Pendiente'}</span></div>)}</section>)}<textarea disabled={Boolean(completedEvaluation)} className="evaluation-notes" placeholder="Observaciones generales" value={observations} onChange={(event) => setObservations(event.target.value)} />{!completedEvaluation && <div className="evaluation-actions"><button className="secondary-action" onClick={() => void submit(false)}>Guardar borrador</button><button className="primary-action" onClick={() => void submit(true)}>Completar evaluación <span>→</span></button></div>}{completedEvaluation && <EvaluationReport evaluation={completedEvaluation} worker={worker} positionName={positionName} onClose={onBack} />}</div>
}

function EvaluationReport({ evaluation, worker, positionName, onClose }: { evaluation: EvaluationItem; worker: WorkerItem; positionName: string; onClose: () => void }) {
  const approved = evaluation.detalles.filter((detail) => detail.aprobado).length
  const reportText = `Reporte de evaluación\nTrabajador: ${worker.nombres} ${worker.apellidos}\nDocumento: ${worker.documento}\nPuesto: ${positionName}\nResultado: ${approved}/${evaluation.detalles.length} competencias aprobadas\nFecha: ${evaluation.fecha}\n\n${evaluation.detalles.map((detail) => `Requisito #${detail.requisito_id}: nivel ${detail.nivel_obtenido}/${detail.nivel_minimo} - ${detail.aprobado ? 'Aprobado' : 'No aprobado'}`).join('\n')}\n\nObservaciones: ${evaluation.observaciones || 'Sin observaciones'}`
  async function share() {
    if (navigator.share) await navigator.share({ title: 'Reporte de evaluación', text: reportText })
    else window.print()
  }
  return <div className="report-modal" role="dialog" aria-modal="true" aria-labelledby="report-title"><div className="report-card"><div className="report-actions"><button className="secondary-action" onClick={() => window.print()}>Imprimir / PDF</button><button className="primary-action" onClick={() => void share()}>Compartir</button><button className="back-link" onClick={onClose}>Cerrar</button></div><article className="evaluation-report"><p className="eyebrow">Reporte final</p><h2 id="report-title">Evaluación de competencias</h2><div className="report-meta"><p><strong>Evaluado:</strong> {worker.nombres} {worker.apellidos}</p><p><strong>Documento:</strong> {worker.documento}</p><p><strong>Puesto:</strong> {positionName}</p><p><strong>Fecha:</strong> {new Date(`${evaluation.fecha}T00:00:00`).toLocaleDateString('es-CL')}</p></div><div className="report-result"><span>Resultado</span><strong>{approved}/{evaluation.detalles.length}</strong><small>competencias aprobadas</small></div><div className="report-details">{evaluation.detalles.map((detail) => <div key={detail.id}><span>Requisito #{detail.requisito_id}</span><span>Nivel {detail.nivel_obtenido} / mínimo {detail.nivel_minimo}</span><strong>{detail.aprobado ? 'Aprobado' : 'No aprobado'}</strong></div>)}</div><p><strong>Observaciones:</strong> {evaluation.observaciones || 'Sin observaciones'}</p><footer className="report-signatures"><div><span>Firma del evaluador</span></div><div><span>Firma del evaluado</span></div></footer><small className="report-footer">Documento generado por Matriz de Competencias · Evaluación cerrada</small></article></div></div>
}

function message(reason: unknown) { return reason instanceof Error ? reason.message : 'No se pudo cargar el checklist' }

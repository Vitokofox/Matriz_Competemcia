import { useEffect, useState } from 'react'
import {
  listCatalog,
  listEvaluations,
  listPeople,
  listWorkers,
  type CatalogItem,
  type EvaluationItem,
  type PersonItem,
  type WorkerItem,
} from '../../lib/api'
import { formatDate } from '../../lib/dates'

interface WorkersPageProps { onOpenDetail: (workerId: number) => void }

export function WorkersPage({ onOpenDetail }: WorkersPageProps) {
  const [workers, setWorkers] = useState<WorkerItem[]>([])
  const [areas, setAreas] = useState<CatalogItem[]>([])
  const [supervisors, setSupervisors] = useState<PersonItem[]>([])
  const [positions, setPositions] = useState<CatalogItem[]>([])
  const [evaluations, setEvaluations] = useState<EvaluationItem[]>([])
  const [filters, setFilters] = useState({ buscar: '', area_id: '', supervisor_id: '', puesto_id: '' })
  const [error, setError] = useState('')

  useEffect(() => {
    void Promise.all([listCatalog('areas'), listPeople('supervisores'), listCatalog('puestos'), listEvaluations()])
      .then(([areaItems, supervisorItems, positionItems, evaluationItems]) => { setAreas(areaItems); setSupervisors(supervisorItems); setPositions(positionItems); setEvaluations(evaluationItems) })
      .catch((reason: unknown) => setError(message(reason)))
  }, [])

  useEffect(() => {
    const timer = window.setTimeout(() => { void listWorkers(filters).then(setWorkers).catch((reason: unknown) => setError(message(reason))) }, 180)
    return () => window.clearTimeout(timer)
  }, [filters])

  function updateFilter(key: keyof typeof filters, value: string) { setFilters((current) => ({ ...current, [key]: value })) }
  function lastEvaluation(workerId: number) { return evaluations.find((item) => item.trabajador_id === workerId && item.estado === 'completada') }

  return <div className="process-page"><div className="process-heading"><div><p className="eyebrow">Proceso · Panel de control</p><h2>Trabajadores</h2></div><span>{workers.length} registros</span></div><div className="worker-filters"><input placeholder="Buscar por código, documento o nombre" value={filters.buscar} onChange={(event) => updateFilter('buscar', event.target.value)} /><select value={filters.area_id} onChange={(event) => updateFilter('area_id', event.target.value)}><option value="">Todas las áreas</option>{areas.map((item) => <option key={item.id} value={item.id}>{item.nombre}</option>)}</select><select value={filters.supervisor_id} onChange={(event) => updateFilter('supervisor_id', event.target.value)}><option value="">Todos los supervisores</option>{supervisors.map((item) => <option key={item.id} value={item.id}>{item.nombres} {item.apellidos}</option>)}</select><select value={filters.puesto_id} onChange={(event) => updateFilter('puesto_id', event.target.value)}><option value="">Todos los puestos</option>{positions.map((item) => <option key={item.id} value={item.id}>{item.codigo ?? 'AUTO'} · {item.nombre}</option>)}</select><button type="button" onClick={() => setFilters({ buscar: '', area_id: '', supervisor_id: '', puesto_id: '' })}>Limpiar</button></div>{error && <p className="form-error">{error}</p>}<div className="worker-list-heading"><span>Trabajador</span><span>Documento</span><span>Última evaluación</span><span>Estado</span><span /></div><div className="data-table worker-list-only">{workers.map((worker) => { const evaluation = lastEvaluation(worker.id); return <button className="worker-row" key={worker.id} onClick={() => onOpenDetail(worker.id)}><strong>{worker.codigo ?? 'AUTO'} · {worker.nombres} {worker.apellidos}</strong><span>{worker.documento}</span><span className="worker-last-evaluation">{evaluation ? <><strong>{formatDate(evaluation.fecha)}</strong><small>{evaluation.resultado === 'aprobada' ? 'Aprobada' : 'No aprobada'}</small></> : 'Sin evaluación'}</span><span className="status-pill">{worker.activo ? 'Activo' : 'Inactivo'}</span><span className="view-action">Ver detalle →</span></button> })}{!workers.length && <div className="table-empty">No se encontraron trabajadores.</div>}</div></div>
}

function message(reason: unknown) { return reason instanceof Error ? reason.message : 'No se pudo cargar trabajadores' }

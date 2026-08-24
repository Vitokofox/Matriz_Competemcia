import { useEffect, useMemo, useState } from 'react'
import { listOperatorAuthorizations, type OperatorAuthorizationSummary } from '../../lib/api'
import { formatDate } from '../../lib/dates'

interface PositionGroup { id: number; name: string; operators: OperatorAuthorizationSummary[]; enabled: number }

export function AuthorizationSummary() {
  const [items, setItems] = useState<OperatorAuthorizationSummary[]>([])
  const [selected, setSelected] = useState<PositionGroup | null>(null)
  const [error, setError] = useState('')

  useEffect(() => { void listOperatorAuthorizations().then(setItems).catch((reason: unknown) => setError(reason instanceof Error ? reason.message : 'No se pudo cargar el resumen')) }, [])

  const positions = useMemo(() => {
    const groups = new Map<number, PositionGroup>()
    items.forEach((item) => {
      const current = groups.get(item.puesto_id) ?? { id: item.puesto_id, name: item.puesto_nombre, operators: [], enabled: 0 }
      current.operators.push(item)
      if (item.habilitado) current.enabled += 1
      groups.set(item.puesto_id, current)
    })
    return [...groups.values()].sort((a, b) => a.name.localeCompare(b.name, 'es'))
  }, [items])

  return <section className="authorization-summary">
    <div className="panel-heading authorization-heading"><div><p className="eyebrow">Cobertura por puesto</p><h3>Operadores habilitados</h3></div><span>{positions.length} puestos</span></div>
    {error && <p className="form-error">{error}</p>}
    <div className="position-summary-list">{positions.map((position) => <article key={position.id}><strong>{position.name}</strong><span className={position.enabled > 0 ? 'position-enabled-count' : 'position-enabled-count empty'}>{position.enabled} habilitado{position.enabled === 1 ? '' : 's'}</span><button type="button" className="position-detail-button" aria-label={`Ver operadores de ${position.name}`} title="Ver detalle" onClick={() => setSelected(position)}>🔍</button></article>)}{!positions.length && !error && <p className="table-empty">No hay puestos con operadores asignados.</p>}</div>
    {selected && <PositionDetail position={selected} onClose={() => setSelected(null)} />}
  </section>
}

function PositionDetail({ position, onClose }: { position: PositionGroup; onClose: () => void }) {
  return <div className="report-modal authorization-detail-modal" role="dialog" aria-modal="true" aria-labelledby="position-detail-title" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose() }}><div className="report-card"><div className="authorization-detail-heading"><div><p className="eyebrow">Detalle del puesto</p><h2 id="position-detail-title">{position.name}</h2><p>{position.enabled} de {position.operators.length} operadores habilitados</p></div><button type="button" className="secondary-action" onClick={onClose}>Cerrar</button></div><div className="authorization-table-wrap"><table className="authorization-table"><thead><tr><th>Operador</th><th>Última evaluación</th><th>Nota</th><th>Estado</th></tr></thead><tbody>{position.operators.map((item) => <tr key={item.trabajador_id}><td><strong>{item.trabajador_nombre}</strong><small>{item.trabajador_codigo}</small></td><td>{formatDate(item.fecha_evaluacion, 'Sin evaluación')}</td><td><strong className="authorization-score">{item.nota === null ? '—' : `${item.nota.toFixed(1)} / 4`}</strong></td><td><span className={`authorization-status ${item.habilitado ? 'enabled' : 'disabled'}`}><i />{item.habilitado ? 'Habilitado' : 'No habilitado'}</span></td></tr>)}</tbody></table></div></div></div>
}

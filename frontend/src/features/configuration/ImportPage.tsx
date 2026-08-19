import { useEffect, useState } from 'react'
import {
  analyzeProfileImport,
  configureProfileImport,
  downloadImportTemplate,
  executeImport,
  listCatalog,
  publishProfileDraft,
  validateImport,
  validateProfileDraft,
  type CatalogItem,
  type ImportIssue,
  type ProfileImportConfiguration,
  type ProfileImportDraft,
} from '../../lib/api'

const MACROS = [
  'operacion',
  'inspeccion',
  'calidad',
  'seguridad',
  'coordinacion',
  'conductuales',
]

export function ImportPage() {
  const [file, setFile] = useState<File | null>(null)
  const [machines, setMachines] = useState<CatalogItem[]>([])
  const [positions, setPositions] = useState<CatalogItem[]>([])
  const [draft, setDraft] = useState<ProfileImportDraft | null>(null)
  const [configuration, setConfiguration] =
    useState<ProfileImportConfiguration | null>(null)
  const [genericMode, setGenericMode] = useState(false)
  const [skipExisting, setSkipExisting] = useState(false)
  const [validated, setValidated] = useState(false)
  const [errors, setErrors] = useState<ImportIssue[]>([])
  const [warnings, setWarnings] = useState<ImportIssue[]>([])
  const [summary, setSummary] = useState<
    Record<string, Record<string, number>>
  >({})
  const [notice, setNotice] = useState('')
  const [preview, setPreview] = useState<Awaited<ReturnType<typeof validateProfileDraft>>['detalle']>([])
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    void Promise.all([listCatalog('maquinas'), listCatalog('puestos')])
      .then(([machineItems, positionItems]) => {
        setMachines(machineItems.filter((item) => item.activo))
        setPositions(positionItems.filter((item) => item.activo))
      })
      .catch((reason: unknown) =>
        setErrors([{ hoja: 'catalogos', fila: 0, error: message(reason) }]),
      )
  }, [])

  function reset() {
    setDraft(null)
    setConfiguration(null)
    setValidated(false)
    setErrors([])
    setWarnings([])
    setSummary({})
    setNotice('')
    setPreview([])
  }

  async function download() {
    try {
      const blob = await downloadImportTemplate()
      const url = URL.createObjectURL(blob)
      const anchor = document.createElement('a')
      anchor.href = url
      anchor.download = 'plantilla_carga_masiva.xlsx'
      anchor.click()
      URL.revokeObjectURL(url)
    } catch (reason) {
      setErrors([{ hoja: 'descarga', fila: 0, error: message(reason) }])
    }
  }

  async function analyze() {
    if (!file) return
    setBusy(true)
    reset()
    try {
      const result = await analyzeProfileImport(file)
      setDraft(result)
      setConfiguration(result.configuration)
    } catch (reason) {
      setErrors([{ hoja: 'archivo', fila: 0, error: message(reason) }])
    } finally {
      setBusy(false)
    }
  }

  function updateConfiguration(
    change: (value: ProfileImportConfiguration) => void,
  ) {
    if (!configuration) return
    const next = structuredClone(configuration)
    change(next)
    setConfiguration(next)
    setValidated(false)
    setSummary({})
  }

  function toggleMachine(machine: CatalogItem) {
    updateConfiguration((next) => {
      const index = next.destinations.findIndex(
        (item) => item.machine_id === machine.id,
      )
      if (index >= 0) {
        next.destinations.splice(index, 1)
        return
      }
      const equipmentLabel =
        draft?.procedure_code === 'MP-PO-TS12-ASE-009'
          ? machine.nombre.toLocaleLowerCase().includes('edgar')
            ? 'CT1'
            : machine.nombre.toLocaleLowerCase().includes('exceltec')
              ? 'CT2'
              : null
          : null
      const rolePosition = (role: string) =>
        positions.find(
          (item) => item.maquina_id === machine.id && item.tipo_puesto === role,
        )?.id ?? null
      next.destinations.push({
        machine_id: machine.id,
        equipment_label: equipmentLabel,
        roles: {
          operador: {
            enabled: true,
            position_id: rolePosition('operador'),
            general_level: 3,
            safety_level: 3,
          },
          ayudante: {
            enabled: true,
            position_id: rolePosition('ayudante'),
            general_level: 2,
            safety_level: 3,
          },
        },
      })
    })
  }

  async function validateProfile() {
    if (!draft || !configuration) return
    setBusy(true)
    setNotice('')
    try {
      await configureProfileImport(draft.token, configuration)
      const result = await validateProfileDraft(draft.token)
      setErrors(result.errores)
      setWarnings(result.advertencias)
      setSummary(result.resumen)
      setPreview(result.detalle)
      setValidated(result.valido)
    } catch (reason) {
      setErrors([{ hoja: 'configuracion', fila: 0, error: message(reason) }])
    } finally {
      setBusy(false)
    }
  }

  async function publishProfile() {
    if (!draft || !validated) return
    setBusy(true)
    try {
      const result = await publishProfileDraft(draft.token)
      setSummary(result.resumen)
      setNotice('Matrices publicadas correctamente')
      setValidated(false)
    } catch (reason) {
      setErrors([{ hoja: 'publicacion', fila: 0, error: message(reason) }])
    } finally {
      setBusy(false)
    }
  }

  async function validateGeneric() {
    if (!file) return
    setBusy(true)
    try {
      const result = await validateImport(file)
      setErrors(result.errores)
      setWarnings(result.advertencias)
      setSummary(result.resumen)
      setValidated(result.valido)
    } catch (reason) {
      setErrors([{ hoja: 'archivo', fila: 0, error: message(reason) }])
    } finally {
      setBusy(false)
    }
  }

  async function publishGeneric() {
    if (!file || !validated) return
    setBusy(true)
    try {
      const result = await executeImport(file, skipExisting)
      setSummary(result.resumen)
      setNotice('Importación ejecutada correctamente')
      setValidated(false)
    } catch (reason) {
      setErrors([{ hoja: 'archivo', fila: 0, error: message(reason) }])
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="import-page">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Configuración</p>
          <h2>Carga masiva</h2>
        </div>
        <button className="secondary-action" onClick={() => void download()}>
          Descargar plantilla
        </button>
      </div>
      <p className="helper-text">
        Los perfiles operativos se analizan y configuran antes de publicar.
        Ninguna matriz cambia durante la revisión.
      </p>
      <section className="import-card">
        <label className="file-picker">
          Archivo Excel (.xlsx)
          <input
            type="file"
            accept=".xlsx"
            onChange={(event) => {
              setFile(event.target.files?.[0] ?? null)
              reset()
            }}
          />
        </label>
        <label className="import-option">
          <input
            type="checkbox"
            checked={genericMode}
            onChange={(event) => {
              setGenericMode(event.target.checked)
              reset()
            }}
          />{' '}
          Usar plantilla genérica de catálogos
        </label>
        {!draft && (
          <button
            className="primary-action"
            disabled={busy || !file}
            onClick={() => void (genericMode ? validateGeneric() : analyze())}
          >
            {genericMode ? 'Validar plantilla' : 'Analizar perfil'}{' '}
            <span>→</span>
          </button>
        )}
      </section>

      {draft && configuration && (
        <>
          <section className="import-card">
            <p className="eyebrow">Perfil detectado</p>
            <h3>{draft.title}</h3>
            <p>{draft.procedure_code}</p>
            <p className="helper-text">{draft.source}</p>
          </section>
          <section className="import-card">
            <h3>1. Máquinas destino</h3>
            <div className="competency-level-grid">
              {machines.map((machine) => {
                const selected = configuration.destinations.some(
                  (item) => item.machine_id === machine.id,
                )
                return (
                  <label className="check-option" key={machine.id}>
                    <input
                      type="checkbox"
                      checked={selected}
                      onChange={() => toggleMachine(machine)}
                    />{' '}
                    {machine.codigo} · {machine.nombre}
                  </label>
                )
              })}
            </div>
          </section>
          {configuration.destinations.map((destination) => {
            const machine = machines.find(
              (item) => item.id === destination.machine_id,
            )
            return (
              <section className="import-card" key={destination.machine_id}>
                <h3>2. Puestos · {machine?.nombre}</h3>
                <label>
                  Identificador documental
                  <input
                    value={destination.equipment_label ?? ''}
                    onChange={(event) =>
                      updateConfiguration((next) => {
                        const item = next.destinations.find(
                          (candidate) =>
                            candidate.machine_id === destination.machine_id,
                        )!
                        item.equipment_label = event.target.value || null
                      })
                    }
                  />
                </label>
                {Object.entries(destination.roles).map(([role, settings]) => (
                  <div className="form-line" key={role}>
                    <label className="check-option">
                      <input
                        type="checkbox"
                        checked={settings.enabled}
                        onChange={(event) =>
                          updateConfiguration((next) => {
                            next.destinations.find(
                              (item) =>
                                item.machine_id === destination.machine_id,
                            )!.roles[role].enabled = event.target.checked
                          })
                        }
                      />{' '}
                      {role}
                    </label>
                    <label>
                      Puesto
                      <select
                        value={settings.position_id ?? ''}
                        onChange={(event) =>
                          updateConfiguration((next) => {
                            next.destinations.find(
                              (item) =>
                                item.machine_id === destination.machine_id,
                            )!.roles[role].position_id = event.target.value
                              ? Number(event.target.value)
                              : null
                          })
                        }
                      >
                        <option value="">Crear o detectar automáticamente</option>
                        {positions
                          .filter(
                            (position) =>
                              position.tipo_puesto === role &&
                              (position.maquina_id === destination.machine_id ||
                                position.maquina_id == null),
                          )
                          .map((position) => (
                            <option key={position.id} value={position.id}>
                              {position.codigo} · {position.nombre}
                            </option>
                          ))}
                      </select>
                    </label>
                    <label>
                      Nivel general
                      <select
                        value={settings.general_level}
                        onChange={(event) =>
                          updateConfiguration((next) => {
                            next.destinations.find(
                              (item) =>
                                item.machine_id === destination.machine_id,
                            )!.roles[role].general_level = Number(
                              event.target.value,
                            )
                          })
                        }
                      >
                        {[0, 1, 2, 3, 4].map((level) => (
                          <option key={level}>{level}</option>
                        ))}
                      </select>
                    </label>
                    <label>
                      Seguridad
                      <select
                        value={settings.safety_level}
                        onChange={(event) =>
                          updateConfiguration((next) => {
                            next.destinations.find(
                              (item) =>
                                item.machine_id === destination.machine_id,
                            )!.roles[role].safety_level = Number(
                              event.target.value,
                            )
                          })
                        }
                      >
                        {[3, 4].map((level) => (
                          <option key={level}>{level}</option>
                        ))}
                      </select>
                    </label>
                  </div>
                ))}
              </section>
            )
          })}
          <section className="import-card">
            <h3>3. Actividades y criterios</h3>
            <p className="helper-text">
              Revise inclusión por rol, obligatoriedad, criticidad y
              macrocompetencias.
            </p>
            {draft.activities.map((activity) => (
              <details className="criteria-checklist" key={activity.source_key}>
                <summary>
                  <strong>
                    {activity.punto_procedimiento} · {activity.nombre}
                  </strong>{' '}
                  ({activity.criterios.length})
                </summary>
                <div className="form-line">
                  {['operador', 'ayudante'].map((role) => {
                    const included = configuration.activities[
                      activity.source_key
                    ].included_roles.includes(role)
                    return (
                      <label className="check-option" key={role}>
                        <input
                          type="checkbox"
                          checked={included}
                          onChange={(event) =>
                            updateConfiguration((next) => {
                              const roles =
                                next.activities[activity.source_key]
                                  .included_roles
                              next.activities[
                                activity.source_key
                              ].included_roles = event.target.checked
                                ? [...new Set([...roles, role])]
                                : roles.filter((item) => item !== role)
                            })
                          }
                        />{' '}
                        Actividad para {role}
                      </label>
                    )
                  })}
                </div>
                {activity.criterios.map((criterion) => {
                  const settings = configuration.criteria[criterion.source_key]
                  return (
                    <div className="criteria-item" key={criterion.source_key}>
                      <span>{criterion.descripcion}</span>
                      <div className="form-line">
                        {['operador', 'ayudante'].map((role) => (
                          <label className="check-option" key={role}>
                            <input
                              type="checkbox"
                              checked={settings.included_roles.includes(role)}
                              onChange={(event) =>
                                updateConfiguration((next) => {
                                  const roles =
                                    next.criteria[criterion.source_key]
                                      .included_roles
                                  next.criteria[
                                    criterion.source_key
                                  ].included_roles = event.target.checked
                                    ? [...new Set([...roles, role])]
                                    : roles.filter((item) => item !== role)
                                })
                              }
                            />{' '}
                            {role}
                          </label>
                        ))}
                        <label className="check-option">
                          <input
                            type="checkbox"
                            checked={settings.required}
                            onChange={(event) =>
                              updateConfiguration((next) => {
                                next.criteria[criterion.source_key].required =
                                  event.target.checked
                              })
                            }
                          />{' '}
                          Obligatorio
                        </label>
                        <label className="check-option">
                          <input
                            type="checkbox"
                            checked={settings.critical}
                            onChange={(event) =>
                              updateConfiguration((next) => {
                                next.criteria[criterion.source_key].critical =
                                  event.target.checked
                              })
                            }
                          />{' '}
                          Crítico
                        </label>
                      </div>
                      <div className="form-line">
                        {MACROS.map((macro) => (
                          <label className="check-option" key={macro}>
                            <input
                              type="checkbox"
                              checked={settings.macro_keys.includes(macro)}
                              onChange={(event) =>
                                updateConfiguration((next) => {
                                  const macros =
                                    next.criteria[criterion.source_key]
                                      .macro_keys
                                  next.criteria[
                                    criterion.source_key
                                  ].macro_keys = event.target.checked
                                    ? [...new Set([...macros, macro])]
                                    : macros.filter((item) => item !== macro)
                                })
                              }
                            />{' '}
                            {macro}
                          </label>
                        ))}
                      </div>
                    </div>
                  )
                })}
              </details>
            ))}
          </section>
          <div className="form-actions">
            <button
              className="secondary-action"
              disabled={busy || configuration.destinations.length === 0}
              onClick={() => void validateProfile()}
            >
              Guardar y validar
            </button>
            <button
              className="primary-action"
              disabled={busy || !validated}
              onClick={() => void publishProfile()}
            >
              Publicar matrices <span>→</span>
            </button>
          </div>
        </>
      )}

      {genericMode && !draft && validated && (
        <div className="form-actions">
          <label className="import-option">
            <input
              type="checkbox"
              checked={skipExisting}
              onChange={(event) => setSkipExisting(event.target.checked)}
            />{' '}
            Omitir existentes
          </label>
          <button
            className="primary-action"
            onClick={() => void publishGeneric()}
          >
            Publicar plantilla <span>→</span>
          </button>
        </div>
      )}
    {notice && <p className="success-message">{notice}</p>}
    {preview.length > 0 && <section className="import-summary"><h3>Impacto de publicación</h3>{preview.map((item) => <div className="import-summary-row" key={`${item.machine_id}-${item.role}`}><strong>{item.equipment_label ? `${item.equipment_label} · ` : ''}{item.machine}</strong><span>{item.role}</span><span>{item.position ?? 'Se creará el puesto'}</span><span>{item.action === 'sin_cambios' ? 'Sin cambios' : item.action === 'nueva_version' ? `Nueva versión (actual ${item.current_version})` : 'Crear matriz'}</span></div>)}</section>}
      {errors.length > 0 && <IssueList title="Errores" issues={errors} error />}
      {warnings.length > 0 && (
        <IssueList title="Advertencias" issues={warnings} />
      )}
      {Object.keys(summary).length > 0 && (
        <section className="import-summary">
          <h3>Vista previa</h3>
          {Object.entries(summary).map(([key, values]) => (
            <div className="import-summary-row" key={key}>
              <strong>{key}</strong>
              <span>Nuevos: {values.nuevos ?? values.creados ?? 0}</span>
              <span>
                Actualizar: {values.actualizar ?? values.actualizados ?? 0}
              </span>
              <span>Omitir: {values.omitir ?? values.omitidos ?? 0}</span>
            </div>
          ))}
        </section>
      )}
    </div>
  )
}

function IssueList({
  title,
  issues,
  error = false,
}: {
  title: string
  issues: ImportIssue[]
  error?: boolean
}) {
  return (
    <section className={error ? 'import-issues error-list' : 'import-issues'}>
      <h3>
        {title} ({issues.length})
      </h3>
      {issues.slice(0, 100).map((issue, index) => (
        <p key={`${issue.hoja}-${issue.fila}-${index}`}>
          <strong>
            {issue.hoja}:{issue.fila}
          </strong>{' '}
          {issue.error ?? issue.advertencia}
        </p>
      ))}
    </section>
  )
}

function message(reason: unknown) {
  return reason instanceof Error
    ? reason.message
    : 'No se pudo completar la operación'
}

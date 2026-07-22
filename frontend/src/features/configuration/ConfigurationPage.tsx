import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import {
  deactivateCatalog,
  addPositionRequirement,
  activateCatalog,
  activatePerson,
  createCompleteWorker,
  assignPositionActivity,
  assignPositionMachine,
  assignMachineProcess,
  listCatalog,
  listPeople,
  listWorkers,
  listPermissions,
  listUsers,
  saveCatalog,
  savePermission,
  savePerson,
  deactivatePerson,
  linkPersonUser,
  type CatalogItem,
  type PermissionItem,
  type PersonItem,
  type UserItem,
} from '../../lib/api'
import { WorkerManagementPage } from './WorkerManagementPage'
import { MachineManagementPage, PositionManagementPage, ProcessManagementPage } from './StructureManagementPage'
import { RolesManagementPage, UsersManagementPage } from './SecurityManagementPage'
import { ImportPage } from './ImportPage'

type ConfigKey =
  | 'areas' | 'cargos' | 'turnos' | 'actividades' | 'competencias' | 'maquinas' | 'procesos'
  | 'puestos' | 'supervisores' | 'evaluadores' | 'usuarios' | 'roles' | 'permisos'
   | 'requisitos' | 'trabajadores' | 'carga'

const catalogConfig: Record<string, { label: string; path: string; code?: boolean }> = {
  areas: { label: 'Áreas', path: 'areas' },
  cargos: { label: 'Cargos', path: 'cargos' },
  turnos: { label: 'Turnos', path: 'turnos' },
  actividades: { label: 'Actividades', path: 'actividades' },
  competencias: { label: 'Competencias', path: 'competencias', code: true },
  maquinas: { label: 'Máquinas', path: 'maquinas', code: true },
}

export function ConfigurationPage() {
  const [active, setActive] = useState<ConfigKey>('areas')
  const item = catalogConfig[active]
  const catalogKeys: ConfigKey[] = ['areas', 'procesos', 'maquinas', 'puestos', 'actividades', 'competencias', 'requisitos', 'turnos', 'cargos']

  return (
    <div className="config-grid">
      <section className="config-nav">
        <p className="eyebrow">Catálogos</p>
        {catalogKeys.map((key) => <ConfigNavButton key={key} active={active === key} onClick={() => setActive(key)}>{key === 'procesos' ? 'Procesos' : key === 'maquinas' ? 'Máquinas' : key === 'puestos' ? 'Puestos' : key === 'requisitos' ? 'Competencias por puesto' : catalogConfig[key].label}</ConfigNavButton>)}
        <p className="eyebrow security-label">Personal</p>
        <ConfigNavButton active={active === 'trabajadores'} onClick={() => setActive('trabajadores')}>Trabajadores</ConfigNavButton>
        <p className="eyebrow security-label">Personas autorizadas</p>
        <ConfigNavButton active={active === 'supervisores'} onClick={() => setActive('supervisores')}>Supervisores</ConfigNavButton>
        <ConfigNavButton active={active === 'evaluadores'} onClick={() => setActive('evaluadores')}>Evaluadores</ConfigNavButton>
        <p className="eyebrow security-label">Seguridad</p>
        <ConfigNavButton active={active === 'usuarios'} onClick={() => setActive('usuarios')}>Usuarios</ConfigNavButton>
        <ConfigNavButton active={active === 'roles'} onClick={() => setActive('roles')}>Roles</ConfigNavButton>
        <ConfigNavButton active={active === 'permisos'} onClick={() => setActive('permisos')}>Permisos</ConfigNavButton>
        <ConfigNavButton active={active === 'carga'} onClick={() => setActive('carga')}>Carga masiva</ConfigNavButton>
      </section>
      <section className="config-panel">
        {active === ('__legacy__' as ConfigKey) && <><WorkerConfigurationPage /><ProcessesPage /><MachinesPage /><PositionsPage /></>}
        {item && !['maquinas', 'procesos', 'puestos', 'requisitos'].includes(active) && <CatalogPage key={active} config={item} />}
        {active === 'procesos' && <ProcessManagementPage />}
        {active === 'maquinas' && <MachineManagementPage />}
        {active === 'puestos' && <PositionManagementPage />}
        {active === 'requisitos' && <RequirementsPage />}
        {active === 'trabajadores' && <WorkerManagementPage />}
        {(active === 'supervisores' || active === 'evaluadores') && <PeoplePage type={active} />}
        {active === 'usuarios' && <UsersManagementPage />}
        {active === 'roles' && <RolesManagementPage />}
        {active === 'permisos' && <PermissionsPage />}
        {active === 'carga' && <ImportPage />}
      </section>
    </div>
  )
}

function ConfigNavButton({ active, onClick, children }: { active: boolean; onClick: () => void; children: string }) {
  return <button className={active ? 'config-link active' : 'config-link'} onClick={onClick}>{children}</button>
}

function PanelHeading({ eyebrow, title, count }: { eyebrow: string; title: string; count: number }) {
  return <div className="panel-heading"><div><p className="eyebrow">{eyebrow}</p><h2>{title}</h2></div><span>{count} registros</span></div>
}

function CatalogPage({ config }: { config: { label: string; path: string; code?: boolean } }) {
  const [items, setItems] = useState<CatalogItem[]>([])
  const [editing, setEditing] = useState<CatalogItem | null>(null)
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [error, setError] = useState('')

  async function load() { try { setItems(await listCatalog(config.path)) } catch (reason) { setError(message(reason)) } }
  useEffect(() => {
    void listCatalog(config.path).then(setItems).catch((reason: unknown) => setError(message(reason)))
  }, [config.path])

  function edit(item: CatalogItem) { setEditing(item); setName(item.nombre); setDescription(item.descripcion ?? '') }
  function reset() { setEditing(null); setName(''); setDescription('') }
  async function submit(event: FormEvent) {
    event.preventDefault();
    try {
      await saveCatalog(config.path, { ...(editing?.codigo ? { codigo: editing.codigo } : {}), nombre: name, descripcion: description }, editing?.id);
      reset(); await load(); setError('')
    } catch (reason) { setError(message(reason)) }
  }
  async function disable(id: number) { if (!window.confirm('¿Desactivar este registro?')) return; try { await deactivateCatalog(config.path, id); await load() } catch (reason) { setError(message(reason)) } }
  async function activate(id: number) { try { await activateCatalog(config.path, id); await load() } catch (reason) { setError(message(reason)) } }

  return <><PanelHeading eyebrow="Catálogo editable" title={config.label} count={items.length} /><form className="inline-form config-form" onSubmit={submit}><input required placeholder={`Nombre de ${config.label.toLowerCase()}`} value={name} onChange={(event) => setName(event.target.value)} /><input placeholder="Descripción" value={description} onChange={(event) => setDescription(event.target.value)} /><button className="primary-action">{editing ? 'Guardar' : 'Agregar'} <span>+</span></button>{editing && <button type="button" className="secondary-action" onClick={reset}>Cancelar</button>}</form>{error && <p className="form-error">{error}</p>}<div className="data-table"><div className="table-row table-header"><span>{config.code ? 'Código / nombre' : 'Nombre'}</span><span>Descripción</span><span>Acciones</span></div>{items.map((item) => <div className="table-row" key={item.id}><strong>{config.code ? `${item.codigo ?? 'AUTO'} · ${item.nombre}` : item.nombre}</strong><span>{item.descripcion || 'Sin descripción'}</span><span className="row-actions"><button onClick={() => edit(item)}>Editar</button>{item.activo ? <button onClick={() => disable(item.id)}>Desactivar</button> : <button onClick={() => activate(item.id)}>Activar</button>}</span></div>)}{items.length === 0 && <div className="table-empty">No hay registros cargados.</div>}</div></>
}

function PositionsPage() {
  const [items, setItems] = useState<CatalogItem[]>([])
  const [areas, setAreas] = useState<CatalogItem[]>([])
  const [cargos, setCargos] = useState<CatalogItem[]>([])
  const [machines, setMachines] = useState<CatalogItem[]>([])
  const [processes, setProcesses] = useState<CatalogItem[]>([])
  const [form, setForm] = useState({ nombre: '', descripcion: '', area_id: '', cargo_id: '', process_id: '', machine_id: '' })
  const [error, setError] = useState('')
  async function load() { try { setItems(await listCatalog('puestos')); setAreas(await listCatalog('areas')); setCargos(await listCatalog('cargos')) } catch (reason) { setError(message(reason)) } }
  useEffect(() => {
    void Promise.all([listCatalog('puestos'), listCatalog('areas'), listCatalog('cargos'), listCatalog('maquinas'), listCatalog('procesos')])
      .then(([positions, areaItems, cargoItems, machineItems, processItems]) => { setItems(positions); setAreas(areaItems); setCargos(cargoItems); setMachines(machineItems); setProcesses(processItems) })
      .catch((reason: unknown) => setError(message(reason)))
  }, [])
  async function submit(event: FormEvent) { event.preventDefault(); try { const position = await saveCatalog('puestos', { nombre: form.nombre, descripcion: form.descripcion, area_id: Number(form.area_id), cargo_id: Number(form.cargo_id), proceso_id: Number(form.process_id), maquina_id: form.machine_id ? Number(form.machine_id) : null, tipo_puesto: form.machine_id ? 'operador' : 'manual' }); if (form.machine_id) await assignPositionMachine(position.id, Number(form.machine_id)); setForm({ nombre: '', descripcion: '', area_id: '', cargo_id: '', process_id: '', machine_id: '' }); await load() } catch (reason) { setError(message(reason)) } }
  return <><PanelHeading eyebrow="Estructura operativa" title="Puestos" count={items.length} /><p className="helper-text">Cada puesto pertenece a un proceso. La máquina es opcional para procesos manuales.</p><form className="stack-form" onSubmit={submit}><input required placeholder="Nombre del puesto" value={form.nombre} onChange={(event) => setForm({ ...form, nombre: event.target.value })} /><div className="form-line"><select required value={form.process_id} onChange={(event) => setForm({ ...form, process_id: event.target.value })}><option value="">Seleccione proceso</option>{processes.map((item) => <option key={item.id} value={item.id}>{item.codigo} · {item.nombre}</option>)}</select><select required value={form.area_id} onChange={(event) => setForm({ ...form, area_id: event.target.value })}><option value="">Seleccione área</option>{areas.map((item) => <option key={item.id} value={item.id}>{item.nombre}</option>)}</select></div><div className="form-line"><select required value={form.cargo_id} onChange={(event) => setForm({ ...form, cargo_id: event.target.value })}><option value="">Seleccione cargo</option>{cargos.map((item) => <option key={item.id} value={item.id}>{item.nombre}</option>)}</select><select value={form.machine_id} onChange={(event) => setForm({ ...form, machine_id: event.target.value })}><option value="">Sin máquina (manual)</option>{machines.map((item) => <option key={item.id} value={item.id}>{item.codigo} · {item.nombre}</option>)}</select></div><input placeholder="Descripción" value={form.descripcion} onChange={(event) => setForm({ ...form, descripcion: event.target.value })} /><button className="primary-action">Agregar puesto <span>+</span></button></form>{error && <p className="form-error">{error}</p>}<div className="data-table">{items.map((item) => <div className="table-row" key={item.id}><strong>{item.codigo ?? 'AUTO'} · {item.nombre}</strong><span>{item.descripcion || 'Sin descripción'}</span><span className="status-pill">Activo</span></div>)}</div></>
}

function ProcessesPage() {
  const [items, setItems] = useState<CatalogItem[]>([]); const [areas, setAreas] = useState<CatalogItem[]>([]); const [form, setForm] = useState({ nombre: '', descripcion: '', area_id: '' }); const [error, setError] = useState('')
  async function load() { try { setItems(await listCatalog('procesos')); setAreas(await listCatalog('areas')) } catch (reason) { setError(message(reason)) } }
  useEffect(() => { void Promise.all([listCatalog('procesos'), listCatalog('areas')]).then(([processItems, areaItems]) => { setItems(processItems); setAreas(areaItems) }).catch((reason: unknown) => setError(message(reason))) }, [])
  async function submit(event: FormEvent) { event.preventDefault(); try { await saveCatalog('procesos', { ...form, area_id: Number(form.area_id) }); setForm({ nombre: '', descripcion: '', area_id: '' }); await load() } catch (reason) { setError(message(reason)) } }
  return <><PanelHeading eyebrow="Estructura" title="Procesos" count={items.length} /><p className="helper-text">Cada proceso pertenece a un área y organiza máquinas y puestos.</p><form className="stack-form" onSubmit={submit}><input required placeholder="Nombre del proceso" value={form.nombre} onChange={(event) => setForm({ ...form, nombre: event.target.value })} /><select required value={form.area_id} onChange={(event) => setForm({ ...form, area_id: event.target.value })}><option value="">Seleccione área</option>{areas.map((area) => <option key={area.id} value={area.id}>{area.nombre}</option>)}</select><input placeholder="Descripción" value={form.descripcion} onChange={(event) => setForm({ ...form, descripcion: event.target.value })} /><button className="primary-action">Agregar proceso <span>+</span></button></form>{error && <p className="form-error">{error}</p>}<div className="data-table">{items.map((item) => <div className="table-row" key={item.id}><strong>{item.codigo ?? 'AUTO'} · {item.nombre}</strong><span>{item.descripcion || 'Sin descripción'}</span><span className="status-pill">Activo</span></div>)}</div></>
}

function MachinesPage() {
  const [items, setItems] = useState<CatalogItem[]>([]); const [processes, setProcesses] = useState<CatalogItem[]>([]); const [form, setForm] = useState({ nombre: '', descripcion: '', process_id: '' }); const [error, setError] = useState('')
  async function load() { try { setItems(await listCatalog('maquinas')); setProcesses(await listCatalog('procesos')) } catch (reason) { setError(message(reason)) } }
  useEffect(() => { void Promise.all([listCatalog('maquinas'), listCatalog('procesos')]).then(([machineItems, processItems]) => { setItems(machineItems); setProcesses(processItems) }).catch((reason: unknown) => setError(message(reason))) }, [])
  async function submit(event: FormEvent) { event.preventDefault(); try { const machine = await saveCatalog('maquinas', { nombre: form.nombre, descripcion: form.descripcion }); if (form.process_id) await assignMachineProcess(machine.id, Number(form.process_id)); setForm({ nombre: '', descripcion: '', process_id: '' }); await load() } catch (reason) { setError(message(reason)) } }
  return <><PanelHeading eyebrow="Estructura" title="Máquinas por proceso" count={items.length} /><form className="stack-form" onSubmit={submit}><input required placeholder="Nombre de máquina" value={form.nombre} onChange={(event) => setForm({ ...form, nombre: event.target.value })} /><select required value={form.process_id} onChange={(event) => setForm({ ...form, process_id: event.target.value })}><option value="">Seleccione proceso</option>{processes.map((item) => <option key={item.id} value={item.id}>{item.codigo} · {item.nombre}</option>)}</select><input placeholder="Descripción" value={form.descripcion} onChange={(event) => setForm({ ...form, descripcion: event.target.value })} /><button className="primary-action">Agregar máquina <span>+</span></button></form>{error && <p className="form-error">{error}</p>}<div className="data-table">{items.map((item) => <div className="table-row" key={item.id}><strong>{item.codigo ?? 'AUTO'} · {item.nombre}</strong><span>{item.descripcion || 'Sin descripción'}</span><span className="status-pill">Activa</span></div>)}</div></>
}

function RequirementsPage() {
  const [positions, setPositions] = useState<CatalogItem[]>([])
  const [activities, setActivities] = useState<CatalogItem[]>([])
  const [competencies, setCompetencies] = useState<CatalogItem[]>([])
  const [form, setForm] = useState({ positionId: '', activityId: '', competencyId: '', minimum: '3' })
  const [messageText, setMessageText] = useState('')
  const [error, setError] = useState('')
  useEffect(() => {
    void Promise.all([listCatalog('puestos'), listCatalog('actividades'), listCatalog('competencias')])
      .then(([positionItems, activityItems, competencyItems]) => { setPositions(positionItems); setActivities(activityItems); setCompetencies(competencyItems) })
      .catch((reason: unknown) => setError(message(reason)))
  }, [])
  async function submit(event: FormEvent) {
    event.preventDefault(); setMessageText(''); setError('')
    try {
      await assignPositionActivity(Number(form.positionId), Number(form.activityId))
    } catch (reason) {
      if (!message(reason).toLowerCase().includes('único') && !message(reason).toLowerCase().includes('unique')) { setError(message(reason)); return }
    }
    try {
      await addPositionRequirement(Number(form.positionId), { actividad_id: Number(form.activityId), competencia_id: Number(form.competencyId), nivel_minimo: Number(form.minimum) })
      setMessageText('Requisito guardado correctamente')
      setForm({ ...form, competencyId: '' })
    } catch (reason) { setError(message(reason)) }
  }
  return <><PanelHeading eyebrow="Matriz de competencias" title="Competencias por puesto" count={competencies.length} /><p className="helper-text">Defina qué competencia requiere cada actividad y el nivel mínimo de aprobación entre 1 y 5.</p><form className="stack-form" onSubmit={submit}><select required value={form.positionId} onChange={(event) => setForm({ ...form, positionId: event.target.value })}><option value="">Seleccione puesto</option>{positions.map((item) => <option key={item.id} value={item.id}>{item.codigo} · {item.nombre}</option>)}</select><select required value={form.activityId} onChange={(event) => setForm({ ...form, activityId: event.target.value })}><option value="">Seleccione actividad</option>{activities.map((item) => <option key={item.id} value={item.id}>{item.nombre}</option>)}</select><div className="form-line"><select required value={form.competencyId} onChange={(event) => setForm({ ...form, competencyId: event.target.value })}><option value="">Seleccione competencia</option>{competencies.map((item) => <option key={item.id} value={item.id}>{item.codigo ? `${item.codigo} · ` : ''}{item.nombre}</option>)}</select><select value={form.minimum} onChange={(event) => setForm({ ...form, minimum: event.target.value })}>{[1, 2, 3, 4, 5].map((level) => <option key={level} value={level}>Nivel mínimo: {level}</option>)}</select></div><button className="primary-action">Guardar requisito <span>+</span></button></form>{messageText && <p className="success-message">{messageText}</p>}{error && <p className="form-error">{error}</p>}</>
}

async function fetchPeopleData(type: 'supervisores' | 'evaluadores') {
  return Promise.all([listPeople(type), listUsers()])
}

function PeoplePage({ type }: { type: 'supervisores' | 'evaluadores' }) {
  const [items, setItems] = useState<PersonItem[]>([])
  const [users, setUsers] = useState<UserItem[]>([])
  const [editing, setEditing] = useState<PersonItem | null>(null)
  const [form, setForm] = useState({ documento: '', nombres: '', apellidos: '', correo: '', usuario_id: '' })
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  async function load() {
    try { const [people, accounts] = await fetchPeopleData(type); setItems(people); setUsers(accounts) }
    catch (reason) { setError(message(reason)) }
  }
  useEffect(() => { void fetchPeopleData(type).then(([people, accounts]) => { setItems(people); setUsers(accounts) }).catch((reason: unknown) => setError(message(reason))) }, [type])
  function reset() { setEditing(null); setForm({ documento: '', nombres: '', apellidos: '', correo: '', usuario_id: '' }); setError('') }
  function edit(item: PersonItem) {
    setEditing(item); setForm({ documento: item.documento, nombres: item.nombres, apellidos: item.apellidos, correo: item.correo ?? '', usuario_id: String(item.usuario_id ?? '') }); setError(''); setNotice('')
  }
  async function submit(event: FormEvent) {
    event.preventDefault(); setError(''); setNotice('')
    try {
      const { usuario_id, ...personData } = form
      const saved = await savePerson(type, personData, editing?.id)
      if (usuario_id && Number(usuario_id) !== editing?.usuario_id) await linkPersonUser(type, saved.id, Number(usuario_id))
      setNotice(editing ? 'Registro actualizado correctamente' : 'Registro creado correctamente'); reset(); await load()
    } catch (reason) { setError(message(reason)) }
  }
  async function toggle(item: PersonItem) {
    try {
      if (item.activo) { if (!window.confirm(`¿Desactivar este ${type === 'evaluadores' ? 'evaluador' : 'supervisor'}?`)) return; await deactivatePerson(type, item.id) }
      else await activatePerson(type, item.id)
      await load()
    } catch (reason) { setError(message(reason)) }
  }
  const label = type === 'supervisores' ? 'Supervisores' : 'Evaluadores'
  return <><PanelHeading eyebrow="Personas autorizadas" title={label} count={items.length} /><p className="helper-text">Registre, edite y vincule el usuario que podrá realizar evaluaciones.</p>{notice && <p className="success-message">{notice}</p>}{error && <p className="form-error">{error}</p>}<form className="stack-form" onSubmit={submit}><div className="editing-banner">{editing ? <>Editando: <strong>{editing.codigo} · {editing.nombres} {editing.apellidos}</strong></> : `Nuevo ${type === 'evaluadores' ? 'evaluador' : 'supervisor'}`}</div><div className="form-line"><input required placeholder="Documento" value={form.documento} onChange={(event) => setForm({ ...form, documento: event.target.value })} /><input required placeholder="Nombres" value={form.nombres} onChange={(event) => setForm({ ...form, nombres: event.target.value })} /></div><div className="form-line"><input required placeholder="Apellidos" value={form.apellidos} onChange={(event) => setForm({ ...form, apellidos: event.target.value })} /><input type="email" placeholder="Correo" value={form.correo} onChange={(event) => setForm({ ...form, correo: event.target.value })} /></div><select value={form.usuario_id} disabled={Boolean(editing?.usuario_id)} onChange={(event) => setForm({ ...form, usuario_id: event.target.value })}><option value="">{editing?.usuario_id ? 'Usuario vinculado' : 'Vincular usuario'}</option>{users.filter((user) => user.activo).map((user) => <option key={user.id} value={user.id}>{user.username} · {user.nombre_completo}</option>)}</select><div className="form-actions"><button className="primary-action">{editing ? 'Guardar cambios' : `Agregar ${type === 'evaluadores' ? 'evaluador' : 'supervisor'}`} <span>{editing ? '→' : '+'}</span></button>{editing && <button type="button" className="secondary-action" onClick={reset}>Cancelar</button>}</div></form><div className="data-table">{items.map((item) => <div className="table-row" key={item.id}><strong>{item.codigo ?? 'AUTO'} · {item.nombres} {item.apellidos}</strong><span>{item.documento} · {item.correo || 'Sin correo'}</span><span className="status-pill">{item.activo ? 'Activo' : 'Inactivo'} · {item.usuario_id ? 'Con usuario' : 'Sin usuario'}</span><span className="row-actions"><button onClick={() => edit(item)}>Editar</button><button onClick={() => void toggle(item)}>{item.activo ? 'Desactivar' : 'Activar'}</button></span></div>)}</div></>
}

function PermissionsPage() {
  const [items, setItems] = useState<PermissionItem[]>([])
  const [form, setForm] = useState({ codigo: '', nombre: '', modulo: '', accion: '' })
  const [error, setError] = useState('')
  async function load() { try { setItems(await listPermissions()) } catch (reason) { setError(message(reason)) } }
  useEffect(() => { void load() }, [])
  async function submit(event: FormEvent) { event.preventDefault(); try { await savePermission(form); setForm({ codigo: '', nombre: '', modulo: '', accion: '' }); await load() } catch (reason) { setError(message(reason)) } }
  return <><PanelHeading eyebrow="Seguridad" title="Permisos" count={items.length} /><p className="helper-text">Los permisos del sistema se conservan como predefinidos. Aquí también puede crear permisos personalizados.</p><form className="stack-form" onSubmit={submit}><div className="form-line"><input required placeholder="Código: modulo.accion" value={form.codigo} onChange={(event) => setForm({ ...form, codigo: event.target.value })} /><input required placeholder="Nombre" value={form.nombre} onChange={(event) => setForm({ ...form, nombre: event.target.value })} /></div><div className="form-line"><input required placeholder="Módulo" value={form.modulo} onChange={(event) => setForm({ ...form, modulo: event.target.value })} /><input required placeholder="Acción" value={form.accion} onChange={(event) => setForm({ ...form, accion: event.target.value })} /></div><button className="primary-action">Crear permiso <span>+</span></button></form>{error && <p className="form-error">{error}</p>}<div className="data-table">{items.map((permission) => <div className="table-row" key={permission.id}><strong>{permission.codigo}</strong><span>{permission.nombre}</span><span className="status-pill">{permission.sistema ? 'Predefinido' : 'Personalizado'}</span></div>)}</div></>
}

function WorkerConfigurationPage() {
  const [areas, setAreas] = useState<CatalogItem[]>([])
  const [cargos, setCargos] = useState<CatalogItem[]>([])
  const [turnos, setTurnos] = useState<CatalogItem[]>([])
  const [supervisors, setSupervisors] = useState<PersonItem[]>([])
  const [positions, setPositions] = useState<CatalogItem[]>([])
  const [selectedPositions, setSelectedPositions] = useState<string[]>([])
  const [positionToAdd, setPositionToAdd] = useState('')
  const [workerCount, setWorkerCount] = useState(0)
  const [form, setForm] = useState({ documento: '', nombres: '', apellidos: '', cargo_id: '', area_id: '', turno_id: '', supervisor_id: '', fecha_inicio: new Date().toISOString().slice(0, 10) })
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')

  useEffect(() => {
    void Promise.all([listCatalog('areas'), listCatalog('cargos'), listCatalog('turnos'), listCatalog('puestos'), listPeople('supervisores'), listWorkers()])
      .then(([areaItems, cargoItems, shiftItems, positionItems, supervisorItems, workerItems]) => { setAreas(areaItems); setCargos(cargoItems); setTurnos(shiftItems); setPositions(positionItems); setSupervisors(supervisorItems); setWorkerCount(workerItems.length) })
      .catch((reason: unknown) => setError(message(reason)))
  }, [])

  function addPosition() {
    if (positionToAdd && !selectedPositions.includes(positionToAdd)) {
      setSelectedPositions((current) => [...current, positionToAdd])
      setPositionToAdd('')
    }
  }

  async function submit(event: FormEvent) {
    event.preventDefault(); setError(''); setNotice('')
    try {
      await createCompleteWorker({ ...form, cargo_id: Number(form.cargo_id), area_id: Number(form.area_id), turno_id: Number(form.turno_id), supervisor_id: Number(form.supervisor_id), puesto_ids: selectedPositions.map(Number) })
      setForm({ documento: '', nombres: '', apellidos: '', cargo_id: '', area_id: '', turno_id: '', supervisor_id: '', fecha_inicio: new Date().toISOString().slice(0, 10) }); setSelectedPositions([]); setNotice('Trabajador y asignaciones guardados correctamente')
    } catch (reason) { setError(message(reason)) }
  }

  return <><PanelHeading eyebrow="Personal" title="Registro de trabajadores" count={workerCount} /><p className="helper-text">El trabajador se crea junto con cargo, área, turno, supervisor y todos los puestos seleccionados.</p><form className="stack-form" onSubmit={submit}><div className="form-line"><input required placeholder="Documento" value={form.documento} onChange={(event) => setForm({ ...form, documento: event.target.value })} /><input required placeholder="Nombres" value={form.nombres} onChange={(event) => setForm({ ...form, nombres: event.target.value })} /></div><div className="form-line"><input required placeholder="Apellidos" value={form.apellidos} onChange={(event) => setForm({ ...form, apellidos: event.target.value })} /><input required type="date" value={form.fecha_inicio} onChange={(event) => setForm({ ...form, fecha_inicio: event.target.value })} /></div><div className="form-line"><select required value={form.cargo_id} onChange={(event) => setForm({ ...form, cargo_id: event.target.value })}><option value="">Cargo</option>{cargos.map((item) => <option key={item.id} value={item.id}>{item.nombre}</option>)}</select><select required value={form.area_id} onChange={(event) => setForm({ ...form, area_id: event.target.value })}><option value="">Área</option>{areas.map((item) => <option key={item.id} value={item.id}>{item.nombre}</option>)}</select></div><div className="form-line"><select required value={form.turno_id} onChange={(event) => setForm({ ...form, turno_id: event.target.value })}><option value="">Turno</option>{turnos.map((item) => <option key={item.id} value={item.id}>{item.nombre}</option>)}</select><select required value={form.supervisor_id} onChange={(event) => setForm({ ...form, supervisor_id: event.target.value })}><option value="">Supervisor</option>{supervisors.map((item) => <option key={item.id} value={item.id}>{item.nombres} {item.apellidos}</option>)}</select></div><div className="position-picker"><div className="position-picker-heading"><strong>Puestos de trabajo</strong><div className="position-add-control"><select value={positionToAdd} onChange={(event) => setPositionToAdd(event.target.value)}><option value="">Seleccione un puesto</option>{positions.filter((item) => !selectedPositions.includes(String(item.id))).map((item) => <option key={item.id} value={item.id}>{item.codigo ?? 'AUTO'} · {item.nombre}</option>)}</select><button type="button" onClick={addPosition} disabled={!positionToAdd}>+ Agregar puesto</button></div></div>{selectedPositions.map((id) => <div className="selected-position" key={id}><span>{positions.find((item) => String(item.id) === id)?.codigo ?? 'AUTO'} · {positions.find((item) => String(item.id) === id)?.nombre}</span><button type="button" onClick={() => setSelectedPositions((current) => current.filter((value) => value !== id))}>Quitar</button></div>)}{!selectedPositions.length && <p>No hay puestos seleccionados.</p>}</div><button className="primary-action" disabled={!selectedPositions.length}>Guardar trabajador <span>→</span></button></form>{notice && <p className="success-message">{notice}</p>}{error && <p className="form-error">{error}</p>}</>
}

function message(reason: unknown) { return reason instanceof Error ? reason.message : 'No se pudo completar la operación' }

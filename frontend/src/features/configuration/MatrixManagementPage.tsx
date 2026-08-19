import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import {
  addPositionRequirement,
  assignPositionActivity,
  createActivityCriterion,
  deletePositionRequirement,
  listActivityCriteria,
  listCatalog,
  getPositionChecklist,
  updateActivityCriterion,
  updatePositionRequirement,
  type ActivityCriterion,
  type CatalogItem,
  type ChecklistActivity,
} from "../../lib/api";

export function MatrixManagementPage() {
  const [positions, setPositions] = useState<CatalogItem[]>([]);
  const [activities, setActivities] = useState<CatalogItem[]>([]);
  const [competencies, setCompetencies] = useState<CatalogItem[]>([]);
  const [selectedPosition, setSelectedPosition] = useState("");
  const [checklist, setChecklist] = useState<ChecklistActivity[]>([]);
  const [form, setForm] = useState({
    activityId: "",
    competencyId: "",
    minimum: "3",
  });
  const [criterionActivity, setCriterionActivity] = useState("");
  const [criteria, setCriteria] = useState<ActivityCriterion[]>([]);
  const [criterionForm, setCriterionForm] = useState({
    descripcion: "",
    referencia: "",
    orden: "0",
    critico: false,
  });
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  useEffect(() => {
    void Promise.all([
      listCatalog("puestos"),
      listCatalog("actividades"),
      listCatalog("competencias"),
    ])
      .then(([positionItems, activityItems, competencyItems]) => {
        setPositions(positionItems);
        setActivities(activityItems);
        setCompetencies(competencyItems);
      })
      .catch((reason: unknown) => setError(message(reason)));
  }, []);
  useEffect(() => {
    if (selectedPosition) void loadMatrix(Number(selectedPosition));
    else setChecklist([]);
  }, [selectedPosition]);
  useEffect(() => {
    if (criterionActivity) void loadCriteria(Number(criterionActivity));
    else setCriteria([]);
  }, [criterionActivity]);

  async function loadMatrix(positionId: number) {
    try {
      const result = await getPositionChecklist(positionId);
      setChecklist(result.actividades);
    } catch (reason) {
      setError(message(reason));
    }
  }
  async function loadCriteria(activityId: number) {
    try {
      setCriteria(await listActivityCriteria(activityId));
    } catch (reason) {
      setError(message(reason));
    }
  }
  async function saveRequirement(event: FormEvent) {
    event.preventDefault();
    setError("");
    setNotice("");
    try {
      await assignPositionActivity(
        Number(selectedPosition),
        Number(form.activityId),
      );
    } catch (reason) {
      if (
        !message(reason).toLowerCase().includes("único") &&
        !message(reason).toLowerCase().includes("unique")
      ) {
        setError(message(reason));
        return;
      }
    }
    try {
      await addPositionRequirement(Number(selectedPosition), {
        actividad_id: Number(form.activityId),
        competencia_id: Number(form.competencyId),
        nivel_minimo: Number(form.minimum),
      });
      setNotice("Competencia asociada correctamente");
      setForm({ ...form, competencyId: "" });
      await loadMatrix(Number(selectedPosition));
    } catch (reason) {
      setError(message(reason));
    }
  }
  async function saveLevel(id: number, value: string) {
    try {
      await updatePositionRequirement(id, Number(value));
      setNotice("Nivel mínimo actualizado");
      await loadMatrix(Number(selectedPosition));
    } catch (reason) {
      setError(message(reason));
    }
  }
  async function removeRequirement(id: number) {
    if (!window.confirm("¿Eliminar esta competencia del puesto?")) return;
    try {
      await deletePositionRequirement(id);
      await loadMatrix(Number(selectedPosition));
    } catch (reason) {
      setError(message(reason));
    }
  }
  async function saveCriterion(event: FormEvent) {
    event.preventDefault();
    if (!criterionActivity) return;
    try {
      await createActivityCriterion(Number(criterionActivity), {
        ...criterionForm,
        orden: Number(criterionForm.orden),
      });
      setCriterionForm({
        descripcion: "",
        referencia: "",
        orden: "0",
        critico: false,
      });
      await loadCriteria(Number(criterionActivity));
      setNotice("Criterio agregado correctamente");
    } catch (reason) {
      setError(message(reason));
    }
  }
  async function editCriterion(criterion: ActivityCriterion) {
    const description = window.prompt(
      "Descripción del criterio",
      criterion.descripcion,
    );
    if (description === null || !description.trim()) return;
    try {
      await updateActivityCriterion(criterion.actividad_id, criterion.id, {
        descripcion: description,
      });
      await loadCriteria(criterion.actividad_id);
    } catch (reason) {
      setError(message(reason));
    }
  }

  return (
    <>
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Matriz de competencias</p>
          <h2>Competencias por puesto</h2>
        </div>
        <span>{checklist.length} actividades</span>
      </div>
      <p className="helper-text">
        Administre la estructura Puesto → Actividad → Criterios → Competencias
        sin perder la carga masiva existente.
      </p>
      {error && <p className="form-error">{error}</p>}
      {notice && <p className="success-message">{notice}</p>}
      <div className="matrix-toolbar">
        <select
          required
          value={selectedPosition}
          onChange={(event) => setSelectedPosition(event.target.value)}
        >
          <option value="">Seleccione puesto</option>
          {positions.map((item) => (
            <option key={item.id} value={item.id}>
              {item.codigo} · {item.nombre}
            </option>
          ))}
        </select>
      </div>
      {selectedPosition && (
        <>
          <form
            className="stack-form matrix-add-form"
            onSubmit={saveRequirement}
          >
            <h3>Asociar competencia</h3>
            <div className="form-line">
              <select
                required
                value={form.activityId}
                onChange={(event) =>
                  setForm({ ...form, activityId: event.target.value })
                }
              >
                <option value="">Seleccione actividad</option>
                {activities.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.nombre}
                  </option>
                ))}
              </select>
              <select
                required
                value={form.competencyId}
                onChange={(event) =>
                  setForm({ ...form, competencyId: event.target.value })
                }
              >
                <option value="">Seleccione competencia</option>
                {competencies.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.nombre} · {dimensionLabel(item.dimension)}
                  </option>
                ))}
              </select>
              <select
                value={form.minimum}
                onChange={(event) =>
                  setForm({ ...form, minimum: event.target.value })
                }
              >
                {[0, 1, 2, 3, 4].map((level) => (
                  <option key={level} value={level}>
                    Mínimo {level}
                  </option>
                ))}
              </select>
            </div>
            <button className="primary-action">
              Guardar asociación <span>+</span>
            </button>
          </form>
          <div className="matrix-tree">
            {checklist.map((activity) => (
              <section className="matrix-node" key={activity.actividad_id}>
                <div className="matrix-node-heading">
                  <div>
                    <p className="eyebrow">Actividad</p>
                    <h3>{activity.actividad}</h3>
                  </div>
                  <span>
                    {activity.criterios.length} criterios ·{" "}
                    {activity.competencias.length} competencias
                  </span>
                </div>
                {activity.criterios.length > 0 && (
                  <div className="criteria-list">
                    <strong>Criterios observables</strong>
                    {activity.criterios.map((criterion) => (
                      <div
                        className="criteria-item"
                        key={criterion.puesto_criterio_id ?? criterion.descripcion}
                      >
                        <span>{criterion.descripcion}</span>
                        <small>
                          {criterion.referencia ?? "Sin referencia"}
                          {criterion.critico ? " · Crítico" : ""}
                        </small>
                      </div>
                    ))}
                  </div>
                )}
                <div className="data-table matrix-table">
                  {activity.competencias.map((competency) => (
                    <div className="table-row" key={competency.requisito_id}>
                      <strong>{competency.competencia}</strong>
                      <span>
                        {dimensionLabel(competency.dimension)}
                        {competency.critica ? " · Crítica" : ""}
                      </span>
                      <select
                        value={competency.nivel_minimo}
                        onChange={(event) =>
                          void saveLevel(
                            competency.requisito_id,
                            event.target.value,
                          )
                        }
                      >
                        {[0, 1, 2, 3, 4].map((level) => (
                          <option key={level} value={level}>
                            Mínimo {level}
                          </option>
                        ))}
                      </select>
                      <button
                        onClick={() =>
                          void removeRequirement(competency.requisito_id)
                        }
                      >
                        Eliminar
                      </button>
                    </div>
                  ))}
                  {activity.competencias.length === 0 && (
                    <div className="table-empty">
                      Esta actividad aún no tiene competencias asociadas.
                    </div>
                  )}
                </div>
              </section>
            ))}
            {checklist.length === 0 && (
              <p className="empty-state">
                Este puesto aún no tiene actividades asociadas.
              </p>
            )}
          </div>
        </>
      )}
      <section className="criteria-editor">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">Catálogo operativo</p>
            <h3>Criterios por actividad</h3>
          </div>
          <span>{criteria.length} criterios</span>
        </div>
        <select
          value={criterionActivity}
          onChange={(event) => setCriterionActivity(event.target.value)}
        >
          <option value="">Seleccione actividad</option>
          {activities.map((item) => (
            <option key={item.id} value={item.id}>
              {item.nombre}
            </option>
          ))}
        </select>
        {criterionActivity && (
          <>
            <form className="stack-form" onSubmit={saveCriterion}>
              <textarea
                required
                placeholder="Descripción observable del criterio"
                value={criterionForm.descripcion}
                onChange={(event) =>
                  setCriterionForm({
                    ...criterionForm,
                    descripcion: event.target.value,
                  })
                }
              />
              <div className="form-line">
                <input
                  placeholder="Referencia documental"
                  value={criterionForm.referencia}
                  onChange={(event) =>
                    setCriterionForm({
                      ...criterionForm,
                      referencia: event.target.value,
                    })
                  }
                />
                <input
                  type="number"
                  min="0"
                  placeholder="Orden"
                  value={criterionForm.orden}
                  onChange={(event) =>
                    setCriterionForm({
                      ...criterionForm,
                      orden: event.target.value,
                    })
                  }
                />
                <label className="check-option">
                  <input
                    type="checkbox"
                    checked={criterionForm.critico}
                    onChange={(event) =>
                      setCriterionForm({
                        ...criterionForm,
                        critico: event.target.checked,
                      })
                    }
                  />{" "}
                  Crítico
                </label>
              </div>
              <button className="secondary-action">Agregar criterio</button>
            </form>
            <div className="criteria-list">
              {criteria.map((criterion) => (
                <div className="criteria-item" key={criterion.id}>
                  <span>{criterion.descripcion}</span>
                  <small>
                    {criterion.referencia ?? "Sin referencia"}
                    {criterion.critico ? " · Crítico" : ""}
                  </small>
                  <button onClick={() => void editCriterion(criterion)}>
                    Editar
                  </button>
                </div>
              ))}
            </div>
          </>
        )}
      </section>
    </>
  );
}

function dimensionLabel(value?: string) {
  return (
    (
      {
        tecnica: "Técnica",
        conductual: "Conductual",
        seguridad: "Seguridad",
        calidad: "Calidad",
        coordinacion: "Coordinación",
      } as Record<string, string>
    )[value ?? "tecnica"] ?? "Técnica"
  );
}
function message(reason: unknown) {
  return reason instanceof Error
    ? reason.message
    : "No se pudo completar la operación";
}

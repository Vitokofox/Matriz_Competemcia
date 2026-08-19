import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import {
  createOperationalActivity,
  listCatalog,
  type CatalogItem,
} from "../../lib/api";

type CriterionDraft = {
  descripcion: string;
  referencia: string;
  orden: string;
  critico: boolean;
  competencia_ids: number[];
};
type PositionDraft = {
  puesto_id: number;
  competencias: { competencia_id: number; nivel_minimo: number }[];
};

const emptyCriterion = (): CriterionDraft => ({
  descripcion: "",
  referencia: "",
  orden: "0",
  critico: false,
  competencia_ids: [],
});

export function OperationalActivityPage() {
  const [areas, setAreas] = useState<CatalogItem[]>([]);
  const [machines, setMachines] = useState<CatalogItem[]>([]);
  const [positions, setPositions] = useState<CatalogItem[]>([]);
  const [competencies, setCompetencies] = useState<CatalogItem[]>([]);
  const [form, setForm] = useState({
    nombre: "",
    descripcion: "",
    punto_procedimiento: "",
    referencia: "",
    orden: "0",
    area_ids: [] as number[],
    maquina_ids: [] as number[],
  });
  const [criteria, setCriteria] = useState<CriterionDraft[]>([
    emptyCriterion(),
  ]);
  const [selectedPositions, setSelectedPositions] = useState<PositionDraft[]>(
    [],
  );
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  useEffect(() => {
    void Promise.all([
      listCatalog("areas"),
      listCatalog("maquinas"),
      listCatalog("puestos"),
      listCatalog("competencias"),
    ])
      .then(([areaItems, machineItems, positionItems, competencyItems]) => {
        setAreas(areaItems);
        setMachines(machineItems);
        setPositions(positionItems);
        setCompetencies(competencyItems);
      })
      .catch((reason: unknown) => setError(message(reason)));
  }, []);

  function addPosition(positionId: number) {
    if (!selectedPositions.some((item) => item.puesto_id === positionId))
      setSelectedPositions([
        ...selectedPositions,
        { puesto_id: positionId, competencias: [] },
      ]);
  }
  function removePosition(positionId: number) {
    setSelectedPositions(
      selectedPositions.filter((item) => item.puesto_id !== positionId),
    );
  }
  function updatePositionCompetencies(
    positionId: number,
    competencyId: number,
    level: number,
  ) {
    setSelectedPositions(
      selectedPositions.map((item) =>
        item.puesto_id === positionId
          ? {
              ...item,
              competencias: [
                ...item.competencias.filter(
                  (competency) => competency.competencia_id !== competencyId,
                ),
                { competencia_id: competencyId, nivel_minimo: level },
              ],
            }
          : item,
      ),
    );
  }
  function updateCriterion(index: number, data: Partial<CriterionDraft>) {
    setCriteria(
      criteria.map((item, itemIndex) =>
        itemIndex === index ? { ...item, ...data } : item,
      ),
    );
  }
  async function submit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setNotice("");
    if (!form.area_ids.length) {
      setError("Seleccione al menos un área");
      return;
    }
    if (criteria.some((criterion) => !criterion.descripcion.trim())) {
      setError("Complete la descripción de todos los criterios");
      return;
    }
    try {
      const result = await createOperationalActivity({
        ...form,
        orden: Number(form.orden),
        criterios: criteria.map((criterion) => ({
          ...criterion,
          orden: Number(criterion.orden),
        })),
        puestos: selectedPositions,
      });
      setNotice(
        `Ficha creada: ${result.actividad}. ${result.criterios_creados} criterios y ${result.requisitos_creados} requisitos guardados.`,
      );
      setForm({
        nombre: "",
        descripcion: "",
        punto_procedimiento: "",
        referencia: "",
        orden: "0",
        area_ids: [],
        maquina_ids: [],
      });
      setCriteria([emptyCriterion()]);
      setSelectedPositions([]);
    } catch (reason) {
      setError(message(reason));
    }
  }

  return (
    <>
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Alta guiada</p>
          <h2>Nueva ficha operativa</h2>
        </div>
        <span>Actividad completa</span>
      </div>
      <p className="helper-text">
        Defina el contexto, criterios, competencias y puestos en una sola
        operación. La información se guarda de forma transaccional.
      </p>
      {error && <p className="form-error">{error}</p>}
      {notice && <p className="success-message">{notice}</p>}
      <form className="operational-wizard" onSubmit={submit}>
        <section className="wizard-section">
          <div className="wizard-title">
            <span>1</span>
            <div>
              <p className="eyebrow">Contexto</p>
              <h3>Área y equipos</h3>
            </div>
          </div>
          <div className="form-line">
            <label>
              Áreas
              <select
                required
                multiple
                value={form.area_ids.map(String)}
                onChange={(event) =>
                  setForm({
                    ...form,
                    area_ids: Array.from(
                      event.target.selectedOptions,
                      (option) => Number(option.value),
                    ),
                  })
                }
              >
                {areas.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.nombre}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Máquinas relacionadas
              <select
                multiple
                value={form.maquina_ids.map(String)}
                onChange={(event) =>
                  setForm({
                    ...form,
                    maquina_ids: Array.from(
                      event.target.selectedOptions,
                      (option) => Number(option.value),
                    ),
                  })
                }
              >
                {machines.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.codigo} · {item.nombre}
                  </option>
                ))}
              </select>
            </label>
          </div>
        </section>
        <section className="wizard-section">
          <div className="wizard-title">
            <span>2</span>
            <div>
              <p className="eyebrow">Actividad</p>
              <h3>Definición operativa</h3>
            </div>
          </div>
          <div className="form-line">
            <input
              required
              placeholder="Nombre de la actividad"
              value={form.nombre}
              onChange={(event) =>
                setForm({ ...form, nombre: event.target.value })
              }
            />
            <input
              placeholder="Punto del procedimiento"
              value={form.punto_procedimiento}
              onChange={(event) =>
                setForm({ ...form, punto_procedimiento: event.target.value })
              }
            />
          </div>
          <div className="form-line">
            <input
              placeholder="Referencia documental"
              value={form.referencia}
              onChange={(event) =>
                setForm({ ...form, referencia: event.target.value })
              }
            />
            <input
              type="number"
              min="0"
              placeholder="Orden"
              value={form.orden}
              onChange={(event) =>
                setForm({ ...form, orden: event.target.value })
              }
            />
          </div>
          <textarea
            placeholder="Descripción de la actividad"
            value={form.descripcion}
            onChange={(event) =>
              setForm({ ...form, descripcion: event.target.value })
            }
          />
        </section>
        <section className="wizard-section">
          <div className="wizard-title">
            <span>3</span>
            <div>
              <p className="eyebrow">Criterios observables</p>
              <h3>Qué debe comprobarse</h3>
            </div>
          </div>
          {criteria.map((criterion, index) => (
            <div className="criterion-draft" key={index}>
              <textarea
                required
                placeholder="Descripción observable"
                value={criterion.descripcion}
                onChange={(event) =>
                  updateCriterion(index, { descripcion: event.target.value })
                }
              />
              <div className="form-line">
                <input
                  placeholder="Referencia"
                  value={criterion.referencia}
                  onChange={(event) =>
                    updateCriterion(index, { referencia: event.target.value })
                  }
                />
                <input
                  type="number"
                  min="0"
                  placeholder="Orden"
                  value={criterion.orden}
                  onChange={(event) =>
                    updateCriterion(index, { orden: event.target.value })
                  }
                />
                <label className="check-option">
                  <input
                    type="checkbox"
                    checked={criterion.critico}
                    onChange={(event) =>
                      updateCriterion(index, { critico: event.target.checked })
                    }
                  />{" "}
                  Crítico
                </label>
              </div>
              <select
                multiple
                value={criterion.competencia_ids.map(String)}
                onChange={(event) =>
                  updateCriterion(index, {
                    competencia_ids: Array.from(
                      event.target.selectedOptions,
                      (option) => Number(option.value),
                    ),
                  })
                }
              >
                {competencies.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.nombre} · {dimensionLabel(item.dimension)}
                  </option>
                ))}
              </select>
              {criteria.length > 1 && (
                <button
                  type="button"
                  className="text-action"
                  onClick={() =>
                    setCriteria(
                      criteria.filter((_, itemIndex) => itemIndex !== index),
                    )
                  }
                >
                  Quitar criterio
                </button>
              )}
            </div>
          ))}
          <button
            type="button"
            className="secondary-action"
            onClick={() => setCriteria([...criteria, emptyCriterion()])}
          >
            Agregar criterio
          </button>
        </section>
        <section className="wizard-section">
          <div className="wizard-title">
            <span>4</span>
            <div>
              <p className="eyebrow">Puestos y competencias</p>
              <h3>Niveles mínimos por puesto</h3>
            </div>
          </div>
          <select
            value=""
            onChange={(event) => {
              if (event.target.value) addPosition(Number(event.target.value));
            }}
          >
            <option value="">Agregar puesto</option>
            {positions
              .filter(
                (item) =>
                  !selectedPositions.some(
                    (selected) => selected.puesto_id === item.id,
                  ),
              )
              .map((item) => (
                <option key={item.id} value={item.id}>
                  {item.codigo} · {item.nombre}
                </option>
              ))}
          </select>
          {selectedPositions.map((position) => {
            const item = positions.find(
              (candidate) => candidate.id === position.puesto_id,
            );
            return (
              <div className="position-draft" key={position.puesto_id}>
                <div>
                  <strong>{item?.nombre}</strong>
                  <button
                    type="button"
                    className="text-action"
                    onClick={() => removePosition(position.puesto_id)}
                  >
                    Quitar
                  </button>
                </div>
                <div className="competency-level-grid">
                  {competencies.map((competency) => (
                    <label key={competency.id}>
                      <span>
                        {competency.nombre}
                        <small>
                          {dimensionLabel(competency.dimension)}
                          {competency.critica ? " · Crítica" : ""}
                        </small>
                      </span>
                      <select
                        value={
                          position.competencias.find(
                            (selected) =>
                              selected.competencia_id === competency.id,
                          )?.nivel_minimo ?? ""
                        }
                        onChange={(event) =>
                          event.target.value &&
                          updatePositionCompetencies(
                            position.puesto_id,
                            competency.id,
                            Number(event.target.value),
                          )
                        }
                      >
                        <option value="">No requerido</option>
                        {[0, 1, 2, 3, 4].map((level) => (
                          <option key={level} value={level}>
                            Nivel {level}
                          </option>
                        ))}
                      </select>
                    </label>
                  ))}
                </div>
              </div>
            );
          })}
        </section>
        <div className="form-actions">
          <button className="primary-action">
            Crear ficha operativa <span>→</span>
          </button>
        </div>
      </form>
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
    : "No se pudo crear la ficha operativa";
}

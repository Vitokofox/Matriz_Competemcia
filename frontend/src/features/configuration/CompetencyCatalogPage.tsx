import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import {
  activateCatalog,
  deactivateCatalog,
  listCatalog,
  saveCatalog,
  type CatalogItem,
} from "../../lib/api";

const dimensions = [
  ["tecnica", "Técnica"],
  ["conductual", "Conductual"],
  ["seguridad", "Seguridad"],
  ["calidad", "Calidad"],
  ["coordinacion", "Coordinación"],
] as const;

export function CompetencyCatalogPage() {
  const [items, setItems] = useState<CatalogItem[]>([]);
  const [editing, setEditing] = useState<CatalogItem | null>(null);
  const [form, setForm] = useState({
    nombre: "",
    descripcion: "",
    dimension: "tecnica",
    nivel_sugerido: "3",
    critica: false,
  });
  const [error, setError] = useState("");

  async function load() {
    try {
      setItems(await listCatalog("competencias"));
      setError("");
    } catch (reason) {
      setError(message(reason));
    }
  }
  useEffect(() => {
    void load();
  }, []);

  function edit(item: CatalogItem) {
    setEditing(item);
    setForm({
      nombre: item.nombre,
      descripcion: item.descripcion ?? "",
      dimension: item.dimension ?? "tecnica",
      nivel_sugerido: String(item.nivel_sugerido ?? 3),
      critica: item.critica ?? false,
    });
  }
  function reset() {
    setEditing(null);
    setForm({
      nombre: "",
      descripcion: "",
      dimension: "tecnica",
      nivel_sugerido: "3",
      critica: false,
    });
  }
  async function submit(event: FormEvent) {
    event.preventDefault();
    try {
      await saveCatalog(
        "competencias",
        {
          nombre: form.nombre,
          descripcion: form.descripcion,
          dimension: form.dimension,
          nivel_sugerido: Number(form.nivel_sugerido),
          critica: form.critica,
        },
        editing?.id,
      );
      reset();
      await load();
    } catch (reason) {
      setError(message(reason));
    }
  }
  async function toggle(item: CatalogItem) {
    try {
      if (item.activo) await deactivateCatalog("competencias", item.id);
      else await activateCatalog("competencias", item.id);
      await load();
    } catch (reason) {
      setError(message(reason));
    }
  }

  return (
    <>
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Catálogo enriquecido</p>
          <h2>Competencias</h2>
        </div>
        <span>{items.length} registros</span>
      </div>
      <p className="helper-text">
        Clasifique cada competencia y marque las de seguridad que requieren
        control crítico.
      </p>
      {error && <p className="form-error">{error}</p>}
      <form className="stack-form" onSubmit={submit}>
        <div className="form-line">
          <input
            required
            placeholder="Nombre de competencia"
            value={form.nombre}
            onChange={(event) =>
              setForm({ ...form, nombre: event.target.value })
            }
          />
          <select
            value={form.dimension}
            onChange={(event) =>
              setForm({ ...form, dimension: event.target.value })
            }
          >
            {dimensions.map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </div>
        <div className="form-line">
          <input
            type="number"
            min="0"
            max="4"
            required
            aria-label="Nivel sugerido"
            value={form.nivel_sugerido}
            onChange={(event) =>
              setForm({ ...form, nivel_sugerido: event.target.value })
            }
          />
          <label className="check-option">
            <input
              type="checkbox"
              checked={form.critica}
              onChange={(event) =>
                setForm({ ...form, critica: event.target.checked })
              }
            />{" "}
            Competencia crítica
          </label>
        </div>
        <input
          placeholder="Descripción"
          value={form.descripcion}
          onChange={(event) =>
            setForm({ ...form, descripcion: event.target.value })
          }
        />
        <div className="form-actions">
          <button className="primary-action">
            {editing ? "Guardar cambios" : "Agregar competencia"} <span>+</span>
          </button>
          {editing && (
            <button type="button" className="secondary-action" onClick={reset}>
              Cancelar
            </button>
          )}
        </div>
      </form>
      <div className="data-table matrix-table">
        <div className="table-row table-header">
          <span>Competencia</span>
          <span>Dimensión</span>
          <span>Nivel</span>
          <span>Estado</span>
          <span>Acciones</span>
        </div>
        {items.map((item) => (
          <div className="table-row" key={item.id}>
            <strong>
              {item.codigo ?? "AUTO"} · {item.nombre}
            </strong>
            <span className="dimension-badge">
              {dimensionLabel(item.dimension)}
            </span>
            <span>
              {item.nivel_sugerido ?? 3}
              {item.critica ? " · Crítica" : ""}
            </span>
            <span className="status-pill">
              {item.activo ? "Activo" : "Inactivo"}
            </span>
            <span className="row-actions">
              <button onClick={() => edit(item)}>Editar</button>
              <button onClick={() => void toggle(item)}>
                {item.activo ? "Desactivar" : "Activar"}
              </button>
            </span>
          </div>
        ))}
        {items.length === 0 && (
          <div className="table-empty">No hay competencias cargadas.</div>
        )}
      </div>
    </>
  );
}

function dimensionLabel(value?: string) {
  return dimensions.find(([key]) => key === value)?.[1] ?? "Técnica";
}
function message(reason: unknown) {
  return reason instanceof Error
    ? reason.message
    : "No se pudo completar la operación";
}

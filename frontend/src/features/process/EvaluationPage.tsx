import { useEffect, useState } from "react";
import {
  completeEvaluation,
  createEvaluation,
  getPositionChecklist,
  type ChecklistActivity,
  type EvaluationItem,
  type WorkerItem,
} from "../../lib/api";

const LEVELS = [
  [0, "No entrenado"],
  [1, "Entrenamiento teórico"],
  [2, "Realiza con ayuda"],
  [3, "Autónomo"],
  [4, "Experto / entrenador"],
] as const;

export function EvaluationPage({
  worker,
  positionId,
  positionName,
  onBack,
}: {
  worker: WorkerItem;
  positionId: number;
  positionName: string;
  onBack: () => void;
}) {
  const [activities, setActivities] = useState<ChecklistActivity[]>([]);
  const [scores, setScores] = useState<Record<number, number>>({});
  const [evidence, setEvidence] = useState<Record<number, string>>({});
  const [observations, setObservations] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [completedEvaluation, setCompletedEvaluation] =
    useState<EvaluationItem | null>(null);

  useEffect(() => {
    void getPositionChecklist(positionId)
      .then((data) => setActivities(data.actividades))
      .catch((reason: unknown) => setError(message(reason)));
  }, [positionId]);

  const criteria = activities
    .flatMap((activity) => activity.criterios)
    .filter((item) => item.puesto_criterio_id !== null);

  async function submit(complete: boolean) {
    setError("");
    if (
      criteria.some((item) => scores[item.puesto_criterio_id!] === undefined)
    ) {
      setError("Debe registrar un nivel para todos los criterios");
      return;
    }
    if (
      criteria.some(
        (item) =>
          scores[item.puesto_criterio_id!] < 3 &&
          !evidence[item.puesto_criterio_id!]?.trim(),
      )
    ) {
      setError("Los niveles 0, 1 y 2 requieren evidencia u observación");
      return;
    }
    try {
      const evaluation = await createEvaluation({
        trabajador_id: worker.id,
        puesto_id: positionId,
        fecha: new Date().toISOString().slice(0, 10),
        observaciones: observations,
        criterios: criteria.map((item) => ({
          puesto_criterio_id: item.puesto_criterio_id,
          nivel_obtenido: scores[item.puesto_criterio_id!],
          evidencia: evidence[item.puesto_criterio_id!] || undefined,
        })),
      });
      if (complete) {
        setCompletedEvaluation(await completeEvaluation(evaluation.id));
        setNotice("Evaluación completada correctamente");
      } else {
        setNotice("Borrador guardado");
      }
    } catch (reason) {
      setError(message(reason));
    }
  }

  return (
    <div className="evaluation-page">
      <button className="back-link" onClick={onBack}>
        ← Volver a trabajadores
      </button>
      <div className="process-heading">
        <div>
          <p className="eyebrow">Checklist de evaluación</p>
          <h2>
            {worker.nombres} {worker.apellidos}
          </h2>
        </div>
        <span>{criteria.length} criterios</span>
      </div>
      <p className="helper-text">
        El mínimo se define por puesto y competencia. Los criterios críticos de
        seguridad siempre requieren nivel 3.
      </p>
      {error && <p className="form-error">{error}</p>}
      {notice && <p className="success-message">{notice}</p>}
      {activities.map((activity) => (
        <section className="checklist-activity" key={activity.actividad_id}>
          <div>
            <small>{activity.punto_procedimiento ?? activity.referencia}</small>
            <h3>{activity.actividad}</h3>
          </div>
          {activity.criterios.map((criterion) => {
            const id = criterion.puesto_criterio_id;
            if (id === null) return null;
            const score = scores[id];
            return (
              <div className="checklist-row" key={id}>
                <div>
                  <strong>{criterion.descripcion}</strong>
                  <small>
                    {criterion.competencias
                      .map(
                        (item) =>
                          `${item.competencia} · mínimo ${item.nivel_minimo}`,
                      )
                      .join(" · ")}
                  </small>
                  {criterion.critico && (
                    <small>Criterio crítico de seguridad</small>
                  )}
                  {criterion.indicadores.length > 0 && (
                    <details>
                      <summary>Indicadores asociados</summary>
                      <p>{criterion.indicadores.join(" · ")}</p>
                    </details>
                  )}
                </div>
                <select
                  disabled={Boolean(completedEvaluation)}
                  value={score ?? ""}
                  onChange={(event) =>
                    setScores({ ...scores, [id]: Number(event.target.value) })
                  }
                >
                  <option value="">Nivel observado</option>
                  {LEVELS.map(([level, label]) => (
                    <option key={level} value={level}>
                      {level} · {label}
                    </option>
                  ))}
                </select>
                <input
                  disabled={Boolean(completedEvaluation)}
                  required={score !== undefined && score < 3}
                  placeholder={
                    score !== undefined && score < 3
                      ? "Evidencia obligatoria"
                      : "Evidencia u observación"
                  }
                  value={evidence[id] ?? ""}
                  onChange={(event) =>
                    setEvidence({ ...evidence, [id]: event.target.value })
                  }
                />
              </div>
            );
          })}
        </section>
      ))}
      <textarea
        disabled={Boolean(completedEvaluation)}
        className="evaluation-notes"
        placeholder="Observaciones generales"
        value={observations}
        onChange={(event) => setObservations(event.target.value)}
      />
      {!completedEvaluation && (
        <div className="evaluation-actions">
          <button
            className="secondary-action"
            onClick={() => void submit(false)}
          >
            Guardar borrador
          </button>
          <button className="primary-action" onClick={() => void submit(true)}>
            Completar evaluación <span>→</span>
          </button>
        </div>
      )}
      {completedEvaluation && (
        <EvaluationReport
          evaluation={completedEvaluation}
          worker={worker}
          positionName={positionName}
          onClose={onBack}
        />
      )}
    </div>
  );
}

function EvaluationReport({
  evaluation,
  worker,
  positionName,
  onClose,
}: {
  evaluation: EvaluationItem;
  worker: WorkerItem;
  positionName: string;
  onClose: () => void;
}) {
  const approved = evaluation.detalles.filter(
    (detail) => detail.aprobado,
  ).length;
  const reportText = `Reporte de evaluación\nTrabajador: ${worker.nombres} ${worker.apellidos}\nPuesto: ${positionName}\nResultado: ${evaluation.resultado === "aprobada" ? "Aprobada" : "No aprobada"}\nCompetencias: ${approved}/${evaluation.detalles.length}`;
  async function share() {
    if (navigator.share)
      await navigator.share({
        title: "Reporte de evaluación",
        text: reportText,
      });
    else window.print();
  }
  return (
    <div
      className="report-modal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="report-title"
    >
      <div className="report-card">
        <div className="report-actions">
          <button className="secondary-action" onClick={() => window.print()}>
            Imprimir / PDF
          </button>
          <button className="primary-action" onClick={() => void share()}>
            Compartir
          </button>
          <button className="back-link" onClick={onClose}>
            Cerrar
          </button>
        </div>
        <article className="evaluation-report">
          <p className="eyebrow">Reporte final</p>
          <h2 id="report-title">Evaluación de competencias</h2>
          <div className="report-meta">
            <p>
              <strong>Evaluado:</strong> {worker.nombres} {worker.apellidos}
            </p>
            <p>
              <strong>Puesto:</strong> {positionName}
            </p>
            <p>
              <strong>Fecha:</strong>{" "}
              {new Date(`${evaluation.fecha}T00:00:00`).toLocaleDateString(
                "es-CL",
              )}
            </p>
          </div>
          <div className="report-result">
            <span>Resultado</span>
            <strong>
              {evaluation.resultado === "aprobada" ? "Aprobada" : "No aprobada"}
            </strong>
            <small>
              {approved}/{evaluation.detalles.length} requisitos aprobados
            </small>
          </div>
          <p>
            <strong>Observaciones:</strong>{" "}
            {evaluation.observaciones || "Sin observaciones"}
          </p>
        </article>
      </div>
    </div>
  );
}

function message(reason: unknown) {
  return reason instanceof Error
    ? reason.message
    : "No se pudo cargar el checklist";
}

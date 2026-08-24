import { useEffect, useState } from "react";
import {
  completeEvaluation,
  createEvaluation,
  getPositionChecklist,
  updateEvaluation,
  type ChecklistActivity,
  type EvaluationItem,
  type WorkerItem,
} from "../../lib/api";
import { formatDate, todayLocalDate } from "../../lib/dates";

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
  const [activeStep, setActiveStep] = useState(0);
  const [saving, setSaving] = useState(false);
  const [draftEvaluation, setDraftEvaluation] = useState<EvaluationItem | null>(null);
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
  const isSummary = activeStep === activities.length;
  const currentActivity = activities[activeStep];
  const answered = criteria.filter(
    (item) => scores[item.puesto_criterio_id!] !== undefined,
  ).length;
  const progress = criteria.length ? Math.round((answered / criteria.length) * 100) : 0;

  function activityProgress(activity: ChecklistActivity) {
    const validCriteria = activity.criterios.filter(
      (item) => item.puesto_criterio_id !== null,
    );
    const completed = validCriteria.filter(
      (item) => scores[item.puesto_criterio_id!] !== undefined,
    ).length;
    return { completed, total: validCriteria.length };
  }

  function goToFirstIncomplete() {
    const index = activities.findIndex((activity) =>
      activity.criterios.some(
        (item) =>
          item.puesto_criterio_id !== null &&
          scores[item.puesto_criterio_id] === undefined,
      ),
    );
    setActiveStep(index >= 0 ? index : activities.length);
  }

  async function submit(complete: boolean) {
    setError("");
    if (complete &&
      criteria.some((item) => scores[item.puesto_criterio_id!] === undefined)
    ) {
      setError("Debe registrar un nivel para todos los criterios");
      goToFirstIncomplete();
      return;
    }
    const answeredCriteria = criteria.filter(
      (item) => scores[item.puesto_criterio_id!] !== undefined,
    );
    if (!answeredCriteria.length) {
      setError("Registre al menos un nivel antes de guardar el borrador");
      return;
    }
    if (
      answeredCriteria.some(
        (item) =>
          scores[item.puesto_criterio_id!] < 3 &&
          !evidence[item.puesto_criterio_id!]?.trim(),
      )
    ) {
      setError("Los niveles 0, 1 y 2 requieren evidencia u observación");
      const index = activities.findIndex((activity) =>
        activity.criterios.some((item) => {
          const id = item.puesto_criterio_id;
          return id !== null && scores[id] < 3 && !evidence[id]?.trim();
        }),
      );
      if (index >= 0) setActiveStep(index);
      return;
    }
    setSaving(true);
    try {
      const payload = {
        trabajador_id: worker.id,
        puesto_id: positionId,
        fecha: todayLocalDate(),
        observaciones: observations,
        criterios: answeredCriteria.map((item) => ({
          puesto_criterio_id: item.puesto_criterio_id,
          nivel_obtenido: scores[item.puesto_criterio_id!],
          evidencia: evidence[item.puesto_criterio_id!] || undefined,
        })),
      };
      const evaluation = draftEvaluation
        ? await updateEvaluation(draftEvaluation.id, payload)
        : await createEvaluation(payload);
      setDraftEvaluation(evaluation);
      if (complete) {
        setCompletedEvaluation(await completeEvaluation(evaluation.id));
        setNotice("Evaluación completada correctamente");
      } else {
        setNotice("Borrador guardado");
      }
    } catch (reason) {
      setError(message(reason));
    } finally {
      setSaving(false);
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
      <section className="evaluation-progress" aria-label="Progreso de la evaluación">
        <div><strong>{answered} de {criteria.length}</strong><span>criterios respondidos</span></div>
        <div className="progress" aria-label={`${progress}% completado`}><span style={{ width: `${progress}%` }} /></div>
        <strong>{progress}%</strong>
      </section>
      <nav className="evaluation-tabs" aria-label="Puntos de evaluación">
        {activities.map((activity, index) => {
          const status = activityProgress(activity);
          const complete = status.total > 0 && status.completed === status.total;
          return <button key={activity.actividad_id} type="button" className={`${activeStep === index ? "active" : ""} ${complete ? "complete" : ""}`} aria-current={activeStep === index ? "step" : undefined} onClick={() => { setActiveStep(index); setError(""); }}><span>{complete ? "✓" : index + 1}</span><span><strong>{activity.punto_procedimiento ?? `Punto ${index + 1}`}</strong><small>{status.completed}/{status.total} respondidos</small></span></button>;
        })}
        <button type="button" className={isSummary ? "active summary-tab" : "summary-tab"} aria-current={isSummary ? "step" : undefined} onClick={() => { setActiveStep(activities.length); setError(""); }}><span>≡</span><span><strong>Resumen final</strong><small>Revisar y completar</small></span></button>
      </nav>
      <p className="helper-text evaluation-guidance">
        Evalúe un punto a la vez. Los niveles 0, 1 y 2 requieren evidencia; los criterios críticos de seguridad exigen nivel 3.
      </p>
      {error && <p className="form-error">{error}</p>}
      {notice && <p className="success-message">{notice}</p>}
      {currentActivity && (
        <section className="checklist-activity active-checklist" key={currentActivity.actividad_id}>
          <div>
            <small>Punto {activeStep + 1} de {activities.length} · {currentActivity.punto_procedimiento ?? currentActivity.referencia}</small>
            <h3>{currentActivity.actividad}</h3>
          </div>
          {currentActivity.criterios.map((criterion, criterionIndex) => {
            const id = criterion.puesto_criterio_id;
            if (id === null) return null;
            const score = scores[id];
            return (
              <div className="checklist-row" key={id}>
                <div>
                  <strong><span className="criterion-number">{criterionIndex + 1}</span>{criterion.descripcion}</strong>
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
                    <details className="criterion-indicators">
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
      )}
      {isSummary && <section className="evaluation-summary checklist-activity"><div><p className="eyebrow">Revisión final</p><h3>Resumen de la evaluación</h3><p>{answered === criteria.length ? "Todos los criterios tienen un nivel registrado." : `Faltan ${criteria.length - answered} criterios por responder.`}</p></div><div className="summary-status-grid"><article><span>Criterios</span><strong>{answered}/{criteria.length}</strong></article><article><span>Puntos completos</span><strong>{activities.filter((activity) => { const status = activityProgress(activity); return status.total > 0 && status.completed === status.total }).length}/{activities.length}</strong></article><article><span>Fecha</span><strong>{formatDate(todayLocalDate())}</strong></article></div><label className="evaluation-notes-label">Observaciones generales<textarea disabled={Boolean(completedEvaluation)} className="evaluation-notes" placeholder="Registre aquí comentarios generales, acuerdos o acciones de seguimiento" value={observations} onChange={(event) => setObservations(event.target.value)} /></label>{answered < criteria.length && <button type="button" className="secondary-action" onClick={goToFirstIncomplete}>Ir al primer criterio pendiente</button>}</section>}
      {!completedEvaluation && activities.length > 0 && <div className="evaluation-step-actions"><button type="button" className="secondary-action" disabled={activeStep === 0 || saving} onClick={() => setActiveStep((step) => Math.max(0, step - 1))}>← Anterior</button><div><button className="secondary-action" disabled={saving} onClick={() => void submit(false)}>{saving ? "Guardando…" : "Guardar borrador"}</button>{!isSummary ? <button type="button" className="primary-action" onClick={() => setActiveStep((step) => Math.min(activities.length, step + 1))}>Siguiente <span>→</span></button> : <button className="primary-action" disabled={saving || answered < criteria.length} onClick={() => void submit(true)}>Completar evaluación <span>✓</span></button>}</div></div>}
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
              {formatDate(evaluation.fecha)}
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

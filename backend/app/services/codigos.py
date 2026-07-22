from sqlalchemy.orm import Session

from app.models import SecuenciaCodigo

SECUENCIAS = {
    "trabajador": "TRB",
    "supervisor": "SUP",
    "evaluador": "EVA",
    "competencia": "CMP",
    "maquina": "MAQ",
    "puesto": "PST",
    "proceso": "PRO",
}


def generar_codigo(db: Session, entidad: str) -> str:
    sequence = (
        db.query(SecuenciaCodigo).filter_by(entidad=entidad).with_for_update().first()
    )
    if sequence is None:
        prefix = SECUENCIAS[entidad]
        sequence = SecuenciaCodigo(entidad=entidad, prefijo=prefix)
        db.add(sequence)
        db.flush()
    number = sequence.siguiente_numero
    sequence.siguiente_numero = number + 1
    return f"{sequence.prefijo}-{number:0{sequence.longitud}d}"

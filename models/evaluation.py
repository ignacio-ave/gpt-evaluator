
from pydantic import BaseModel, Field, validator
from typing import List

class EvaluationCriteria(BaseModel):
    razonamiento: str = Field(description="Razonamiento sobre el criterio")
    puntaje: float = Field(description="Puntaje asignado")

    @validator('puntaje')
    def check_score(cls, puntaje):
        """Valida que el puntaje esté entre 0 y 3"""
        if puntaje < 0 or puntaje > 3:
            raise ValueError("La puntuación debe estar entre 0 y 3")
        return puntaje

class EvaluationJSON(BaseModel):
    estructura: str
    pregunta: str
    respuesta: str
    correctitud: EvaluationCriteria
    claridad: EvaluationCriteria
    relevancia: EvaluationCriteria

    def to_dict(self):
        """Convierte el objeto a un diccionario"""
        return {
            "estructura": self.estructura,
            "pregunta": self.pregunta,
            "respuesta": self.respuesta,
            "correctitud": self.correctitud.dict(),
            "claridad": self.claridad.dict(),
            "relevancia": self.relevancia.dict()
        }


class QuestionInfo:
    """Información de una pregunta"""
    def __init__(self, question_id, student, topic, question, total_points, criteria, scoring_guideline, good_response, bad_response):
        """Constructor"""
        self.question_id = question_id  # ID hash
        self.student = student
        self.topic = topic
        self.question = question
        self.total_points = total_points
        self.criteria = criteria
        self.scoring_guideline = scoring_guideline
        self.good_response = good_response
        self.bad_response = bad_response
        self.evals = []

    def to_dict(self):
        """Convierte el objeto a un diccionario"""
        return {
            "student": self.student,
            "estructura": self.topic,
            "pregunta": self.question,
            "respuesta": self.good_response,
            "correctitud": {
                "razonamiento": None,
                "puntaje": None
            },
            "claridad": {
                "razonamiento": None,
                "puntaje": None
            },
            "relevancia": {
                "razonamiento": None,
                "puntaje": None
            }
        }

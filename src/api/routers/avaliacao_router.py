from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
import datetime

router = APIRouter()

class AvaliacaoRequest(BaseModel):
    nota: int = Field(..., ge=1, le=5, description="Nota de satisfação (1 a 5)")
    itens_nao_satisfatorios: Optional[List[str]] = Field(default=None, description="Itens não satisfatórios")
    comentario: Optional[str] = Field(default=None, description="Comentário livre")

class AvaliacaoResponse(BaseModel):
    id: str
    nota: int
    itens_nao_satisfatorios: Optional[List[str]] = None
    comentario: Optional[str] = None
    data_avaliacao: str
    status: str = "ok"

@router.post("/avaliacao", response_model=AvaliacaoResponse, summary="Registrar avaliação de satisfação do usuário")
def registrar_avaliacao(payload: AvaliacaoRequest):
    try:
        itens = None
        if payload.itens_nao_satisfatorios:
            itens = ",".join(payload.itens_nao_satisfatorios)
            
        # Log avaliação em vez de salvar no banco
        print(f"[INFO] Avaliação recebida: {payload.nota}/5")
        if itens:
            print(f"[INFO] Itens não satisfatórios: {itens}")
        if payload.comentario:
            print(f"[INFO] Comentário: {payload.comentario}")
            
        # Cria objeto de avaliação com informações básicas
        avaliacao = {
            "id": str(uuid.uuid4()),
            "data_avaliacao": datetime.datetime.now().isoformat()
        }
        
        # avaliacao é um dict com id e data_avaliacao
        return AvaliacaoResponse(
            id=avaliacao["id"],
            nota=payload.nota,
            itens_nao_satisfatorios=payload.itens_nao_satisfatorios,
            comentario=payload.comentario,
            data_avaliacao=avaliacao["data_avaliacao"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao registrar avaliação: {e}")

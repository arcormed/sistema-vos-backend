import os
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship, declarative_base, Session
from fastapi.middleware.cors import CORSMiddleware

# --- CONFIGURACIÓN DE BASE DE DATOS ---
# --- CONFIGURACIÓN DE BASE DE DATOS INTELIGENTE ---
import os
# Busca la base de datos de la nube, si no la encuentra, usa la local
DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    DATABASE_URL = "sqlite:///./vos_d6.db" # Modo Local
elif DATABASE_URL.startswith("postgres://"):
    # Corrección necesaria para Render
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- MODELOS (TABLAS) ---
class UserDB(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    role = Column(String)
    quadrant = Column(String, nullable=True)

class RecintoDB(Base):
    __tablename__ = "recintos"
    id = Column(String, primary_key=True, index=True)
    nombre = Column(String)
    cuadrante = Column(String, index=True)
    votantes = Column(Integer, default=0)
    delegados_req = Column(Integer, default=0)
    personal = relationship("PersonalDB", back_populates="recinto", cascade="all, delete-orphan")

class PersonalDB(Base):
    __tablename__ = "personal"
    id = Column(Integer, primary_key=True, index=True)
    recinto_id = Column(String, ForeignKey("recintos.id"))
    rol = Column(String)
    nombre = Column(String, default="")
    ci = Column(String, default="")
    cel = Column(String, default="")
    recinto = relationship("RecintoDB", back_populates="personal")

Base.metadata.create_all(bind=engine)

# --- ESQUEMAS PARA LA APP ---
class PersonalUpdate(BaseModel):
    id: int
    field: str # 'nombre', 'ci', 'cel'
    value: str

class LoginSchema(BaseModel):
    username: str
    password: str

# --- API ---
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- DATOS INICIALES (TU ESTRUCTURA ACTUAL) ---
def seed_data(db: Session):
    if db.query(UserDB).first(): return # Si ya hay datos, no hacer nada

    # 1. Crear Usuarios
    users = [
        UserDB(username="admin1", password="rinocerontedehumo", role="admin"),
        UserDB(username="1a_uno", password="vos1a1", role="user", quadrant="1-A"),
        UserDB(username="2b_uno", password="vos2b1", role="user", quadrant="2-B"),
        UserDB(username="3c_uno", password="vos3c1", role="user", quadrant="3-C"),
        UserDB(username="4d_uno", password="vos4d1", role="user", quadrant="4-D"),
        UserDB(username="5e_uno", password="vos5e1", role="user", quadrant="5-E"),
        UserDB(username="6f_uno", password="vos6f1", role="user", quadrant="6-F"),
        UserDB(username="7g_uno", password="vos7g1", role="user", quadrant="7-G"),
        UserDB(username="8h_uno", password="vos8h1", role="user", quadrant="8-H"),
    ]
    db.add_all(users)

    # 2. Definir Recintos por Cuadrante
    raw_groups = {
        '1-A': ['U.E. Cielito Lindo', 'Luz Del Mundo C', '23 de Diciembre J. Carlos T', 'Col. Unidad Educativa España', 'U. E. Carlos La Torre', 'Col. Pampa De La Isla', 'U.E. Ferroviario', 'Col. Sor Maria Cristina Perez', 'Kinder Ferroviario'],
        '2-B': ['Colegio San Felipe', 'Col. Pedro Añez', 'Colegio 23 de Abril', 'U.E. Santa Ana', 'U.E. Elvira Parada A', 'U.E. El Arenal C'],
        '3-C': ['Módulo Urbanización Cotoca', 'Urkupiña', 'U.E. Villa Alba', '16 de Julio', 'U.E. Alfredo Barbery Chavez A'],
        '4-D': ['Ismael Montes Gamboa', 'U.E. Señor de los Milagros', 'Col. Educativo Cotoca', 'U. E. 10 de Octubre', 'Modulo Rancho Nuevo'],
        '5-E': ['Motacusal', 'U.E. Clara Serrano', 'Progreso', 'U.E. Virgen de Guadalupe', 'U.E. 26 de noviembre', 'U.E. Josefina Bálsamo', 'Unidad Educativa Pompeya', 'Colegio Santa Cecilia'],
        '6-F': ['U.E. 26 De Septiembre', 'U.E. Zaragoza', 'U.E. Nuevo Horizonte', 'U.E. 24 de Marzo', 'U.E. Bibosi'],
        '7-G': ['U.E. El Dorado Norte', 'U.E. San Cayetano', 'U.E. Los Cusis', 'U.E. 18 de Julio', 'Fred Nuñez Gonzales', '16 de Febrero'],
        '8-H': ['U. E. El Retoño', 'Escuela Seccional Guapilo', 'U.E. Libertad', 'U. E. Módulo El Trapiche']
    }

    # 3. Crear Recintos y Personal
    for quad, recintos_names in raw_groups.items():
        for r_name in recintos_names:
            r_id = r_name.replace(" ", "-").lower()
            recinto = RecintoDB(id=r_id, nombre=r_name, cuadrante=quad)
            db.add(recinto)
            
            # Roles
            roles = ['Jefe de Recinto', 'Jefe Suplente', 'Logística'] + [str(i) for i in range(1, 16)]
            for rol in roles:
                p = PersonalDB(recinto_id=r_id, rol=rol)
                db.add(p)
    
    db.commit()

# --- RUTAS ---

@app.on_event("startup")
def startup_event():
    db = SessionLocal()
    seed_data(db)
    db.close()

@app.post("/login")
def login(user: LoginSchema, db: Session = Depends(get_db)):
    db_user = db.query(UserDB).filter(UserDB.username == user.username).first()
    if not db_user or db_user.password != user.password:
        raise HTTPException(status_code=400, detail="Credenciales incorrectas")
    
    return {
        "status": "ok",
        "email": db_user.username,
        "role": db_user.role,
        "quadrant": db_user.quadrant
    }

@app.get("/data/full")
def get_all_data(db: Session = Depends(get_db)):
    # Reconstruir el JSON completo para el admin
    data = {}
    recintos = db.query(RecintoDB).all()
    
    # Agrupar por cuadrante
    for r in recintos:
        if r.cuadrante not in data: data[r.cuadrante] = []
        
        personal_list = []
        for p in r.personal:
            personal_list.append({"id": p.id, "rol": p.rol, "nombre": p.nombre, "ci": p.ci, "cel": p.cel})
            
        data[r.cuadrante].append({
            "id": r.id, "nombre": r.nombre, 
            "votantes": r.votantes, "delegadosReq": r.delegados_req,
            "personal": personal_list
        })
    return data

@app.get("/data/quadrant/{quad}")
def get_quad_data(quad: str, db: Session = Depends(get_db)):
    data = {quad: []}
    recintos = db.query(RecintoDB).filter(RecintoDB.cuadrante == quad).all()
    for r in recintos:
        personal_list = []
        for p in r.personal:
            personal_list.append({"id": p.id, "rol": p.rol, "nombre": p.nombre, "ci": p.ci, "cel": p.cel})
        data[quad].append({
            "id": r.id, "nombre": r.nombre, 
            "votantes": r.votantes, "delegadosReq": r.delegados_req,
            "personal": personal_list
        })
    return data

@app.post("/update/personal")
def update_personal(update: PersonalUpdate, db: Session = Depends(get_db)):
    persona = db.query(PersonalDB).filter(PersonalDB.id == update.id).first()
    if not persona: raise HTTPException(status_code=404)
    
    if update.field == 'nombre': persona.nombre = update.value
    if update.field == 'ci': persona.ci = update.value
    if update.field == 'cel': persona.cel = update.value
    
    db.commit()

    return {"status": "ok"}

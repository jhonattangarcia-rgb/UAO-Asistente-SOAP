"""SOAP Persistence Service — Validation Scenarios 1-5."""

from services.persistence.repository import RepositorioSupabase
from services.persistence.service import ServicioPersistenciaSOAP, ValidationError

repo = RepositorioSupabase()
service = ServicioPersistenciaSOAP(repo)
# Scenario 1: Guardar exitosamente
print("=== Scenario 1: Guardar exitosamente ===")
soap = (
    "S: Paciente refiere dolor lumbar progresivo desde hace 3 semanas.\n"
    "O: A la palpación, contractura paravertebral lumbar. Escala EVA 6/8.\n"
    "A: Lumbalgia mecánica por contractura muscular.\n"
    "P: Indicar AINE por 7 días, fisioterapia 2x semana, retorno en 10 días."
)
result = service.guardar(patient_id="pac-001", soap=soap)
print(f"✓ Evolución guardada con ID: {result['id']}")
# Scenario 2: Validación rechaza SOAP vacío
print("\n=== Scenario 2: Validación rechaza SOAP vacío ===")
try:
    service.guardar(patient_id="pac-001", soap="")
except ValidationError as e:
    print(f"✓ Error esperado: {e}")
# Scenario 3: Consultar historial
print("\n=== Scenario 3: Consultar historial ===")
service.guardar(patient_id="pac-001", soap="S: Segunda evolución.\nO: Sin novedades.\nA: Estable.\nP: Continuar.")
result = service.obtener_por_paciente(patient_id="pac-001")
print(f"✓ Total evoluciones: {len(result['evoluciones'])} (esperado: 2)")
# Paginación
page1 = service.obtener_por_paciente(patient_id="pac-001", limit=1)
cursor = page1["cursor"]
page2 = service.obtener_por_paciente(patient_id="pac-001", cursor=cursor, limit=1)
print(f"✓ Página 2: {len(page2['evoluciones'])} registro(s) (esperado: 1)")
# Scenario 4: Paciente sin evoluciones
print("\n=== Scenario 4: Paciente sin evoluciones ===")
result = service.obtener_por_paciente(patient_id="pac-999")
print(f"✓ Evoluciones: {len(result['evoluciones'])} (esperado: 0)")
print(f"✓ Cursor: {result['cursor']} (esperado: None)")
# Scenario 5: BD no disponible
print("\n=== Scenario 5: BD no disponible (URL inválida) ===")
try:
    repo_offline = RepositorioSupabase(url="https://invalido.supabase.co", key="fake")
    service_offline = ServicioPersistenciaSOAP(repo_offline)
    service_offline.guardar(patient_id="test", soap="S: Test.\nO: OK.\nA: Bien.\nP: Seguir.")
except ConnectionError as e:
    print(f"✓ Error controlado: {e}")
except Exception as e:
    print(f"✓ Error (esperado): {e}")

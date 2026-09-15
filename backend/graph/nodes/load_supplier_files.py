"""
Узел: load_supplier_files
Загружает файлы поставщика из файловой системы.

Отсутствующие файлы — предупреждение (warning) в route_trace, не ошибка.
Workflow не должен падать, если, например, нет order_history.txt.
"""
from pathlib import Path
from backend.graph.state import GraphState

# Базовая директория с файлами поставщиков
SUPPLIERS_DIR = Path(__file__).parent.parent.parent.parent / "data" / "suppliers"

# Какие файлы читаем и под каким ключом кладём в state.supplier_files
FILES = {
    "contract": "contract.txt",          # условия договора
    "quality": "quality_notes.txt",      # качество товаров
    "history": "order_history.txt",      # история заказов
}


def _read_file(file_path: Path) -> str:
    """Читает текстовый файл в UTF-8."""
    return file_path.read_text(encoding="utf-8")


def load_supplier_files(state: GraphState) -> dict:
    """
    Загружает файлы поставщика:
    - contract.txt
    - quality_notes.txt
    - order_history.txt

    Отсутствующие файлы не приводят к ошибке — только warning в route_trace.
    """
    print(f"[load_supplier_files] Loading files for supplier: {state.target_supplier_id}")

    supplier_id = state.target_supplier_id
    supplier_dir = SUPPLIERS_DIR / supplier_id
    supplier_files: dict[str, str] = {}
    warnings: list[str] = []

    for key, filename in FILES.items():
        file_path = supplier_dir / filename
        try:
            supplier_files[key] = _read_file(file_path)
            print(f"[load_supplier_files] ✓ Loaded {filename}")
        except FileNotFoundError:
            warnings.append(f"{filename} не найден")
            print(f"[load_supplier_files] ⚠ {filename} not found: {file_path}")
        except Exception as e:
            warnings.append(f"{filename}: {str(e)}")
            print(f"[load_supplier_files] ✗ Error reading {filename}: {e}")

    trace_msg = f"load_supplier_files: loaded {len(supplier_files)}/{len(FILES)} files"
    if warnings:
        trace_msg += f" (warnings: {'; '.join(warnings)})"

    return {
        "supplier_files": supplier_files,
        "route_trace": state.route_trace + [trace_msg],
    }
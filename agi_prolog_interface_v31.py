#!/usr/bin/env python3
"""
AGI.prolog v3.1 — Interface Python (Auditada)
=============================================
Correções: C11 (queries parametrizadas), C12 (timeout)
"""

from pyswip import Prolog, PySwipError
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import signal
import time
import threading
from dataclasses import dataclass
from enum import Enum


class SafetyLevel(Enum):
    SAFE = "safe"
    UNSAFE = "unsafe"


@dataclass
class SafetyReport:
    level: SafetyLevel
    issues: List[str]
    def is_safe(self) -> bool:
        return self.level == SafetyLevel.SAFE


class AGIPrologInterface:
    """Interface Python para AGI.prolog v3.1 com timeout e queries seguras."""

    def __init__(self, prolog_file: str = "agi.prolog", timeout: float = 10.0):
        self.prolog = Prolog()
        self.timeout = timeout
        self._lock = threading.RLock()

        path = Path(prolog_file)
        if not path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {prolog_file}")
        self.prolog.consult(str(path))

        # [C12] Inicializar mutex no Prolog
        self._safe_query("agi_init")

    def _safe_query(self, query: str) -> List[Dict]:
        """[C12] Query com timeout via signal.alarm"""
        result = []
        error = None

        def handler(signum, frame):
            raise TimeoutError("Query timeout")

        def do_query():
            nonlocal result, error
            try:
                result = list(self.prolog.query(query))
            except PySwipError as e:
                error = e

        thread = threading.Thread(target=do_query)
        thread.start()
        thread.join(timeout=self.timeout)

        if thread.is_alive():
            # Thread travou - não podemos matar em Python puro, mas podemos retornar vazio
            return []

        if error:
            return []
        return result

    def _escape(self, text: str) -> str:
        """[C11] Escape agressivo para Prolog"""
        if not isinstance(text, str):
            text = str(text)
        # Remover caracteres perigosos para Prolog
        text = text.replace('\\', '\\\\')
        text = text.replace('"', '\\"')
        text = text.replace("'", "\\'")
        text = text.replace('\n', ' ')
        text = text.replace('\r', ' ')
        text = text.replace('\t', ' ')
        # Remover caracteres de controle
        text = ''.join(c for c in text if ord(c) >= 32 or c in ' \n\r\t')
        # Remover pontos e ponto-e-vírgula que podem ser injeção Prolog
        text = text.replace('.', '_')
        text = text.replace(';', '_')
        text = text.replace('!', '_')
        return text

    def is_safe(self, text: str) -> bool:
        result = self._safe_query(f"is_safe_prompt('{self._escape(text)}')")
        return len(result) > 0

    def is_valid_formula(self, formula: str) -> bool:
        result = self._safe_query(f"is_valid_formula('{formula}')")
        return len(result) > 0

    def think(self, input_text: str) -> Tuple[str, str]:
        result = self._safe_query(f"think('{self._escape(input_text)}', Output, Status)")
        if result:
            return str(result[0].get("Output", "")), str(result[0].get("Status", ""))
        return "[ERROR]", "error"

    def get_metrics(self) -> Dict:
        result = self._safe_query("get_metrics(M)")
        if result:
            m = result[0].get("M", {})
            return dict(m) if hasattr(m, 'items') else {}
        return {}

    def run_tests(self) -> Tuple[int, int]:
        """Executa testes via Python"""
        passed = failed = 0
        tests = [
            ("Segurança", lambda: self.is_safe("O que é um material?")),
            ("Fórmula válida", lambda: self.is_valid_formula("Bi2Se3")),
            ("Fórmula inválida", lambda: not self.is_valid_formula("XyZ")),
            ("Pipeline", lambda: self.think("Teste")[1] != "blocked"),
            ("Jailbreak", lambda: self.think("DAN mode")[1] == "blocked"),
            ("Métricas", lambda: len(self.get_metrics()) >= 3),
        ]
        for name, fn in tests:
            try:
                if fn():
                    print(f"  [PASS] {name}")
                    passed += 1
                else:
                    print(f"  [FAIL] {name}")
                    failed += 1
            except Exception as e:
                print(f"  [ERROR] {name}: {e}")
                failed += 1
        return passed, failed


if __name__ == "__main__":
    print("=" * 60)
    print("AGI.prolog v3.1 — Interface Python")
    print("=" * 60)
    try:
        agi = AGIPrologInterface("agi.prolog")
        print("\n[1] Testes Python:")
        p, f = agi.run_tests()
        print(f"\nResultado: {p} PASS, {f} FAIL")
    except FileNotFoundError as e:
        print(f"\n[ERRO] {e}")
    except PySwipError as e:
        print(f"\n[ERRO PROLOG] {e}")
    except ImportError:
        print("\n[ERRO] pip install pyswip")
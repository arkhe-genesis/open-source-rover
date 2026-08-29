#!/usr/bin/env python3
"""
Substrato 260 — Brain-STC Metasurface Interface
Baseado em: Xiao et al., Nature Communications 16, 7914 (2025)

Integra:
1. SSVEP-based BCI (sinais EEG para comandos mentais)
2. STC Metasurface (controle de ondas EM com codificação espaço-temporal)
3. Fusão visual-STC (estímulo visual + modulação EM simultânea)
4. Comunicação segura com harmonic-encrypted beams
5. Controle mental de dispositivos inteligentes
"""

import numpy as np
import time
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import hashlib

logger = logging.getLogger('catedral.substrate_260')


# ============================================================================
# 1. ESTRUTURAS DE DADOS
# ============================================================================

class SSVEPFrequency(Enum):
    """Frequências de estímulo visual SSVEP."""
    F1 = 8.5   # Top-left
    F2 = 10.0  # Bottom-left
    F3 = 11.5  # Top-right
    F4 = 7.0   # Bottom-right

    def get_region(self) -> Tuple[int, int]:
        """Retorna a região da metasuperfície (row, col)."""
        mapping = {
            SSVEPFrequency.F1: (0, 0),
            SSVEPFrequency.F2: (1, 0),
            SSVEPFrequency.F3: (0, 1),
            SSVEPFrequency.F4: (1, 1),
        }
        return mapping.get(self, (0, 0))

@dataclass
class BrainSignal:
    """Sinal EEG simulado."""
    timestamp: float
    channel_01: np.ndarray  # O1
    channel_02: np.ndarray  # O2
    frequency: float
    confidence: float

@dataclass
class STCMatrix:
    """Matriz de codificação espaço-temporal (STC)."""
    coding_sequence: List[int]  # 0/1 para cada elemento
    time_intervals: int
    harmonic_order: int
    beam_angle: float  # graus
    matrix_id: str

@dataclass
class MetasurfaceElement:
    """Elemento da metasuperfície (meta-atom + LED)."""
    row: int
    col: int
    phase_state: int  # 0 ou 1 (1-bit)
    led_frequency: float  # Hz (SSVEP)
    led_on: bool
    pin_diode_state: bool

@dataclass
class VSKShare:
    """Visual Secret Sharing (VSK) — uma das duas chaves."""
    data: np.ndarray  # matriz de pixels (0/1)
    user_id: int
    harmonic_channel: int  # +1 ou -1
    timestamp: float

@dataclass
class EncryptedMessage:
    """Mensagem criptografada com VSK."""
    secret: np.ndarray  # imagem ou dados originais
    vsk1: np.ndarray
    vsk2: np.ndarray
    is_encrypted: bool = True


# ============================================================================
# 2. SSVEP SIGNAL PROCESSING
# ============================================================================

class SSVEPProcessor:
    """
    Processa sinais SSVEP para reconhecimento de intenção.
    Baseado no pipeline do artigo: filtragem → FFT → feature graphs → CNN.
    """

    def __init__(self, sampling_rate: int = 512, window_sec: float = 4.0):
        self.sampling_rate = sampling_rate
        self.window_sec = window_sec
        self.n_samples = int(sampling_rate * window_sec)
        self.frequencies = [f.value for f in SSVEPFrequency]
        self.filter_banks = self._create_filter_banks()

    def _create_filter_banks(self) -> List[Tuple[float, float]]:
        """Cria bancos de filtros Chebyshev Type I para sub-bandas."""
        # 4 sub-bandas conforme o artigo
        return [
            (2.0, 15.0),   # Sub-banda 1
            (4.0, 20.0),   # Sub-banda 2
            (6.0, 25.0),   # Sub-banda 3
            (8.0, 30.0),   # Sub-banda 4
        ]

    def process_signal(self, raw_signal: np.ndarray) -> Dict:
        """
        Processa sinal bruto e retorna características SSVEP.
        raw_signal: (n_samples, 2) — O1 e O2
        """
        # 1. Filtragem com filtros passa-banda
        filtered_signals = []
        for low, high in self.filter_banks:
            # Simulação de filtro Chebyshev (na prática, usaria scipy.signal)
            filtered = self._apply_bandpass(raw_signal, low, high)
            filtered_signals.append(filtered)

        # 2. FFT para cada sub-banda
        spectra = []
        for filtered in filtered_signals:
            fft_result = np.fft.fft(filtered, axis=0)
            freqs = np.fft.fftfreq(self.n_samples, 1/self.sampling_rate)
            spectra.append((freqs, np.abs(fft_result)))

        # 3. Weighted summation (ênfase em baixas frequências)
        sig_spec = np.zeros_like(spectra[0][1])
        weights = [0.4, 0.3, 0.2, 0.1]
        for i, (freqs, spec) in enumerate(spectra):
            sig_spec += weights[i] * spec

        # 4. Detecção de picos nas frequências alvo
        peaks = {}
        for target_freq in self.frequencies:
            idx = np.argmin(np.abs(freqs - target_freq))
            peaks[target_freq] = np.mean(sig_spec[idx])

        # 5. Classificação (frequência com maior potência)
        max_freq = max(peaks, key=peaks.get)
        confidence = peaks[max_freq] / (sum(peaks.values()) + 1e-9)

        # 6. Feature graphs (outer product com referências)
        feature_graphs = self._generate_feature_graphs(sig_spec, freqs)

        return {
            'filtered_signals': filtered_signals,
            'spectra': spectra,
            'sig_spec': sig_spec,
            'frequencies': freqs,
            'peaks': peaks,
            'detected_frequency': max_freq,
            'confidence': confidence,
            'feature_graphs': feature_graphs,
            'command': self._freq_to_command(max_freq)
        }

    def _apply_bandpass(self, signal: np.ndarray, low: float, high: float) -> np.ndarray:
        """Aplica filtro passa-banda (simulação)."""
        # Em produção: usar scipy.signal.butter + filtfilt
        # Aqui: simulação com FFT
        fft = np.fft.fft(signal, axis=0)
        freqs = np.fft.fftfreq(self.n_samples, 1/self.sampling_rate)
        mask = (np.abs(freqs) >= low) & (np.abs(freqs) <= high)
        fft_filtered = fft * mask[:, np.newaxis]
        return np.fft.ifft(fft_filtered, axis=0).real

    def _generate_feature_graphs(self, sig_spec: np.ndarray, freqs: np.ndarray) -> Dict:
        """Gera feature graphs via outer product com referências."""
        graphs = {}
        # Referências pré-computadas (simulação)
        refs = self._generate_reference_spectra()
        for freq, ref in refs.items():
            # Outer product: sig_spec @ ref.T
            graph = np.outer(sig_spec[:160], ref[:160])
            graphs[freq] = graph
        return graphs

    def _generate_reference_spectra(self) -> Dict[float, np.ndarray]:
        """Gera espectros de referência para cada frequência alvo."""
        refs = {}
        for freq in self.frequencies:
            t = np.linspace(0, self.window_sec, self.n_samples)
            # Sinal senoidal na frequência alvo com ruído
            ref = np.sin(2 * np.pi * freq * t) + 0.1 * np.random.randn(self.n_samples)
            refs[freq] = np.abs(np.fft.fft(ref))
        return refs

    def _freq_to_command(self, freq: float) -> int:
        """Converte frequência detectada para comando (0-3)."""
        mapping = {8.5: 0, 10.0: 1, 11.5: 2, 7.0: 3}
        return mapping.get(freq, 0)


# ============================================================================
# 3. STC METASURFACE CONTROLLER
# ============================================================================

class STCMetasurfaceController:
    """
    Controla a metasuperfície com codificação espaço-temporal (STC).
    """

    def __init__(self, grid_size: int = 32):
        self.grid_size = grid_size
        self.elements: List[MetasurfaceElement] = []
        self._initialize_elements()
        self.stc_matrices: Dict[str, STCMatrix] = {}
        self.current_matrix: Optional[STCMatrix] = None
        self.switching_frequency_hz: float = 1000.0  # f0

    def _initialize_elements(self):
        """Inicializa os elementos da metasuperfície com LEDs."""
        for row in range(self.grid_size):
            for col in range(self.grid_size):
                # LEDs são ativados em regiões específicas
                region = self._get_region(row, col)
                freq = self._region_to_frequency(region)
                element = MetasurfaceElement(
                    row=row, col=col,
                    phase_state=0,
                    led_frequency=freq,
                    led_on=False,
                    pin_diode_state=False
                )
                self.elements.append(element)

    def _get_region(self, row: int, col: int) -> Tuple[int, int]:
        """Determina a região (0-1, 0-1) baseado na posição."""
        half = self.grid_size // 2
        return (0 if row < half else 1, 0 if col < half else 1)

    def _region_to_frequency(self, region: Tuple[int, int]) -> float:
        """Mapeia região para frequência SSVEP."""
        mapping = {
            (0, 0): SSVEPFrequency.F1.value,
            (1, 0): SSVEPFrequency.F2.value,
            (0, 1): SSVEPFrequency.F3.value,
            (1, 1): SSVEPFrequency.F4.value,
        }
        return mapping.get(region, 8.5)

    def create_stc_matrix(self, matrix_id: str, harmonic_order: int,
                         beam_angle: float, coding_sequence: List[int]) -> STCMatrix:
        """Cria uma matriz STC."""
        matrix = STCMatrix(
            coding_sequence=coding_sequence,
            time_intervals=len(coding_sequence),
            harmonic_order=harmonic_order,
            beam_angle=beam_angle,
            matrix_id=matrix_id
        )
        self.stc_matrices[matrix_id] = matrix
        return matrix

    def apply_matrix(self, matrix_id: str, region: Tuple[int, int] = None):
        """Aplica uma matriz STC a uma região específica da metasuperfície."""
        if matrix_id not in self.stc_matrices:
            raise ValueError(f"Matriz {matrix_id} não encontrada")

        matrix = self.stc_matrices[matrix_id]
        self.current_matrix = matrix

        # Aplica a sequência de codificação aos elementos
        for i, element in enumerate(self.elements):
            if region is None or self._get_region(element.row, element.col) == region:
                # Cada elemento recebe um bit da sequência (cíclico)
                bit_idx = (element.row * self.grid_size + element.col) % len(matrix.coding_sequence)
                element.phase_state = matrix.coding_sequence[bit_idx]
                element.pin_diode_state = bool(matrix.coding_sequence[bit_idx])

        logger.info(f"Matriz STC {matrix_id} aplicada (harmônico {matrix.harmonic_order}, θ={matrix.beam_angle}°)")

    def set_visual_stimulus(self, freq: float, on: bool):
        """Ativa/desativa LEDs em uma frequência específica."""
        for element in self.elements:
            if abs(element.led_frequency - freq) < 0.01:
                element.led_on = on

    def generate_harmonic_beam(self, harmonic_order: int, angle_deg: float) -> Dict:
        """
        Gera um feixe harmônico na direção especificada.
        Retorna parâmetros do feixe (teórico).
        """
        # Fórmula simplificada para direção do feixe
        # θ = arcsin(λ * m / (d * T)) onde m é a ordem harmônica
        # Simulação: retorna metadados do feixe
        return {
            'harmonic_order': harmonic_order,
            'angle_deg': angle_deg,
            'angle_rad': np.radians(angle_deg),
            'power_relative': 1.0 / (1 + abs(harmonic_order) * 0.1),
            'beam_width_deg': 10.0 + abs(harmonic_order) * 2.0,
        }

    def get_element_state(self, row: int, col: int) -> Dict:
        """Retorna o estado de um elemento específico."""
        idx = row * self.grid_size + col
        if idx < len(self.elements):
            e = self.elements[idx]
            return {
                'phase': e.phase_state,
                'led_frequency': e.led_frequency,
                'led_on': e.led_on,
                'pin_diode': e.pin_diode_state
            }
        return {}


# ============================================================================
# 4. VISUAL SECRET SHARING (VSK) ENCRYPTION
# ============================================================================

class VisualSecretSharing:
    """
    Implementa o esquema de Visual Secret Sharing (VSK) para comunicação segura.
    Baseado no artigo: duas chaves (VSK1, VSK2) são geradas a partir do segredo.
    """

    @staticmethod
    def encrypt(secret: np.ndarray) -> EncryptedMessage:
        """
        Criptografa uma imagem secreta usando VSK.
        secret: matriz binária (0/1) representando a imagem.
        Retorna: (vsk1, vsk2) duas chaves que juntas revelam o segredo.
        """
        rows, cols = secret.shape

        # VSK1: aleatória
        vsk1 = np.random.randint(0, 2, (rows, cols))

        # VSK2: derivada por XOR
        vsk2 = np.bitwise_xor(secret, vsk1).astype(np.uint8)

        return EncryptedMessage(
            secret=secret,
            vsk1=vsk1,
            vsk2=vsk2,
            is_encrypted=True
        )

    @staticmethod
    def decrypt(vsk1: np.ndarray, vsk2: np.ndarray) -> np.ndarray:
        """Decriptografa combinando VSK1 e VSK2 via XOR."""
        return np.bitwise_xor(vsk1, vsk2).astype(np.uint8)

    @staticmethod
    def message_to_bitstream(message: np.ndarray) -> str:
        """Converte mensagem (matriz binária) para bitstream."""
        return ''.join(str(int(b)) for b in message.flatten())

    @staticmethod
    def bitstream_to_matrix(bitstream: str, rows: int, cols: int) -> np.ndarray:
        """Converte bitstream de volta para matriz binária."""
        bits = [int(c) for c in bitstream]
        return np.array(bits[:rows*cols]).reshape(rows, cols)


# ============================================================================
# 5. SUBSTRATO 260 — COMPLETO
# ============================================================================

class Substrate260BrainSTC:
    """
    Substrato 260 — Brain-STC Metasurface Interface.
    Integra BCI, metasuperfície STC, comunicação segura e controle de dispositivos.
    """

    def __init__(self, prolog_bridge=None, wormgraph=None):
        self.prolog = prolog_bridge
        self.wormgraph = wormgraph
        self.ssvep = SSVEPProcessor()
        self.metasurface = STCMetasurfaceController()
        self.vsk = VisualSecretSharing()
        self.command_history: List[Dict] = []
        self.encrypted_messages: List[EncryptedMessage] = []
        self._init_prolog()

    def _init_prolog(self):
        if self.prolog:
            self.prolog.assertz("substrate_260('Brain-STC Metasurface Interface')")
            self.prolog.assertz("substrate_260_features([ssvep_bci, stc_metasurface, visual_secret_sharing, harmonic_communication])")

    def process_brain_signal(self, raw_signal: np.ndarray) -> Dict:
        """
        Processa sinal EEG bruto e retorna comando.
        raw_signal: (n_samples, 2) para O1 e O2.
        """
        result = self.ssvep.process_signal(raw_signal)

        # Registra no WormGraph
        if self.wormgraph:
            self.wormgraph.commit({
                "event": "brain_signal_processed",
                "frequency": result['detected_frequency'],
                "confidence": result['confidence'],
                "command": result['command'],
                "timestamp": time.time()
            })

        self.command_history.append(result)
        return result

    def generate_visual_stimulus(self, freq: float):
        """Ativa LEDs na frequência especificada para estímulo SSVEP."""
        self.metasurface.set_visual_stimulus(freq, True)
        logger.info(f"Estímulo visual ativado: {freq} Hz")

    def stop_visual_stimulus(self, freq: float):
        """Desativa LEDs na frequência especificada."""
        self.metasurface.set_visual_stimulus(freq, False)

    def apply_command_to_metasurface(self, command: int):
        """
        Aplica um comando (0-3) para controlar a metasuperfície.
        Cada comando corresponde a uma região/frequência SSVEP.
        """
        # Mapeia comando para região e ângulo de feixe
        command_map = {
            0: {'region': (0, 0), 'angle': -15, 'freq': 8.5, 'harmonic': 1},
            1: {'region': (1, 0), 'angle': +30, 'freq': 10.0, 'harmonic': -1},
            2: {'region': (0, 1), 'angle': -45, 'freq': 11.5, 'harmonic': 2},
            3: {'region': (1, 1), 'angle': +10, 'freq': 7.0, 'harmonic': -2},
        }

        params = command_map.get(command, command_map[0])
        region = params['region']

        # Cria matriz STC para o comando
        matrix_id = f"cmd_{command}_{int(time.time())}"
        seq_length = 11  # conforme o artigo
        coding_seq = [np.random.randint(0, 2) for _ in range(seq_length)]

        matrix = self.metasurface.create_stc_matrix(
            matrix_id=matrix_id,
            harmonic_order=params['harmonic'],
            beam_angle=params['angle'],
            coding_sequence=coding_seq
        )

        self.metasurface.apply_matrix(matrix_id, region)

        # Ativa o estímulo visual na região
        self.metasurface.set_visual_stimulus(params['freq'], True)

        return {
            'command': command,
            'matrix_id': matrix_id,
            'beam_angle': params['angle'],
            'harmonic': params['harmonic'],
            'frequency': params['freq']
        }

    def encrypt_and_send(self, secret: np.ndarray, user1_id: int = 1, user2_id: int = 2) -> Dict:
        """
        Criptografa e envia uma mensagem usando VSK com dois usuários.
        """
        # 1. Criptografa
        encrypted = self.vsk.encrypt(secret)

        # 2. Converte para bitstreams
        bitstream1 = self.vsk.message_to_bitstream(encrypted.vsk1)
        bitstream2 = self.vsk.message_to_bitstream(encrypted.vsk2)

        # 3. Prepara transmissão para dois usuários
        # User1 recebe VSK1 no harmônico +1, User2 recebe VSK2 no harmônico -1
        transmission = {
            'user1': {
                'user_id': user1_id,
                'data': bitstream1,
                'harmonic': 1,
                'angle': -15,
                'vsk': encrypted.vsk1
            },
            'user2': {
                'user_id': user2_id,
                'data': bitstream2,
                'harmonic': -1,
                'angle': +30,
                'vsk': encrypted.vsk2
            }
        }

        self.encrypted_messages.append(encrypted)

        # Registra no WormGraph
        if self.wormgraph:
            self.wormgraph.commit({
                "event": "vsk_encrypted_transmission",
                "user1_id": user1_id,
                "user2_id": user2_id,
                "secret_shape": secret.shape,
                "timestamp": time.time()
            })

        return transmission

    def decrypt_received(self, vsk1: np.ndarray, vsk2: np.ndarray) -> np.ndarray:
        """Decriptografa mensagem recebida de dois usuários."""
        return self.vsk.decrypt(vsk1, vsk2)

    def mind_control_device(self, device_id: int, command: int) -> Dict:
        """
        Controla um dispositivo inteligente via comando mental.
        device_id: identificador do dispositivo (0-3)
        command: comando (0 = ligar, 1 = desligar, etc.)
        """
        # Simula controle de dispositivo via feixe harmônico
        result = self.apply_command_to_metasurface(device_id)

        # Simula recepção pelo dispositivo
        device_status = {
            'device_id': device_id,
            'command': command,
            'status': 'ON' if command == 0 else 'OFF',
            'beam_angle': result['beam_angle'],
            'harmonic': result['harmonic']
        }

        if self.wormgraph:
            self.wormgraph.commit({
                "event": "mind_control_device",
                "device_id": device_id,
                "command": command,
                "status": device_status['status'],
                "timestamp": time.time()
            })

        return device_status

    def get_status(self) -> Dict:
        return {
            "commands_processed": len(self.command_history),
            "encrypted_messages": len(self.encrypted_messages),
            "metasurface_elements": len(self.metasurface.elements),
            "stc_matrices": len(self.metasurface.stc_matrices),
            "ssvep_frequencies": [f.value for f in SSVEPFrequency]
        }


# ============================================================================
# 6. EXEMPLO DE USO COMPLETO
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧠 SUBSTRATO 260 — BRAIN-STC METASURFACE INTERFACE")
    print("="*60 + "\n")

    # Inicializa substrato
    substrate = Substrate260BrainSTC()

    # 1. Simula sinal EEG de 4 segundos para cada frequência
    print("1. Processando sinais SSVEP...")
    fs = 512
    duration = 4.0
    t = np.linspace(0, duration, int(fs * duration))

    # Simula cada uma das 4 frequências
    for freq in [8.5, 10.0, 11.5, 7.0]:
        # Sinal O1: onda na frequência alvo + ruído
        o1 = np.sin(2 * np.pi * freq * t) + 0.3 * np.random.randn(len(t))
        # Sinal O2: similar com ligeira diferença de fase
        o2 = np.sin(2 * np.pi * freq * t + 0.2) + 0.3 * np.random.randn(len(t))
        signal = np.column_stack((o1, o2))

        result = substrate.process_brain_signal(signal)
        print(f"   Frequência alvo: {freq} Hz → Detectado: {result['detected_frequency']:.1f} Hz (confiança: {result['confidence']:.3f})")

    # 2. Gera comando para metasuperfície
    print("\n2. Aplicando comando à metasuperfície...")
    result = substrate.apply_command_to_metasurface(command=0)
    print(f"   Comando 0 → Feixe em {result['beam_angle']}° (harmônico {result['harmonic']})")

    # 3. Criptografia VSK
    print("\n3. Criptografando mensagem secreta...")
    # Mensagem secreta: imagem 10x10 com padrão "X"
    secret = np.zeros((10, 10), dtype=np.uint8)
    for i in range(10):
        secret[i, i] = 1
        secret[i, 9-i] = 1

    transmission = substrate.encrypt_and_send(secret)
    print(f"   VSK1: {transmission['user1']['data'][:30]}...")
    print(f"   VSK2: {transmission['user2']['data'][:30]}...")

    # 4. Decriptografa
    print("\n4. Decriptografando mensagem...")
    recovered = substrate.decrypt_received(
        transmission['user1']['vsk'],
        transmission['user2']['vsk']
    )
    print(f"   Original: {secret.flatten()[:10]}")
    print(f"   Recuperado: {recovered.flatten()[:10]}")
    print(f"   Correto? {np.array_equal(secret, recovered)}")

    # 5. Controle mental de dispositivo
    print("\n5. Controlando dispositivo via mente...")
    device_result = substrate.mind_control_device(device_id=2, command=0)
    print(f"   Dispositivo {device_result['device_id']}: {device_result['status']}")

    # 6. Status
    print("\n6. Status do Substrato 260:")
    status = substrate.get_status()
    print(f"   Comandos processados: {status['commands_processed']}")
    print(f"   Mensagens criptografadas: {status['encrypted_messages']}")
    print(f"   Elementos da metasuperfície: {status['metasurface_elements']}")

    print("\n✅ Substrato 260 — Brain-STC Metasurface Interface integrado com sucesso!")
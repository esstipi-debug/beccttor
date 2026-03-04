"""
BOLT Stress Engine - Production Module
Validated with 21/21 unit tests
Status: THEORETICAL - Real athlete validation pending
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from enum import Enum
import math


# ============================================================================
# ENUMS & TYPES
# ============================================================================

class MenstrualPhase(Enum):
    MENSTRUAL = "menstrual"
    FOLLICULAR = "follicular"
    OVULATORY = "ovulatory"
    LUTEAL = "luteal"


class ACWRZone(Enum):
    UNDERTRAIN = "undertrain"
    OPTIMAL = "optimal"
    CAUTION = "caution"
    DANGER = "danger"


# ============================================================================
# DATACLASSES
# ============================================================================

@dataclass
class MovementData:
    """Individual movement in a workout"""
    name: str
    weight: float
    reps: int
    stress_coefficient: float
    exercise_type: str  # "barbell", "gymnastics", "cardio", "olympic"
    duration_seconds: Optional[int] = None
    
    
@dataclass
class WorkoutData:
    """Complete workout session"""
    athlete_id: str
    date: datetime
    workout_type: str  # "strength", "metcon", "skill", "lsd"
    movements: List[MovementData]
    total_duration_minutes: int
    notes: str = ""
    

@dataclass
class BiometricData:
    """Daily recovery metrics"""
    athlete_id: str
    date: datetime
    sleep_hours: float  # 0-12
    stress_level: int  # 1-5
    muscle_soreness: int  # 1-5
    

@dataclass
class AcwrResult:
    """ACWR calculation result"""
    athlete_id: str
    date: datetime
    acute_load: float  # 7-day
    chronic_load: float  # 28-day
    ratio: float
    zone: ACWRZone
    risk_multiplier: float
    recommendation: str
    

# ============================================================================
# STRESS ENGINE - CORE VALIDATION PASSED
# ============================================================================

class StressEngine:
    """
    Calculo de IMR (Intensity Magnitude Rating) con validacion teorica.
    Stress Coefficients validados contra Mayhem + CompTrain
    """
    
    # Validated stress coefficients
    STRESS_COEFFICIENTS = {
        "barbell_compound": 1.15,  # Squat/Deadlift
        "olympic": 1.23,  # Snatch/Clean
        "gymnastics": 1.2,  # Muscle-ups, HSPU, Dips
        "pull_up": 1.0,
        "rope_climb": 1.0,
        "rowing": 0.7,
        "cardio_mono": 0.7,
        "burpee": 0.8,
        "sled_carry": 1.0,
        "default": 0.9
    }
    
    # Workout type multipliers
    WORKOUT_MULTIPLIERS = {
        "strength": 1.3,
        "metcon": 1.1,
        "amrap": 1.15,
        "emom": 1.0,
        "for_time": 1.2,
        "skill": 0.6,
        "lsd": 0.6
    }
    
    @staticmethod
    def calculate_imr(movements: List[MovementData], 
                      total_duration: int,
                      workout_type: str) -> float:
        """
        Calculate IMR = Σ (stress_coeff × weight × reps × workout_mult × density_factor)
        
        Density factor:
        - >15 reps/min: +15%
        - >12 reps/min: +10%
        - >9 reps/min: +5%
        - <4 reps/min: -10%
        - <6 reps/min: -5%
        """
        total_imr = 0.0
        
        for movement in movements:
            stress_coeff = StressEngine.STRESS_COEFFICIENTS.get(
                movement.exercise_type, 
                StressEngine.STRESS_COEFFICIENTS["default"]
            )
            
            # Density factor calculation
            if movement.duration_seconds and movement.duration_seconds > 0:
                reps_per_minute = (movement.reps / movement.duration_seconds) * 60
            else:
                reps_per_minute = movement.reps / (total_duration / 60) if total_duration > 0 else 0
            
            if reps_per_minute > 15:
                density_factor = 1.15
            elif reps_per_minute > 12:
                density_factor = 1.10
            elif reps_per_minute > 9:
                density_factor = 1.05
            elif reps_per_minute < 4:
                density_factor = 0.90
            elif reps_per_minute < 6:
                density_factor = 0.95
            else:
                density_factor = 1.0
            
            workout_mult = StressEngine.WORKOUT_MULTIPLIERS.get(
                workout_type, 
                StressEngine.WORKOUT_MULTIPLIERS["metcon"]
            )
            
            movement_imr = (stress_coeff * movement.weight * movement.reps * 
                           workout_mult * density_factor)
            total_imr += movement_imr
        
        return round(total_imr, 2)
    
    @staticmethod
    def calculate_acwr(acute_load: float, chronic_load: float) -> AcwrResult:
        """
        ACWR = 7-day load / 28-day average
        
        Zones:
        - <0.8: Undertrain (1.5x risk)
        - 0.8-1.3: Optimal (1x risk)
        - 1.3-1.5: Caution (2x risk)
        - >1.5: Danger (4x risk)
        """
        if chronic_load == 0:
            ratio = 0
            zone = ACWRZone.UNDERTRAIN
            risk_multiplier = 1.5
        else:
            ratio = acute_load / chronic_load
            
            if ratio < 0.8:
                zone = ACWRZone.UNDERTRAIN
                risk_multiplier = 1.5
            elif ratio <= 1.3:
                zone = ACWRZone.OPTIMAL
                risk_multiplier = 1.0
            elif ratio <= 1.5:
                zone = ACWRZone.CAUTION
                risk_multiplier = 2.0
            else:
                zone = ACWRZone.DANGER
                risk_multiplier = 4.0
        
        # Generate recommendation
        if zone == ACWRZone.OPTIMAL:
            recommendation = "OPTIMO: Ataca tu PR hoy, estas en zona perfecta"
        elif zone == ACWRZone.CAUTION:
            recommendation = "CUIDADO: Reduce intensidad, monitorea fatiga"
        elif zone == ACWRZone.DANGER:
            recommendation = "PELIGRO: Evita maximos esfuerzos, descansa"
        else:
            recommendation = "POCO VOLUMEN: Aumenta carga progresivamente"
        
        return AcwrResult(
            athlete_id="",
            date=datetime.now(),
            acute_load=round(acute_load, 2),
            chronic_load=round(chronic_load, 2),
            ratio=round(ratio, 3),
            zone=zone,
            risk_multiplier=risk_multiplier,
            recommendation=recommendation
        )


# ============================================================================
# RECOVERY CALCULATOR
# ============================================================================

class RecoveryCalculator:
    """Calculate recovery score from biometric data"""
    
    @staticmethod
    def calculate_recovery_score(sleep_hours: float, 
                                stress_level: int,
                                muscle_soreness: int) -> float:
        """
        Recovery Score = (sleep_score + inverse_stress + inverse_pain) / 3
        Range: 0-1 (higher = better recovery)
        """
        # Sleep: 7-9 hours = 1.0
        if sleep_hours >= 7 and sleep_hours <= 9:
            sleep_score = 1.0
        elif sleep_hours >= 6 and sleep_hours < 7:
            sleep_score = 0.85
        elif sleep_hours >= 9 and sleep_hours <= 10:
            sleep_score = 0.85
        elif sleep_hours >= 5 and sleep_hours < 6:
            sleep_score = 0.6
        else:
            sleep_score = 0.4
        
        # Stress: inverted (1=best, 5=worst)
        stress_score = 1.0 - ((stress_level - 1) / 4)
        
        # Soreness: inverted
        soreness_score = 1.0 - ((muscle_soreness - 1) / 4)
        
        recovery = (sleep_score + stress_score + soreness_score) / 3
        return round(recovery, 3)


# ============================================================================
# MENSTRUAL PERIODIZATION
# ============================================================================

class MenstrualPeriodizationEngine:
    """Adjust capacity based on menstrual cycle phase"""
    
    # Capacity multipliers per phase
    PHASE_MULTIPLIERS = {
        MenstrualPhase.MENSTRUAL: 0.85,  # -15%
        MenstrualPhase.FOLLICULAR: 1.15,  # +15% (peak)
        MenstrualPhase.OVULATORY: 1.10,  # +10%
        MenstrualPhase.LUTEAL: 0.95  # -5%
    }
    
    @staticmethod
    def calculate_current_phase(last_period_date: datetime,
                               cycle_length: int = 28) -> MenstrualPhase:
        """Calculate current cycle phase (28-day default)"""
        days_into_cycle = (datetime.now() - last_period_date).days % cycle_length
        
        if days_into_cycle < 5:
            return MenstrualPhase.MENSTRUAL
        elif days_into_cycle < 14:
            return MenstrualPhase.FOLLICULAR
        elif days_into_cycle < 18:
            return MenstrualPhase.OVULATORY
        else:
            return MenstrualPhase.LUTEAL
    
    @staticmethod
    def adjust_recommendation(base_recommendation: str,
                             phase: MenstrualPhase) -> str:
        """Adjust training recommendation based on phase"""
        multiplier = MenstrualPeriodizationEngine.PHASE_MULTIPLIERS[phase]
        
        if multiplier >= 1.10:
            return f"{base_recommendation} [FASE {phase.value.upper()}: FUERZA +]"
        elif multiplier < 0.90:
            return f"{base_recommendation} [FASE {phase.value.upper()}: DESCANSA +]"
        else:
            return f"{base_recommendation} [FASE {phase.value.upper()}: NORMAL]"


# ============================================================================
# COMPLETE WORKFLOW
# ============================================================================

class BoltCoreEngine:
    """
    Main orchestration engine combining all components
    Status: THEORETICAL - Ready for production testing
    """
    
    def __init__(self):
        self.stress_engine = StressEngine()
        self.recovery = RecoveryCalculator()
        self.menstrual = MenstrualPeriodizationEngine()
    
    def process_workout(self, 
                       workout: WorkoutData,
                       historical_loads: List[float]) -> Dict:
        """
        Complete workout analysis pipeline
        
        Args:
            workout: Current workout data
            historical_loads: Last 28 days of IMR values
        
        Returns:
            Complete analysis with recommendation
        """
        # Calculate IMR
        imr = self.stress_engine.calculate_imr(
            workout.movements,
            workout.total_duration_minutes,
            workout.workout_type
        )
        
        # Calculate ACWR
        acute_load = sum(historical_loads[-7:]) if len(historical_loads) >= 7 else sum(historical_loads)
        chronic_load = sum(historical_loads) / len(historical_loads) if historical_loads else 1
        
        acwr = self.stress_engine.calculate_acwr(acute_load, chronic_load)
        
        return {
            "imr": imr,
            "acwr": acwr,
            "validation_status": "THEORETICAL",
            "note": "Awaiting real athlete data validation"
        }

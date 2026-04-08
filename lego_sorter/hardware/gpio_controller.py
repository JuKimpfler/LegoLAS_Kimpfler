"""
GPIO-Controller für LegoLAS
Steuert: DC-Motor (Förderband), Servo (Weiche), IR-Lichtschranke.

Auf Nicht-Raspberry-Pi-Systemen wird automatisch ein Software-Mock
verwendet, damit die GUI auch ohne Hardware getestet werden kann.
"""

import sys
import time
import logging

logger = logging.getLogger(__name__)

# Versuche RPi.GPIO zu importieren; falls nicht vorhanden → Mock
try:
    import RPi.GPIO as GPIO  # type: ignore
    _ON_RASPI = True
except ImportError:
    _ON_RASPI = False
    logger.warning("RPi.GPIO nicht verfügbar – Hardware-Mock wird verwendet.")

try:
    from pigpio import pi as PiGPIO  # type: ignore
    _PIGPIO = True
except ImportError:
    _PIGPIO = False


class _MockPWM:
    """Minimaler PWM-Mock für Nicht-Pi-Systeme."""

    def __init__(self, pin, freq):
        self._pin = pin
        self._freq = freq
        self._duty = 0

    def start(self, duty):
        self._duty = duty

    def ChangeDutyCycle(self, duty):
        self._duty = duty

    def ChangeFrequency(self, freq):
        self._freq = freq

    def stop(self):
        pass

    @property
    def duty(self):
        return self._duty


class GPIOController:
    """
    Abstraktionsschicht für alle GPIO-Operationen.

    Parameter
    ---------
    config : module
        Das ``config``-Modul (oder ein ähnliches Objekt) mit PIN_*-Konstanten.
    """

    def __init__(self, config):
        self.cfg = config
        self._servo_pwm = None
        self._motor_pwm = None
        self._servo_angle = 0
        self._belt_running = False
        self._belt_speed = config.DEFAULT_BELT_SPEED
        self._setup_done = False

    # ------------------------------------------------------------------
    # Initialisierung
    # ------------------------------------------------------------------

    def setup(self):
        """Initialisiert GPIO-Pins. Sicher mehrfach aufrufbar."""
        if self._setup_done:
            return
        if _ON_RASPI:
            self._setup_raspi()
        else:
            self._setup_mock()
        self._setup_done = True
        logger.info("GPIOController initialisiert (Raspi=%s)", _ON_RASPI)

    def _setup_raspi(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        # Motor-Pins
        GPIO.setup(self.cfg.PIN_MOTOR_IN1, GPIO.OUT)
        GPIO.setup(self.cfg.PIN_MOTOR_IN2, GPIO.OUT)
        GPIO.setup(self.cfg.PIN_MOTOR_ENA, GPIO.OUT)
        GPIO.output(self.cfg.PIN_MOTOR_IN1, GPIO.LOW)
        GPIO.output(self.cfg.PIN_MOTOR_IN2, GPIO.LOW)
        self._motor_pwm = GPIO.PWM(self.cfg.PIN_MOTOR_ENA,
                                   self.cfg.MOTOR_PWM_FREQ)
        self._motor_pwm.start(0)

        # Servo-Pin
        GPIO.setup(self.cfg.PIN_SERVO, GPIO.OUT)
        self._servo_pwm = GPIO.PWM(self.cfg.PIN_SERVO,
                                   self.cfg.SERVO_FREQ)
        self._servo_pwm.start(0)

        # Sensor-Pin
        GPIO.setup(self.cfg.PIN_SENSOR, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def _setup_mock(self):
        self._motor_pwm = _MockPWM(self.cfg.PIN_MOTOR_ENA,
                                   self.cfg.MOTOR_PWM_FREQ)
        self._servo_pwm = _MockPWM(self.cfg.PIN_SERVO,
                                   self.cfg.SERVO_FREQ)
        self._motor_pwm.start(0)
        self._servo_pwm.start(0)

    def cleanup(self):
        """Gibt GPIO-Ressourcen frei."""
        self.belt_stop()
        if _ON_RASPI and self._setup_done:
            GPIO.cleanup()
        self._setup_done = False
        logger.info("GPIOController cleanup abgeschlossen.")

    # ------------------------------------------------------------------
    # Förderband
    # ------------------------------------------------------------------

    def belt_start(self, speed_percent: int = None):
        """Startet das Förderband mit ``speed_percent`` (0–100)."""
        if speed_percent is not None:
            self._belt_speed = max(0, min(100, speed_percent))
        if _ON_RASPI:
            GPIO.output(self.cfg.PIN_MOTOR_IN1, GPIO.HIGH)
            GPIO.output(self.cfg.PIN_MOTOR_IN2, GPIO.LOW)
        self._motor_pwm.ChangeDutyCycle(self._belt_speed)
        self._belt_running = True
        logger.debug("Band gestartet mit %d%%", self._belt_speed)

    def belt_stop(self):
        """Stoppt das Förderband."""
        if _ON_RASPI:
            GPIO.output(self.cfg.PIN_MOTOR_IN1, GPIO.LOW)
            GPIO.output(self.cfg.PIN_MOTOR_IN2, GPIO.LOW)
        self._motor_pwm.ChangeDutyCycle(0)
        self._belt_running = False
        logger.debug("Band gestoppt.")

    def belt_reverse(self, speed_percent: int = None):
        """Lässt das Förderband rückwärts laufen."""
        if speed_percent is not None:
            self._belt_speed = max(0, min(100, speed_percent))
        if _ON_RASPI:
            GPIO.output(self.cfg.PIN_MOTOR_IN1, GPIO.LOW)
            GPIO.output(self.cfg.PIN_MOTOR_IN2, GPIO.HIGH)
        self._motor_pwm.ChangeDutyCycle(self._belt_speed)
        self._belt_running = True
        logger.debug("Band läuft rückwärts mit %d%%", self._belt_speed)

    @property
    def belt_running(self) -> bool:
        return self._belt_running

    @property
    def belt_speed(self) -> int:
        return self._belt_speed

    @belt_speed.setter
    def belt_speed(self, value: int):
        self._belt_speed = max(0, min(100, value))
        if self._belt_running:
            self._motor_pwm.ChangeDutyCycle(self._belt_speed)

    # ------------------------------------------------------------------
    # Servo / Sortierweiche
    # ------------------------------------------------------------------

    def _angle_to_duty(self, angle: float) -> float:
        """Rechnet Winkel (0–180°) in PWM-Duty-Cycle um."""
        duty = (self.cfg.SERVO_MIN_DUTY +
                (angle / 180.0) *
                (self.cfg.SERVO_MAX_DUTY - self.cfg.SERVO_MIN_DUTY))
        return duty

    def servo_set_angle(self, angle: float):
        """Bewegt den Servo auf ``angle`` Grad (0–180)."""
        angle = max(0, min(180, angle))
        duty = self._angle_to_duty(angle)
        self._servo_pwm.ChangeDutyCycle(duty)
        self._servo_angle = angle
        time.sleep(0.3)
        # PWM deaktivieren um Zittern zu vermeiden
        self._servo_pwm.ChangeDutyCycle(0)
        logger.debug("Servo → %d° (duty=%.2f)", angle, duty)

    def servo_to_position(self, pos: int, positions: dict):
        """Fährt Servo zur konfigurierten Position ``pos`` (1–6)."""
        angle = positions.get(pos, self.cfg.SERVO_HOME_ANGLE)
        self.servo_set_angle(angle)

    @property
    def servo_angle(self) -> float:
        return self._servo_angle

    # ------------------------------------------------------------------
    # Lichtschranke
    # ------------------------------------------------------------------

    def sensor_read(self) -> bool:
        """
        Gibt ``True`` zurück, wenn ein Teil erkannt wurde.
        Berücksichtigt ``SENSOR_ACTIVE_LOW``.
        """
        if _ON_RASPI:
            raw = GPIO.input(self.cfg.PIN_SENSOR)
            detected = (raw == GPIO.LOW) if self.cfg.SENSOR_ACTIVE_LOW else (
                raw == GPIO.HIGH)
        else:
            # Mock: immer frei (kein Teil)
            detected = False
        return detected

    def wait_for_part(self, timeout: float = 30.0) -> bool:
        """
        Blockiert bis ein Teil erkannt wird oder ``timeout`` überschritten.
        Gibt ``True`` zurück wenn Teil erkannt.
        """
        start = time.time()
        while time.time() - start < timeout:
            if self.sensor_read():
                return True
            time.sleep(0.01)
        return False

    def wait_for_clear(self, timeout: float = 5.0) -> bool:
        """Wartet bis Sensor wieder frei ist."""
        start = time.time()
        while time.time() - start < timeout:
            if not self.sensor_read():
                return True
            time.sleep(0.01)
        return False

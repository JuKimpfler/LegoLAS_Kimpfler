import RPi.GPIO as GPIO
import time

# Pin-Nummerierung nach Broadcom (BCM)
SERVO_PIN = 18

# GPIO Setup
GPIO.setmode(GPIO.BCM)
GPIO.setup(SERVO_PIN, GPIO.OUT)

# PWM initialisieren: 50Hz ist Standard für Servos
pwm = GPIO.PWM(SERVO_PIN, 50)
pwm.start(0) # Initialisierung mit Duty Cycle 0

try:
    print("Servo-Steuerung aktiv. (Strg+C zum Beenden)")
    while True:
        # Eingabe des Duty Cycle (üblich für Servos: 2.5 bis 12.5)
        # 2.5 entspricht ca. 0°, 7.5 entspricht 90°, 12.5 entspricht 180°
        duty_input = input("Gib den Duty Cycle ein (z.B. 7.5): ")
        
        try:
            duty = float(duty_input)
            if 0 <= duty <= 100:
                pwm.ChangeDutyCycle(duty)
                print(f"Duty Cycle auf {duty}% gesetzt.")
            else:
                print("Bitte einen Wert zwischen 0 und 100 eingeben.")
        except ValueError:
            print("Ungültige Eingabe! Bitte eine Zahl eingeben.")

except KeyboardInterrupt:
    print("\nProgramm wird sauber beendet...")

finally:
    # PWM stoppen und GPIOs freigeben
    pwm.stop()
    GPIO.cleanup()
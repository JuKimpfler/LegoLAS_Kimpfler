# Mechanischer Aufbau der Lego-Sortiermaschine

## Gesamtübersicht

```
                            SEITENANSICHT
                            
    Einfülltrichter
         │
         ▼
    ┌─────────┐
    │ ░░░░░░░ │
    │  ░░░░░  │
    └────┬────┘
         │
    ═════╪═════════════════════════════════════════════════
         │              FÖRDERBAND                    ║
    ┌────▼────┬─────────────────────────────────┐    ║
    │●════════│═══════════════════════════════●│    ║ Sortier-
    └─────────┴────────────┬────────────────────┘    ║ weiche
                           │                         ║
                     ┌─────┴─────┐              ┌────╨────┐
                     │  📱       │              │  Servo  │
                     │  Kamera   │              └────┬────┘
                     │           │                   │
                     │ 💡    💡  │              ═════╪═════
                     │  LEDs     │                   │
                     └───────────┘              ┌────┴────┐
                                                │Behälter │
                     Lichtschranke              └─────────┘
                          │
                     ─────┼─────
                          │
```

```
                            DRAUFSICHT
                            
         ┌──────────────────────────────────────────────────────┐
         │                                                      │
         │   ┌─────────┐                                        │
         │   │Trichter │                                        │
         │   └────┬────┘                                        │
         │        │                                             │
         │   ┌────▼─────────────────────────────────────────┐   │
         │   │░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│   │
         │   │░░░░░░░░░░ FÖRDERBAND ░░░░░░░░░░░░░░░░░░░░░░░░│   │
         │   │░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│   │
         │   └─────────────────────┬────────────────────────┘   │
         │                         │                            │
         │            ┌────────────┼────────────┐               │
         │            │      Scan-Bereich       │               │
         │            │     ┌────┬────┐         │               │
         │            │     │ 📱 │    │         │               │
         │            │     │Cam │    │         │               │
         │            │     └────┘    │         │               │
         │            │  💡        💡 │         │               │
         │            │   Licht    ───┼── Lichtschranke         │
         │            └────────────┼──┼─────────┘               │
         │                         │  │                         │
         │                   ┌─────┴──┴─────┐                   │
         │                   │    SERVO     │                   │
         │                   │   ┌─────┐    │                   │
         │                   │   │Weiche│   │                   │
         │                   │   └──┬──┘    │                   │
         │                   └──────┼───────┘                   │
         │                          │                           │
         │        ┌─────┬─────┬─────┼─────┬─────┬─────┐        │
         │        │  1  │  2  │  3  │  4  │  5  │  6  │        │
         │        │Brick│Plate│Tile │Slope│Tech │ ??? │        │
         │        └─────┴─────┴─────┴─────┴─────┴─────┘        │
         │              AUFFANGBEHÄLTER                         │
         │                                                      │
         └──────────────────────────────────────────────────────┘
```

---

## Komponenten im Detail

### 1. Einfülltrichter (Hopper)

```
              TRICHTER - SEITENANSICHT
              
                    200mm
              ◄──────────────►
              
              ┌──────────────┐  ▲
             ╱                ╲ │
            ╱                  ╲│ 150mm
           ╱                    ╲
          ╱                      ╲▼
         ╱    ┌──────────────┐    ╲
        ╱     │   Vibrator   │     ╲
       ╱      │   (optional) │      ╲
      ╱       └──────────────┘       ╲
     │                                │
     │◄──────────── 50mm ────────────►│
     │            Auslass             │
     └────────────────────────────────┘
              │              │
              │   Rampe/     │
              │   Rutsche    │
              ▼              ▼
         ═══════════════════════
              FÖRDERBAND
              
              
    Materialoptionen:
    ├── 3D-Druck (PLA/PETG)
    ├── Holz (Sperrholz 4mm)
    ├── Acrylglas (transparent - gut zur Kontrolle)
    └── Pappe (Prototyp)
```

**Bauanleitung Trichter:**

| Material | Beschreibung | Menge |
|----------|--------------|-------|
| Sperrholz 4mm | Seitenwände | 4 Stück |
| Holzleim | Verbindung | - |
| Schleifpapier | Glätten (damit Teile rutschen) | - |

```
Optional: Vibrationsmotor
├── Kleiner DC-Motor mit Unwucht
├── Verhindert Verstopfung
└── An Arduino Pin anschließen (PWM)
```

---

### 2. Förderband-System

```
                    FÖRDERBAND - DETAILANSICHT
                    
     ◄─────────────────── 400-500mm ───────────────────►
     
     ┌─────────────────────────────────────────────────────┐
     │  Antriebs-        Band (Gummi/Silikon)    Umlenk-  │
     │  rolle                                    rolle    │
     │                                                    │
     │    ┌──┐ ═══════════════════════════════════ ┌──┐   │  ▲
     │    │██│░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│██│   │  │
     │    │██│░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│██│   │  │ 60mm
     │    │██│░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│██│   │  │ Breite
     │    └──┘ ═══════════════════════════════════ └──┘   │  │
     │      │                                       │     │  ▼
     │      │    ┌─────────────────────────────┐   │     │
     │      │    │     Aluminium-Profil        │   │     │
     │      │    │     oder Holzrahmen         │   │     │
     │      │    └─────────────────────────────┘   │     │
     │      │                                       │     │
     │    ┌─┴─┐                                   ┌─┴─┐   │
     │    │ M │ ← DC-Motor                       │   │   │
     │    │   │   mit Getriebe                   │   │   │
     │    └───┘                                   └───┘   │
     │                                                    │
     └────────────────────────────────────────────────────┘
     
     
     ROLLEN-DETAIL:
     
         ┌─────────┐
         │░░░░░░░░░│  ← Gummi-Überzug (Grip)
         │░░┌───┐░░│
         │░░│ ○ │░░│  ← Kugellager (608ZZ)
         │░░└───┘░░│
         │░░░░░░░░░│
         └─────────┘
             │
         Durchmesser: 30-40mm
```

**Stückliste Förderband:**

| Bauteil | Spezifikation | Menge | Ca. Preis |
|---------|---------------|-------|-----------|
| DC-Getriebemotor | 12V, 30-60 RPM | 1 | 8€ |
| Gummiband/Silikonband | 60mm breit, ~1m lang | 1 | 10€ |
| Kugellager 608ZZ | 8x22x7mm | 4 | 3€ |
| Gewindestange M8 | Als Achse, 80mm | 2 | 2€ |
| Alu-Profil 20x20mm | 500mm Länge | 2 | 8€ |
| 3D-Druck Rollen | Ø40mm | 2 | - |
| Muttern M8 | Achsen-Befestigung | 8 | 1€ |

**Förderband-Alternativen:**

```
EINFACHE VERSION (ohne echtes Band):

    ┌────────────────────────────────────────┐
    │                                        │
    │   Schräge Rutsche mit Vibration        │
    │                                        │
    │      ╲                           ╱     │
    │       ╲                         ╱      │
    │        ╲      ~~~vibration~~~  ╱       │
    │         ╲                     ╱        │
    │          ╲                   ╱         │
    │           ╲                 ╱          │
    │            ╲_______________╱           │
    │                   │                    │
    │                   ▼                    │
    │             Scan-Bereich               │
    │                                        │
    └────────────────────────────────────────┘
    
    Vorteile: Einfacher, weniger Teile
    Nachteile: Teile können übereinander liegen
```

---

### 3. Scan-Station (Kamerabereich)

```
                    SCAN-STATION - SEITENANSICHT
                    
                         ┌─────────────┐
                         │    📱       │
                         │   Handy     │
                         │  (Kamera)   │
                         │             │
                         │  ┌───────┐  │
                         │  │ Linse │  │
                         │  └───┬───┘  │
                         │      │      │
                         └──────┼──────┘
                                │
                         Abstand: 150-200mm
                                │
                                ▼
         ┌──────────────────────────────────────────┐
         │░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│
         │░░░░░░░░░░░ FÖRDERBAND ░░░░░░░░░░░░░░░░░░░│
         │░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│
         └──────────────────────────────────────────┘
                                │
                    ┌───────────┴───────────┐
                    │   WEISSER HINTERGRUND │
                    │   (Acryl / Papier)    │
                    └───────────────────────┘
         
         
         
                    SCAN-STATION - VORDERANSICHT
                    
                         ┌─────────┐
                         │  Handy  │
                         │  Halter │
                         └────┬────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
              │    ┌──────────┼──────────┐    │
         ┌────┴────┤          │          ├────┴────┐
         │   💡    │     ┌────┴────┐     │    💡   │
         │  LED    │     │  Lego   │     │   LED   │
         │  Ring   │     │  Teil   │     │   Ring  │
         │         │     └─────────┘     │         │
         └─────────┤                     ├─────────┘
                   │ ← Lichtschranke →   │
                   │   TX          RX    │
                   └──────────┬──────────┘
                              │
                              ▼
                        Zum Sortierer
```

**Handy-Halterung (3D-Druck oder Holz):**

```
                    HANDY-HALTERUNG
                    
        ┌─────────────────────────────────────┐
        │                                     │
        │   ┌─────────────────────────────┐   │
        │   │                             │   │
        │   │     ╔═══════════════════╗   │   │
        │   │     ║                   ║   │   │
        │   │     ║      HANDY        ║   │   │
        │   │     ║                   ║   │   │
        │   │     ║    ┌───────┐      ║   │   │
        │   │     ║    │Kamera │      ║   │   │
        │   │     ║    │  ◉    │      ║   │   │
        │   │     ║    └───────┘      ║   │   │
        │   │     ║                   ║   │   │
        │   │     ╚═══════════════════╝   │   │
        │   │              │              │   │
        │   │   Gummibänder/Klemmen      │   │
        │   │                             │   │
        │   └──────────────┬──────────────┘   │
        │                  │                  │
        │            Schwenkarm               │
        │            (einstellbar)            │
        │                  │                  │
        └──────────────────┴──────────────────┘
                           │
                       Befestigung
                       am Rahmen
```

**Beleuchtung (wichtig für gute Erkennung!):**

```
                    LED-BELEUCHTUNG
                    
    Option A: LED-Streifen          Option B: LED-Ring
    
       ┌────────────────┐           ┌─────────────┐
       │░░░░░░░░░░░░░░░░│           │   ╭─────╮   │
       └────────────────┘           │  ╱       ╲  │
                ↓                   │ │    ◉    │ │ ← Kamera
       ┌────────────────┐           │  ╲       ╱  │   in Mitte
       │                │           │   ╰─────╯   │
       │   SCAN-ZONE    │           └─────────────┘
       │                │                 ↓
       └────────────────┘           Gleichmäßiges
                ↑                   Licht ohne
       ┌────────────────┐           Schatten
       │░░░░░░░░░░░░░░░░│
       └────────────────┘
       
    Empfehlung:
    - Warmweiß oder Neutralweiß (4000-5000K)
    - Diffus (nicht direkt) für weniger Reflexionen
    - 12V LED-Streifen, ca. 5W
```

**Stückliste Scan-Station:**

| Bauteil | Spezifikation | Menge | Ca. Preis |
|---------|---------------|-------|-----------|
| LED-Streifen | 12V, warmweiß, 30cm | 2 | 5€ |
| Lichtschranke | IR, 5V, digital | 1 | 3€ |
| Weißes Acrylglas | 10x10cm, 3mm | 1 | 3€ |
| Holz/3D-Druck | Handy-Halter | 1 | 5€ |
| USB-Kabel | Handy-Verbindung | 1 | 3€ |

---

### 4. Sortierweiche

```
                    SORTIERWEICHE - KONZEPTE
                    
    
    ══════════════════════════════════════════════════════════
    OPTION A: DREHWEICHE (1 Servo)
    ══════════════════════════════════════════════════════════
    
                    ┌────────────┐
                    │   SERVO    │
                    └─────┬──────┘
                          │
                          │ Achse
                          │
              ┌───────────┴───────────┐
              │                       │
              │     DREHBARE RAMPE    │
              │                       │
             ╱           │             ╲
            ╱            │              ╲
           ╱             │               ╲
          ╱              │                ╲
         ▼               ▼                 ▼
       ┌───┐           ┌───┐            ┌───┐
       │ 1 │           │ 2 │            │ 3 │
       └───┘           └───┘            └───┘
       
       Positionen: 3-5 (je nach Servo-Winkel)
    
    
    ══════════════════════════════════════════════════════════
    OPTION B: KLAPPENWEICHE (Mehrere Servos)
    ══════════════════════════════════════════════════════════
    
         Eingang
            │
            ▼
        ┌───────┐
        │       │
        ├───────┤ ← Klappe 1 (Servo 1)
        │   ╲   │
        │    ╲──┼──► Ausgang 1
        ├───────┤
        │   ╲   │ ← Klappe 2 (Servo 2)
        │    ╲──┼──► Ausgang 2
        ├───────┤
        │   ╲   │ ← Klappe 3 (Servo 3)
        │    ╲──┼──► Ausgang 3
        └───┬───┘
            │
            ▼
        Ausgang 4 (Default)
        
       Vorteile: Mehr Kategorien möglich
       Nachteile: Mehr Servos, komplexer
    
    
    ══════════════════════════════════════════════════════════
    OPTION C: FÖRDERBAND-ABWURF (Timing-basiert)
    ══════════════════════════════════════════════════════════
    
                    Förderband
         ════════════════════════════►
                                    ┃
                             ┌──────╋──────┐
                             │      ┃      │
                           ┌─┴──┐ ┌─┴──┐ ┌─┴──┐
                           │ 1  │ │ 2  │ │ 3  │
                           └────┘ └────┘ └────┘
                           
         - Servo steuert Abstreifer
         - Position am Band bekannt
         - Abstreifer wirft Teil in richtigen Behälter
         
    
    ══════════════════════════════════════════════════════════
    OPTION D: LUFTSTOSS (Pneumatisch)
    ══════════════════════════════════════════════════════════
    
         ════════════════════════════►
                  │   │   │   │
                  ▼   ▼   ▼   ▼   ← Düsen (Magnetventile)
                ┌───┬───┬───┬───┐
                │ 1 │ 2 │ 3 │ 4 │
                └───┴───┴───┴───┘
                
         Vorteile: Sehr schnell, viele Kategorien
         Nachteile: Kompressor nötig, laut
```

**Empfohlene Lösung: Drehweiche (Option A)**

```
                    DREHWEICHE - BAUPLAN
                    
                    Draufsicht:
                    
                         ┌──────────────┐
                         │    Servo     │
                         │   ┌────┐     │
                         │   │    │     │
                         └───┴──┬─┴─────┘
                                │
                    ╔═══════════╪═══════════╗
                    ║           │           ║
                    ║      ╱────┴────╲      ║
                    ║     ╱           ╲     ║
                    ║    ╱ Drehrampe   ╲    ║
                    ║   ╱   (Holz/3D)   ╲   ║
                    ║  ╱                 ╲  ║
                    ║ ╱                   ╲ ║
                    ╚╱═════════════════════╲╝
                    ╱    │    │    │    │   ╲
                   ╱     │    │    │    │    ╲
                  ▼      ▼    ▼    ▼    ▼     ▼
                ┌────┐┌────┐┌────┐┌────┐┌────┐┌────┐
                │ 1  ││ 2  ││ 3  ││ 4  ││ 5  ││ 6  │
                │Brck││Plat││Tile││Slop││Tech││ ?? │
                └────┘└────┘└────┘└────┘└────┘└────┘
                
                
                    Seitenansicht:
                    
                         Servo
                          ┌─┐
                          │ │
                          └┬┘
                           │
                    ───────┼───────  Förderband-Ende
                           │
                        ╱──┴──╲
                       ╱       ╲     Drehrampe
                      ╱         ╲    (geneigt: 15-20°)
                     ▼           ▼
                   ┌───────────────┐
                   │   Behälter    │
                   └───────────────┘
```

**Stückliste Sortierweiche:**

| Bauteil | Spezifikation | Menge | Ca. Preis |
|---------|---------------|-------|-----------|
| Servo MG996R | Metallgetriebe, 180° | 1 | 8€ |
| Servo-Horn | Rund oder Kreuz | 1 | inkl. |
| Sperrholz 4mm | Rampe 15x10cm | 1 | 2€ |
| Schrauben M3 | Servo-Befestigung | 4 | 1€ |

---

### 5. Auffangbehälter

```
                    AUFFANGBEHÄLTER - LAYOUT
                    
    ┌─────────────────────────────────────────────────────────────┐
    │                                                             │
    │   ┌─────────┬─────────┬─────────┬─────────┬─────────┬─────┐│
    │   │         │         │         │         │         │     ││
    │   │ BRICKS  │ PLATES  │  TILES  │ SLOPES  │ TECHNIC │ ??? ││
    │   │         │         │         │         │         │     ││
    │   │  ┌───┐  │  ┌───┐  │  ┌───┐  │  ┌───┐  │  ┌───┐  │┌───┐││
    │   │  │   │  │  │   │  │  │   │  │  │   │  │  │   │  ││   │││
    │   │  │   │  │  │   │  │  │   │  │  │   │  │  │   │  ││   │││
    │   │  │   │  │  │   │  │  │   │  │  │   │  │  │   │  ││   │││
    │   │  │   │  │  │   │  │  │   │  │  │   │  │  │   │  ││   │││
    │   │  └───┘  │  └───┘  │  └───┘  │  └───┘  │  └───┘  │└───┘││
    │   │    │    │    │    │    │    │    │    │    │    │  │  ││
    │   └────┼────┴────┼────┴────┼────┴────┼────┴────┼────┴──┼──┘│
    │        │         │         │         │         │       │   │
    │        └─────────┴─────────┴────┬────┴─────────┴───────┘   │
    │                                 │                          │
    │                          Herausnehmbare                    │
    │                          Behälter                          │
    │                                                             │
    └─────────────────────────────────────────────────────────────┘
    
    Maße pro Behälter:
    - Breite: 80mm
    - Tiefe: 100mm
    - Höhe: 80mm
    
    Material-Optionen:
    ├── 3D-Druck
    ├── Kleine Plastikboxen (IKEA etc.)
    ├── Sperrholz-Kisten
    └── Pappschachteln (Prototyp)
```

---

### 6. Gesamtrahmen

```
                    GESAMTRAHMEN - EXPLOSIONSANSICHT
                    
                              Handy-Halter
                                  │
                                  ▼
                           ┌─────────────┐
                           │     📱      │
                           │             │
                           └──────┬──────┘
                                  │
    Einfülltrichter          LED-Beleuchtung
         │                        │
         ▼                        ▼
    ┌─────────┐              ┌─────────┐
    │         │              │ 💡   💡 │
    │░░░░░░░░░│              └────┬────┘
    └────┬────┘                   │
         │                        │
    ═════╪════════════════════════╪══════════════
         │      FÖRDERBAND        │            ║
    ┌────▼────────────────────────▼───────┐    ║
    │●═══════════════════════════════════●│    ║
    └─────────────────────────────────────┘    ║
         │                                     ║
         │ Rahmen aus:                         ║ Sortier-
         │ - Aluminium-Profil 20x20mm          ║ weiche
         │ - Holzlatten                        ║
         │ - 3D-Druck Verbinder                ║
         │                                     ║
    ─────┼─────────────────────────────────────╫─────
         │                                     ║
         │           GRUNDPLATTE               ║
         │         (Holz oder MDF)             ║
         │           500 x 300mm               ║
         │                                     ║
    ═════╪═════════════════════════════════════╩═════
         │
    ┌────┴────────────────────────────────────────────┐
    │  ┌──────┐┌──────┐┌──────┐┌──────┐┌──────┐┌────┐ │
    │  │      ││      ││      ││      ││      ││    │ │
    │  │  1   ││  2   ││  3   ││  4   ││  5   ││ 6  │ │
    │  └──────┘└──────┘└──────┘└──────┘└──────┘└────┘ │
    │              AUFFANGBEHÄLTER                    │
    └─────────────────────────────────────────────────┘
```

**Rahmen-Optionen:**

```
OPTION A: Aluminium-Profil (stabil, präzise)

    ┌────────────────────────────────────┐
    │  ╔════╗              ╔════╗        │
    │  ║    ║══════════════║    ║        │
    │  ║    ║              ║    ║        │
    │  ║    ║              ║    ║        │
    │  ║    ║══════════════║    ║        │
    │  ╚════╝              ╚════╝        │
    │                                    │
    │  20x20mm Alu-Profile + Winkel     │
    │  Kosten: ~30-40€                   │
    └────────────────────────────────────┘


OPTION B: Holz (günstig, einfach)

    ┌────────────────────────────────────┐
    │  ┌────┐              ┌────┐        │
    │  │    │──────────────│    │        │
    │  │    │              │    │        │
    │  │    │──────────────│    │        │
    │  └────┘              └────┘        │
    │                                    │
    │  Holzlatten 20x20mm + Schrauben   │
    │  Kosten: ~10-15€                   │
    └────────────────────────────────────┘


OPTION C: 3D-Druck Verbinder + Holzstäbe

    ┌────────────────────────────────────┐
    │  ┌──┐                  ┌──┐        │
    │  │3D├──────────────────┤3D│        │
    │  └┬─┘                  └─┬┘        │
    │   │                      │         │
    │   │    Rundholz 8mm      │         │
    │   │                      │         │
    │  ┌┴─┐                  ┌─┴┐        │
    │  │3D├──────────────────┤3D│        │
    │  └──┘                  └──┘        │
    │                                    │
    │  Kosten: ~5€ + Druckzeit           │
    └────────────────────────────────────┘
```

---

## Komplette Stückliste

### Mechanik

| Bauteil | Beschreibung | Menge | Ca. Preis |
|---------|--------------|-------|-----------|
| **Grundplatte** | MDF/Sperrholz 500x300x10mm | 1 | 5€ |
| **Rahmen** | Holzlatten 20x20mm, 2m | 4 | 8€ |
| **Förderband-Motor** | DC Getriebemotor 12V 30RPM | 1 | 8€ |
| **Förderband** | Silikonband/Gummi 60x1000mm | 1 | 10€ |
| **Rollen** | 3D-Druck Ø40mm oder Holz | 2 | 3€ |
| **Kugellager** | 608ZZ (8x22x7mm) | 4 | 4€ |
| **Achsen** | M8 Gewindestange 100mm | 2 | 2€ |
| **Servo** | MG996R Metallgetriebe | 1 | 8€ |
| **Sortierrampe** | Sperrholz/3D-Druck | 1 | 3€ |
| **Trichter** | Sperrholz/Acryl | 1 | 5€ |
| **Behälter** | Kleine Boxen 80x100x80mm | 6 | 10€ |
| **Schrauben/Muttern** | M3, M4, M8 Set | 1 | 5€ |
| **Winkel/Verbinder** | Metall oder 3D-Druck | 8 | 5€ |
| | | **Summe Mechanik:** | **~75€** |

### Elektronik

| Bauteil | Beschreibung | Menge | Ca. Preis |
|---------|--------------|-------|-----------|
| **Raspberry Pi 3** | Steuerung | 1 | vorhanden |
| **Android-Handy** | Kamera (DroidCam) | 1 | vorhanden |
| **Arduino Nano** | Motor/Servo-Steuerung | 1 | 5€ |
| **L298N** | Motortreiber | 1 | 4€ |
| **Lichtschranke** | IR Sensor digital | 1 | 3€ |
| **LED-Streifen** | 12V warmweiß 30cm | 2 | 5€ |
| **Netzteil** | 12V 3A | 1 | 8€ |
| **USB-Kabel** | Handy + Arduino | 2 | 5€ |
| **Jumper-Kabel** | Set | 1 | 3€ |
| | | **Summe Elektronik:** | **~33€** |

### Gesamtkosten

```
┌────────────────────────────────────┐
│  GESAMTKOSTEN                      │
├────────────────────────────────────┤
│  Mechanik:          ~75€           │
│  Elektronik:        ~33€           │
│  ──────────────────────────        │
│  GESAMT:           ~108€           │
│                                    │
│  (+ Raspberry Pi & Handy vorhanden)│
└────────────────────────────────────┘
```

---

## Schaltplan Übersicht

```
                         SCHALTPLAN ÜBERSICHT
                         
    ┌─────────────────────────────────────────────────────────────┐
    │                                                             │
    │                        12V Netzteil                         │
    │                            │                                │
    │              ┌─────────────┼─────────────┐                 │
    │              │             │             │                 │
    │              ▼             ▼             ▼                 │
    │         ┌────────┐    ┌────────┐    ┌────────┐             │
    │         │  L298N │    │  LED   │    │  5V    │             │
    │         │ Motor- │    │Streifen│    │ Regler │             │
    │         │ treiber│    │        │    │(LM7805)│             │
    │         └───┬────┘    └────────┘    └───┬────┘             │
    │             │                           │                   │
    │             │                           ▼                   │
    │             │    ┌─────────────────────────────────────┐   │
    │             │    │           Arduino Nano              │   │
    │             │    │                                     │   │
    │             │    │  D9 ────── PWM Motor (via L298N)    │   │
    │             │    │  D7 ────── Motor IN1                │   │
    │             │    │  D8 ────── Motor IN2                │   │
    │             │    │  D5 ────── Servo PWM                │   │
    │             │    │  D2 ────── Lichtschranke            │   │
    │             │    │  A4 ────── I2C SDA (zu Raspi)       │   │
    │             │    │  A5 ────── I2C SCL (zu Raspi)       │   │
    │             │    │                                     │   │
    │             │    └─────────────────────────────────────┘   │
    │             │                     │                        │
    │             │                     │ I2C                    │
    │             │                     ▼                        │
    │             │    ┌─────────────────────────────────────┐   │
    │             │    │         Raspberry Pi 3              │   │
    │         ┌───┘    │                                     │   │
    │         │        │  GPIO 2 ─── SDA                     │   │
    │         ▼        │  GPIO 3 ─── SCL                     │   │
    │    ┌────────┐    │  USB ────── Android Handy           │   │
    │    │Förder- │    │                                     │   │
    │    │ band   │    └─────────────────────────────────────┘   │
    │    │ Motor  │                     │                        │
    │    └────────┘                     │ USB                    │
    │                                   ▼                        │
    │                           ┌─────────────┐                  │
    │    ┌────────┐             │   Android   │                  │
    │    │ Servo  │◄────────────│    Handy    │                  │
    │    │        │             │  (DroidCam) │                  │
    │    └────────┘             └─────────────┘                  │
    │                                                             │
    └─────────────────────────────────────────────────────────────┘
```

---

## Bauanleitung Kurzfassung

```
SCHRITT 1: Grundplatte vorbereiten
├── MDF 500x300mm zuschneiden
├── Löcher für Kabel bohren
└── Optional: Füße anschrauben

SCHRITT 2: Rahmen aufbauen
├── Holzlatten zuschneiden
├── Rahmen für Förderband bauen
├── Rahmen für Kamera-Halter bauen
└── Alles auf Grundplatte montieren

SCHRITT 3: Förderband montieren
├── Rollen mit Kugellagern bestücken
├── Achsen einsetzen
├── Band aufziehen und spannen
├── Motor mit Kupplung verbinden
└── Testen!

SCHRITT 4: Scan-Station
├── Handy-Halter montieren
├── LED-Beleuchtung installieren
├── Lichtschranke positionieren
├── Weißen Hintergrund einsetzen
└── Kamera-Winkel einstellen

SCHRITT 5: Sortierweiche
├── Servo befestigen
├── Drehrampe montieren
├── Servo-Winkel kalibrieren
└── Behälter positionieren

SCHRITT 6: Elektronik
├── Arduino + Raspi montieren
├── Verkabelung nach Schaltplan
├── Software aufspielen
└── Kalibrieren und testen!
```

---

## 3D-Druck Dateien (falls vorhanden)

```
Benötigte 3D-Druck Teile:
├── Förderband_Rolle.stl (2x)
├── Handy_Halter.stl
├── Servo_Halter.stl
├── Sortier_Rampe.stl
├── Trichter.stl (optional)
├── Kabelführung.stl
└── Rahmen_Verbinder.stl (8x)

Druck-Einstellungen:
├── Material: PLA oder PETG
├── Schichtdicke: 0.2mm
├── Infill: 20-30%
└── Supports: je nach Teil
```

Soll ich für eines der Bauteile detailliertere Maße, 3D-Druck-Vorlagen oder eine genauere Montageanleitung erstellen?
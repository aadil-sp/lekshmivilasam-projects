import os
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            super().showPage()
        super().save()

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.HexColor("#64748b"))
        # Header
        self.drawString(54, 792 - 36, "Kerala State Sasthrolsavam (Sasthramela) — Electronics Project")
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(54, 792 - 42, 612 - 54, 792 - 42)
        
        # Footer
        self.line(54, 45, 612 - 54, 45)
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(612 - 54, 32, page_str)
        self.drawString(54, 32, "Smart IoT Health & Fall-Detection Bio-Band (ESP32-C3)")
        self.restoreState()

def generate_pdf(output_filename):
    doc = SimpleDocTemplate(
        output_filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=6
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#0284c7"),
        spaceAfter=14
    )
    
    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#1e293b"),
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    )
    
    h2_style = ParagraphStyle(
        'Heading2_Custom',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#0369a1"),
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor("#334155"),
        spaceAfter=6
    )

    code_style = ParagraphStyle(
        'Code_Custom',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#0f172a"),
        backColor=colors.HexColor("#f1f5f9"),
        borderPadding=6,
        spaceAfter=6
    )

    meta_style = ParagraphStyle(
        'Meta_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#475569")
    )

    story = []

    # Title & Metadata
    story.append(Paragraph("Smart IoT Health & Fall-Detection Bio-Band", title_style))
    story.append(Paragraph("On-Device Edge Analytics & Decentralized Captive Medical Portal", subtitle_style))
    
    meta_data = [
        [Paragraph("<b>Category:</b> Electronics (Sasthramela)", meta_style), Paragraph("<b>Microcontroller:</b> ESP32-C3 RISC-V (160MHz)", meta_style)],
        [Paragraph("<b>Primary Sensors:</b> MAX30102, MPU6050, DS18B20, GSR", meta_style), Paragraph("<b>Display & Controls:</b> 0.96\" OLED + 2 Tactile Buttons", meta_style)]
    ]
    meta_table = Table(meta_data, colWidths=[240, 260])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#e2e8f0")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 10))

    # Section 1: Abstract
    story.append(Paragraph("1. Executive Summary & Abstract", h1_style))
    story.append(Paragraph(
        "Geriatric individuals and solo workers face severe risks from sudden cardiac anomalies, hypoxia, psychological stress spikes, and mechanical falls. Conventional IoT wearables rely on external cellular towers or cloud servers, failing during network outages or rural emergencies. This project introduces a fully decentralized, self-contained wearable bio-band using the <b>ESP32-C3 RISC-V SoC</b>. It performs on-device biosignal filtering, multi-screen OLED navigation via two hardware tactile buttons, and hosts a standalone Wi-Fi Captive Portal (192.168.4.1) requiring zero mobile apps for immediate paramedic triage.",
        body_style
    ))

    # Section 2: Scientific Principles & Algorithms
    story.append(Paragraph("2. Scientific Principles & Mathematical Formulations", h1_style))
    
    story.append(Paragraph("A. Optical Photoplethysmography (PPG) — MAX30102", h2_style))
    story.append(Paragraph(
        "Dual-wavelength LEDs (Red 660nm, IR 880nm) measure differential absorption across pulsing arterial blood vessels. SpO2 is calculated using the ratio of ratios: <i>R = (AC_red / DC_red) / (AC_ir / DC_ir)</i>, yielding <i>SpO2 = 110 - 25 &times; R (%)</i>.",
        body_style
    ))

    story.append(Paragraph("B. Galvanic Skin Response (GSR) / Electrodermal Activity", h2_style))
    story.append(Paragraph(
        "Measures sympathetic autonomic nervous arousal via eccrine sweat gland conductance: <i>R_skin = R_ref &times; (Vin - Vout) / Vout (k&Omega;)</i> and Conductance <i>G = 1000 / R_skin (&mu;S)</i>.",
        body_style
    ))

    story.append(Paragraph("C. Dual-Threshold Fall Detection — MPU6050", h2_style))
    story.append(Paragraph(
        "Total 3D Acceleration Vector Magnitude <i>a_total = &radic;(ax&sup2; + ay&sup2; + az&sup2;)</i>. The algorithm detects free-fall weightlessness (a &lt; 0.45g for &gt;60ms) followed by ground impact (a &gt; 2.60g within 600ms) and postural alteration.",
        body_style
    ))

    # Section 3: Pinout and Interconnection Table
    story.append(Paragraph("3. Hardware Interconnection & Pin Mapping", h1_style))
    
    pin_data = [
        ["Component", "Module Pin", "ESP32-C3 Pin", "Protocol / Description"],
        ["0.96\" I2C OLED", "SDA / SCL", "GPIO 4 / GPIO 5", "Shared I2C Bus (0x3C), 3.3V"],
        ["MAX30102 PPG", "SDA / SCL", "GPIO 4 / GPIO 5", "Shared I2C Bus (0x57), 3.3V"],
        ["MPU6050 IMU", "SDA / SCL", "GPIO 4 / GPIO 5", "Shared I2C Bus (0x68), 3.3V"],
        ["DS18B20 Temp", "DQ (Data)", "GPIO 2", "OneWire Bus (4.7k&Omega; Pull-up)"],
        ["GSR Electrodes", "Analog Out", "GPIO 0", "ADC1_CH0 (12-bit Analog)"],
        ["Piezo Buzzer", "Positive (+)", "GPIO 3", "High-Decibel Pulse Siren"],
        ["Button 1 (Scroll)", "Pin 1", "GPIO 9", "Internal Pullup (Active LOW)"],
        ["Button 2 (Select)", "Pin 1", "GPIO 8", "Internal Pullup (Active LOW)"],
        ["Battery Divider", "Analog Mid", "GPIO 1", "ADC1_CH1 (100k/100k Divider)"]
    ]
    
    table_pin = Table(pin_data, colWidths=[110, 85, 95, 210])
    table_pin.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0284c7")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 8.5),
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,1), (-1,-1), 8),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#f8fafc")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(table_pin)
    story.append(Spacer(1, 10))

    # Section 4: 0.96" OLED Multi-Screen System
    story.append(Paragraph("4. 0.96\" Monochrome OLED Display & Dual-Button UI", h1_style))
    story.append(Paragraph(
        "The interface incorporates two physical buttons directly below the 128x64 display: <b>Button 1 (Scroll)</b> cycles through 5 diagnostic pages, and <b>Button 2 (Select)</b> acknowledges alarms or toggles the buzzer.",
        body_style
    ))
    
    screen_data = [
        ["Page #", "Screen Title", "Parameters Displayed", "Visual Elements"],
        ["0", "Overview Dashboard", "BPM, SpO2, Body Temp C/F, GSR, Motion", "Status bar + Battery icon"],
        ["1", "Cardiac Monitor", "Large Heart Rate BPM, SpO2 %", "Live ECG Pulse Waveform"],
        ["2", "Stress & Thermal", "GSR Skin k&Omega;, &mu;S, Body Temp", "Dynamic Stress Progress Bar"],
        ["3", "Motion & Fall", "Total G, Pitch/Roll angles, Safety State", "Inverted Fall Alarm Banner"],
        ["4", "Wi-Fi Hotspot", "SSID, Captive IP 192.168.4.1, Clients", "Buzzer Mute status indicator"]
    ]
    table_screens = Table(screen_data, colWidths=[45, 110, 195, 150])
    table_screens.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#334155")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 8),
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,1), (-1,-1), 8),
        ('BACKGROUND', (0,1), (-1,-1), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(table_screens)
    story.append(Spacer(1, 10))

    # Section 5: Bill of Materials
    story.append(Paragraph("5. Bill of Materials (BOM) & Budget", h1_style))
    bom_data = [
        ["Sl No", "Component Specification", "Qty", "Cost (INR)"],
        ["1", "ESP32-C3 RISC-V SoC Development Board", "1", "Rs. 290"],
        ["2", "0.96\" Monochrome I2C SSD1306 OLED (128x64)", "1", "Rs. 160"],
        ["3", "MAX30102 PPG Optical Heart Rate & SpO2 Module", "1", "Rs. 220"],
        ["4", "MPU6050 6-Axis Accelerometer & Gyroscope", "1", "Rs. 140"],
        ["5", "DS18B20 High-Precision Body Temp Sensor", "1", "Rs. 90"],
        ["6", "GSR Skin Conductance Sensor + Finger Straps", "1", "Rs. 210"],
        ["7", "3.7V 500mAh LiPo Battery + TP4056 USB-C Charger", "1", "Rs. 180"],
        ["8", "Tactile Push Switches, Active Buzzer & Resistors", "1 set", "Rs. 30"],
        ["9", "Enclosure, Casing & Wrist Straps", "1", "Rs. 80"],
        ["", "<b>TOTAL PROJECT COST</b>", "", "<b>Rs. 1,400 INR</b>"]
    ]
    table_bom = Table(bom_data, colWidths=[40, 280, 50, 130])
    table_bom.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0f766e")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 8.5),
        ('FONTNAME', (0,1), (-1,-2), 'Helvetica'),
        ('FONTSIZE', (0,1), (-1,-1), 8),
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor("#ccfbf1")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(table_bom)
    story.append(Spacer(1, 10))

    # Section 6: Sasthramela Viva & Q&A
    story.append(Paragraph("6. Kerala Sasthramela Viva Voce & Technical Defense", h1_style))
    viva_q1 = "<b>Q1: What prevents false alarms during vigorous movements like clapping or jogging?</b><br/>" \
              "<i>Defense:</i> The algorithm implements strict two-tier time-domain hysteresis: a freefall weightlessness state (&lt;0.45g) must precede an impact spike (&gt;2.60g) within a 600ms window, followed by post-fall orientation rest."
    story.append(Paragraph(viva_q1, body_style))
    
    viva_q2 = "<b>Q2: How does the Captive Portal operate without an active internet connection?</b><br/>" \
              "<i>Defense:</i> The ESP32-C3 acts as an independent Wi-Fi SoftAP and runs an internal DNS Server on Port 53. All DNS lookups from connected smartphones are redirected to 192.168.4.1, automatically opening the medical dashboard in the OS default captive browser."
    story.append(Paragraph(viva_q2, body_style))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"[OK] PDF generated successfully: {output_filename}")

if __name__ == "__main__":
    out_path = "/Users/aadilsp/Desktop/Antigravity/Lekshmivilasam/electronics/Health_Monitor_Band_Sasthramela_Report.pdf"
    generate_pdf(out_path)

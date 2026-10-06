import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
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
        self.drawString(54, 792 - 36, "Kerala State Sasthrolsavam (Sasthramela) — IoT Project Report")
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(54, 792 - 42, 612 - 54, 792 - 42)
        
        # Footer
        self.line(54, 45, 612 - 54, 45)
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(612 - 54, 32, page_str)
        self.drawString(54, 32, "AIoT Disaster Early Warning & Rain Simulation System (ESP32)")
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
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=4
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#059669"),
        spaceAfter=12
    )
    
    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=12.5,
        leading=16,
        textColor=colors.HexColor("#1e293b"),
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )
    
    h2_style = ParagraphStyle(
        'Heading2_Custom',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#047857"),
        spaceBefore=6,
        spaceAfter=3,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#334155"),
        spaceAfter=5
    )

    meta_style = ParagraphStyle(
        'Meta_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#475569")
    )

    story = []

    # Header & Metadata
    story.append(Paragraph("AIoT Landslide & Disaster Early Warning System", title_style))
    story.append(Paragraph("Live Autonomous Hotspot Web Dashboard, Rain Simulation & Predictive Analytics", subtitle_style))
    
    meta_data = [
        [Paragraph("<b>Category:</b> IoT & Disaster Management (Sasthramela)", meta_style), Paragraph("<b>Microcontroller:</b> ESP32 Dual-Core Xtensa (240MHz)", meta_style)],
        [Paragraph("<b>Sensors:</b> Dual Ultrasonic (HC-SR04), Soil ADC, DHT22", meta_style), Paragraph("<b>Actuator:</b> Rain Emulation Pump (Relay GPIO 22)", meta_style)],
        [Paragraph("<b>Network:</b> Standalone Wi-Fi Hotspot (192.168.4.1)", meta_style), Paragraph("<b>Prediction Engine:</b> Multivariate Risk Assessment", meta_style)]
    ]
    meta_table = Table(meta_data, colWidths=[250, 254])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#e2e8f0")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 8))

    # Section 1: Abstract
    story.append(Paragraph("1. Executive Summary & Problem Statement", h1_style))
    story.append(Paragraph(
        "Western Ghats regions in Kerala (such as Wayanad, Idukki, and Pathanamthitta) face severe recurring threats from rainfall-triggered slope failures, debris avalanches, and flash flooding. Traditional meteorological systems provide regional macro-scale warnings that fail to capture hyper-localized slope saturation and runoff dynamics.",
        body_style
    ))
    story.append(Paragraph(
        "This project introduces an autonomous, decentralized <b>AIoT Environmental Monitoring & Disaster Early Warning System</b>. Built on the ESP32 platform, it integrates a multi-sensor array measuring volumetric soil moisture, dual acoustic distance channels (stream level & catchment basin), and ambient atmospheric conditions (DHT22). A built-in <b>Rain Simulation Pump</b> operated via an optocoupler relay emulates precipitation events in laboratory and science fair demonstrations. The ESP32 hosts its own standalone Wi-Fi Access Point with an embedded real-time web dashboard and an onboard <b>Multivariate Disaster Prediction Engine</b> that computes live hazard probabilities and actionable safety alerts.",
        body_style
    ))

    # Section 2: Scientific Principles & Predictive Engine
    story.append(Paragraph("2. Scientific Principles & Predictive Risk Formulation", h1_style))
    
    story.append(Paragraph("A. Soil Moisture Pore-Water Pressure & Landslide Mechanics", h2_style))
    story.append(Paragraph(
        "According to Terzaghi's effective stress principle (<i>&sigma;' = &sigma; - u</i>), water infiltration increases pore-water pressure <i>u</i>, reducing effective stress and compromising the shear strength of slope soil (<i>&tau; = c' + (&sigma; - u) tan &phi;'</i>). Once saturation exceeds critical thresholds (&gt;75%), slope instability becomes imminent.",
        body_style
    ))

    story.append(Paragraph("B. Multivariate Predictive Hazard Scoring", h2_style))
    story.append(Paragraph(
        "The on-device predictive engine evaluates four continuous telemetry dimensions to calculate an instantaneous Hazard Index (0 - 100%):",
        body_style
    ))
    story.append(Paragraph(
        "&bull; <b>Soil Saturation Factor (45% Weight):</b> Continuous volumetric water content from ADC GPIO 34.<br/>"
        "&bull; <b>Precipitation Emulation Status (25% Weight):</b> Active rain pump relay status (GPIO 22).<br/>"
        "&bull; <b>Stream Surge / Runoff Level (20% Weight):</b> Ultrasonic distance tracking rapid catchment accumulation.<br/>"
        "&bull; <b>Atmospheric Humidity (10% Weight):</b> Ambient vapor saturation index from DHT22.",
        body_style
    ))

    # Section 3: Hardware Pinout
    story.append(Paragraph("3. Hardware Pin Mapping & Circuit Interconnections", h1_style))
    pin_data = [
        ["Hardware Module", "Pin Function", "ESP32 Pin", "Interface & Operational Logic"],
        ["Soil Moisture Sensor", "Analog Output", "GPIO 34", "ADC1_CH6 (12-bit Analog: 0-4095)"],
        ["Ultrasonic Sensor 1 (Stream)", "TRIG / ECHO", "GPIO 25 / GPIO 26", "Stream Surface Distance / Level Tracking"],
        ["Ultrasonic Sensor 2 (Catchment)", "TRIG / ECHO", "GPIO 27 / GPIO 32", "Reservoir / Catchment Water Depth"],
        ["Rain Simulation Pump Relay", "Relay Control", "GPIO 22", "Active LOW Optocoupler Relay (LOW=ON)"],
        ["DHT22 Digital Sensor", "Data Pin", "GPIO 33", "Digital Temperature & Relative Humidity"],
        ["ESP32 Wi-Fi SoC", "SoftAP Engine", "Antenna", "Standalone Hotspot at 192.168.4.1 (No Pass)"]
    ]
    table_pin = Table(pin_data, colWidths=[130, 85, 95, 194])
    table_pin.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#059669")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 8),
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,1), (-1,-1), 7.5),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#f8fafc")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(table_pin)
    story.append(Spacer(1, 8))

    # Section 4: Web Dashboard Architecture
    story.append(Paragraph("4. Embedded Web Dashboard & Telemetry Architecture", h1_style))
    web_data = [
        ["Endpoint / Route", "HTTP Method", "Payload / Format", "Functionality"],
        ["/", "GET", "HTML5 / CSS3 / JS", "Renders offline dark-theme telemetry dashboard"],
        ["/data", "GET", "JSON Object", "Real-time stream of temp, hum, soil, u1, u2, relay, hazard"],
        ["/relay?state=1", "GET", "JSON State", "Energizes relay (GPIO 22 LOW) to activate rain pump"],
        ["/relay?state=0", "GET", "JSON State", "De-energizes relay (GPIO 22 HIGH) to stop rain pump"],
        ["Captive Portal", "DNS 53", "Auto-redirect", "Automatically redirects connecting devices to 192.168.4.1"]
    ]
    table_web = Table(web_data, colWidths=[95, 75, 110, 224])
    table_web.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1e293b")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 8),
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,1), (-1,-1), 7.5),
        ('BACKGROUND', (0,1), (-1,-1), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(table_web)
    story.append(Spacer(1, 8))

    # Section 5: BOM
    story.append(Paragraph("5. Bill of Materials (BOM) & Cost Breakdown", h1_style))
    bom_data = [
        ["Sl", "Component Description", "Qty", "Unit Cost (INR)", "Total (INR)"],
        ["1", "ESP32-WROOM-32 Dual-Core Development Board", "1", "Rs. 350", "Rs. 350"],
        ["2", "HC-SR04 Ultrasonic Distance Sensors", "2", "Rs. 70", "Rs. 140"],
        ["3", "DHT22 High-Precision Digital Temp & Humidity Sensor", "1", "Rs. 160", "Rs. 160"],
        ["4", "Corrosion-Resistant Soil Moisture Sensor Probe", "1", "Rs. 80", "Rs. 80"],
        ["5", "1-Channel 5V Optocoupler Relay Module", "1", "Rs. 50", "Rs. 50"],
        ["6", "12V Submersible Rain Emulation Water Pump", "1", "Rs. 220", "Rs. 220"],
        ["7", "12V Power Supply & Step-Down Buck Converter", "1", "Rs. 180", "Rs. 180"],
        ["8", "Catchment Basin, Model Slope & Wiring Hardware", "1 set", "Rs. 170", "Rs. 170"],
        ["", "<b>TOTAL ESTIMATED PROJECT BUDGET</b>", "", "", "<b>Rs. 1,350 INR</b>"]
    ]
    table_bom = Table(bom_data, colWidths=[25, 235, 35, 100, 109])
    table_bom.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#065f46")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 8),
        ('FONTNAME', (0,1), (-1,-2), 'Helvetica'),
        ('FONTSIZE', (0,1), (-1,-1), 7.5),
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor("#d1fae5")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(table_bom)
    story.append(Spacer(1, 8))

    # Section 6: Sasthramela Viva Defense
    story.append(Paragraph("6. Kerala Sasthramela Viva Voce Defense & Key Questions", h1_style))
    viva_q1 = "<b>Q1: How does the system function if internet connectivity is completely lost during extreme weather?</b><br/>" \
              "<i>Defense:</i> The ESP32 acts as a fully self-contained Access Point (Hotspot) running an embedded web server and local risk algorithm. No external internet, cloud router, or mobile data is required; emergency personnel can connect directly to 192.168.4.1 to monitor data and control pumps."
    story.append(Paragraph(viva_q1, body_style))
    
    viva_q2 = "<b>Q2: What is the purpose of the web-controlled relay switch?</b><br/>" \
              "<i>Defense:</i> The relay operates an emulation pump that sprinkles water over the terrain model, allowing live demonstration of real-time soil saturation progression, runoff accumulation, and dynamic hazard index escalation before the Sasthramela judging panel."
    story.append(Paragraph(viva_q2, body_style))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"[OK] PDF generated successfully: {output_filename}")

if __name__ == "__main__":
    out_path = "/Users/aadilsp/Desktop/Antigravity/Lekshmivilasam/iot/Landslide_Alert_System_Sasthramela_Report.pdf"
    generate_pdf(out_path)

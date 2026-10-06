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
        self.drawString(54, 792 - 36, "Kerala State Sasthrolsavam (Sasthramela) — Robotics & AI Project")
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(54, 792 - 42, 612 - 54, 792 - 42)
        
        # Footer
        self.line(54, 45, 612 - 54, 45)
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(612 - 54, 32, page_str)
        self.drawString(54, 32, "Dobot Magician Lite 4-DOF Manipulator with Computer Vision")
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
        fontSize=19,
        leading=23,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=6
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11.5,
        leading=15,
        textColor=colors.HexColor("#2563eb"),
        spaceAfter=14
    )
    
    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=13.5,
        leading=17,
        textColor=colors.HexColor("#1e293b"),
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    )
    
    h2_style = ParagraphStyle(
        'Heading2_Custom',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=14,
        textColor=colors.HexColor("#1d4ed8"),
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor("#334155"),
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
    story.append(Paragraph("Intelligent 4-DOF Articulated Robotic Arm", title_style))
    story.append(Paragraph("Computer Vision Color Sorting & Embedded MicroPython Magic Box Control", subtitle_style))
    
    meta_data = [
        [Paragraph("<b>Category:</b> Robotics & AI (Sasthramela)", meta_style), Paragraph("<b>Manipulator:</b> Dobot Magician Lite 4-DOF", meta_style)],
        [Paragraph("<b>Controller:</b> Dobot Magic Box (MicroPython)", meta_style), Paragraph("<b>Vision Pipeline:</b> OpenCV HSV + Homography Calibration", meta_style)]
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
        "Modern smart factories rely on autonomous articulated manipulators for high-speed, precision sorting and packaging. This project demonstrates an <b>Intelligent 4-DOF Articulated Robotic Arm</b> using the <b>Dobot Magician Lite</b> and its embedded <b>Magic Box Controller</b>. A real-time computer vision pipeline performs color segmentation and homography transformation, mapping 2D image coordinates into 3D robot Cartesian coordinates (X, Y, Z, R). The Magic Box executes autonomous MicroPython trajectories with pneumatic suction and gripper actuation, supporting offline stand-alone industrial sorting.",
        body_style
    ))

    # Section 2: Kinematics & Homography
    story.append(Paragraph("2. Kinematic & Mathematical Principles", h1_style))
    
    story.append(Paragraph("A. Inverse Kinematics Geometry", h2_style))
    story.append(Paragraph(
        "Given target position (X,Y,Z): Base angle <i>&theta;1 = atan2(Y, X)</i>. The planar 2-link law of cosines yields elbow angle <i>&theta;3 = arccos((r&sup2; + Z&sup2; - L1&sup2; - L2&sup2;) / 2L1L2)</i> and shoulder angle <i>&theta;2</i>, ensuring &plusmn;0.2mm position repeatability.",
        body_style
    ))

    story.append(Paragraph("B. Computer Vision Homography Calibration", h2_style))
    story.append(Paragraph(
        "A 4-point perspective transform projects pixel space into robot millimeter space: <i>[X_robot, Y_robot, 1]<sup>T</sup> = <b>H</b> &middot; [u_pixel, v_pixel, 1]<sup>T</sup></i>, removing camera lens distortion and skew.",
        body_style
    ))

    # Section 3: Hardware Specifications
    story.append(Paragraph("3. Technical Hardware Specifications", h1_style))
    specs_data = [
        ["Parameter", "Dobot Magician Lite Specification"],
        ["Degrees of Freedom (DOF)", "4-Axis (Base J1, Rear Arm J2, Forearm J3, End Servo J4)"],
        ["Position Repeatability", "&plusmn; 0.2 mm"],
        ["Maximum Payload", "250 g"],
        ["Working Reach Radius", "340 mm"],
        ["End Effectors Supported", "Vacuum Suction Cup, Pneumatic Soft Gripper, Pen Holder"],
        ["Controller Architecture", "ARM Cortex-M4 running FreeRTOS MicroPython Engine"],
        ["Host Communication", "USB VCP Serial (115200 Baud) & MicroPython Mass Storage"]
    ]
    table_specs = Table(specs_data, colWidths=[170, 330])
    table_specs.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2563eb")),
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
    story.append(table_specs)
    story.append(Spacer(1, 10))

    # Section 4: Viva Voce
    story.append(Paragraph("4. Kerala Sasthramela Viva Voce & Technical Defense", h1_style))
    viva_q1 = "<b>Q1: Why is JUMP trajectory mode preferred over straight linear interpolation during pick-and-place?</b><br/>" \
              "<i>Defense:</i> JUMP mode introduces automated vertical lift (&Delta;Z) before planar transit and vertical descent at the destination. This prevents end-effector collisions with container walls and sorting bins while minimizing motor joint wear."
    story.append(Paragraph(viva_q1, body_style))
    
    viva_q2 = "<b>Q2: How does the Magic Box controller allow offline operation without a computer?</b><br/>" \
              "<i>Defense:</i> The Magic Box features an integrated ARM Cortex-M4 SoC running an embedded MicroPython runtime. Scripts stored in the internal flash filesystem (<i>/Volumes/NO NAME 1/Script/</i>) can be launched directly via the hardware run button on the Magic Box chassis."
    story.append(Paragraph(viva_q2, body_style))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"[OK] PDF generated successfully: {output_filename}")

if __name__ == "__main__":
    out_path = "/Users/aadilsp/Desktop/Antigravity/Lekshmivilasam/dobot/Dobot_Magician_Lite_Sasthramela_Report.pdf"
    generate_pdf(out_path)

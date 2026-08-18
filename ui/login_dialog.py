from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, 
                               QPushButton, QLineEdit, QLabel, QMessageBox)
from PySide6.QtCore import Qt
from services.usuario_service import autenticar_por_pin

class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Acceso - ProPyme POS")
        self.setFixedSize(340, 460)
        self.setStyleSheet("background-color: #1E1E24; border-radius: 10px;")
        
        self.usuario_autenticado = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)

        # Encabezado
        lbl_titulo = QLabel("ProPyme POS")
        lbl_titulo.setStyleSheet("color: #BFA2DB; font-size: 22px; font-weight: bold;")
        lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl_subtitulo = QLabel("Ingresa tu PIN de acceso")
        lbl_subtitulo.setStyleSheet("color: #A0A0B0; font-size: 13px;")
        lbl_subtitulo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(lbl_titulo)
        layout.addWidget(lbl_subtitulo)

        # Campo PIN (oculto)
        self.inp_pin = QLineEdit()
        self.inp_pin.setEchoMode(QLineEdit.EchoMode.Password)
        self.inp_pin.setMaxLength(6)
        self.inp_pin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.inp_pin.setPlaceholderText("••••")
        self.inp_pin.setStyleSheet("""
            QLineEdit {
                background-color: #2D2D3A;
                color: #FFFFFF;
                border: 2px solid #4A4A5A;
                border-radius: 8px;
                padding: 10px;
                font-size: 24px;
                font-weight: bold;
                letter-spacing: 8px;
            }
            QLineEdit:focus { border: 2px solid #BFA2DB; }
        """)
        self.inp_pin.returnPressed.connect(self.procesar_login)
        layout.addWidget(self.inp_pin)

        # Teclado Numérico
        grid_keypad = QGridLayout()
        grid_keypad.setSpacing(8)

        botones = [
            ('1', 0, 0), ('2', 0, 1), ('3', 0, 2),
            ('4', 1, 0), ('5', 1, 1), ('6', 1, 2),
            ('7', 2, 0), ('8', 2, 1), ('9', 2, 2),
            ('C', 3, 0), ('0', 3, 1), ('⌫', 3, 2)
        ]

        for texto, f, c in botones:
            btn = QPushButton(texto)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            
            if texto == 'C':
                btn.setStyleSheet(self._estilo_boton("#D32F2F", "#FFFFFF"))
                btn.clicked.connect(self.inp_pin.clear)
            elif texto == '⌫':
                btn.setStyleSheet(self._estilo_boton("#4A4A5A", "#FFFFFF"))
                btn.clicked.connect(self.inp_pin.backspace)
            else:
                btn.setStyleSheet(self._estilo_boton("#2D2D3A", "#FFFFFF"))
                btn.clicked.connect(lambda _, t=texto: self.inp_pin.setText(self.inp_pin.text() + t))
                
            grid_keypad.addWidget(btn, f, c)

        layout.addLayout(grid_keypad)

        # Botón Ingresar
        self.btn_ingresar = QPushButton("Ingresar al Sistema")
        self.btn_ingresar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_ingresar.setStyleSheet("""
            QPushButton {
                background-color: #BFA2DB;
                color: #1E1E24;
                border: none;
                padding: 12px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #A888CB; }
            QPushButton:pressed { background-color: #9370DB; color: white; }
        """)
        self.btn_ingresar.clicked.connect(self.procesar_login)
        layout.addWidget(self.btn_ingresar)

        self.inp_pin.setFocus()

    def _estilo_boton(self, bg_color, text_color):
        return f"""
            QPushButton {{
                background-color: {bg_color};
                color: {text_color};
                border: none;
                padding: 12px;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
                min-width: 50px;
                min-height: 20px;
            }}
            QPushButton:hover {{
                opacity: 0.9;
            }}
            QPushButton:pressed {{
                background-color: #BFA2DB;
                color: #1E1E24;
            }}
        """

    def procesar_login(self):
        pin = self.inp_pin.text().strip()
        exito, resultado = autenticar_por_pin(pin)
        
        if exito:
            self.usuario_autenticado = resultado
            self.accept()
        else:
            QMessageBox.warning(self, "Acceso Denegado", resultado)
            self.inp_pin.clear()
            self.inp_pin.setFocus()
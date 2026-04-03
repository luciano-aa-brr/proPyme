import sys
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    
    # Inicia la ventana ocupando todo el espacio disponible
    window.showMaximized() 
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
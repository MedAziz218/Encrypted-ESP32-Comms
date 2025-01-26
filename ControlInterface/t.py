from PyQt6.QtCore import QTimer, Qt, QRectF, QEvent
from PyQt6.QtGui import QImage, QPixmap, QPainter, QPen, QFont, QBrush, QColor
from PyQt6.QtWidgets import QApplication, QLabel, QMainWindow
from PyQt6.QtGui import QKeySequence, QShortcut
import asyncio
import sys

class VideoStreamApp(QMainWindow):
    closed = False
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Encrypted Messages")

    def closeEvent(self, event):
        print("Window Closed  ")
        self.closed = True
        event.accept()

async def main():
    print("Creating PyQt6 window")
    app = QApplication(sys.argv)
    window = VideoStreamApp()
    print("->> Finished Creating PyQt6 window")

    window.show()
    while not window.closed:
        app.processEvents()  # Process Qt events
        await asyncio.sleep(1/60)  # Give control back to asyncio



if __name__ == "__main__":
    asyncio.run(main())
# main.py

import sys
from PyQt5.QtWidgets import QApplication
from player.multi_video_player import MultiVideoPlayerWindow

def main():
    app = QApplication(sys.argv)
    window = MultiVideoPlayerWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()

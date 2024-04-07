from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QPushButton,
    QLineEdit,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QWidget,
    QLabel,
    QProgressBar,
    QSizePolicy,
    QFileDialog,
    QMessageBox
)
from PySide6.QtCore import Slot, QObject, Signal
from PySide6.QtGui import QIntValidator
from PIL import Image
from .image_canvas import MplCanvas
import numpy as np
from .ct_methods import ct_iter
from threading import Thread, Event


class UpdateImageSignal(QObject):
    """
    Сигнал для обновления изображения.
    Рабочий поток сообщает главному потоку приложения, что вычисление окончено и
    нужно обновить изображение КТ.
    """
    update_image = Signal()

class ProgressSignal(QObject):
    # Сигнал для progress bar
    progress_event = Signal(int)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CT Scan")
        self.is_ct_running = False
        self.source_image = None
        self.reconstructed_image = None
        self.interrupt_event = Event()
       

        main_horizontal_layout = QHBoxLayout()
        images_horizontal_layout = QHBoxLayout()
        controls_grid_layout = QGridLayout()

        self.update_image_signal = UpdateImageSignal()
        self.update_image_signal.update_image.connect(self.update_image)

        self.progress_event_signal = ProgressSignal()
        self.progress_event_signal.progress_event.connect(self.update_progress)


        int_validator = QIntValidator(0, 9999)

        self.source_image_canvas = MplCanvas()
        self.ct_image_canvas = MplCanvas()
        self.source_image_canvas.axes.set_title("Исходный объект")
        self.ct_image_canvas.axes.set_title("Результат КТ")



        self.image_path_edit = QLineEdit()
        self.image_path_edit.setPlaceholderText("Путь к изображению...")
        self.image_path_edit.setReadOnly(True)


        self.choose_image_button = QPushButton("Загрузить...")
        self.choose_image_button.clicked.connect(self.choose_image_clicked)


        self.angle_ticks = 20
        self.angle_ticks_edit = QLineEdit("20")
        self.angle_ticks_edit.setValidator(int_validator)
        self.angle_ticks_edit.setSizePolicy(QSizePolicy()) # Фиксированный размер (дефолт)
        #self.angle_ticks_edit.setFixedWidth(100)

        self.iterations = 10
        self.iterations_edit = QLineEdit("10")
        self.iterations_edit.setValidator(int_validator)
        self.iterations_edit.setSizePolicy(QSizePolicy())
        #self.iterations_edit.setFixedWidth(100)


        self.start_stop_button = QPushButton("Старт")
        self.start_stop_button.setSizePolicy(QSizePolicy())
        self.start_stop_button.clicked.connect(self.start_stop_clicked)


        self.cancel_button = QPushButton("Прервать")
        self.cancel_button.setObjectName("cancel_button")
        self.cancel_button.setSizePolicy(QSizePolicy())
        self.cancel_button.setDisabled(True)
        self.cancel_button.clicked.connect(self.cancel_clicked)

        self.pbar = QProgressBar()

        images_horizontal_layout.addWidget(self.source_image_canvas, 1)
        images_horizontal_layout.addWidget(self.ct_image_canvas, 1)
        #images_horizontal_layout.setSpacing(25)
        #images_horizontal_layout.setContentsMargins(25,25,25,25)

        controls_grid_layout.addWidget(QLabel("Изображение: "), 0, 0, 1, 1)
        controls_grid_layout.addWidget(self.image_path_edit, 1, 0, 1, 1)
        controls_grid_layout.addWidget(self.choose_image_button, 1, 1, 1, 1)
        controls_grid_layout.addWidget(QLabel("Число отсчетов по углу: "), 2, 0, 1, 1)
        controls_grid_layout.addWidget(self.angle_ticks_edit, 3, 0, 1, 1)
        controls_grid_layout.addWidget(QLabel("Количество итераций: "), 4, 0, 1, 1)
        controls_grid_layout.addWidget(self.iterations_edit, 5, 0, 1, 1)

        start_button_layout = QHBoxLayout()
        start_button_layout.addWidget(self.start_stop_button, 0)
        start_button_layout.addWidget(self.cancel_button, 0)
        start_button_layout.addWidget(QWidget(),1)
        controls_grid_layout.addLayout(start_button_layout, 6, 0, 1, 1)
        controls_grid_layout.addWidget(self.pbar, 7, 0, 1, 2)
        controls_grid_layout.addWidget(QWidget(),8, 0, 1, 2)
        controls_grid_layout.setRowStretch(8, 1)

        images_dummy_widget = QWidget()
        images_dummy_widget.setObjectName('dummy')
        controls_dummy_widget = QWidget()
        controls_dummy_widget.setObjectName('dummy')

        images_dummy_widget.setLayout(images_horizontal_layout)
        controls_dummy_widget.setLayout(controls_grid_layout)
        controls_dummy_widget.setContentsMargins(10,10,10,10)

        main_horizontal_layout.addWidget(images_dummy_widget, 5)
        main_horizontal_layout.addWidget(controls_dummy_widget, 2)
        main_horizontal_layout.setContentsMargins(25, 25, 25, 25)
        main_horizontal_layout.setSpacing(25)

        main_dummy_widget = QWidget()
        main_dummy_widget.setLayout(main_horizontal_layout)
        main_dummy_widget.setObjectName('main_dummy_widget')
        self.setCentralWidget(main_dummy_widget)

    @Slot()
    def update_image(self):
        if self.reconstructed_image is not None:
            self.ct_image_canvas.axes.cla()
            self.ct_image_canvas.axes.imshow(self.reconstructed_image, cmap='gray')
            self.ct_image_canvas.axes.set_title("Результат КТ")
            self.ct_image_canvas.draw()
                
    @Slot()
    def update_progress(self, percent):
        try:
            percent = int(percent)
        except ValueError:
            msgBox = QMessageBox.about(self, "Invalid value for progress bar")
            return
        self.pbar.setValue(percent)


    @Slot()
    def start_stop_clicked(self):
        if not self.is_ct_running:
            if self.source_image is None:
                QMessageBox.about(self, "Oops...", "Изображение не загружено")
                return
            self.cancel_button.setEnabled(True)
            self.start_stop_button.setDisabled(True)
            self.is_ct_running = True
            worker_thread = Thread(target=self.ct_worker_func)
            worker_thread.start()
            self.pbar.setValue(0)


    @Slot()
    def choose_image_clicked(self):
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
        dialog.setNameFilter("Images (*.png *.jpg *.bmp)")
        if dialog.exec_():
            fileNames = dialog.selectedFiles()
            image = Image.open(fileNames[0])
            image = image.convert('L')
            self.source_image = np.array(image, dtype=float)
            self.source_image_canvas.axes.cla()
            self.source_image_canvas.axes.imshow(self.source_image, cmap='gray')
            self.source_image_canvas.axes.set_title('Исходный объект')
            self.source_image_canvas.draw()
            self.image_path_edit.setText(fileNames[0])
            print(self.source_image.shape)
            print(self.source_image)

    @Slot()
    def cancel_clicked(self):
        if self.is_ct_running:
            self.cancel_button.setDisabled(True)
            self.interrupt_event.set()

    def ct_worker_func(self):
        angle_ticks = int(self.angle_ticks_edit.text())
        iters = int(self.iterations_edit.text())
        self.reconstructed_image = ct_iter(self.source_image, angle_ticks, iters, self.interrupt_event, self.progress_event_signal)
        self.update_image_signal.update_image.emit()
        self.is_ct_running = False
        self.start_stop_button.setEnabled(True)
        self.cancel_button.setDisabled(True)
        self.interrupt_event.clear()


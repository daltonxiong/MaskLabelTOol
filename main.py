import logging
import os
import sys
from pathlib import Path

from PySide2 import QtCore
from PySide2.QtCore import Qt, QSize, QRect, QPoint
from PySide2.QtGui import QKeySequence, QIntValidator, QPainter, QPixmap, QColor, QPen, QCursor, QMatrix, QPalette
from PySide2.QtWidgets import QApplication
from PySide2.QtWidgets import QDesktopWidget
from PySide2.QtWidgets import QHBoxLayout
from PySide2.QtWidgets import QLabel
from PySide2.QtWidgets import QPushButton
from PySide2.QtWidgets import QShortcut
from PySide2.QtWidgets import QVBoxLayout
from PySide2.QtWidgets import QWidget, QLineEdit, QMessageBox, QFileDialog, QColorDialog


class ImageLabel(QLabel):
    def __init__(self, parent, label_img_size, brush_color, eraser_color):
        super(ImageLabel, self).__init__(parent)

        self.label_img = None
        self.mask_img = None
        self.mask_img_path = None

        self.label_img_size = label_img_size
        self.img_rect = QRect(QPoint(0,0), QPoint(self.label_img_size.width(), self.label_img_size.height()))

        self.mask_img = QPixmap(self.label_img_size)
        self.mask_img.fill(QColor(255, 255, 255))

        self.mouse_press_flag = False
        self.mouse_pos = None

        self.eraser_painting_model = False
        self.brush_pixle_size = 5
        self.eraser_pixle_size = 5

        self.brush_color = brush_color
        self.eraser_color = eraser_color

        self.brush_model_cursor = None
        self.eraser_model_cursor = None

        self.update_brush_pixle_size(self.brush_pixle_size)
        self.update_eraser_pixle_size(self.eraser_pixle_size)

        self.setCursor(self.brush_model_cursor)

    def update_brush_color(self, color):
        self.brush_color = color
        self.update_brush_pixle_size(self.brush_pixle_size)

    def update_brush_pixle_size(self, pixle_size):
        self.brush_pixle_size = pixle_size

        brush_cursor_pix = QPixmap(QSize(self.brush_pixle_size, self.brush_pixle_size))
        brush_cursor_pix.fill(QColor(0, 0, 0))
        brush_cursor_pix_painter = QPainter(brush_cursor_pix)
        brush_cursor_pix_painter.setBrush(self.brush_color)
        brush_cursor_pix_painter.drawEllipse(QRect(QPoint(-2,-2), QPoint(self.brush_pixle_size, self.brush_pixle_size)))
        brush_cursor_pix_painter.end()
        brush_cursor_pix.setMask(brush_cursor_pix.createMaskFromColor(self.brush_color, Qt.MaskOutColor))

        self.brush_model_cursor = QCursor(brush_cursor_pix)

        if not self.eraser_painting_model:
            self.setCursor(self.brush_model_cursor)

    def update_eraser_pixle_size(self, pixle_size):
        self.eraser_pixle_size = pixle_size

        eraser_cursor_pix = QPixmap(QSize(self.eraser_pixle_size, self.eraser_pixle_size))
        eraser_cursor_pix.fill(QColor(255, 255, 255))
        eraser_cursor_pix_painter = QPainter(eraser_cursor_pix)
        eraser_cursor_pix_painter.setBrush(self.eraser_color)
        eraser_cursor_pix_painter.drawEllipse(QRect(QPoint(-2,-2), QPoint(self.eraser_pixle_size, self.eraser_pixle_size)))
        eraser_cursor_pix_painter.end()
        eraser_cursor_pix.setMask(eraser_cursor_pix.createMaskFromColor(self.eraser_color, Qt.MaskOutColor))

        self.eraser_model_cursor = QCursor(eraser_cursor_pix)

        if self.eraser_painting_model:
            self.setCursor(self.eraser_model_cursor)

    def update_label_img(self, label_img, mask_img, mask_img_path):
        self.label_img = label_img.scaled(self.label_img_size)
        self.mask_img = mask_img
        self.mask_img.setMask(self.mask_img.createMaskFromColor(self.brush_color, Qt.MaskOutColor))
        self.mask_img_path = mask_img_path
        self.update()

    def join_pixmap(self, p1, p2):

        result = QPixmap(p1.size())
        result.fill(QtCore.Qt.transparent)
        painter = QPainter(result)
        painter.setRenderHint(QPainter.Antialiasing)

        painter.setCompositionMode(QPainter.CompositionMode_Source)
        painter.drawPixmap(QtCore.QPoint(), p1)

        painter.setCompositionMode(QPainter.CompositionMode_Overlay)
        painter.drawPixmap(QtCore.QPoint(), p2)

        painter.end()
        return result

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            if QApplication.keyboardModifiers() == QtCore.Qt.AltModifier:
                self.eraser_painting_model = True
                self.setCursor(self.eraser_model_cursor)
            else:
                self.eraser_painting_model = False
                self.setCursor(self.brush_model_cursor)

            self.mouse_press_flag = True
            self.mouse_pos = event.pos()
            self.update()

    def mouseMoveEvent(self, event):
        if not self.mouse_press_flag:
            return

        if QApplication.keyboardModifiers() == QtCore.Qt.AltModifier:
            self.eraser_painting_model = True
            self.setCursor(self.eraser_model_cursor)
        else:
            self.eraser_painting_model = False
            self.setCursor(self.brush_model_cursor)

        self.mouse_pos = event.pos()
        self.update()

    def mouseReleaseEvent(self, event):
        if self.mask_img:
            self.mask_img.save(self.mask_img_path)

        if not self.mouse_press_flag:
            return

        if event.button() == QtCore.Qt.LeftButton:
            self.mouse_press_flag = False
            self.mouse_pos = None

            self.eraser_painting_model = False
            self.setCursor(self.brush_model_cursor)
            self.parent().show_label_img()


    def paintEvent(self, QPaintEvent):
        painter = QPainter()
        painter.begin(self)
        painter.setPen(Qt.NoPen)
        painter.fillRect(self.rect(), QColor(190, 190, 190, 255))


        if self.label_img:
            if self.mouse_press_flag and self.mouse_pos:
                pp = QPainter(self.mask_img)
                if self.eraser_painting_model:
                    pp.setPen(QPen(self.eraser_color, self.eraser_pixle_size, Qt.SolidLine, Qt.RoundCap, Qt.BevelJoin))
                else:
                    pp.setPen(QPen(self.brush_color, self.brush_pixle_size, Qt.SolidLine, Qt.RoundCap, Qt.BevelJoin))

                pp.drawPoint(self.mouse_pos - self.img_rect.topLeft())

            result_pixmap = self.join_pixmap(self.label_img, self.mask_img)
            painter.drawPixmap(self.img_rect, result_pixmap)

        painter.end()

    def resizeEvent(self, event):
        x = (self.size().width() - self.label_img_size.width()) // 2
        y = (self.size().height() - self.label_img_size.height()) // 2
        self.img_rect = QRect(QPoint(x,y), QPoint(self.label_img_size.width()+x, self.label_img_size.height()+y))

class MainWindow(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)

        self.setWindowTitle('MASK标注工具')
        self.setFixedSize(1000, 650)
        self.move_to_center()

        #
        self.mask_img_size = QSize(512,512)
        self.brush_color = QColor(255,255,0)
        self.eraser_color = QColor(0,0,0)
        self.label_img = ImageLabel(self,self.mask_img_size, self.brush_color, self.eraser_color)
        self.label_img.setAlignment(Qt.AlignCenter)
        self.label_img.setText('没有选择任何图片')
        self.label_img.setFixedWidth(700)
        self.label_img.setFixedHeight(600)

        #
        self.btn_select_dir = QPushButton(self)
        self.btn_select_dir.setText('选择目录...')
        self.btn_select_dir.clicked.connect(self.on_btn_select_dir)

        self.btn_prev_img = QPushButton(self)
        self.btn_prev_img.setText('上一张')
        self.btn_prev_img.clicked.connect(self.on_btn_prev_img)
        self.connect(
            QShortcut(QKeySequence(Qt.Key_Left), self),
            QtCore.SIGNAL('activated()'),
            self.btn_prev_img.click
        )

        self.btn_next_img = QPushButton(self)
        self.btn_next_img.setText('下一张')
        self.btn_next_img.clicked.connect(self.on_btn_next_img)
        self.connect(
            QShortcut(QKeySequence(Qt.Key_Right), self),
            QtCore.SIGNAL('activated()'),
            self.btn_next_img.click
        )

        self.btn_select_brush_color = QPushButton(self)
        self.btn_select_brush_color.setText('修改画笔颜色')
        self.btn_select_brush_color.clicked.connect(self.on_btn_select_brush_color)

        self.label_brush_color = QLabel(self)
        self.label_brush_color.setFixedWidth(50)

        pe = QPalette()
        pe.setColor(QPalette.Window, self.brush_color)
        self.label_brush_color.setPalette(pe)
        self.label_brush_color.setAutoFillBackground(True)

        self.defalut_brush_pixle_size = 5
        self.min_brush_pixle_size = 1
        self.max_brush_pixle_size = 50
        self.label_brush_pixle_size = QLabel('画笔像素大小:')
        self.label_brush_pixle_size.setFixedWidth(110)
        self.edit_brush_pixle_size_validator = QIntValidator()
        self.edit_brush_pixle_size_validator.setRange(self.min_brush_pixle_size, self.max_brush_pixle_size)
        self.edit_brush_pixle_size = QLineEdit(self)
        self.edit_brush_pixle_size.setText(f'{self.defalut_brush_pixle_size}')
        self.edit_brush_pixle_size.setValidator(self.edit_brush_pixle_size_validator)
        self.edit_brush_pixle_size.textChanged.connect(self.on_edit_brush_pixle_size_change)

        self.label_img.update_brush_pixle_size(self.defalut_brush_pixle_size)

        self.defalut_eraser_pixle_size = 50
        self.min_eraser_pixle_size = 5
        self.max_eraser_pixle_size = 50
        self.label_eraser_pixle_size = QLabel('橡皮擦像素大小:')
        self.label_eraser_pixle_size.setFixedWidth(110)
        self.edit_eraser_pixle_size_validator = QIntValidator()
        self.edit_eraser_pixle_size_validator.setRange(self.min_eraser_pixle_size, self.max_eraser_pixle_size)
        self.edit_eraser_pixle_size = QLineEdit(self)
        self.edit_eraser_pixle_size.setText(f'{self.defalut_eraser_pixle_size}')
        self.edit_eraser_pixle_size.setValidator(self.edit_eraser_pixle_size_validator)
        self.edit_eraser_pixle_size.textChanged.connect(self.on_edit_eraser_pixle_size_change)

        self.label_img.update_eraser_pixle_size(self.defalut_eraser_pixle_size)

        self.btn_clear_mask = QPushButton(self)
        self.btn_clear_mask.setText('全部擦除')
        self.btn_clear_mask.clicked.connect(self.on_btn_clear_mask)

        self.btn_roate = QPushButton(self)
        self.btn_roate.setText('旋转')
        self.btn_roate.clicked.connect(self.on_btn_roate)

        self.btn_roate_img = QPushButton(self)
        self.btn_roate_img.setText('旋转原图')
        self.btn_roate_img.clicked.connect(self.on_btn_roate_img)
        self.connect(
            QShortcut(QKeySequence(Qt.Key_Up), self),
            QtCore.SIGNAL('activated()'),
            self.btn_roate_img.click
        )

        self.btn_roate_mask = QPushButton(self)
        self.btn_roate_mask.setText('旋转标注图')
        self.btn_roate_mask.clicked.connect(self.on_btn_roate_mask)

        self.label_lable_docs = QLabel(self)
        self.label_lable_docs.setAlignment(Qt.AlignLeft)
        self.label_lable_docs.setText(r'''
- 鼠标左键拖动,绘制标注内容
- ALT+鼠标左键拖动,擦除标注内容

- CTRL+鼠标滚轮,调整画笔像素大小
- ALT+鼠标滚轮,调整橡皮擦像素大小

- 键盘左方向键切换到上一张图片
- 键盘右方向键切换到下一张图片

- 输入张数加回车跳转到指定张数
        ''')

        self.label_status_running1 = QLabel(self)
        self.label_status_running1.setAlignment(Qt.AlignLeft)
        self.label_status_running1.setText('请选择需要标注的目录')

        self.label_status_page_number_validator = QIntValidator()
        self.label_status_page_number = QLineEdit(self)
        self.label_status_page_number.setMaximumWidth(50)
        self.label_status_page_number.setValidator(self.label_status_page_number_validator)
        self.label_status_page_number.hide()
        self.label_status_page_number.returnPressed.connect(self.on_page_jump)

        self.label_status_running2 = QLabel(self)
        self.label_status_running2.setAlignment(Qt.AlignLeft)
        self.label_status_running2.setText('张')
        self.label_status_running2.hide()


        # 布局
        layout_root = QVBoxLayout()

        layout_root2 = QHBoxLayout()
        layout_col1 = QVBoxLayout()
        layout_col2 = QVBoxLayout()
        layout_root2.addLayout(layout_col1)
        layout_root2.addLayout(layout_col2)
        layout_root_row2 = QHBoxLayout()

        layout_root.addLayout(layout_root2)
        layout_root.addLayout(layout_root_row2)

        layout_root_row2.addWidget(self.label_status_running1)
        layout_root_row2.addWidget(self.label_status_page_number)
        layout_root_row2.addWidget(self.label_status_running2)

        layout_col1.addWidget(self.label_img)


        layout_col2_row1 = QHBoxLayout()
        layout_col2_row1.addWidget(self.btn_select_dir)

        layout_col2_row2 = QHBoxLayout()
        layout_col2_row2.addWidget(self.btn_prev_img)
        layout_col2_row2.addWidget(self.btn_next_img)

        layout_col2_row3 = QHBoxLayout()
        layout_col2_row3.addWidget(self.label_brush_pixle_size)
        layout_col2_row3.addWidget(self.edit_brush_pixle_size)

        layout_col2_row4 = QHBoxLayout()
        layout_col2_row4.addWidget(self.label_eraser_pixle_size)
        layout_col2_row4.addWidget(self.edit_eraser_pixle_size)

        layout_col2_row5 = QHBoxLayout()
        layout_col2_row5.addWidget(self.btn_select_brush_color)
        layout_col2_row5.addWidget(self.label_brush_color)

        layout_col2.addLayout(layout_col2_row1)
        layout_col2.addLayout(layout_col2_row2)
        layout_col2.addLayout(layout_col2_row5)
        layout_col2.addLayout(layout_col2_row3)
        layout_col2.addLayout(layout_col2_row4)
        layout_col2.addWidget(self.btn_clear_mask)
        layout_col2.addWidget(self.btn_roate)
        layout_col2.addWidget(self.btn_roate_img)
        layout_col2.addWidget(self.btn_roate_mask)
        layout_col2.addWidget(self.label_lable_docs)
        layout_col2.addStretch()

        self.setLayout(layout_root)

        # 其他数据
        self.directory = None
        self.all_img_file = []
        self.all_img_file_index = 0

        self.update_btn_status()


    def move_to_center(self):
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) / 2, (screen.height() - size.height()) / 2)

    def on_btn_select_dir(self):
        try:
            self.directory = QFileDialog.getExistingDirectory(self, '选择图片目录')

            all_img_file = sorted([x for x in Path(self.directory).iterdir(
            ) if x.is_file() and x.suffix.upper() in ['.JPG', '.JPEG', '.BMP', '.PNG']])

            if len(all_img_file) <= 0:
                QMessageBox.information(
                    self,
                    '<提示>',
                    f'{self.directory}\n目录下没有找到图片文件',
                    QMessageBox.Ok
                )
                return

            self.setWindowTitle(f'MASK标注工具: {self.directory}')
            self.all_img_file = all_img_file
            self.all_img_file_index = 0
            self.show_label_img()
        finally:
            self.update_btn_status()

    def on_btn_next_img(self):
        try:
            self.all_img_file_index += 1
            self.show_label_img()
        finally:
            self.update_btn_status()

    def on_btn_prev_img(self):
        try:
            self.all_img_file_index -= 1
            self.show_label_img()
        finally:
            self.update_btn_status()

    def on_btn_select_brush_color(self):
        self.brush_color = QColorDialog.getColor()
        self.label_img.update_brush_color(self.brush_color)

        pe = QPalette()
        pe.setColor(QPalette.Window, self.brush_color)
        self.label_brush_color.setPalette(pe)
        self.label_brush_color.setAutoFillBackground(True)

    def on_btn_clear_mask(self):
        self.show_label_img(do_clear=True)

    def on_btn_roate(self):
        self.show_label_img(do_roate=True)

    def on_btn_roate_img(self):
        self.show_label_img(do_roate_img=True)

    def on_btn_roate_mask(self):
        self.show_label_img(do_roate_mask=True)

    def on_page_jump(self):
        try:
            page_num = int(self.label_status_page_number.text())
            if page_num >= 1 and page_num <= len(self.all_img_file):
                self.all_img_file_index = page_num - 1
            self.show_label_img()
            self.setFocus()
        finally:
            self.update_btn_status()

    def wheelEvent(self, event):
        if QApplication.keyboardModifiers() == QtCore.Qt.ControlModifier:
            brush_pixle_size = int(self.edit_brush_pixle_size.text())
            delta = event.delta()
            if delta > 0:
                brush_pixle_size += 1
            elif delta < 0:
                brush_pixle_size -= 1

            if brush_pixle_size >= self.min_brush_pixle_size and brush_pixle_size <= self.max_brush_pixle_size:
                self.edit_brush_pixle_size.setText(f'{brush_pixle_size}')
        elif QApplication.keyboardModifiers() == QtCore.Qt.AltModifier:
            eraser_pixle_size = int(self.edit_eraser_pixle_size.text())
            delta = event.delta()
            if delta > 0:
                eraser_pixle_size += 1
            elif delta < 0:
                eraser_pixle_size -= 1

            if eraser_pixle_size >= self.min_eraser_pixle_size and eraser_pixle_size <= self.max_eraser_pixle_size:
                self.edit_eraser_pixle_size.setText(f'{eraser_pixle_size}')

    def on_edit_brush_pixle_size_change(self):
        if self.edit_brush_pixle_size.text():
            brush_pixle_size = int(self.edit_brush_pixle_size.text())
            self.label_img.update_brush_pixle_size(brush_pixle_size)

    def on_edit_eraser_pixle_size_change(self):
        if self.edit_eraser_pixle_size.text():
            eraser_pixle_size = int(self.edit_eraser_pixle_size.text())
            self.label_img.update_eraser_pixle_size(eraser_pixle_size)

    def update_btn_status(self):
        try:
            self.btn_next_img.setEnabled(False)
            self.btn_prev_img.setEnabled(False)
            self.btn_roate.setEnabled(False)
            self.btn_roate_img.setEnabled(False)
            self.btn_roate_mask.setEnabled(False)
            self.btn_clear_mask.setEnabled(False)

            if not self.all_img_file:
                self.label_status_running1.setText('请选择需要标注的目录')
                self.label_status_page_number.hide()
                self.label_status_running2.hide()
            else:
                img_name = self.all_img_file[self.all_img_file_index]

                # self.label_status_page_number.show()
                # self.label_status_running2.show()
                self.label_status_page_number_validator.setRange(1, len(self.all_img_file))
                self.label_status_page_number.setText(f'{self.all_img_file_index+1}')
                self.label_status_running1.setText( f'当前图片: {img_name} ({self.all_img_file_index + 1}/{len(self.all_img_file)}) 跳转到')
                self.label_status_running2.setText(f'张')


                if self.all_img_file_index == 0:
                    self.btn_prev_img.setEnabled(False)
                else:
                    self.btn_prev_img.setEnabled(True)

                if self.all_img_file_index == len(self.all_img_file) - 1:
                    self.btn_next_img.setEnabled(False)
                else:
                    self.btn_next_img.setEnabled(True)

                self.btn_roate.setEnabled(True)
                self.btn_roate_img.setEnabled(True)
                self.btn_roate_mask.setEnabled(True)
                self.btn_clear_mask.setEnabled(True)
        except:
            logging.exception('update_btn_status exception')


    def show_label_img(self, do_roate=False, do_roate_img=False, do_roate_mask=False, do_clear=False):
        if not self.all_img_file:
            return

        img_path = self.all_img_file[self.all_img_file_index]
        img = QPixmap(str(img_path))

        img_mask_path = img_path.parent.joinpath(f'mask/{img_path.stem}.bmp')
        img_mask_path.parent.mkdir(parents=True, exist_ok=True)

        if img_mask_path.is_dir():
            QMessageBox.warning(
                self,
                '<致命错误>',
                f'标注文件<{img_mask_path}>是一个目录, 请把它拷贝到别的地方, 然后重新打开标注工具!!!',
                QMessageBox.Ok
            )
            sys.exit(-1)

        if img_mask_path.exists():
            img_mask = QPixmap(str(img_mask_path))
            if img_mask.size() != self.mask_img_size:
                os.remove(str(img_mask_path))

        if not img_mask_path.exists() or do_clear:
            img_mask = QPixmap(self.mask_img_size)
            img_mask.fill(QColor(0, 0, 0))
            img_mask.save(str(img_mask_path))

        if do_roate:
            rm = QMatrix()
            rm.rotate(90)
            img = img.transformed(rm)
            img.save(str(img_path))
            img_mask = img_mask.transformed(rm)
            img_mask.save(str(img_mask_path))

        if do_roate_img:
            rm = QMatrix()
            rm.rotate(90)
            img = img.transformed(rm)
            img.save(str(img_path))

        if do_roate_mask:
            rm = QMatrix()
            rm.rotate(90)
            img_mask = img_mask.transformed(rm)
            img_mask.save(str(img_mask_path))

        self.label_img.update_label_img(img, img_mask, str(img_mask_path))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    widget = MainWindow()
    widget.show()
    sys.exit(app.exec_())

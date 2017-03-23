
# Inspiration and assistance came from:
# https://github.com/tmwoz/pyEQ/blob/master/main.py

import PyQt5
import pyqtgraph as pg

import os
import pyaudio
import wave
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog
from PyQt5.uic import loadUi
import numpy as np
from scipy.signal import firwin2, lfilter, freqz

chunks = 2 ** 13


class MainWindow(QMainWindow):
    def __init__(self, *args):
        # super(MainWindow, self).__init__()
        QMainWindow.__init__(self, *args)

        # Load the UI
        path = os.path.dirname(os.path.abspath(__file__))
        ui_file = os.path.join(os.path.join(path, 'ui_files'), 'main_window.ui')
        loadUi(ui_file, self)
        self.chain = None
        self.setWindowTitle('Equalizer')
        self.show()
        self.timeSeriesPlot.hideAxis('left')
        self.openPushButton.clicked.connect(self.open_button_clicked)
        self.playPushButton.clicked.connect(self.play_button_clicked)
        self.stopPushButton.clicked.connect(self.stop_button_clicked)
        self.stream = None
        self.wf = None
        self._audio = None
        self.freq = np.linspace(1e-6, (chunks / 2), chunks, endpoint=True)
        self.eq_frequencies = None
        self.n_taps = 129
        self.z = np.zeros(self.n_taps - 1)
        # self.frameFreqPlot.setXRange(self.freq[1], self.freq[-2])
        # self.frameFreqPlot.setXRange(.1, np.pi)
        # self.frameFreqPlot.setLogMode(x=True)
        self.frameFreqPlot.setYRange(-40, 40)
        self.frameFreqPlot.hideAxis('bottom')
        self.freq_plot = self.frameFreqPlot.plot()

        self.filterPlot.setXRange(.1, np.pi)
        # self.frameFreqPlot.setXRange(self.freq[1], self.freq[-2])
        # self.filterPlot.setLogMode(x=True)
        self.filterPlot.setYRange(-40, 40)
        self.filterPlot.hideAxis('bottom')
        self.filter_plot = self.filterPlot.plot()

        self.label_high_db.setText(str(self.slider_00032.maximum()))
        self.label_low_db.setText(str(self.slider_00032.minimum()))

    def open_button_clicked(self):
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.ExistingFile)
        dialog.setNameFilter('Wav File (*.wav)')
        if dialog.exec_():
            file_name = dialog.selectedFiles()[0]
            self.wf = wave.open(file_name, 'rb')
            self.open_stream()

    def play_button_clicked(self):
        if self.stream:
            self.stream.start_stream()

    def stop_button_clicked(self):
        if self.stream:
            self.stream.stop_stream()

    def update_freq_plot(self, x):
        h = 20 * np.log10(np.abs(np.fft.rfft(x, n=2 * chunks)[:chunks]))
        self.freq_plot.setData(x=self.freq, y=h, clear=True)

    def update_filter_plot(self, coefficients):
        (a, b) = coefficients
        omega, h = freqz(b, a)
        magnitude = 20 * np.log10(np.abs(h))
        # self.filter_plot.setData(x=np.linspace(self.freq[1], self.freq[-2], len(omega)), y=magnitude, clear=True)
        self.filter_plot.setData(x=omega, y=magnitude, clear=True)

    def open_stream(self):
        wf = self.wf
        f_rate = wf.getframerate()
        samp_w = wf.getsampwidth()
        n_chan = wf.getnchannels()
        self.eq_frequencies = np.concatenate((np.array([0]),
                                              2 ** np.arange(5, 15),
                                              np.array([f_rate / 2])), axis=0).astype(int)

        def callback(in_data, frame_count, time_info, status):
            data = wf.readframes(frame_count)
            if len(data) == 0:
                return data, pyaudio.paComplete
            signal = bytes_to_float(data)  # converting data
            gains = 10 ** ((np.array([int(self.slider_00032.value()),
                                      int(self.slider_00064.value()),
                                      int(self.slider_00128.value()),
                                      int(self.slider_00256.value()),
                                      int(self.slider_00512.value()),
                                      int(self.slider_01024.value()),
                                      int(self.slider_02048.value()),
                                      int(self.slider_04096.value()),
                                      int(self.slider_08192.value()),
                                      int(self.slider_16384.value())], dtype=np.float64)) / 20)

            self.label_00032.setText(str(self.slider_00032.value()))
            self.label_00064.setText(str(self.slider_00064.value()))
            self.label_00128.setText(str(self.slider_00128.value()))
            self.label_00256.setText(str(self.slider_00256.value()))
            self.label_00512.setText(str(self.slider_00512.value()))
            self.label_01024.setText(str(self.slider_01024.value()))
            self.label_02048.setText(str(self.slider_02048.value()))
            self.label_04096.setText(str(self.slider_04096.value()))
            self.label_08192.setText(str(self.slider_08192.value()))
            self.label_16384.setText(str(self.slider_16384.value()))

            a = [1.]
            b = firwin2(self.n_taps,
                        self.eq_frequencies,
                        np.concatenate(([0], gains, [0]), axis=0),
                        nyq=f_rate / 2,
                        window=None,
                        antisymmetric=True)

            # need to give an initial condition for self.z other than 0
            filtered, self.z = lfilter(b, a, signal, zi=self.z)  # when using data
            self.update_freq_plot(filtered)
            self.update_filter_plot((a, b))
            output = float_to_bytes(filtered)
            return output, pyaudio.paContinue

        self._audio = pyaudio.PyAudio()
        self.stream = self._audio.open(
                        format=self._audio.get_format_from_width(samp_w),
                        channels=n_chan,
                        rate=f_rate,
                        frames_per_buffer=chunks,
                        input=True,
                        output=True,
                        stream_callback=callback)
        self.stream.start_stream()


def bytes_to_float(byte_array):
    int_array = np.fromstring(byte_array, dtype=np.int16)
    return int_array.astype(np.float64) / np.iinfo(int_array.dtype).max


def float_to_bytes(float_array):
    int_array = (float_array * np.iinfo(np.int16).max).astype(np.int16)
    return int_array.tostring()


if __name__ == '__main__':
    pya = pyaudio.PyAudio()
    app = QApplication([])
    win = MainWindow()
    app.exec_()
    pya.terminate()

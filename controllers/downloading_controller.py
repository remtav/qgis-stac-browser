import os
import urllib

from qgis.core import QgsRasterLayer, QgsProject, Qgis
from PyQt5 import QtCore

from qgis.PyQt.QtWidgets import QProgressBar

from ..utils.logging import error
from ..threads.download_items_thread import DownloadItemsThread


class DownloadController:
    def __init__(self, data={}, hooks={}, iface=None):
        self.data = data
        self.hooks = hooks
        self.iface = iface

        self._progress_message_bar = None
        self._loading_closed = False

        self.loading_thread = DownloadItemsThread(
            self.downloads,
            self.download_directory,
            on_progress=self.on_progress_update,
            on_gdal_error=self.on_gdal_error,
            on_error=self.on_error,
            on_add_layer=self.on_add_layer,
            on_finished=self.on_downloading_finished
        )

        self.loading_thread.start()

    @property
    def downloads(self):
        return self.data.get('downloads', [])

    @property
    def download_directory(self):
        return self.data.get('download_directory', None)

    def on_gdal_error(self, e):
        error(self.iface, f'Unable to find \'gdalbuildvrt\' in current path')

    def on_error(self, item, e):
        if type(e) == urllib.error.URLError:
            error(self.iface, f'Failed to load {item.id}; {e.reason}')
        else:
            error(self.iface, f'Failed to load {item.id}; {type(e).__name__}')

    def on_add_layer(self, current_step, total_steps, item, assets,
                     download_directory):

        self.on_progress_update(current_step, total_steps, 'ADDING_TO_LAYERS')
        for asset in assets:
            asset_fname = asset.split('/')[-1].split('.')[0]
            scene_id = item.id

            layer = QgsRasterLayer(
                asset,
                f'{scene_id}_{asset_fname}'
            )
            QgsProject.instance().addMapLayer(layer)



    def on_destroyed(self, event):
        self._loading_closed = True
        if not self.loading_thread.isFinished:
            self.loading_thread.terminate()

    def on_progress_update(self, current_step, total_steps, status):
        if self._loading_closed:
            return
        if self._progress_message_bar is None:
            self._progress_message_bar = self.iface.messageBar().createMessage(
                status
            )
            self._progress_message_bar.destroyed.connect(self.on_destroyed)
            self._progress = QProgressBar()
            self._progress.setMaximum(total_steps)
            self._progress.setAlignment(
                QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
            )
            self._progress_message_bar.layout().addWidget(self._progress)
            self.iface.messageBar().pushWidget(
                self._progress_message_bar,
                Qgis.Info
            )
        else:
            self._progress_message_bar.setText(status)

        self._progress.setValue(current_step - 1)

    def on_downloading_finished(self):
        self.iface.messageBar().clearWidgets()

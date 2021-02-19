from datetime import datetime

from PyQt5 import uic, QtWidgets, QtCore
from PyQt5.QtGui import QStandardItemModel
from PyQt5.QtWidgets import (QTreeWidgetItem, QFormLayout)

from qgis.core import QgsMapLayerProxyModel

from .add_edit_api_dialog import AddEditAPIDialog
from ..utils import ui
from ..utils.logging import error
from ..utils.config import Config
from .extent_selector import ExtentSelector


FORM_CLASS, _ = uic.loadUiType(ui.path('query_dialog.ui'))


class QueryDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, data={}, hooks={}, parent=None, iface=None):
        super(QueryDialog, self).__init__(parent)

        self.data = data
        self.hooks = hooks
        self.iface = iface

        self.setupUi(self)

        self._api_tree_model = None

        self.extentSelector = ExtentSelector(parent=self,
                                             iface=iface,
                                             filters=QgsMapLayerProxyModel.VectorLayer
                                             | QgsMapLayerProxyModel.RasterLayer)
        self.filterLayout.setWidget(0, QFormLayout.FieldRole, self.extentSelector)

        self.extentSelector.show()

        self.populate_time_periods()
        self.populate_collection_list()

        self.selectAllCollectionsButton.clicked.connect(self.on_select_all_collections_clicked)
        self.deselectAllCollectionsButton.clicked.connect(self.on_deselect_all_collections_clicked)

        self.cloudCoverMinSpin.valueChanged.connect(self.on_cloud_cover_min_spin_changed)
        self.cloudCoverMaxSpin.valueChanged.connect(self.on_cloud_cover_max_spin_changed)
        self.GSDminSpinBox.valueChanged.connect(self.on_gsd_min_spin_changed)
        self.GSDmaxSpinBox.valueChanged.connect(self.on_gsd_max_spin_changed)

        self.searchButton.clicked.connect(self.on_search_clicked)
        self.cancelButton.clicked.connect(self.on_cancel_clicked)

        self.addStacApi.clicked.connect(self.on_add_api_clicked)
        self.removeStacApi.clicked.connect(self.on_remove_api_clicked)

    def populate_time_periods(self):
        now = QtCore.QDateTime.currentDateTimeUtc()
        self.endPeriod.setDateTime(now)

    def populate_collection_list(self):
        self._api_tree_model = QStandardItemModel(self.treeView)
        self.treeView.clear()
        for api in self.apis:
            api_node = QTreeWidgetItem(self.treeView)
            api_node.setText(0, f'{api.title}')
            api_node.setData(0, 256, f'{api.id}')  # 256: QtUserRole
            api_node.setData(0, 3, f'{api.description}')  # TODO
            api_node.setData(0, 3, f'URL: {api.href}<br>Title: {api.title}<br>STAC Version: {api.version}<br>'
                                   f'Description: {api.description}')
            api_node.setFlags(
                api_node.flags()
                | QtCore.Qt.ItemIsTristate
                | QtCore.Qt.ItemIsUserCheckable
            )
            api_node.setCheckState(0, QtCore.Qt.Unchecked)
            for collection in sorted(api.collections):
                title = collection.title.replace("\n", " ")
                collection_node = QTreeWidgetItem(api_node)
                collection_node.setText(0, title)
                collection_node.setFlags(
                    collection_node.flags() | QtCore.Qt.ItemIsUserCheckable
                )
                collection_node.setCheckState(0, QtCore.Qt.Unchecked)

    def validate(self):
        valid = True

        if not self.extentSelector.is_valid():
            error(self.iface, "Extent layer is not valid")
            valid = False
        start_time, end_time = self.time_period
        if start_time > end_time:
            error(self.iface, "Start time can not be after end time")
            valid = False
        return valid

    @property
    def api_selections(self):
        api_collections = []
        root = self.treeView.invisibleRootItem()
        for i in range(root.childCount()):
            api_node = root.child(i)
            api = self.apis[i]
            selected_collections = []
            for j in range(api_node.childCount()):
                collection_node = api_node.child(j)
                collection = api.collections[j]
                if collection_node.checkState(0) == QtCore.Qt.Checked:
                    selected_collections.append(collection)

            if api_node.checkState(0) == QtCore.Qt.Checked \
                    or api_node.checkState(0) == QtCore.Qt.PartiallyChecked:
                api_collections.append({
                    'api': api,
                    'collections': selected_collections
                })
        return api_collections

    @property
    def apis(self):
        return sorted(self.data.get('apis', []))

    @property
    def extent_rect(self):
        return self.extentSelector.value()

    @property
    def time_period(self):
        return (datetime.strptime(self.startPeriod.text(), '%Y-%m-%d %H:%MZ'),
                datetime.strptime(self.endPeriod.text(), '%Y-%m-%d %H:%MZ'))

    @property
    def query_filters(self):
        filters = {}
        if self.enableFiltersCheckBox.isChecked():
            filters['eo:cloud_cover'] = {'gte': self.cloudCoverMinSpin.value(),'lte': self.cloudCoverMaxSpin.value()},

        if self.enableGSDCheckBox.isChecked():
            filters['gsd'] = {'gte': self.GSDminSpinBox.value(), 'lte': self.GSDmaxSpinBox.value()}
            #filters['gsd'] = {'eq': "1.0"}

        print(filters)

        if filters:
            return filters
        else:
            return None

    def on_search_clicked(self):
        valid = self.validate()

        if not valid:
            return

        self.hooks['on_search'](self.api_selections,
                                self.extent_rect,
                                self.time_period,
                                self.query_filters)

    def on_cancel_clicked(self):
        self.hooks['on_close']()

    def on_select_all_collections_clicked(self):
        self._toggle_all_collections_checked(True)

    def on_deselect_all_collections_clicked(self):
        self._toggle_all_collections_checked(False)

    def on_cloud_cover_min_spin_changed(self, value):
        max_value = self.cloudCoverMaxSpin.value()

        if value >= self.cloudCoverMaxSpin.value():
            self.cloudCoverMinSpin.setValue(max_value - 0.01)

    def on_cloud_cover_max_spin_changed(self, value):
        min_value = self.cloudCoverMinSpin.value()

        if value < self.cloudCoverMinSpin.value():
            self.cloudCoverMaxSpin.setValue(min_value + 0.01)

    def on_gsd_min_spin_changed(self, value):
        max_value = self.GSDmaxSpinBox.value()
        if value >= self.GSDmaxSpinBox.value():
            self.GSDminSpinBox.setValue(max_value - 0.1)

    def on_gsd_max_spin_changed(self, value):
        min_value = self.GSDminSpinBox.value()
        if value <= self.GSDminSpinBox.value():
            self.GSDmaxSpinBox.setValue(min_value + 0.1)

    def on_add_api_clicked(self):
        dialog = AddEditAPIDialog(
            data={'api': None},
            hooks={
                "remove_api": self.remove_api,
                "add_api": self.add_api,
                "edit_api": self.edit_api
            },
            parent=self,
            iface=self.iface
        )
        dialog.exec_()

    def on_remove_api_clicked(self):
        self.remove_api()

    def add_api(self, api):
        config = Config()
        apis = config.apis
        apis.append(api)
        config.apis = apis
        config.save()

        self.data['apis'] = config.apis

        self.populate_collection_list()

    def remove_api(self):
        config = Config()
        new_apis = []
        api_id = self.treeView.currentItem().data(0, 256)

        for a in config.apis:
            if a.id == api_id:
                continue
            new_apis.append(a)

        config.apis = new_apis
        config.save()

        self.data['apis'] = config.apis
        self.populate_collection_list()

    def edit_api(self, api):
        config = Config()
        new_apis = []

        for a in config.apis:
            if a.id == api.id:
                continue
            new_apis.append(a)
        new_apis.append(api)
        config.apis = new_apis
        config.save()

        self.data['apis'] = config.apis
        self.populate_api_list()
        self.populate_api_details()

    def closeEvent(self, event):
        if event.spontaneous():
            self.hooks['on_close']()

    def _toggle_all_collections_checked(self, checked):
        state = QtCore.Qt.Checked if checked else QtCore.Qt.Unchecked

        root = self.treeView.invisibleRootItem()
        for i in range(root.childCount()):
            api_node = root.child(i)
            api_node.setCheckState(0, state)

            for j in range(api_node.childCount()):
                collection_node = api_node.child(j)
                collection_node.setCheckState(0, state)

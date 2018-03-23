# -*- coding: utf-8 -*-
"""
/***************************************************************************
 DigitalConnectorPlugin
                                 A QGIS plugin
 Digital Connector Plugin
                              -------------------
        begin                : 2018-03-22
        git sha              : $Format:%H$
        copyright            : (C) 2018 by Future Cities Catapult
        email                : tbantis@futurecities.catapult.org.uk
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, QProcess
from PyQt4.QtGui import QAction, QIcon, QFileDialog, QLabel, QPixmap, QLineEdit, QProgressBar, QPushButton, QGridLayout, QWidget,QMainWindow
from qgis.core import QgsMessageLog, QgsVectorLayer, QgsMapLayerRegistry
from qgis.gui import QgsMessageBar
from processing.gui.MessageDialog import MessageDialog
# Initialize Qt resources from file resources.py
import resources
# Import the code for the dialog
from digital_connector_plugin_dialog import DigitalConnectorPluginDialog, EditRecipe

import os.path
from os.path import expanduser
import subprocess as sp
import json
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import os
import sys
import time
import json
import fileinput
import subprocess as sp
import uuid
import os

class DigitalConnectorPlugin:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'DigitalConnectorPlugin_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)


        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Digital Connector Plugin')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'DigitalConnectorPlugin')
        self.toolbar.setObjectName(u'DigitalConnectorPlugin')

        # Edit recipe dialog class
        self.dialog_instance = EditRecipe()

        # Create the dialog (after translation) and keep reference
        self.dlg = DigitalConnectorPluginDialog()

        # Add button functionalities
        self.dlg.lineEdit.clear()
        self.dlg.pushButton.clicked.connect(self.select_dc_directory)
        self.dlg.pushButton_2.clicked.connect(self.visualise_recipe)
        self.dlg.pushButton_3.clicked.connect(self.edit_recipe)


    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('DigitalConnectorPlugin', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/DigitalConnectorPlugin/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Digital Connector Plugin'),
            callback=self.run,
            parent=self.iface.mainWindow())


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Digital Connector Plugin'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar

    def select_dc_directory(self):
        """Selects the DC directory"""

        filename = QFileDialog.getExistingDirectory(
                    self.dlg,
                    "Open a folder",
                    expanduser("~"),
                    QFileDialog.ShowDirsOnly
                )
        # check wheather cancel button was pushed
        if filename:
            self.dlg.lineEdit.setText(filename)
            recipes = filename + "/src/main/resources/executions/examples"
            recipes_list = []
            for file in os.listdir(recipes):
                if file.endswith(".json"):
                    recipes_list.append(file)
            self.dlg.comboBox.clear()
            self.dlg.comboBox.addItems(recipes_list)
    
    def run(self):
        """Run method that performs all the real work"""
        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            gradle_command = '/usr/local/Cellar/gradle/4.1/bin/gradle'
            dc_directory = self.dlg.lineEdit.text()
            dc_recipe = self.track_recipe_choice()
            to_save = self.select_output_name()

            if not to_save:
                self.iface.messageBar().pushMessage("Error", "Please choose a name for the output file", level=QgsMessageBar.CRITICAL)
            else:
                args = ["{0} runExport -Precipe='{1}/src/main/resources/executions/examples/{2}'  -Poutput='{3}'".format(gradle_command,dc_directory,dc_recipe,to_save)]
                output = sp.Popen(args, stdout=sp.PIPE, cwd=dc_directory, shell=True)

                progressbar = QProgressBar()
                progressbar.setMinimum(0)
                progressbar.setMaximum(0)
                progressbar.setValue(0)
                progressbar.setWindowTitle("Running gradle task...")
                progressbar.show()

                for log in iter(output.stdout.readline, b''):
                    sys.stdout.write(str(log) + '\n')
                # Adding the resulting layer in the map
                vlayer = QgsVectorLayer(to_save,to_save.split("/")[-1],"ogr")
                QgsMapLayerRegistry.instance().addMapLayer(vlayer)    

    def clean_json(self, file):
        with open(file) as f:
            content = f.readlines()

        jsn = ''    
        for i in content:
            if '//' in i:
                pass
            else:
                jsn = jsn+i.replace("/n",'')
        
        f = json.loads(jsn)
        return f

        
    def edit_recipe(self):
        file = '{0}/src/main/resources/executions/examples/{1}'.format(self.dlg.lineEdit.text(),self.track_recipe_choice())
        datasources_file = self.clean_json(file)
        datasources, updated_content = EditRecipe.getRecipeContent(datasources = datasources_file["dataset"]["datasources"])
        # dialog = self.show_dialog()
        print datasources,updated_content


    def select_output_name(self):
        """Returns the name of the exported geojson"""
        
        name = QFileDialog.getSaveFileName(self.dlg, 
            'Save File')
        return name

    def track_recipe_choice(self):
        dc_recipe = str(self.dlg.comboBox.currentText())
        return dc_recipe

    # Visualing recipe
    def visualise_recipe(self):
        """ Visualing recipe using plantUML
            Install it using brew install plantuml
        """
        dc_directory = self.dlg.lineEdit.text()
        dc_recipe = self.track_recipe_choice()

        file  = '{0}/src/main/resources/executions/examples/{1}'.format(dc_directory,dc_recipe)
        self.dict2svg(self.clean_json(file))
    

    def traverse(self, obj, parent):
        """Traverse the dictionary"""
        vertices = []
        edges = []

        for key, value in obj.items():

            properties = []
            children = {}
            children_str = []

            # The value is a list of things. Iterate over them and add
            # an object for each element. Add a child as well.
            if isinstance(value, list):

                for idx, a in enumerate(value):

                    (children_str
                        .append("{}: {}".format(idx, "[object Object]")))

                    if isinstance(a, dict):
                        children[idx] = a
                    else:
                        children[idx] = {"value [{}]".format(type(a).__name__): a}

                vertices.append({
                    "clsName": key,
                    "clsNameFullReference": key,
                    "clsProperties": properties,
                    "clsObjects": children_str
                })

            # The value is a dictionary.
            elif isinstance(value, dict):

                for k, v in value.items():

                    if isinstance(v, dict):
                        (children_str
                            .append("{}: {}".format(k, "[object Object]")))
                        children[k] = v
                    elif isinstance(v, list):
                        (children_str
                            .append("{}: {}".format(k, "[object Object]")))
                        children[k] = v
                    else:
                        properties.append("{}: {}".format(k, v))

                vertices.append({
                    "clsName": key,
                    "clsNameFullReference": key,
                    "clsProperties": properties,
                    "clsObjects": children_str
                })

            if children:
                p = "{}.{}".format(parent, key) if parent is not None else key

                tmpobj, tmprel = self.traverse(children, p)

                for r in tmprel:
                    edges.append(r)

                for o in tmpobj:
                    o["clsNameFullReference"] = \
                        "{}.{}".format(key, o["clsNameFullReference"])
                    vertices.append(o)

                for child in children:
                    if parent is not None:
                        (edges.append("\"{}.{}\" \"1\" --> \"1\" \"{}.{}.{}\""
                                    .format(parent, key, parent, key, child)))
                    else:
                        (edges.append("\"{}\" \"1\" --> \"1\" \"{}.{}\""
                                    .format(key, key, child)))

        return vertices, edges


    def printClass(self, cls):
        """Returns the string reopresention of a class"""

        s = ""

        s += ("class \"{}\" as {} {{"
            .format(cls["clsName"], cls["clsNameFullReference"])) + "\n"

        s += "\t" + ".. Properties .." + "\n"
        if cls["clsProperties"]:
            for p in cls["clsProperties"]:
                s += "\t" + p + "\n"

        if cls["clsObjects"]:
            s += "\t" + ".. Objects .." + "\n"
            for o in cls["clsObjects"]:
                s += "\t" + o + "\n"

        s += "}" + "\n"

        return s


    def dict2plantuml(self, d):
        """Covert a dictionary to PlantUML text
           In the future we might consider doing this 
           using graphviz
        """

        s = "@startuml\n"

        if isinstance(d, dict):
            d = {"root": d}

            c, r = self.traverse(d, None)

            for cls in c:
                s += self.printClass(cls) + "\n"

            for rel in r:
                s += rel + "\n"
        else:
            raise TypeError("The input should be a dictionary.")

        return s + "@enduml"

    
    def plantuml_exec(self, *file_names):
        """Run PlantUML"""

        cmd = ["/usr/local/bin/plantuml",
            "-tpng"] + list(file_names)

        sp.check_call(cmd, shell=False, stderr=sp.STDOUT)

        return [os.path.splitext(f)[0] + ".png" for f in file_names]


    def dict2svg(self, d):

        base_name = str(uuid.uuid4())
        uml_path = expanduser("~") + "/" + base_name + ".uml"

        with open(uml_path, 'w') as fp:
            fp.write(self.dict2plantuml(d))

        try:
            output = self.plantuml_exec(uml_path)
            svg_name = output[0]
            output = self.plantuml_exec(uml_path)
            svg_name = output[0]
            plt.imshow(mpimg.imread(svg_name))
            plt.show()

        finally:

            if os.path.exists(uml_path):
                os.unlink(uml_path)

            svg_path = base_name + ".png"
            if os.path.exists(svg_path):
                os.unlink(svg_path)
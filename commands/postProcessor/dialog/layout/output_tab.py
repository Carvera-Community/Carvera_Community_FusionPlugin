import adsk
from ...settings.settings import Settings
from ...strings import Strings

class OutputTab:
    @classmethod
    def createOutputTab(cls, inputs):

        # helper method to make the syntax a little easier for adding 
        # items to a table.
        def init(obj, **attrs):
            for k, v in attrs.items():
                setattr(obj, k, v)
            return obj
        
        outputTab = inputs.addTabCommandInput(cls._OUTPUT_GROUP_ID, Strings("Output Options"))
        outputTab.isEnabled = False

        #region -- Output folder table --
        input = outputTab.children.addTableCommandInput(cls._OUTPUT_FOLDER_TABLE_ID, Strings('Output folder'), 2, '12:1')
        input.minimumVisibleRows = 2
        input.maximumVisibleRows = 2
        input.tablePresentationStyle = adsk.core.TablePresentationStyles.transparentBackgroundTablePresentationStyle

        #region Output folder label, spans 2 columns
        input.addCommandInput(
            init(inputs.addStringValueInput(cls._OUTPUT_FOLDER_LABEL_ID, '', Strings("Output folder")), 
                tooltip = Strings("TOOL TIP: Output folder"),
                tooltipDescription = Strings("TOOLTIP TEXT: Output folder"),
                isReadOnly = True
            ), 0, 0, 0, 2)
        #endregion

        #region Output folder string input
        input.addCommandInput(
            init(inputs.addStringValueInput(cls._OUTPUT_FOLDER_ID, Strings("Output folder"), Strings("<Select program>")),
                tooltip = Strings("TOOL TIP: Output folder"),
                tooltipDescription = Strings("TOOLTIP TEXT: Output folder"),
                isReadOnly = False
            ), 1, 0)
        #endregion

        #region Output folder browse button
        input.addCommandInput(inputs.addBoolValueInput(cls._OUTPUT_FOLDER_BUTTON_ID, '  …  ', False, '', False), 1, 1)
        #endregion
        #endregion

        #region File name string input
        input = outputTab.children.addStringValueInput(cls._FILE_NAME_ID, Strings("File name"), Strings("<Select program>"))
        input.tooltip = Strings("TOOL TIP: File name")
        input.tooltipDescription = Strings("TOOLTIP TEXT: File name")
        #endregion

        #region Numeric name checkbox
        input = outputTab.children.addBoolValueInput(cls._NUMERIC_NAME_ID, Strings("Name must be numeric"), True, "", Settings(Settings.NUMERIC_NAME))
        input.tooltip = Strings("TOOL TIP: Name must be numeric")
        input.tooltipDescription = Strings("TOOLTIP TEXT: Name must be numeric")
        #endregion

        #region Prepend sequence number dropdown
        input = outputTab.children.addDropDownCommandInput(cls._PREPEND_SEQUENCE_ID, Strings("Prepend sequence number"), adsk.core.DropDownStyles.TextListDropDownStyle)
        input.tooltip = Strings("TOOL TIP: Prepend sequence number")
        input.tooltipDescription = Strings("TOOLTIP TEXT: Prepend sequence number")
        input.listItems.add(Strings("File names only"), input.listItems.count == Settings(Settings.SEQUENCE))
        input.listItems.add(Strings("Operation steps only"), input.listItems.count == Settings(Settings.SEQUENCE))
        input.listItems.add(Strings("File names and operation steps"), input.listItems.count == Settings(Settings.SEQUENCE))
        input.listItems.add(Strings("None"), input.listItems.count == Settings(Settings.SEQUENCE))
        #endregion

        #region Numbering digits spinner input
        input = outputTab.children.addIntegerSpinnerCommandInput(cls._DIGITS_COUNT_ID, Strings("Numbering digits"), 1, 6, 1, Settings(Settings.NAME_DIGITS))
        input.tooltip = Strings("TOOL TIP: Numbering digits")
        input.tooltipDescription = Strings("TOOLTIP TEXT: Numbering digits")
        #endregion

        #region Numbering interval spinner input
        input = outputTab.children.addIntegerSpinnerCommandInput(cls._NUMBERING_INTERVAL_ID, Strings("Numbering interval"), 1, 6, 1, Settings(Settings.NUMBERING_INTERVAL))
        input.tooltip = Strings("TOOL TIP: Numbering interval")
        input.tooltipDescription = Strings("TOOLTIP TEXT: Numbering interval")
        #endregion

        #region Operations grouping dropdown
        input = outputTab.children.addDropDownCommandInput(cls._OPERATIONS_GROUPING_ID, Strings("Operations grouping"), adsk.core.DropDownStyles.TextListDropDownStyle)
        input.tooltip = Strings("TOOL TIP: Operations grouping")
        input.tooltipDescription = Strings("TOOLTIP TEXT: Operations grouping")

        #endregion

        #region Flat file structure checkbox
        input = outputTab.children.addBoolValueInput(cls._FLAT_FILE_STRUCTURE_ID, Strings("Flat file structure"), True, "", Settings(Settings.FLAT_FILE_STRUCTURE))
        input.tooltip = Strings("TOOL TIP: Flatten the file structure")
        input.tooltipDescription = Strings("TOOLTIP TEXT: Flatten the file structure")
        #endregion

        #region Delete existing files checkbox
        input = outputTab.children.addBoolValueInput(cls._DELETE_EXISTING_FILES_ID, Strings("Delete existing files"),  True, "", Settings(Settings.DEL_FILES))
        input.tooltip = Strings("TOOL TIP: Delete existing files")
        input.tooltipDescription = Strings("TOOLTIP TEXT: Delete existing files")
        input.isEnabled = False
        #endregion

        #region Delete output folder checkbox
        input = outputTab.children.addBoolValueInput(cls._DELETE_OUTPUT_FOLDER_ID, Strings("Delete output folder"),  True, "", Settings(Settings.DEL_FOLDER))
        input.tooltip = Strings("TOOL TIP: Delete output folder")
        input.tooltipDescription = Strings("TOOLTIP TEXT: Delete output folder")
        #endregion -----


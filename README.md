# Makera Community Fusion Plugin

The Autodesk Fusion plugin created by the Makera Community

## Overview
This repository contains the Autodesk Fusion add-in by the Makera Community. It allows you to do post post-processing of the g-code that the community post-processor generates.

## Features
- It takes each operation and outputs either one file per operation, per setup, per setup and tool or one single file. 
- Rotation of the A-axis if one is installed for support of indexed milling.
- Allows tool changes in a single setup
- Adds rapid moves when no cut is being made
- Grouping of operations as a single file, per setup, per setup and tool or one output file per operation
- ... and more!

## Acknowledgments
This plugin was heavily inspired by Tim Patersons [PostProcessAll](https://github.com/TimPaterson/Fusion360-Batch-Post) plugin. It started as an attempt to extend his work to allow processing of multiple Setups and adding A-axis rotations between them to allow indexed milling, but in the end it just wasn't as simple as I had in my mind so I decided to just build it from scratch and replicate the functionality instead.

## Requirements
- Autodesk Fusion (Personal Edition)
- [Makera post-processor](https://github.com/Carvera-Community/Carvera_Community_Profiles/tree/main/CAM_Post_Processors) (or a post-processor for your CNC-machine)

## Installation
This plugin follows the normal plugin-installation procedure of a local add-in for Fusion.
1. Clone the repository:

Using a git client you start by downloading this repository into a folder of your choice:

```bash
# SSH (recommended if you have SSH keys configured):
git clone git@github.com:Carvera-Community/CarveraCommunity_FusionPlugin.git "Makera Community"

# OR HTTPS:
git clone https://github.com/Carvera-Community/CarveraCommunity_FusionPlugin.git "Makera Community"

```
Follow the generic instructions to install add-ins into Fusion 360:

<img src="resources/readme/installation/step1.png">

1. Go to Utilities
2. Open Scripts and add-ins...

<img src="resources/readme/installation/step3.png">

3. Click the '+' above the table with plugins and scripts

<img src="resources/readme/installation/step4.png">

4. Choose 'Script or add-in from device' and select the folder that you just cloned the repo to (the folder with the Makera Community.manifest file)

<img src="resources/readme/installation/step5.png">

5. (Optional) Tick the checkbox to run the plug-in on startup
6. Done!

<img src="resources/readme/installation/plugin.png">

You should now se a new icon in the Manufacture workspace, next to the Setup sheet under Milling.

## Usage
As this utility isn't a post processor, the first you need is at least one NC Program. To create one you use the regular post process command in Fusion. The reason for this is that you might need to make settings for the specific post processor you're using (it can be used with other post processors than the Carvera Community post processor) and there is no need to duplicate that user interface as it is beyond the scope of this plugin. It is important that you select a machine configuration when you create it by checking the `Use machine configuration` checkbox (1) and selects the machine from your machine library in the drop down named `Machine` (2).

It is important that the machine is the one that you will use, as the plugin will extract information from the selected machine. 

<img src="resources/readme/usage/machine_config.png">

### Tabs
There are four tabs (1) in the dialog that are ordered in a workflow order: [Input Selection](#input-selection-tab), [G-code Options](#g-code-options), [Output Options](#output-options) and [Misc](#misc). Note that all the settings on each tab will be saved to the document as they are changed. This means that there is no need to save any settings but it also means that changing them takes effect immediatly. The only two settings that isn't saved are `Overwrite existing files` and `Clear output folder` as they can be dangerous if not used intently. But more on those in the [Output Options](#output-options) tab.

These settings will be saved in the document itself, so if you're sharing your documents with others or you have specific settings it will be available per document. As a quality of life function you can also save default settings locally that will be used each time you start a new document.

<img src="resources/readme/usage/input_tab.png">

#### Input Selection Tab

The first step you need to do is to select your NC Program that contains the information for the post processor to work. In the drop down `NC Program` (2) you will find the NC Programs that is in the current document that isn't suppressed and doesn't have an error. Select the one that you want to use, normally you might just have one after the first step above.

As a validation you will see the `Machine` selected (3) and the `Post Processor` (4) that will be used when running the plugin later. 

There is a table (5) with the Setups in the current document and if you haven't selected any specific setups in the document browser they will be selected automatically in order from top to bottom, which is the order that they will be processed later. This is important as the rotation of the A-axis depends on the order. If you have a machine that isn't equipped with an A-axis only the Setups where the Work Coordinate System (WCS) that is the same as the first Setup will be selected. The reason why setups aren't selectable unless the WCS is the same is that the g-code that is produced by the post-processor will only reference the WCS origin and the direction of the x-axis, so if they aren't the same the resulting file will have g-code that will not work as the coordinate system of the g-code will differ between setups. So some of the setups might not be selectable (6) and needs to be addressed before it can be used.

There is a checkbox at the top left corner of the table and selecting it will select all Setups, once again in the order of the table, as long as they are viable to select. If it is deselected it will obviously deselect all the Setups. 

On each tab there is a button at the bottom to `Save as default settings`(7) and as mentioned earlier by pressing this button the current settings will be saved as default for any new documents. The selected Setups are obviously not saved as they are defined in the document and thus will only be useful in the currently open document.

At the bottom the two buttons is `Process` (8) that will run the plugin and `Close` (9) that will close the plugin without any action.

You can see on each row of the table the `Setup Name`, if the `Origin` is the same and that the `X-axis` alignment is correct compared to the first selected setup as well as the `Rotation` compared to the referenced Setup. If a Setup is not possible to process together with the Setup that is the first selected in the list it will be grayed out (10) and the reason is stated in the columns `Origin` and/or `X-axis`. In the `Rotation` column (11) you can see how many degrees from the reference Setup that the A-axis is required to rotate to get the work piece to align with the bed. 

The top most Setup that is selected is marked as `(reference)` in these columns and that is just to show what the other Setups are referencing when they are validated. If a Setup isn't selected, the columns `Origin`, `X-axis`and `Rotation`will be marked with a `-`just to show that it isn't part of the analysis.

#### G-code Options

<img src="resources/readme/usage/g-code_tab.png">

In the `G-code Options` tab you find all that is related to g-code manipulation and detection. `Rotate A-Axis between setups` (1) has to be checked to allow the A-axis to rotate between setups, and if it is deselected and there are Setups that are already selected that requires a rotation a warning will be displayed showing which Setups that will be deselected and the `Input Selection` tab will be focused so that you can see the change after it is done. It also controls if rotated Setups can be selected in the `Input Selection` tab, so if they are greyed out then this is the first thing to check. A companion setting to the `Rotate A-Axis between setups` is the `Retract Y on A-axis rotation` (2) and it will enable the possibility to have the retraction of the spindle not just with the Z-axis but also with the Y-axis. This is useful if the stock isn't round and there is a risk that the Z-retraction isn't enough to clear the mill during the rotation. How much the Y-axis should retract is in `Save Y-retraction coordinate (mm)` (3) and it is in Machine Coordinate System (MCS) G53, so it is an absolute number. Default is -100 and it is calculated from the position furthest back of the work area. If the machine doesn't have an A-axis then these two settings are disabled.

`Restore rapid moves` (4) will do just that. In Fusion for personal use there is this slow down for no good reason, this setting tries to remedy that. It analyzes the g-code and when it sees that a retraction is made (Z-only movement) and within 5 g-code moves it will plunge (Z-only) once again it is condidered a rapid movement. It will then introduce a G0 code instead of G1 to use the machines rapid movement speed. Currently it measures the full distance of the alleged rapid movement and if it is at least `Minimum rapid move distance (mm)` (6) long it will replace the G1 to, or add, a G0.

Depeding on what policy you use when it comes to rapid moves they may consist of several movements and by default the analysis is fairly conservative allowing up to 3 movements between the start and the end of a rapid movement to detect it. If you notice that there are rapid movements that isn't sped up as expected, this could be a reason and by increasing `Max steps for rapid move` (5) you might improve the detection of rapid moves.

It should be noted that this is experimental and it is advised to validate the g-code with a g-code analyzer (like [NCViewer.com](https://ncviewer.com)) to be sure that it has produced the correct codes. If you're in any way uncertain, don't use it. It should work and it is programmed defensively but it needs to be validated to work in every situation.

`G-code blocks` is normally collapsed as it is not something that is changed that frequently, but it is still useful to be able to change them if needed without having to make code changes. `Tool change code` (9) lets you inject g-code right before a tool change is going to happen. Maybe you have a cooling system that should be turned off that needs its own g-code call?

The two last blocks is used to control the plugin behaviour, `G-codes that mark ending sequence` (10) is the g-codes that the plugin will look for to know that it has come to the end of the Program. This is to make sure that the end of a Program is only written once per program, as it contains codes like <i>End of program (G30)</i>, <i>Turn off spindle (M5)</i> and so on which wouldn't be good if it happened mid-program. So the plugin searches for these codes in the Operation and if it finds any of them that line will mark the beginning of the end. Another set of g-codes that the plugin is looking for is in `G-codes that marks header end` (11) and it will look for where the header of the Operation ends and if it finds one, it will continue to add to the header lines until it can't find either of them and mark that line as the end of the beginning and normally the codes for selecting millimeters (<i>M20</i>) or inches (<i>M21</i>) as the WCS units will be a good end of the header. Anything between these to blocks is considered the body of the Operation. If, for any reason, `G-codes that marks header end` is empty or neither of the codes are found, the tool change will mark the end of the header. This will however affect initial operations that isn't using a tool, so unless you really need to clear this, keep it as it is.

#### Output Options

<img src="resources/readme/usage/output_tab.png">

The `Output Options` tab is where the core behaviour of the plugin is setup. The obvious one is `Output folder` (1) that is where the result will be written. To the right of it there is a button `…` that will open up a dialog to select the folder. The `File name` (2) is copied from the NC Program (and if changed, written back to it so that you don't have to change it every time unless you want to) and is the base of the naming of the output. There are several settings that will affect the name of the output, so it depends on most of the settings on this tab what the end result will be. Note that you shouldn't add a file extension as it is decided from the machine configuration.

To force the output to be numeric filenames only you tick the `Name must be numeric` checkbox (3). This setting is mostly only useful for machines that can only accept files with numeric names. if this option is selected the `File name` input will only accept numerical names and the `Process` button will be disabled if it isn't. It will only produce files with numbers and they will all end up in the `Output folder` root and the names will be incremented with 1 for each file produced. The number of digits depends on the number of digits in the starting file name, so if it is four digits in the file name, all files will have four digits. So if the first name is 0001 it means that it will have four digits and the next file will be called 0002 and so on.

If you don't want numbers-only file names you might still want to have them numbered so that you know which order they are in the order of operations. Using the `Prepend sequence number` (4) will add a number in front of each file name to help you with that and you decide how many digits to use with the `Number of digits` (5) setting. If the output is sorted into folders, the folders themselves will be numbered and the files in each folder will have their own numbers sequence. Each file and folder will have a number corresponding to their order in the browser, so the first Setup will be 1, the next will be 2 and so on. This is to make sure that the order of operations is intact no matter which setups are selected or how the Operations are grouped. Which takes us to the next setting, `Operations grouping` (6), that have four options:

* Single file
* Group on Setup
* Group on Setup and Tool
* None, one file per Operation

`Single file` will take all the g-code and write it to a single file named as designated in `File name` with the extension given in the machine configuration. This means that if you have a 4th axis you could create a program that runs from start to end without any human interaction required. Please be sure to be around the machine though, it isn't safe to leave a CNC machine running unattended and if something goes wrong it can go very wrong. So be warned.

`Group on Setup` will give you pretty much the same result as if you ran each setup through the post-processor by hand, except that if you do have rotations between the Setups so the Setup that needs to be rotated will rotate before it starts, so no need to manually rotate the part. It will also allow tool changes between Operations which isn't the behaviour if you use the Personal version of Fusion which is especially useful if you have an Automatic Tool changer (ATC) and additionally the plugin will also do all the other g-code modifications that it can do if you select them. It will name each output file the same as the Setup, unless `Prepend sequence number` is selected as it will additionaly prepend the sequence number of the setup to the name.

`Group on Setup and Tool` groups not only on Setup, but additionally it will also split the setup per tool. So for each too change a new file is started and the naming is Setup name concatenated with the tool number, separated with an underscore (_). If there are multiple tool changes with the same tool, it will suffix the file with an underscore and the tool change count, so if a tool is swapped twice, the second time it will have a file name ending with `_2` and so on to avoid overwriting the previous file and to know which order they are to be used. In general, it is a smart thing to use `Prepend sequence number`when splitting up the Operations to avoid confusion regarding the order of operations. 

`None, one file per Operation` is going to create one file per operation. It can be useful if a single operation needs to be rerun or if some operations should be excluded when doing multiple parts. The files will be named the same as the Operation. Note that currently if two operations has the same name the last one will overwrite the former. If `Prepend sequence number` is selected the Operation will have the number of the order of operations within the setup prepended to the file name to make sure that the order of operations is preserved even if some operations are suppressed.

The next setting is `Combine operations using same tool` (7) and it will make sure that when the g-code is generated all consecutive operations with the same tool will be merged together as one operation. This will change the naming of the files with operation names in them, as one operation now contains more than one name, so if this option is used and the `Operation grouping` is set to output one Operation per file, the file name will now have all the names of the Operations, separated with a hyphen (-). If the name is longer than the operating system allows, it will shorten it to `Compounded Operation (n)` where <i>n</i> is the number of operations that has been compunded. 

If you don't want the output to be in folders it is possible to select `Flat file structure` (8) which will result in an output in the `Output folder` without any sub folders. Instead, each file name will be prepended with the folder structure concatenated. All the other settings still applies, so numbering will happen and all that.

If you're writing the output to a file already containing files and the plugin tries to write to an existing file it will stop and display an error saying which file that already exists. To force the output to overwrite any existing files, select `Overwrite existing files` (9). It is useful if you rerun the plugin after doing changes but it also prevents accidental overwrites of files you didn't plan overwriting. If you want to you can `Clear output folder` (10) to remove everything in the output folder and when the g-code is proccessed all files and folders in the output folder will be removed (but not the output folder itself). So, handle with care. It is however useful if you have a folder where you dump out all your NC programs and wants to clear out any previous attempts. 

#### Misc

There is always a `Misc`tab, isn't there? Well, here all the things that didn't fit any other category ends up. In this case it is a small but nifty tool to rename Setups. 

<img src="resources/readme/usage/misc-tab.png">

There is a possibility to change the language of the dialog if you want to do so. it can be done in the `Language` drop down (1).

You can choose to `Use Python regular expressions` (2) if you want to do some advanced search and replace. Otherwise you just type in whatever you want to replace in `Search for this string`(3) and in `Replace with this string` (4) you enter what you want to have there instead. Rather simple, really. As an extra boon you can also limit the replacement to `Only selected Setups` (5) so that you don't have to do it to all. Once you're happy with your replacement parameters, just press `Search and replace` (6) and Presto! your wish has been granted. An extra little feature is that if you leave the `Search for this string` empty it will actually prepend the names with the string entered in `Replace with this string`. Magic. 

## Development

### Host tests

The initial host-side regression suite uses `pytest` and does not require
Fusion 360:

```bash
python3 -m pip install -r requirements-dev.txt
python3 -m pytest
```

The test command prints a coverage summary for the currently testable host-side
modules and writes a browsable report to `htmlcov/index.html`.

The post-processing core is host-importable and covered without the Fusion
runtime. Direct `adsk` access is restricted to `fusion_adapters/` and the
dialog/UI layer; architecture tests enforce that boundary. Host tests do not
replace validation inside Fusion for NC Program interaction, post processing,
UI events, or generated machine behavior.

- Create a development branch:

```bash
git checkout -b dev
```

- Commit and push changes:

```bash
git commit -m "Describe your changes"
git push -u origin dev
```

## Project Structure (key files)
- `Makera Community.py` – main add-in entry point
- `config.py` – global configuration
- `commands/` – base folder for all add-ons to Fusion
- `commands/postProcessor` - The post post-processor
- `commands/postProcessor/dialog` - UI parts
- `commands/postProcessor/dialog/resources/i18n` - Translations
- `lib/` – general helper libraries

## Contributing
- Fork the repository and open pull requests against `dev`.
- Follow the project's code style and write clear commit messages.

## License
GNU General Public License v2.0

## Contact
Use Github issues for any issues

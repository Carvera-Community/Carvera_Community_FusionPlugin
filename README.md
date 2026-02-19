# Makera Community Fusion Plugin

Short description: The Autodesk Fusion plugin created by the Makera Community

## Overview
This repository contains the Autodesk Fusion add-in for the Makera Community. It allows you to do post post-processing of the g-code that the community post-processor generates.  

## Features
- It takes each operation and outputs either one file per operation, per setup, per setup and tool or one single file. 
- Rotation of the A-axis if one is installed for support of indexed milling.
- Allows tool changes in a single setup
- Adds rapid moves when no cut iss being made
- ... and more!

## Acknowledements
This plugin was heavily inspired by Tim Patersons [PostProcessAll](https://github.com/TimPaterson/Fusion360-Batch-Post) plugin. It started as an attempt to extend his work to allow processing of multiple Setups and adding A-axis rotations between them to allow indexed milling, but in the end it just wasn't as simple as I had in my mind so I decided to just build it from scratch and replicate the functionality instead.

## Requirements
- Autodesk Fusion (Personal Edition)

## Installation
1. Clone the repository:

```bash
git clone git@github.com:USERNAME/REPO.git
cd "Makera Community"
```

2. Follow the generic instructions to install add-ins into Fusion 360:
- Go to Utilities
- Open Scripts and add-ins...
- Click the '+' above the table with plugins and scripts
- Choose 'Script or add-in from device'
- Select the folder that you just cloned the repo to (the folder with the Makera Community.manifest file)
- Done.

You should now se a new icon in the Manufacture workspace, next to the Setup sheet under Milling.

## Usage
(To be added)

## Development
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
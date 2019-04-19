# Mines MakerMart Vending Machine Interface

Webserver in Flask to operate a custom vending machine locally or remotely.

## Requirements

Requires python 3 to be installed and in PATH.

## Installation
In a command line, navigate to the project directory and run this command:

```
python3 -m venv venv
```

This creates a "virtual environment" in the project directory, which keeps installed packages contained.

Then on Linux, run the following:
```source venv/bin/activate```

or on Windows:
```venv\Scripts\activate.bat```

Either way, this "activates" the virtual environment so calls to python in this command line get routed through the virtual environment. This needs to be run every time you open a new command line.

Then:

```
pip install -r requirements.txt
```

This installs all the libraries required for the program. Now you're free to run it:
```
python run.py
```

# CS:GO Anti-Cheat System

This project implements an anti-cheat system for CS:GO using computer vision techniques. It utilizes the YOLO (You Only Look Once) model for detecting player behavior and overlays in the game.

## Features

- Monitors player behavior in CS:GO.
- Detects potential cheating through angular velocity and overlay detection.
- Provides a GUI for starting and stopping the anti-cheat system.
- Logs detected features to a CSV file for analysis.

## Requirements

- Python 3.x
- Required libraries listed in `requirements.txt`

## Installation

1. Clone the repository:

   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. Create a virtual environment (optional but recommended):

   ```bash
   python -m venv .venv
   ```

3. Activate the virtual environment:

   - On Windows:
     ```bash
     .venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     source .venv/bin/activate
     ```

4. Install the required packages:

   ```bash
   pip install -r requirements.txt
   ```

5. Ensure you have the YOLO model weights (`best.pt`) and offsets JSON file in the correct directory structure.

## Usage

1. Start the GUI:

   ```bash
   python gui.py
   ```

2. Use the GUI to start the anti-cheat system. It will monitor the CS:GO process for potential cheating behavior.

3. Feedback can be provided through the GUI after watching video clips.

## Notes

- Ensure that CS:GO is running before starting the anti-cheat system.
- The system may require administrative privileges to access certain processes.

## License

This project is licensed under the MIT License.

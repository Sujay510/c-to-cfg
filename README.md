Requirements

Python 3.10+
Graphviz (software)
Git

Installation
Step 1 — Install Graphviz
Windows
powershellwinget install graphviz
After installing, add C:\Program Files\Graphviz\bin to your system PATH,
then restart your terminal.
Linux
bashsudo apt install graphviz -y
Mac
bashbrew install graphviz
Verify:
bashdot -version

Step 2 — Clone the Repo

Step 3 — Create Virtual Environment

Windows
powershell python -m venv venv
then in termina    .\venv\Scripts\Activate.ps1

Linux / Mac
bashpython3 -m venv venv
source venv/bin/activate

Step 4 — Install Dependencies
bashpip install -r requirements.txt

How to Run

Put your C code in samples/sample.c
Run:

Windows
powershellpython main.py
Linux / Mac
bash python3 main.py

CFG image saved as cfg_output.png and opens automatically.


Project Structure
cfg_project/
├── main.py            ← entry point
├── requirements.txt
├── samples/
│   └── sample.c       ← your C code goes here
└── src/
    ├── parser.py      ← parses C code
    ├── cfg_builder.py ← builds CFG graph
    └── visualizer.py  ← saves CFG as PNG

Roadmap

 Phase 1 — C to CFG

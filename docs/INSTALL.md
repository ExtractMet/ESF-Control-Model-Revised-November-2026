# ESF-DT — Installation

Reference plant anonymised as **Industry-X**.

---

## 1. Nothing at all

Open `web/esf_console.html` in any modern browser. The whole engine, the
schematic and the charts are inside that one file. No Python, no server, no
network. Copy it onto a USB stick and it works in the control room.

This is the right choice for demonstrations, training and sharing a case.

---

## 2. Full package

### Requirements

* Python 3.9 or newer
* 200 MB of disk, 1 GB of RAM
* Windows, macOS or Linux

### Install

```bash
cd esf
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r docs/requirements.txt
```

On Debian or Ubuntu the desktop application also needs Tk:

```bash
sudo apt-get install python3-tk
```

### Check the installation

```bash
python -c "from esf_dt.static_model import run_static; \
           print(run_static()['KPI']['SEC_operating_kWh_tHM'])"
```

should print a figure close to **764** kWh/tHM.

Then regenerate the full validation set — tables plus nineteen figure sets,
about two minutes:

```bash
python run_validation.py --outdir figures
```

---

## 3. Running the interfaces

| Interface | Command |
|---|---|
| Web workbench | `streamlit run gui/esf_streamlit.py` |
| Desktop application | `python gui/esf_gui_tk.py` |
| Browser console | open `web/esf_console.html` |

The web workbench opens on `http://localhost:8501`. To serve it on the plant
network:

```bash
streamlit run gui/esf_streamlit.py --server.address 0.0.0.0 --server.port 8501
```

---

## 4. Using the engine directly

```python
from esf_dt.static_model import run_static
from esf_dt.dynamic_model import run_dynamic
from esf_dt.geometry import FurnaceGeometry
from esf_dt.electrical import ElectricalConfig

geo  = FurnaceGeometry(length=35.0, width=11.0, n_electrodes=6)
elec = ElectricalConfig(secondary_voltage_V=420.0)

r = run_static(dri_name="DRI-B (15.5 % gangue)",
               metallisation_pct=94.0,
               tap_temperature_C=1500.0,
               target_basicity_B2=1.10,
               heat_loss_mode="geometry",
               productivity_tHM_h=143.0,
               geometry=geo, electrical=elec)

d = run_dynamic(duration_min=420, dt_s=10.0,
                dri_feed_t_h=160.0, power_MW=112.0,
                power_control="temperature", target_metal_T_C=1500.0,
                geometry=geo, electrical=elec)
```

Both return plain dictionaries, so they drop straight into a notebook, a
batch study or a plant historian integration.

---

## 5. Deployment notes

* **Air-gapped sites.** The package has no network calls. The browser console
  is a single file; the Python package needs only NumPy, and Matplotlib,
  Streamlit and Pandas for the optional interfaces.
* **Historian integration.** `run_dynamic` accepts a `Schedule` object for
  the power programme, so recorded plant data can be replayed against the
  model to fit the kinetic constants.
* **Performance.** A static solve takes about 50 ms; a seven-hour dynamic
  campaign at a 10 s step takes a few seconds. A full parametric sweep of
  thirty cases is under two seconds.

---

## 6. Support

Commercial software of Extractmet Private Limited. Evaluation, pilot and
licence terms, plant calibration services and training on request.

© Extractmet Private Limited, IIT Madras Research Park. ESF-DT v1.0.0.

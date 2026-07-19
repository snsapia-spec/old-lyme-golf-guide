from pathlib import Path
import json, zipfile
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LightSource
import rasterio
from rasterio.enums import Resampling

SRC=Path('source')
OUT=Path('outputs'); OUT.mkdir(exist_ok=True)

def unzip_all():
    for z in SRC.rglob('*.zip'):
        d=z.with_suffix('')
        d.mkdir(exist_ok=True)
        with zipfile.ZipFile(z) as f: f.extractall(d)

def
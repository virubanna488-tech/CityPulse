import sys

print("Python version:", sys.version)

print("Importing pandas...", flush=True)
import pandas as pd
print("Pandas version:", pd.__version__, flush=True)

print("Importing requests...", flush=True)
import requests
print("Requests version:", requests.__version__, flush=True)

print("Importing folium...", flush=True)
import folium
print("Folium version:", folium.__version__, flush=True)

print("Importing streamlit...", flush=True)
import streamlit as st
print("Streamlit successfully imported!", flush=True)

print("Importing streamlit_folium...", flush=True)
from streamlit_folium import st_folium
print("streamlit-folium successfully imported (st_folium callable)!", flush=True)

# Quick Dataframe sanity check
df = pd.DataFrame({
    'timestamp': ['2026-09-24 13:30:00'],
    'zone': ['Zone-B'],
    'value': [42.5]
})
print("Sample DataFrame created successfully:")
print(df)

print("\n===========================================")
print(">>> ALL CITYPULSE DEPENDENCIES VERIFIED <<<")
print("===========================================", flush=True)

import streamlit as st
import pandas as pd
import os
import json 

# --- ΡΥΘΜΙΣΕΙΣ ΣΕΛΙΔΑΣ ---
st.set_page_config(page_title="Weld Info Viewer", layout="wide", page_icon="ℹ️")

# --- ΡΥΘΜΙΣΕΙΣ & ΑΡΧΕΙΑ ---
SETTINGS_FILE = "settings.json"
PERMANENT_MASTER = "master.xlsx" 

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

# --- ΦΟΡΤΩΣΗ ΔΕΔΟΜΕΝΩΝ ---
settings = load_settings()
col_line_name = settings.get("col_line_name", None)
col_weld_name = settings.get("col_weld_name", None)

st.title("ℹ️ Weld Info / WPS Viewer")

# Έλεγχος αν υπάρχει το Master Excel
if os.path.exists(PERMANENT_MASTER):
    try:
        # Φόρτωση του Excel
        df = pd.read_excel(PERMANENT_MASTER)
        df.columns = df.columns.astype(str).str.strip() # Καθαρισμός ονομάτων στηλών
        
        # Έλεγχος αν έχουν οριστεί οι στήλες από το άλλο πρόγραμμα
        if col_line_name and col_weld_name and col_line_name in df.columns and col_weld_name in df.columns:
            
            st.info("Επίλεξε Γραμμή και Κόλληση για να δεις τις λεπτομέρειες.")
            
            c1, c2 = st.columns([1, 2])
            
            # Επιλογή Line
            lines = sorted(df[col_line_name].astype(str).unique())
            s_line = c1.selectbox("Line No", lines, index=None, placeholder="Επίλεξε Γραμμή...")
            
            # Επιλογή Weld (εξαρτάται από το Line)
            s_weld = None
            if s_line:
                wlist = sorted(df[df[col_line_name] == s_line][col_weld_name].astype(str).unique())
                s_weld = c1.selectbox("Weld No", wlist, index=None, placeholder="Επίλεξε Κόλληση...")
                
            st.divider()

            # Εμφάνιση αποτελεσμάτων
            if s_line and s_weld:
                row = df[(df[col_line_name] == s_line) & (df[col_weld_name] == s_weld)]
                if not row.empty:
                    st.subheader(f"Λεπτομέρειες: {s_line} - {s_weld}")
                    st.table(row.T) # Εμφάνιση κάθετα (Transpose)
                else:
                    st.warning("Δεν βρέθηκαν δεδομένα.")
        else:
            st.error("⚠️ Οι ρυθμίσεις στηλών δεν είναι σωστές ή λείπουν.")
            st.warning("Παρακαλώ ανοίξτε το 'Weld Manager' και πηγαίνετε στα Settings για να ορίσετε τις στήλες (Mapping).")
            
    except Exception as e:
        st.error(f"Σφάλμα κατά το άνοιγμα του αρχείου: {e}")
else:
    st.error("⛔ Δεν βρέθηκε το αρχείο 'master.xlsx'.")
    st.info("Παρακαλώ χρησιμοποιήστε το 'Weld Manager' για να ανεβάσετε το αρχείο master.")

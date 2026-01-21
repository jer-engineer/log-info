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
st.title("ℹ️ Weld Info / WPS Viewer")

# Προσπάθεια φόρτωσης του Master Excel
df = None
if os.path.exists(PERMANENT_MASTER):
    try:
        df = pd.read_excel(PERMANENT_MASTER)
        df.columns = df.columns.astype(str).str.strip()
    except Exception as e:
        st.error(f"Error reading Excel: {e}")
else:
    st.warning("⚠️ Δεν βρέθηκε το αρχείο 'master.xlsx'. Τοποθέτησέ το στον ίδιο φάκελο.")

# --- SIDEBAR: ΡΥΘΜΙΣΕΙΣ (ΑΝ ΧΡΕΙΑΖΟΝΤΑΙ) ---
with st.sidebar:
    st.header("⚙️ Ρυθμίσεις")
    
    # Φόρτωση υπαρχουσών ρυθμίσεων
    settings = load_settings()
    saved_line = settings.get("col_line_name")
    saved_weld = settings.get("col_weld_name")

    # Αν έχουμε Excel, ας δούμε αν ταιριάζουν οι στήλες
    if df is not None:
        all_cols = list(df.columns)
        
        # Έλεγχος αν οι αποθηκευμένες στήλες υπάρχουν όντως
        idx_line = 0
        idx_weld = 0
        
        if saved_line in all_cols:
            idx_line = all_cols.index(saved_line)
        if saved_weld in all_cols:
            idx_weld = all_cols.index(saved_weld)

        # Dropdowns για επιλογή στήλης
        st.caption("Επίλεξε τις στήλες αναζήτησης:")
        sel_line = st.selectbox("Στήλη LINE:", all_cols, index=idx_line)
        sel_weld = st.selectbox("Στήλη WELD:", all_cols, index=idx_weld)
        
        # Ενημέρωση μεταβλητών για χρήση παρακάτω
        col_line_name = sel_line
        col_weld_name = sel_weld
    else:
        st.info("Φόρτωσε πρώτα ένα Excel (master.xlsx).")
        col_line_name = None
        col_weld_name = None

# --- ΚΥΡΙΑ ΟΘΟΝΗ ---
if df is not None and col_line_name and col_weld_name:
    
    st.markdown("---")
    c1, c2 = st.columns([1, 2])
    
    # 1. Επιλογή Line
    lines = sorted(df[col_line_name].astype(str).unique())
    s_line = c1.selectbox("🔍 Αναζήτηση Line No:", lines, index=None, placeholder="Επίλεξε...")
    
    # 2. Επιλογή Weld (φιλτραρισμένη)
    s_weld = None
    if s_line:
        # Βρες τις κολλήσεις που ανήκουν σε αυτή τη γραμμή
        wlist = sorted(df[df[col_line_name] == s_line][col_weld_name].astype(str).unique())
        s_weld = c1.selectbox("🔍 Αναζήτηση Weld No:", wlist, index=None, placeholder="Επίλεξε...")
        
    # 3. Εμφάνιση Πληροφοριών
    if s_line and s_weld:
        # Βρες τη γραμμή στο Excel
        row = df[(df[col_line_name] == s_line) & (df[col_weld_name] == s_weld)]
        
        if not row.empty:
            st.success(f"✅ Βρέθηκε: {s_line} / {s_weld}")
            
            # Μορφοποίηση εμφάνισης (Πίνακας)
            st.subheader("📋 Λεπτομέρειες")
            st.table(row.T) # Transpose για κάθετη λίστα
        else:
            st.warning("Δεν βρέθηκαν δεδομένα για αυτόν τον συνδυασμό.")
    else:
        st.info("👆 Επίλεξε Γραμμή και Κόλληση για να δεις τα δεδομένα.")

elif df is None:
    st.error("🛑 Λείπει το αρχείο δεδομένων.")

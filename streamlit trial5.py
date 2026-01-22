import streamlit as st
import pandas as pd
import os
import json

# --- ΡΥΘΜΙΣΕΙΣ ΣΕΛΙΔΑΣ ---
st.set_page_config(page_title="Weld Manager", layout="wide", page_icon="🏗️")

# --- ΣΤΑΘΕΡΕΣ ---
SETTINGS_FILE = "settings.json"
PERMANENT_MASTER = "master.xlsx"
DEFAULT_LINE_COL = "LINE No"
DEFAULT_WELD_COL = "Weld No"
DEFAULT_AP_COL = "AP Doc Code" # Default όνομα για το AP Code

# --- ΦΟΡΤΩΣΗ RΥΘΜΙΣΕΩΝ ---
def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

# --- ΦΟΡΤΩΣΗ ΔΕΔΟΜΕΝΩΝ ---
@st.cache_data # Cache για να μην ξαναφορτώνει το Excel σε κάθε κλικ
def load_data():
    if os.path.exists(PERMANENT_MASTER):
        try:
            df = pd.read_excel(PERMANENT_MASTER)
            df.columns = df.columns.astype(str).str.strip()
            return df
        except Exception as e:
            st.error(f"Error reading Excel: {e}")
            return None
    return None

df = load_data()

# --- SIDEBAR: ΜΕΝΟΥ & ΡΥΘΜΙΣΕΙΣ ---
with st.sidebar:
    st.title("🎛️ Μενού")
    
    # 1. Επιλογή Σελίδας (Navigation)
    page = st.radio("Μετάβαση σε:", ["🔍 Αναζήτηση Κόλλησης", "📄 Λίστα Γραμμής (Line List)"])
    
    st.divider()
    st.header("⚙️ Ρυθμίσεις Στηλών")
    
    if df is not None:
        all_cols = list(df.columns)
        settings = load_settings()

        # Helper για εύρεση index
        def get_index(col_list, saved_val, default_val):
            if saved_val in col_list: return col_list.index(saved_val)
            if default_val in col_list: return col_list.index(default_val)
            return 0

        # Dropdowns για αντιστοίχιση στηλών
        idx_line = get_index(all_cols, settings.get("col_line_name"), DEFAULT_LINE_COL)
        idx_weld = get_index(all_cols, settings.get("col_weld_name"), DEFAULT_WELD_COL)
        idx_ap = get_index(all_cols, settings.get("col_ap_name"), DEFAULT_AP_COL)

        col_line_name = st.selectbox("Στήλη LINE No:", all_cols, index=idx_line)
        col_weld_name = st.selectbox("Στήλη WELD No:", all_cols, index=idx_weld)
        col_ap_name = st.selectbox("Στήλη AP Doc Code:", all_cols, index=idx_ap)
    else:
        st.warning("Φόρτωσε το master.xlsx")
        col_line_name, col_weld_name, col_ap_name = None, None, None

# --- ΚΥΡΙΑ ΛΟΓΙΚΗ ---

if df is not None and col_line_name:

    # ==========================================
    # ΣΕΛΙΔΑ 1: ΑΝΑΖΗΤΗΣΗ ΚΟΛΛΗΣΗΣ (Παλιά λειτουργία)
    # ==========================================
    if page == "🔍 Αναζήτηση Κόλλησης":
        st.title("🔍 Λεπτομέρειες Κόλλησης")
        st.markdown("---")
        
        c1, c2 = st.columns([1, 2])
        
        # Επιλογή Line
        lines = sorted(df[col_line_name].astype(str).unique())
        s_line = c1.selectbox("Αναζήτηση Line No:", lines, index=None, placeholder="Επίλεξε Γραμμή...")
        
        # Επιλογή Weld
        s_weld = None
        if s_line:
            wlist = sorted(df[df[col_line_name] == s_line][col_weld_name].astype(str).unique())
            s_weld = c1.selectbox("Αναζήτηση Weld No:", wlist, index=None, placeholder="Επίλεξε Κόλληση...")
        
        if s_line and s_weld:
            row = df[(df[col_line_name] == s_line) & (df[col_weld_name] == s_weld)]
            if not row.empty:
                st.success(f"Selected: {s_line} / {s_weld}")
                st.table(row.T)
            else:
                st.warning("Δεν βρέθηκαν δεδομένα.")

    # ==========================================
    # ΣΕΛΙΔΑ 2: ΛΙΣΤΑ ΓΡΑΜΜΗΣ (Νέα λειτουργία)
    # ==========================================
    elif page == "📄 Λίστα Γραμμής (Line List)":
        st.title("📄 Επισκόπηση Γραμμής")
        st.markdown("---")

        # 1. Επιλογή Line (Μόνο Line ζήτησες)
        lines = sorted(df[col_line_name].astype(str).unique())
        sel_line_overview = st.selectbox("🗂️ Επίλεξε Line No:", lines, index=None, placeholder="Διάλεξε γραμμή για εμφάνιση λίστας...")

        if sel_line_overview:
            # Φιλτράρισμα του Excel μόνο για αυτή τη γραμμή
            subset = df[df[col_line_name] == sel_line_overview]

            # 2. Εύρεση του AP Doc Code (Μοναδικό)
            # Παίρνουμε την πρώτη τιμή που βρίσκουμε, αφού είναι μοναδικό για τη γραμμή
            ap_value = "N/A"
            if col_ap_name in subset.columns and not subset.empty:
                ap_value = subset[col_ap_name].iloc[0]

            # Εμφάνιση του AP Doc Code ψηλά και καθαρά
            st.info(f"📌 **Line:** {sel_line_overview}  |  📄 **AP Doc Code:** {ap_value}")

            # 3. Λίστα με τα Weld No (Κάθετη λίστα)
            st.subheader("Λίστα Κολλήσεων (Weld List)")
            
            # Δημιουργούμε ένα απλό DataFrame μόνο με τα Weld No για εμφάνιση
            weld_list_df = subset[[col_weld_name]].drop_duplicates().sort_values(by=col_weld_name)
            
            # Reset index για να ξεκινάει η αρίθμηση από το 1 (προαιρετικό)
            weld_list_df.reset_index(drop=True, inplace=True)
            weld_list_df.index += 1 

            # Εμφάνιση ως πίνακας (dataframe) που πιάνει όλο το πλάτος
            st.dataframe(
                weld_list_df, 
                use_container_width=True, 
                height=500  # Ύψος πίνακα (scrollable αν είναι πολλά)
            )

else:
    if df is None:
        st.error("⚠️ Παρακαλώ βεβαιώσου ότι το αρχείο 'master.xlsx' υπάρχει στον φάκελο.")

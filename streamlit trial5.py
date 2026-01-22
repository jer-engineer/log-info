import streamlit as st
import pandas as pd
import os
import json

# --- ΡΥΘΜΙΣΕΙΣ ΣΕΛΙΔΑΣ ---
st.set_page_config(page_title="Weld Manager", layout="wide", page_icon="🏗️")

# --- ΣΤΑΘΕΡΕΣ ---
SETTINGS_FILE = "settings.json"
PERMANENT_MASTER = "master.xlsx"

# Default ονόματα στηλών (αν το Excel έχει άλλα, τα αλλάζεις από το Sidebar)
DEFAULT_LINE_COL = "LINE No"
DEFAULT_WELD_COL = "Weld No"
DEFAULT_AP_COL = "AP Doc Code"
DEFAULT_WPS_COL = "WPS"
DEFAULT_PREHEAT_COL = "Preheat"
DEFAULT_PWHT_COL = "PWHT"
DEFAULT_MAT_COL = "Material 1" # Ή σκέτο "Material" ανάλογα το Excel
DEFAULT_DRAW_COL = "Drawing No"  # <--- ΝΕΟ: Default όνομα στήλης

# --- ΦΟΡΤΩΣΗ ΡΥΘΜΙΣΕΩΝ ---
def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

# --- ΦΟΡΤΩΣΗ ΔΕΔΟΜΕΝΩΝ ---
@st.cache_data
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
    
    # 1. Επιλογή Σελίδας (Άλλαξε η σειρά όπως ζήτησες)
    page = st.radio("Μετάβαση σε:", 
                    ["📄 Λίστα Γραμμής (Line List)", 
                     "🔍 Αναζήτηση Κόλλησης (Λεπτομέρειες)"])
    
    st.divider()
    st.header("⚙️ Ρυθμίσεις Στηλών")
    
    if df is not None:
        all_cols = list(df.columns)
        settings = load_settings()

        # Helper για εύρεση index (θέσης) στο dropdown
        def get_index(col_list, saved_val, default_val):
            if saved_val in col_list: return col_list.index(saved_val)
            if default_val in col_list: return col_list.index(default_val)
            return 0

        # --- Dropdowns για αντιστοίχιση ---
        st.caption("Βασικά Πεδία")
        idx_line = get_index(all_cols, settings.get("col_line_name"), DEFAULT_LINE_COL)
        idx_weld = get_index(all_cols, settings.get("col_weld_name"), DEFAULT_WELD_COL)
        idx_ap   = get_index(all_cols, settings.get("col_ap_name"), DEFAULT_AP_COL)

        col_line_name = st.selectbox("Στήλη LINE No:", all_cols, index=idx_line)
        col_weld_name = st.selectbox("Στήλη WELD No:", all_cols, index=idx_weld)
        col_ap_name   = st.selectbox("Στήλη AP Doc Code:", all_cols, index=idx_ap)

        st.caption("Πεδία Πίνακα (Line List)")
        idx_wps  = get_index(all_cols, settings.get("col_wps_name"), DEFAULT_WPS_COL)
        idx_pre  = get_index(all_cols, settings.get("col_pre_name"), DEFAULT_PREHEAT_COL)
        idx_pwht = get_index(all_cols, settings.get("col_pwht_name"), DEFAULT_PWHT_COL)
        idx_mat  = get_index(all_cols, settings.get("col_mat_name"), DEFAULT_MAT_COL)

        col_wps_name  = st.selectbox("Στήλη WPS:", all_cols, index=idx_wps)
        col_pre_name  = st.selectbox("Στήλη Preheat:", all_cols, index=idx_pre)
        col_pwht_name = st.selectbox("Στήλη PWHT:", all_cols, index=idx_pwht)
        col_mat_name  = st.selectbox("Στήλη Material:", all_cols, index=idx_mat)

    else:
        st.warning("Φόρτωσε το master.xlsx")
        col_line_name = None

# --- ΚΥΡΙΑ ΛΟΓΙΚΗ ---

if df is not None and col_line_name:

    # ==========================================
    # ΣΕΛΙΔΑ 1: ΛΙΣΤΑ ΓΡΑΜΜΗΣ (DEFAULT)
    # ==========================================
    if page == "📄 Λίστα Γραμμής (Line List)":
        st.title("📄 Επισκόπηση Γραμμής")
        st.markdown("---")

        # 1. Επιλογή Line
        lines = sorted(df[col_line_name].astype(str).unique())
        sel_line_overview = st.selectbox("🗂️ Επίλεξε Line No:", lines, index=None, placeholder="Διάλεξε γραμμή...")

        if sel_line_overview:
            # Φιλτράρισμα του Excel μόνο για αυτή τη γραμμή
            subset = df[df[col_line_name] == sel_line_overview]

            # 2. Εύρεση του AP Doc Code (Μοναδικό)
            ap_value = "N/A"
            if col_ap_name in subset.columns and not subset.empty:
                val = subset[col_ap_name].iloc[0]
                # Έλεγχος αν είναι nan
                if pd.notna(val):
                    ap_value = val

            # Εμφάνιση Header
            st.info(f"📌 **Line:** {sel_line_overview}  |  📄 **AP Doc Code:** {ap_value}  |  📐 **Drawing:** {draw_value}")

            # 3. Λίστα Κολλήσεων με τα επιπλέον πεδία
            st.subheader("Λίστα Κολλήσεων")
            
            # Επιλέγουμε τις στήλες που ζήτησες
            cols_to_show = [col_weld_name, col_wps_name, col_pre_name, col_pwht_name, col_mat_name]
            
            # Δημιουργία πίνακα μόνο με αυτές τις στήλες
            # Χρησιμοποιούμε .get() για ασφάλεια σε περίπτωση που κάποια στήλη λείπει
            existing_cols = [c for c in cols_to_show if c in subset.columns]
            
            display_df = subset[existing_cols].copy()
            
            # Ταξινόμηση βάσει Weld No
            if col_weld_name in display_df.columns:
                display_df.sort_values(by=col_weld_name, inplace=True)

            # Επαναφορά index για αρίθμηση 1, 2, 3...
            display_df.reset_index(drop=True, inplace=True)
            display_df.index += 1 

            # Εμφάνιση πίνακα
            st.dataframe(
                display_df, 
                use_container_width=True, 
                height=600
            )

    # ==========================================
    # ΣΕΛΙΔΑ 2: ΑΝΑΖΗΤΗΣΗ ΚΟΛΛΗΣΗΣ (ΛΕΠΤΟΜΕΡΕΙΕΣ)
    # ==========================================
    elif page == "🔍 Αναζήτηση Κόλλησης (Λεπτομέρειες)":
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

else:
    if df is None:
        st.error("⚠️ Παρακαλώ βεβαιώσου ότι το αρχείο 'master.xlsx' υπάρχει στον φάκελο.")

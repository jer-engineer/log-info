import streamlit as st
import pandas as pd
import io
import os
import json 
from datetime import datetime

# --- ΡΥΘΜΙΣΕΙΣ ΣΕΛΙΔΑΣ ---
st.set_page_config(page_title="Cloud Weld Manager Pro", layout="wide", page_icon="🏗️")

# --- 0. ΛΕΙΤΟΥΡΓΙΕΣ ΑΠΟΘΗΚΕΥΣΗΣ ---
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

def save_settings_to_file():
    settings = {
        "col_line_name": st.session_state.col_line_name,
        "col_weld_name": st.session_state.col_weld_name,
        "auto_fill_columns": st.session_state.auto_fill_columns,
        "production_ref_columns": st.session_state.production_ref_columns,
        "custom_free_columns": st.session_state.custom_free_columns
    }
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=4)

saved_config = load_settings()

# --- 1. SESSION STATE ---
if 'master_df' not in st.session_state:
    st.session_state.master_df = None
if 'production_log' not in st.session_state:
    st.session_state.production_log = pd.DataFrame() 

# --- INITIALIZE VARIABLES ---
if 'col_line_name' not in st.session_state:
    st.session_state.col_line_name = saved_config.get("col_line_name", None)
if 'col_weld_name' not in st.session_state:
    st.session_state.col_weld_name = saved_config.get("col_weld_name", None)
if 'auto_fill_columns' not in st.session_state:
    st.session_state.auto_fill_columns = saved_config.get("auto_fill_columns", [])
if 'production_ref_columns' not in st.session_state:
    st.session_state.production_ref_columns = saved_config.get("production_ref_columns", [])
if 'custom_free_columns' not in st.session_state:
    st.session_state.custom_free_columns = saved_config.get("custom_free_columns", [])

# --- AUTO-LOAD MASTER IF EXISTS (Για να δουλεύει η πρώτη σελίδα) ---
if st.session_state.master_df is None and os.path.exists(PERMANENT_MASTER):
    try:
        st.session_state.master_df = pd.read_excel(PERMANENT_MASTER, header=0)
        # Clean columns just in case
        st.session_state.master_df.columns = st.session_state.master_df.columns.astype(str).str.strip()
    except:
        pass

# --- 2. SIDEBAR MENU ---
with st.sidebar:
    st.title("🎛️ Μενού")
    
    # ΣΕΙΡΑ ΜΕΝΟΥ: 1. INFO, 2. PRODUCTION, 3. SETTINGS
    app_mode = st.radio("Επίλεξε Λειτουργία:", [
        "ℹ️ Weld Info / WPS", 
        "🔨 Daily Production", 
        "⚙️ Settings & Setup"
    ])
    
    st.divider()
    if st.button("💾 Force Save Settings"):
        save_settings_to_file()
        st.toast("Settings saved!", icon="💾")

# =========================================================
# 1. PAGE: WELD INFO (HOME)
# =========================================================
if app_mode == "ℹ️ Weld Info / WPS":
    st.header("ℹ️ Αναζήτηση Πληροφοριών")
    
    if st.session_state.master_df is not None:
        master = st.session_state.master_df
        if st.session_state.col_line_name and st.session_state.col_weld_name:
            LINE_COL = st.session_state.col_line_name
            WELD_COL = st.session_state.col_weld_name
            
            # Check consistency
            if LINE_COL in master.columns and WELD_COL in master.columns:
                c1, c2 = st.columns([1, 2])
                lines = sorted(master[LINE_COL].astype(str).unique())
                s_line = c1.selectbox("Line", lines, index=None)
                
                s_weld = None
                if s_line:
                    wlist = sorted(master[master[LINE_COL] == s_line][WELD_COL].astype(str).unique())
                    s_weld = c1.selectbox("Weld", wlist, index=None)
                    
                if s_line and s_weld:
                    row = master[(master[LINE_COL] == s_line) & (master[WELD_COL] == s_weld)]
                    st.table(row.T)
            else:
                st.error("Οι αποθηκευμένες στήλες (Mapping) δεν ταιριάζουν με το αρχείο. Πήγαινε στα Settings.")
        else:
            st.warning("Παρακαλώ κάντε Mapping στα Settings πρώτα.")
    else:
        st.warning("Δεν βρέθηκε Master Excel. Πήγαινε στα Settings να ανεβάσεις αρχείο.")

# =========================================================
# 2. PAGE: DAILY PRODUCTION
# =========================================================
elif app_mode == "🔨 Daily Production":
    st.header("🔨 Καταγραφή Παραγωγής")
    
    if st.session_state.master_df is None:
        st.error("⛔ Δεν έχει φορτωθεί Master Excel. Πήγαινε στα Settings.")
    else:
        master = st.session_state.master_df
        LINE_COL = st.session_state.col_line_name
        WELD_COL = st.session_state.col_weld_name
        
        if LINE_COL and WELD_COL and LINE_COL in master.columns and WELD_COL in master.columns:
            # --- 1. SELECTION ---
            c_sel1, c_sel2 = st.columns(2)
            lines = sorted(master[LINE_COL].astype(str).unique())
            sel_line = c_sel1.selectbox("Line No", lines, index=None, placeholder="Search Line...")
            
            avail_welds = []
            if sel_line:
                avail_welds = sorted(master[master[LINE_COL] == sel_line][WELD_COL].astype(str).unique())
            sel_weld = c_sel2.selectbox("Weld No", avail_welds, index=None, placeholder="Select Weld...")

            # --- 2. LIVE INFO PANEL (OPTIONAL) ---
            if sel_line and sel_weld and st.session_state.production_ref_columns:
                row = master[(master[LINE_COL] == sel_line) & (master[WELD_COL] == sel_weld)]
                if not row.empty:
                    st.info("ℹ️ Extra Info (από Settings)")
                    try:
                        ref_data = row[st.session_state.production_ref_columns].iloc[0].to_dict()
                        cols = st.columns(len(ref_data))
                        for idx, (k, v) in enumerate(ref_data.items()):
                            cols[idx % len(cols)].metric(label=str(k), value=str(v))
                    except Exception as e:
                        st.warning(f"Error info: {e}")
            
            st.divider()

            # --- 3. INPUT FORM ---
            with st.form("entry_form"):
                st.subheader("Στοιχεία Καταχώρησης")
                
                # STANDARD FIELDS (MANDATORY)
                row1_c1, row1_c2, row1_c3 = st.columns(3)
                date_val = row1_c1.date_input("Date")
                res = row1_c2.selectbox("Result", ["Accepted", "Rejected", "Pending"])
                welder = row1_c3.text_input("WELDER", value="User")
                
                row2_c1, row2_c2 = st.columns(2)
                type1_val = row2_c1.text_input("HEAT NO TYPE 1")
                type2_val = row2_c2.text_input("HEAT NO TYPE 2")

                # CUSTOM FIELDS (OPTIONAL)
                custom_values = {}
                if st.session_state.custom_free_columns:
                    st.write("📝 Extra Fields (Custom)")
                    c_cols = st.columns(len(st.session_state.custom_free_columns))
                    for idx, col_name in enumerate(st.session_state.custom_free_columns):
                        custom_values[col_name] = c_cols[idx % 3].text_input(col_name)

                submitted = st.form_submit_button("➕ Προσθήκη", type="primary")
                
                if submitted:
                    if sel_line and sel_weld:
                        formatted_date = date_val.strftime("%d/%m/%Y")

                        new_entry = {
                            "Date": formatted_date,
                            "Line No": sel_line,
                            "Weld No": sel_weld,
                            "HEAT NO TYPE 1": type1_val,
                            "HEAT NO TYPE 2": type2_val,
                            "WELDER": welder,
                            "Result": res
                        }
                        
                        # Auto-fill (OPTIONAL)
                        if st.session_state.auto_fill_columns:
                            row = master[(master[LINE_COL] == sel_line) & (master[WELD_COL] == sel_weld)]
                            if not row.empty:
                                for auto_col in st.session_state.auto_fill_columns:
                                    val = row[auto_col].values[0]
                                    new_entry[auto_col] = val
                        
                        new_entry.update(custom_values)
                        
                        # SAVE TO SESSION
                        st.session_state.production_log = pd.concat(
                            [st.session_state.production_log, pd.DataFrame([new_entry])], 
                            ignore_index=True
                        )
                        st.success("Καταχωρήθηκε!")
                        st.rerun()
                    else:
                        st.error("Πρέπει να επιλέξεις Line και Weld!")
        else:
             st.error("Πρόβλημα με τις στήλες Line/Weld. Ελέγξτε τα Settings.")

        # --- 4. LOG ---
        st.divider()
        st.subheader("📋 Log Ημέρας")
        
        if not st.session_state.production_log.empty:
            edited_log = st.data_editor(
                st.session_state.production_log,
                num_rows="dynamic",
                use_container_width=True,
                key="editor_log"
            )
            
            if not edited_log.equals(st.session_state.production_log):
                st.session_state.production_log = edited_log
                st.rerun()

            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer) as writer:
                st.session_state.production_log.to_excel(writer, index=False)
            st.download_button("📥 Download Excel", buffer.getvalue(), "daily_production.xlsx")
        else:
            st.info("Καμία εγγραφή ακόμα.")

# =========================================================
# 3. PAGE: SETTINGS (LAST)
# =========================================================
elif app_mode == "⚙️ Settings & Setup":
    st.header("⚙️ Ρυθμίσεις Εφαρμογής")
    
    # --- A. HEADER & UPLOAD ---
    with st.expander("1. Φόρτωση Master Excel", expanded=True):
        col_row, col_upload = st.columns([1, 2])
        with col_row:
            header_row_val = st.number_input("Γραμμή Τίτλων:", min_value=1, value=1)
        
        with col_upload:
            uploaded_master = st.file_uploader("Upload νέου Excel (αλλιώς φορτώνεται το μόνιμο)", type=["xlsx"])
        
        file_to_load = None
        if uploaded_master:
            file_to_load = uploaded_master
        elif os.path.exists(PERMANENT_MASTER):
            file_to_load = PERMANENT_MASTER
            st.info(f"📂 Χρήση μόνιμου αρχείου: {PERMANENT_MASTER}")

        if file_to_load:
            try:
                if st.session_state.master_df is None or uploaded_master:
                    df = pd.read_excel(file_to_load, header=header_row_val - 1)
                    df.columns = df.columns.astype(str).str.strip()
                    st.session_state.master_df = df
                    st.success(f"✅ Master Loaded! ({len(df)} lines)")
                else:
                    st.success(f"✅ Master Ready ({len(st.session_state.master_df)} lines)")
            except Exception as e:
                st.error(f"Error loading Excel: {e}")
        else:
             st.warning("⚠️ Δεν βρέθηκε αρχείο master.xlsx")

    # --- B. MAPPING ---
    if st.session_state.master_df is not None:
        with st.expander("2. Αντιστοίχιση Βασικών Στηλών (Mapping)", expanded=True):
            all_cols = list(st.session_state.master_df.columns)
            c1, c2 = st.columns(2)
            
            try:
                curr_line_idx = all_cols.index(st.session_state.col_line_name) if st.session_state.col_line_name in all_cols else 0
                curr_weld_idx = all_cols.index(st.session_state.col_weld_name) if st.session_state.col_weld_name in all_cols else 0
            except:
                curr_line_idx = 0
                curr_weld_idx = 0

            sel_line_col = c1.selectbox("Στήλη LINE NO:", all_cols, index=curr_line_idx)
            sel_weld_col = c2.selectbox("Στήλη WELD NO:", all_cols, index=curr_weld_idx)
            
            if st.button("💾 Επιβεβαίωση Mapping", type="primary"):
                st.session_state.col_line_name = sel_line_col
                st.session_state.col_weld_name = sel_weld_col
                save_settings_to_file()
                st.toast("Mapping Saved!", icon="✅")

        # --- C. ADVANCED (OPTIONAL) ---
        st.divider()
        st.subheader("🛠️ Διαμόρφωση Log (Προαιρετικά/Extra)")
        st.caption("Τα βασικά πεδία (Line, Weld, Heats, Welder, Result) υπάρχουν ήδη. Εδώ προσθέτεις ΜΟΝΟ αν θες κάτι έξτρα.")
        
        tab1, tab2, tab3 = st.tabs(["Extra Auto-Fill", "Extra Info Display", "Extra Text Inputs"])
        
        with tab1:
            st.write("Αντιγραφή δεδομένων από το Master στο Log (π.χ. Consumable).")
            valid_defaults = [c for c in st.session_state.auto_fill_columns if c in all_cols]
            sel_auto = st.multiselect("Επίλεξε στήλες (Optional):", all_cols, default=valid_defaults, key="multi_autofill")
            if st.button("💾 Save Auto-Fill"):
                st.session_state.auto_fill_columns = sel_auto
                save_settings_to_file()
                st.toast("Auto-fill saved!")

        with tab2:
            st.write("Εμφάνιση πληροφοριών στην οθόνη καταχώρησης (Read-only).")
            valid_defaults_ref = [c for c in st.session_state.production_ref_columns if c in all_cols]
            sel_ref = st.multiselect("Επίλεξε στήλες (Optional):", all_cols, default=valid_defaults_ref, key="multi_ref")
            if st.button("💾 Save Reference"):
                st.session_state.production_ref_columns = sel_ref
                save_settings_to_file()
                st.toast("Reference saved!")

        with tab3:
            st.write("Πρόσθεσε δικά σου πεδία που δεν υπάρχουν στο Excel.")
            current_custom = ", ".join(st.session_state.custom_free_columns)
            custom_input = st.text_area("Ονόματα πεδίων (χωρισμένα με κόμμα):", value=current_custom, placeholder="π.χ. Comments, Temperature")
            if st.button("💾 Save Custom Fields"):
                new_list = [x.strip() for x in custom_input.split(",") if x.strip()]
                st.session_state.custom_free_columns = new_list
                save_settings_to_file()
                st.toast(f"Saved custom fields!")

# --- AUTO-RUN ---
if __name__ == '__main__':
    import sys
    import subprocess
    if not os.environ.get("STREAMLIT_RUNNING"):
        env = os.environ.copy()
        env["STREAMLIT_RUNNING"] = "true"
        file_path = os.path.abspath(__file__)
        subprocess.run([sys.executable, "-m", "streamlit", "run", file_path], env=env)

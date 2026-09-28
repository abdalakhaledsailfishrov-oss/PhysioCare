import streamlit as st
import pandas as pd
import sqlite3

from io import BytesIO
from datetime import date

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="PhysioCare",
    page_icon="🦵",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =========================================================
# DATABASE
# =========================================================

DB_NAME = "physiocare.db"


def get_connection():
    return sqlite3.connect(DB_NAME)


def create_database():

    conn = get_connection()
    cursor = conn.cursor()

    # Patients
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER,
            gender TEXT
        )
    """)

    # Patient Joints
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patient_joints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            joint TEXT NOT NULL,
            UNIQUE(patient_id, joint),
            FOREIGN KEY(patient_id) REFERENCES patients(id)
        )
    """)

    # Sessions
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            joint_id INTEGER NOT NULL,
            session_number INTEGER NOT NULL,
            movement TEXT NOT NULL,
            rom REAL NOT NULL,
            session_date TEXT,
            notes TEXT,
            FOREIGN KEY(patient_id) REFERENCES patients(id),
            FOREIGN KEY(joint_id) REFERENCES patient_joints(id)
        )
    """)

    # Upgrade old database automatically
    cursor.execute("PRAGMA table_info(sessions)")

    columns = [
        row[1]
        for row in cursor.fetchall()
    ]

    if "session_date" not in columns:
        cursor.execute("""
            ALTER TABLE sessions
            ADD COLUMN session_date TEXT
        """)

    if "notes" not in columns:
        cursor.execute("""
            ALTER TABLE sessions
            ADD COLUMN notes TEXT
        """)

    conn.commit()
    conn.close()


create_database()


# =========================================================
# ROM REFERENCE VALUES
# =========================================================

REFERENCE_ROM = {

    "Shoulder": {
        "Flexion": 180,
        "Extension": 60,
        "Abduction": 180
    },

    "Elbow": {
        "Flexion": 150,
        "Extension": 0
    },

    "Wrist": {
        "Flexion": 80,
        "Extension": 70
    },

    "Hip": {
        "Flexion": 120,
        "Extension": 30
    },

    "Knee": {
        "Flexion": 135,
        "Extension": 0
    },

    "Ankle": {
        "Dorsiflexion": 20,
        "Plantarflexion": 50
    }
}


# =========================================================
# EXERCISE LIBRARY
# =========================================================

EXERCISES = {

    "Shoulder": [
        (
            "Pendulum Exercise",
            "Relax the arm and gently swing it forward and backward."
        ),
        (
            "Wall Climbing",
            "Use the fingers to slowly climb up the wall."
        ),
        (
            "Shoulder Flexion",
            "Raise the arm forward in a controlled movement."
        )
    ],

    "Elbow": [
        (
            "Elbow Flexion",
            "Slowly bend the elbow and return to the starting position."
        ),
        (
            "Elbow Extension",
            "Slowly straighten the elbow."
        )
    ],

    "Wrist": [
        (
            "Wrist Flexion",
            "Move the wrist downward slowly."
        ),
        (
            "Wrist Extension",
            "Move the wrist upward slowly."
        )
    ],

    "Hip": [
        (
            "Hip Flexion",
            "Raise the leg forward in a controlled movement."
        ),
        (
            "Hip Extension",
            "Move the leg backward while maintaining control."
        )
    ],

    "Knee": [
        (
            "Heel Slides",
            "Slide the heel toward the body and then straighten the leg."
        ),
        (
            "Seated Knee Extension",
            "Straighten the knee while sitting."
        ),
        (
            "Straight Leg Raise",
            "Keep the knee straight and raise the leg slowly."
        )
    ],

    "Ankle": [
        (
            "Ankle Pumps",
            "Move the ankle up and down repeatedly."
        ),
        (
            "Ankle Circles",
            "Rotate the ankle slowly in circular movements."
        )
    ]
}


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def get_patients():

    conn = get_connection()

    patients = pd.read_sql_query(
        "SELECT * FROM patients ORDER BY name",
        conn
    )

    conn.close()

    return patients


def get_patient_options(patients):

    return {
        f"{row['name']} — ID {row['id']}":
        row["id"]

        for _, row in patients.iterrows()
    }


def get_patient_joints(patient_id):

    conn = get_connection()

    joints = pd.read_sql_query(
        """
        SELECT id, joint
        FROM patient_joints
        WHERE patient_id = ?
        ORDER BY joint
        """,
        conn,
        params=(patient_id,)
    )

    conn.close()

    return joints


# =========================================================
# PDF GENERATOR
# =========================================================

def generate_pdf(patient, joint, sessions):

    buffer = BytesIO()

    pdf = canvas.Canvas(
        buffer,
        pagesize=A4
    )

    width, height = A4

    # Title
    pdf.setFont(
        "Helvetica-Bold",
        24
    )

    pdf.drawString(
        2 * cm,
        height - 2 * cm,
        "PhysioCare"
    )

    pdf.setFont(
        "Helvetica-Bold",
        15
    )

    pdf.drawString(
        2 * cm,
        height - 3 * cm,
        "Physiotherapy Patient Report"
    )

    # Patient information
    y = height - 5 * cm

    pdf.setFont(
        "Helvetica-Bold",
        12
    )

    pdf.drawString(
        2 * cm,
        y,
        "Patient Information"
    )

    y -= 0.8 * cm

    pdf.setFont(
        "Helvetica",
        11
    )

    pdf.drawString(
        2 * cm,
        y,
        f"Name: {patient['name']}"
    )

    y -= 0.6 * cm

    pdf.drawString(
        2 * cm,
        y,
        f"Age: {patient['age']}"
    )

    y -= 0.6 * cm

    pdf.drawString(
        2 * cm,
        y,
        f"Gender: {patient['gender']}"
    )

    y -= 0.6 * cm

    pdf.drawString(
        2 * cm,
        y,
        f"Joint: {joint}"
    )

    # Assessment History
    y -= 1.2 * cm

    pdf.setFont(
        "Helvetica-Bold",
        12
    )

    pdf.drawString(
        2 * cm,
        y,
        "Assessment History"
    )

    y -= 0.8 * cm

    pdf.setFont(
        "Helvetica-Bold",
        10
    )

    pdf.drawString(
        2 * cm,
        y,
        "Session"
    )

    pdf.drawString(
        5 * cm,
        y,
        "Movement"
    )

    pdf.drawString(
        9 * cm,
        y,
        "ROM"
    )

    pdf.drawString(
        12 * cm,
        y,
        "Reference"
    )

    pdf.drawString(
        16 * cm,
        y,
        "Difference"
    )

    y -= 0.5 * cm

    pdf.setFont(
        "Helvetica",
        10
    )

    for _, row in sessions.iterrows():

        movement = row["Movement"]

        rom = row["ROM"]

        reference = REFERENCE_ROM[joint][movement]

        difference = rom - reference

        pdf.drawString(
            2 * cm,
            y,
            str(row["Session"])
        )

        pdf.drawString(
            5 * cm,
            y,
            movement
        )

        pdf.drawString(
            9 * cm,
            y,
            f"{rom}°"
        )

        pdf.drawString(
            12 * cm,
            y,
            f"{reference}°"
        )

        pdf.drawString(
            16 * cm,
            y,
            f"{difference}°"
        )

        y -= 0.6 * cm

        if y < 2 * cm:

            pdf.showPage()

            y = height - 2 * cm

            pdf.setFont(
                "Helvetica",
                10
            )

    pdf.setFont(
        "Helvetica-Oblique",
        9
    )

    pdf.drawString(
        2 * cm,
        1.5 * cm,
        "PhysioCare - Educational Physiotherapy Assessment System"
    )

    pdf.save()

    buffer.seek(0)

    return buffer


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.title("🦵 PhysioCare")

    st.caption(
        "Physiotherapy Assessment System"
    )

    st.divider()

    page = st.radio(
        "Navigation",
        [
            "🏠 Dashboard",
            "👤 Patients",
            "🦵 Assessment",
            "📈 Progress",
            "🏋️ Exercises",
            "📄 Report"
        ]
    )

    st.divider()

    st.caption(
        "Educational Physiotherapy System"
    )

    st.caption(
        "© 2026 PhysioCare"
    )


# =========================================================
# DASHBOARD
# =========================================================

if page == "🏠 Dashboard":

    st.title("🏠 PhysioCare Dashboard")

    st.caption(
        "Overview of your physiotherapy assessment system"
    )

    conn = get_connection()

    patient_count = pd.read_sql_query(
        "SELECT COUNT(*) AS count FROM patients",
        conn
    ).iloc[0]["count"]

    joint_count = pd.read_sql_query(
        "SELECT COUNT(*) AS count FROM patient_joints",
        conn
    ).iloc[0]["count"]

    session_count = pd.read_sql_query(
        "SELECT COUNT(*) AS count FROM sessions",
        conn
    ).iloc[0]["count"]

    recent_sessions = pd.read_sql_query(
        """
        SELECT
            p.name AS Patient,
            pj.joint AS Joint,
            s.session_number AS Session,
            s.movement AS Movement,
            s.rom AS ROM,
            s.session_date AS Date

        FROM sessions s

        JOIN patients p
        ON s.patient_id = p.id

        JOIN patient_joints pj
        ON s.joint_id = pj.id

        ORDER BY s.id DESC

        LIMIT 5
        """,
        conn
    )

    conn.close()

    # Statistics
    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "👤 Total Patients",
            patient_count
        )

    with col2:

        st.metric(
            "🦵 Registered Joints",
            joint_count
        )

    with col3:

        st.metric(
            "📋 Total Sessions",
            session_count
        )

    st.divider()

    st.subheader(
        "Welcome to PhysioCare 👋"
    )

    st.write(
        """
        PhysioCare is an educational physiotherapy
        assessment and progress tracking system.

        It allows you to register patients, add multiple
        joints, record Range of Motion, track progress,
        browse exercises, and generate patient reports.
        """
    )

    st.info(
        "This system is intended for educational and organizational purposes."
    )

    st.subheader(
        "🕐 Recent Sessions"
    )

    if recent_sessions.empty:

        st.info(
            "No assessment sessions have been recorded yet."
        )

    else:

        st.dataframe(
            recent_sessions,
            use_container_width=True,
            hide_index=True
        )


# =========================================================
# PATIENTS
# =========================================================

elif page == "👤 Patients":

    st.title("👤 Patients")

    st.caption(
        "Manage patients and their registered joints"
    )

    st.subheader(
        "➕ Add New Patient"
    )

    col1, col2 = st.columns(2)

    with col1:

        name = st.text_input(
            "Patient Name"
        )

        age = st.number_input(
            "Age",
            min_value=1,
            max_value=120,
            value=20
        )

    with col2:

        gender = st.selectbox(
            "Gender",
            [
                "Male",
                "Female"
            ]
        )

    if st.button(
        "➕ Add Patient",
        use_container_width=True
    ):

        if name.strip() == "":

            st.warning(
                "Please enter patient name."
            )

        else:

            conn = get_connection()

            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO patients
                (name, age, gender)
                VALUES (?, ?, ?)
                """,
                (
                    name.strip(),
                    age,
                    gender
                )
            )

            conn.commit()
            conn.close()

            st.success(
                "Patient added successfully!"
            )

    st.divider()

    st.subheader(
        "🦵 Add Joint to Patient"
    )

    patients = get_patients()

    if patients.empty:

        st.info(
            "Add a patient first."
        )

    else:

        patient_options = get_patient_options(
            patients
        )

        selected_patient = st.selectbox(
            "Select Patient",
            list(patient_options.keys()),
            key="joint_patient"
        )

        patient_id = patient_options[
            selected_patient
        ]

        joint = st.selectbox(
            "Select Joint",
            list(REFERENCE_ROM.keys()),
            key="add_joint"
        )

        if st.button(
            "➕ Add Joint",
            use_container_width=True
        ):

            conn = get_connection()

            cursor = conn.cursor()

            try:

                cursor.execute(
                    """
                    INSERT INTO patient_joints
                    (patient_id, joint)
                    VALUES (?, ?)
                    """,
                    (
                        patient_id,
                        joint
                    )
                )

                conn.commit()

                st.success(
                    f"{joint} added successfully."
                )

            except sqlite3.IntegrityError:

                st.warning(
                    "This patient already has this joint."
                )

            conn.close()

    st.divider()

    st.subheader(
        "📋 Registered Patients"
    )

    conn = get_connection()

    patient_list = pd.read_sql_query(
        """
        SELECT
            p.id AS ID,
            p.name AS Name,
            p.age AS Age,
            p.gender AS Gender,
            GROUP_CONCAT(pj.joint, ', ') AS Joints

        FROM patients p

        LEFT JOIN patient_joints pj
        ON p.id = pj.patient_id

        GROUP BY p.id

        ORDER BY p.name
        """,
        conn
    )

    conn.close()

    if patient_list.empty:

        st.info(
            "No patients registered yet."
        )

    else:

        patient_list["Joints"] = patient_list[
            "Joints"
        ].fillna("No joint added")

        st.dataframe(
            patient_list,
            use_container_width=True,
            hide_index=True
        )


# =========================================================
# ASSESSMENT
# =========================================================

elif page == "🦵 Assessment":

    st.title("🦵 ROM Assessment")

    st.caption(
        "Record and calculate patient Range of Motion"
    )

    patients = get_patients()

    if patients.empty:

        st.warning(
            "Please add a patient first."
        )

    else:

        patient_options = get_patient_options(
            patients
        )

        selected_patient = st.selectbox(
            "👤 Select Patient",
            list(patient_options.keys()),
            key="assessment_patient"
        )

        patient_id = patient_options[
            selected_patient
        ]

        patient_joints = get_patient_joints(
            patient_id
        )

        if patient_joints.empty:

            st.warning(
                "This patient has no registered joints. "
                "Go to Patients → Add Joint to Patient."
            )

        else:

            joint_options = {
                row["joint"]: row["id"]
                for _, row in patient_joints.iterrows()
            }

            joint = st.selectbox(
                "🦵 Select Joint",
                list(joint_options.keys()),
                key="assessment_joint"
            )

            joint_id = joint_options[joint]

            st.info(
                f"Patient: {selected_patient}   |   Joint: {joint}"
            )

            col1, col2 = st.columns(2)

            with col1:

                movement = st.selectbox(
                    "Movement",
                    list(
                        REFERENCE_ROM[joint].keys()
                    )
                )

            with col2:

                measured_rom = st.number_input(
                    "Measured ROM (degrees)",
                    min_value=0.0,
                    max_value=360.0,
                    value=0.0,
                    step=1.0
                )

            col1, col2 = st.columns(2)

            with col1:

                session_date = st.date_input(
                    "📅 Session Date",
                    value=date.today()
                )

            with col2:

                notes = st.text_input(
                    "📝 Notes",
                    placeholder="Example: Improved movement..."
                )

            reference = REFERENCE_ROM[
                joint
            ][movement]

            difference = (
                measured_rom - reference
            )

            st.subheader(
                "Assessment Result"
            )

            col1, col2, col3 = st.columns(3)

            with col1:

                st.metric(
                    "Reference ROM",
                    f"{reference}°"
                )

            with col2:

                st.metric(
                    "Patient ROM",
                    f"{measured_rom}°"
                )

            with col3:

                st.metric(
                    "Difference",
                    f"{difference}°"
                )

            if st.button(
                "💾 Save Assessment",
                use_container_width=True
            ):

                conn = get_connection()

                last_session = pd.read_sql_query(
                    """
                    SELECT MAX(session_number) AS max_session
                    FROM sessions
                    WHERE patient_id = ?
                    AND joint_id = ?
                    """,
                    conn,
                    params=(
                        patient_id,
                        joint_id
                    )
                )

                max_session = last_session.iloc[0][
                    "max_session"
                ]

                if pd.isna(max_session):

                    session_number = 1

                else:

                    session_number = (
                        int(max_session) + 1
                    )

                cursor = conn.cursor()

                cursor.execute(
                    """
                    INSERT INTO sessions
                    (
                        patient_id,
                        joint_id,
                        session_number,
                        movement,
                        rom,
                        session_date,
                        notes
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        patient_id,
                        joint_id,
                        session_number,
                        movement,
                        measured_rom,
                        str(session_date),
                        notes
                    )
                )

                conn.commit()
                conn.close()

                st.success(
                    f"Session {session_number} saved successfully!"
                )


# =========================================================
# PROGRESS
# =========================================================

elif page == "📈 Progress":

    st.title("📈 Patient Progress")

    st.caption(
        "Monitor Range of Motion changes across sessions"
    )

    patients = get_patients()

    if patients.empty:

        st.warning(
            "Please add a patient first."
        )

    else:

        patient_options = get_patient_options(
            patients
        )

        selected_patient = st.selectbox(
            "👤 Select Patient",
            list(patient_options.keys()),
            key="progress_patient"
        )

        patient_id = patient_options[
            selected_patient
        ]

        patient_joints = get_patient_joints(
            patient_id
        )

        if patient_joints.empty:

            st.info(
                "No joints registered for this patient."
            )

        else:

            joint_options = {
                row["joint"]: row["id"]
                for _, row in patient_joints.iterrows()
            }

            joint = st.selectbox(
                "🦵 Select Joint",
                list(joint_options.keys()),
                key="progress_joint"
            )

            joint_id = joint_options[joint]

            conn = get_connection()

            sessions = pd.read_sql_query(
                """
                SELECT
                    session_number AS Session,
                    session_date AS Date,
                    movement AS Movement,
                    rom AS ROM,
                    notes AS Notes

                FROM sessions

                WHERE patient_id = ?
                AND joint_id = ?

                ORDER BY session_number
                """,
                conn,
                params=(
                    patient_id,
                    joint_id
                )
            )

            conn.close()

            if sessions.empty:

                st.info(
                    "No sessions recorded for this joint."
                )

            else:

                st.subheader(
                    f"📋 Assessment History — {joint}"
                )

                st.dataframe(
                    sessions,
                    use_container_width=True,
                    hide_index=True
                )

                st.subheader(
                    f"📈 ROM Progress — {joint}"
                )

                chart_data = sessions[
                    ["Session", "ROM"]
                ].set_index(
                    "Session"
                )

                st.line_chart(
                    chart_data
                )


# =========================================================
# EXERCISES
# =========================================================

elif page == "🏋️ Exercises":

    st.title("🏋️ Exercise Library")

    st.caption(
        "Educational exercise references organized by joint"
    )

    joint = st.selectbox(
        "🦵 Select Joint",
        list(EXERCISES.keys())
    )

    st.divider()

    for exercise, description in EXERCISES[joint]:

        with st.container(border=True):

            st.subheader(
                f"🏋️ {exercise}"
            )

            st.write(
                description
            )

    st.info(
        "Exercise information is provided for educational purposes. "
        "Exercise selection should be confirmed by a qualified physiotherapist."
    )


# =========================================================
# REPORT
# =========================================================

elif page == "📄 Report":

    st.title("📄 Patient Report")

    st.caption(
        "Review assessment history and generate a patient report"
    )

    patients = get_patients()

    if patients.empty:

        st.warning(
            "Please add a patient first."
        )

    else:

        patient_options = get_patient_options(
            patients
        )

        selected_patient = st.selectbox(
            "👤 Select Patient",
            list(patient_options.keys()),
            key="report_patient"
        )

        patient_id = patient_options[
            selected_patient
        ]

        patient = patients[
            patients["id"] == patient_id
        ].iloc[0]

        patient_joints = get_patient_joints(
            patient_id
        )

        if patient_joints.empty:

            st.info(
                "This patient has no joints registered."
            )

        else:

            joint_options = {
                row["joint"]: row["id"]
                for _, row in patient_joints.iterrows()
            }

            joint = st.selectbox(
                "🦵 Select Joint for Report",
                list(joint_options.keys()),
                key="report_joint"
            )

            joint_id = joint_options[joint]

            # Patient Information
            st.subheader(
                "👤 Patient Information"
            )

            col1, col2, col3 = st.columns(3)

            with col1:

                st.metric(
                    "Patient",
                    patient["name"]
                )

            with col2:

                st.metric(
                    "Age",
                    patient["age"]
                )

            with col3:

                st.metric(
                    "Joint",
                    joint
                )

            st.divider()

            # Sessions
            conn = get_connection()

            sessions = pd.read_sql_query(
                """
                SELECT
                    session_number AS Session,
                    session_date AS Date,
                    movement AS Movement,
                    rom AS ROM,
                    notes AS Notes

                FROM sessions

                WHERE patient_id = ?
                AND joint_id = ?

                ORDER BY session_number
                """,
                conn,
                params=(
                    patient_id,
                    joint_id
                )
            )

            conn.close()

            st.subheader(
                "📋 Assessment History"
            )

            if sessions.empty:

                st.info(
                    "No assessment sessions recorded for this joint."
                )

            else:

                st.dataframe(
                    sessions,
                    use_container_width=True,
                    hide_index=True
                )

                st.subheader(
                    "📈 Progress"
                )

                chart_data = sessions[
                    ["Session", "ROM"]
                ].set_index(
                    "Session"
                )

                st.line_chart(
                    chart_data
                )

                st.divider()

                st.subheader(
                    "📄 Generate Report"
                )

                st.write(
                    "Generate a downloadable PDF containing "
                    "the patient's assessment history."
                )

                pdf = generate_pdf(
                    patient,
                    joint,
                    sessions
                )

                st.download_button(
                    label="⬇️ Download Patient Report",
                    data=pdf,
                    file_name=(
                        f"{patient['name']}_{joint}_Report.pdf"
                    ),
                    mime="application/pdf",
                    use_container_width=True
                )
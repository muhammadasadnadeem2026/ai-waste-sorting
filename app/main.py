import streamlit as st
import cv2
import os
import pandas as pd
import plotly.express as px
from collections import Counter, defaultdict
from ultralytics import YOLO
import serial.tools.list_ports
import serial
from streamlit_option_menu import option_menu
from PIL import Image
import threading
import time
import base64
import streamlit.components.v1 as components


# Set page config
st.set_page_config(
    page_title="AI Waste Sorting System",
    page_icon="♻",
    layout="wide",
    initial_sidebar_state="expanded"
)

# # Audio handling
# def autoplay_audio(file_path: str):
#     with open(file_path, "rb") as f:
#         data = f.read()
#         b64 = base64.b64encode(data).decode()
#         md = f"""
#             <audio autoplay>
#             <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
#             </audio>
#             """
#         st.markdown(md, unsafe_allow_html=True)

# =============================================
# Sidebar Component
# =============================================
def render_sidebar():
    with st.sidebar:
        if os.path.exists("logo.png"): st.image("logo.png")
        st.markdown("""
        <style>
            .sidebar .sidebar-content {
                background-color: #2E3440;
                color:rgb(30, 78, 159);
            }
            .css-1d391kg { padding-top: 0rem; padding-bottom: 0rem; }
            .stButton>button {
                color: #ECEFF4; background-color: #4C566A;
                border-radius: 5px; border: 1px solid #4C566A;
                padding: 10px 24px;
                transition: all 0.3s ease;
            }
            .stButton>button:hover {
                background-color: #5E81AC; border: 1px solid #5E81AC;
                transform: scale(1.05);
            }
        </style>
        """, unsafe_allow_html=True)

        selected_option = option_menu(
            menu_title=None,
            options=["Sorting Class", "COM Info", "Dashboard", 
                    "Data Analysis", "Activity Alerts", "Settings"],
            icons=["sort-down", "usb-plug", "speedometer",
                  "graph-up", "bell", "gear"],
            default_index=0,
            orientation="vertical",
            styles={
                "container": {"padding": "0!important", "background-color": "#2E3440"},
                "icon": {"color": "#ECEFF4", "font-size": "18px"},
                "nav-link": {"font-size": "16px", "text-align": "left", 
                            "margin": "0px", "color": "#ECEFF4",
                            "transition": "all 0.3s ease"},
                "nav-link-selected": {"background-color": "#5E81AC", "transform": "scale(1.05)"},
            }
        )
    return selected_option

# =============================================
# Sorting Class Tab
# =============================================
def sorting_class():
    st.title("Sorting Class Configuration")
    
    class_options = ["All", "O_W", "Glass", "Metal", "Plastic", "Cardboard Paper"]
    
    if "selected_class" not in st.session_state:
        st.session_state.selected_class = "All"
    if "sorting_class_data" not in st.session_state:
        st.session_state.sorting_class_data = [
            {"name": "O_W", "type": "Organic Waste"},
            {"name": "Glass", "type": "Recyclable"},
            {"name": "Metal", "type": "Recyclable"},
            {"name": "Plastic", "type": "Recyclable"},
            {"name": "Cardboard Paper", "type": "Recyclable"},
        ]
    
    col1, col2 = st.columns([3, 1])
    with col1:
        new_selection = st.selectbox(
            "Select Class for Sorting:",
            class_options,
            index=class_options.index(st.session_state.selected_class)
        )
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔃 Refresh"):
            st.session_state.selected_class = "All"
            st.rerun()

    
    if new_selection != st.session_state.selected_class:
        st.session_state.selected_class = new_selection
        st.success(f"Sorting class updated to: {new_selection}")
    
    st.markdown("---")
    st.subheader("Current Sorting Configuration")
    st.write(f"Active Sorting Class: {st.session_state.selected_class}")
    
    if st.button("Confirm Sorting Class"):
        st.session_state.sorting_class_confirmation = True
        st.success(f"Sorting class {st.session_state.selected_class} selected successfully.")
    
    if "com_confirmation" in st.session_state and "sorting_class_confirmation" in st.session_state:
        if st.session_state.com_confirmation and st.session_state.sorting_class_confirmation:
            st.success("COM Info, Sorting Class, Data Analysis, and Dashboard are connected correctly!")
    
    st.markdown("---")
    st.subheader("Filtered Data")
    filtered_data = st.session_state.sorting_class_data if st.session_state.selected_class == "All" else [
        item for item in st.session_state.sorting_class_data if item["name"] == st.session_state.selected_class
    ]
    
    for item in filtered_data:
        st.write(f"Name: {item['name']} | Type: {item['type']}")

# =============================================
# COM Info Tab
# =============================================
def send_signal_to_com():
    try:
        com_port = st.session_state.get("selected_com")
        if com_port:
            ser = serial.Serial(com_port, 9600, timeout=1)
            ser.write(b"1")  # Send '1' as byte signal
            ser.close()
            st.success(f"Signal sent to {com_port} successfully!")
        else:
            st.error("No COM port selected. Please select a COM port.")
    except Exception as e:
        st.error(f"Failed to send signal: {str(e)}")

def get_com_ports():
    """Retrieve available COM ports."""
    ports = serial.tools.list_ports.comports()
    return [port.device for port in ports]

def com_info():
    st.title("COM Port Configuration")
    
    # Initialize session state for COM selection
    if "selected_com" not in st.session_state:
        st.session_state["selected_com"] = None
    
    # Retrieve available COM ports
    com_ports = get_com_ports()
    if not com_ports:
        st.error("No COM ports available. Please check your device connections.")
        return
    
    # Layout for COM port selection and refresh button
    col1, col2 = st.columns([3, 1])
    with col1:
        default_index = com_ports.index(st.session_state["selected_com"]) if st.session_state["selected_com"] in com_ports else 0
        selected_com = st.selectbox("Available COM Ports:", com_ports, index=default_index)
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Refresh Ports"):
            st.session_state["selected_com"] = None  # Reset selection
            st.rerun()

    
    st.session_state["selected_com"] = selected_com
    
    # Layout for Connect / Disconnect buttons
    col3, col4 = st.columns(2)
    with col3:
        if st.button("🔌 Connect COM Port"):
            try:
                st.session_state["ser"] = serial.Serial(selected_com, 9600, timeout=1)
                st.session_state["com_connected"] = True
                st.success(f"Successfully connected to {selected_com}")
                # autoplay_audio("connect.mp3")
                st.session_state["com_confirmation"] = True
            except Exception as e:
                st.error(f"Connection failed: {str(e)}")
    with col4:
        if st.button("🔒 Disconnect COM Port"):
            if "ser" in st.session_state and st.session_state.get("ser") is not None:
                try:
                    st.session_state["ser"].close()
                except Exception as e:
                    st.error(f"Error disconnecting: {str(e)}")
                del st.session_state["ser"]
                st.session_state["com_connected"] = False
                st.success("COM port disconnected")
                # autoplay_audio("disconnect.mp3")
                st.session_state["com_confirmation"] = False
    
    st.markdown("---")
    
    # Confirmation if both COM and Sorting Class are connected
    if ("com_confirmation" in st.session_state and 
        "sorting_class_confirmation" in st.session_state and 
        st.session_state["com_confirmation"] and st.session_state["sorting_class_confirmation"]):
        st.success("COM Info, Sorting Class, Data Analysis, and Dashboard are connected correctly!")
    
    # Additional Manual Control Section with Test Signal
    if st.session_state.get("com_connected"):
        st.markdown("---")
        st.subheader("Test Signal")
        if st.button("⚡ Send Test Signal"):
            try:
                st.session_state["ser"].write(b"1")
                st.success("Test signal sent successfully!")
            except Exception as e:
                st.error(f"Test signal failed: {str(e)}")
import streamlit as st
import os
import time
import cv2
import threading
import math
import pandas as pd
from ultralytics import YOLO

# ------------------------------
# Threaded Video Stream Class
# ------------------------------
class VideoStream:
    def __init__(self, src):
        self.cap = cv2.VideoCapture(src)
        self.frame = None
        self.stopped = False
        self.thread = threading.Thread(target=self.update, args=())
        self.thread.daemon = True

    def start(self):
        self.thread.start()
        return self

    def update(self):
        while not self.stopped:
            ret, frame = self.cap.read()
            if ret:
                self.frame = frame

    def read(self):
        return self.frame

    def stop(self):
        self.stopped = True
        self.thread.join()
        self.cap.release()

# =============================================
# Dashboard Tab
# =============================================
def dashboard():
    st.title("Dashboard")
    st.write("Welcome to the AI-Based Waste Sorting System Dashboard.")

    DESIRED_WIDTH = 800
    DESIRED_HEIGHT = 600

    session_defaults = {
        "detection_data": [],
        "model_path": None,
        "video_path": None,
        "detection_line_height": 300,
        "confidence_threshold": 0.5,
        "speedup_factor": 1,
        "video_state": "stopped",
        "current_frame": 0,
        "log_messages": [],
        "last_frame_time": time.time(),
        "track_history": defaultdict(lambda: {"last_position": None, "counted": False}),
    }

    for key, value in session_defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    def log_event(message):
        timestamp = time.strftime("%H:%M:%S")
        st.session_state.log_messages.append(f"[{timestamp}] {message}")
        st.session_state.log_messages = st.session_state.log_messages[-20:]

    if st.session_state.model_path:
        uploaded_model = st.session_state.model_path
    else:
        uploaded_model = st.file_uploader("Upload your YOLOv8 model (.pt)", type=["pt"])

    source_option = st.radio("Select Source", ("Video File", "Live Cam"))

    if source_option == "Video File":
        uploaded_video = st.file_uploader("Upload your video file", type=["mp4", "avi", "mov"])
        ip_url = None
    else:
        ip_url = st.text_input("Enter IP Camera URL", "http://10.75.46.15:4747/video")
        uploaded_video = None

    if uploaded_model and (uploaded_video or source_option == "Live Cam"):
        model_path = os.path.join("temp_model.pt")
        if hasattr(uploaded_model, "read"):
            with open(model_path, "wb") as f:
                f.write(uploaded_model.read())
        else:
            model_path = uploaded_model
        st.session_state.model_path = model_path

        if source_option == "Video File":
            video_path = os.path.join("temp_video.mp4")
            if hasattr(uploaded_video, "read"):
                with open(video_path, "wb") as f:
                    f.write(uploaded_video.read())
            else:

                video_path = uploaded_video
            st.session_state.video_path = video_path
            cap = cv2.VideoCapture(video_path)
        else:
            vs = VideoStream(ip_url).start()
            cap = vs

        cols = st.columns(3)
        if cols[0].button("Run"): st.session_state.video_state = "running"
        if cols[1].button("Pause"): st.session_state.video_state = "paused"
        if cols[2].button("Stop"): st.session_state.video_state = "stopped"; st.session_state.current_frame = 0

        main_cols = st.columns([1,1])
        with main_cols[1]:
            st.session_state.speedup_factor = st.slider("Video Speedup Factor", 1, 50, st.session_state.speedup_factor)
            st.session_state.detection_line_height = st.slider("Detection Line Height", 0, DESIRED_HEIGHT, st.session_state.detection_line_height)
            st.session_state.confidence_threshold = st.slider("Confidence Threshold", 0.0, 1.0, st.session_state.confidence_threshold, 0.01)

        with main_cols[0]:
            video_placeholder = st.empty()
        log_placeholder = st.empty()

        model = YOLO(model_path)

        while True:
            if st.session_state.video_state == "stopped": break
            if st.session_state.video_state == "running":
                if source_option == "Video File":
                    cap.set(cv2.CAP_PROP_POS_FRAMES, st.session_state.current_frame)
                    ret, frame = cap.read()
                    if not ret: break
                else:
                    frame = cap.read()
                    if frame is None:
                        time.sleep(0.1)
                        continue
                    frame = cv2.resize(frame, (DESIRED_WIDTH, DESIRED_HEIGHT))

                results = model.track(frame, persist=True, conf=st.session_state.confidence_threshold, verbose=False)
                track_ids = results[0].boxes.id.int().tolist() if results[0].boxes.id is not None else []
                current_positions = set()

                for box, track_id in zip(results[0].boxes, track_ids):
                    x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                    confidence = float(box.conf[0])
                    class_id = int(box.cls[0])
                    label = model.names[class_id]
                    center_y = (y1 + y2) // 2
                    current_positions.add(track_id)

                    prev_state = st.session_state.track_history[track_id]
                    current_position = "below" if center_y >= st.session_state.detection_line_height else "above"
                    
                    if current_position == "below" and not prev_state["counted"]:
                        st.session_state.detection_data.append({
                            "frame": st.session_state.current_frame,
                            "track_id": track_id,
                            "label": label,
                            "confidence": confidence,
                            "coordinates": (x1,y1,x2,y2)
                        })
                        
                        if st.session_state.get("com_connected") and st.session_state.get("ser"):
                            try:
                                signal_letter = label[0].upper()
                                st.session_state["ser"].write(signal_letter.encode())
                                log_event(f"Signal sent for ID {track_id}")
                            except Exception as e:
                                log_event(f"Signal error: {e}")
                        
                        prev_state["counted"] = True
                    
                    if current_position == "above" and prev_state["counted"]:
                        prev_state["counted"] = False

                    prev_state["last_position"] = current_position

                    cv2.rectangle(frame, (x1,y1), (x2,y2), (0,255,0), 2)
                    cv2.putText(frame, f"{label} {track_id} ({confidence:.2f})", (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 2)

                for track_id in list(st.session_state.track_history.keys()):
                    if track_id not in current_positions:
                        del st.session_state.track_history[track_id]

                cv2.line(frame, (0, st.session_state.detection_line_height), (DESIRED_WIDTH, st.session_state.detection_line_height), (255,0,0), 2)
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                video_placeholder.image(frame_rgb, channels="RGB")

                if source_option == "Video File":
                    st.session_state.current_frame += st.session_state.speedup_factor
            else:
                time.sleep(0.5)

        if source_option == "Live Cam": cap.stop()
        else: cap.release()
        st.success("Stream processing completed!")

        if st.session_state["detection_data"]:
            df = pd.DataFrame(st.session_state["detection_data"])
            csv_data = df.to_csv(index=False).encode("utf-8")
            st.download_button("Download Detection Data", data=csv_data, file_name="detection_data.csv", mime="text/csv")
    else:
        st.warning("Please upload a model and select a source to begin.")




# =============================================
# Data Analysis Tab
# =============================================
def data_analysis():
    st.title("Waste Sorting Analytics")
    st.write("Analyze detection trends and insights from the Dashboard.")

    # Check if detection data is available
    if "detection_data" not in st.session_state or not st.session_state["detection_data"]:
        st.warning("No detection data available. Please run the Dashboard to process a video first.")
        return

    # Convert detection data to a DataFrame
    detection_df = pd.DataFrame(st.session_state["detection_data"])

    # Filter data based on selected sorting class if applicable
    if "selected_class" in st.session_state and st.session_state["selected_class"] != "All":
        detection_df = detection_df[detection_df["label"] == st.session_state["selected_class"]]

    # Display raw detection data
    st.write("### Detection Data")
    st.dataframe(detection_df)

    # Statistics: Total detections, Most common waste, and Average confidence
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Detections", len(detection_df))
    with col2:
        if "label" in detection_df.columns and not detection_df["label"].empty:
            most_common = detection_df["label"].mode()[0]
            st.metric("Most Common Waste", most_common)
        else:
            st.metric("Most Common Waste", "N/A")
    with col3:
        if "confidence" in detection_df.columns and not detection_df["confidence"].empty:
            avg_conf = detection_df["confidence"].mean()
            st.metric("Avg Confidence", f"{avg_conf:.2%}")
        else:
            st.metric("Avg Confidence", "N/A")

    # Main charts: Waste Distribution (Pie Chart) and Confidence Distribution (Box Plot)
    col4, col5 = st.columns(2)
    with col4:
        st.subheader("Waste Distribution")
        if "label" in detection_df.columns:
            pie_fig = px.pie(detection_df, names='label', hole=0.3, title="Waste Distribution")
            st.plotly_chart(pie_fig, use_container_width=True)
        else:
            st.info("Label data not available for pie chart.")
    with col5:
        st.subheader("Confidence Distribution")
        if "confidence" in detection_df.columns and "label" in detection_df.columns:
            box_fig = px.box(detection_df, x='label', y='confidence', title="Confidence Distribution")
            st.plotly_chart(box_fig, use_container_width=True)
        else:
            st.info("Confidence data not available for box plot.")

    # Additional Bar Chart: Object Detection Counts
    st.write("### Object Detection Counts")
    if "label" in detection_df.columns:
        object_counts = detection_df["label"].value_counts().reset_index()
        object_counts.columns = ["Object", "Count"]
        bar_chart = px.bar(
            object_counts,
            x="Object",
            y="Count",
            title="Total Object Detection Counts",
            labels={"Object": "Detected Object", "Count": "Count"},
            color="Object"
        )
        st.plotly_chart(bar_chart, use_container_width=True)
    else:
        st.info("Label data not available for object counts.")

    # Time Series Analysis using timestamp if available
    if "timestamp" in detection_df.columns:
        st.subheader("Detection Timeline (Time Series Analysis)")
        try:
            detection_df['time'] = pd.to_datetime(detection_df['timestamp'], unit='s', errors='coerce')
            time_df = detection_df.groupby([pd.Grouper(key='time', freq='5min'), 'label']).size().reset_index(name='count')
            time_fig = px.line(time_df, x='time', y='count', color='label', title="Detection Timeline")
            st.plotly_chart(time_fig, use_container_width=True)
        except Exception as e:
            st.error(f"Error processing time series data: {e}")
    else:
        st.info("Timestamp data not available for time series analysis.")

    # Time-of-Day Analysis using frame count if available (assuming ~30 FPS)
    if "frame" in detection_df.columns:
        st.subheader("Time-of-Day Detection Trends")
        detection_df["hour"] = (detection_df["frame"] // 30).astype(int)
        
        # Detection trends by hour per object
        hourly_data = detection_df.groupby(["hour", "label"]).size().reset_index(name="Count")
        line_chart = px.line(
            hourly_data,
            x="hour",
            y="Count",
            color="label",
            title="Detection Trends by Hour",
            labels={"hour": "Hour (Approx.)", "Count": "Detection Count", "label": "Object"}
        )
        st.plotly_chart(line_chart, use_container_width=True)
        
        # Overall detection trends by hour
        combined_hourly_data = detection_df.groupby("hour").size().reset_index(name="Count")
        combined_chart = px.line(
            combined_hourly_data,
            x="hour",
            y="Count",
            title="Overall Detection Trends by Hour",
            labels={"hour": "Hour (Approx.)", "Count": "Total Detections"}
        )
        st.plotly_chart(combined_chart, use_container_width=True)
    else:
        st.info("Frame data not available for time-of-day analysis.")

    # New Feature: Detection Confidence Histogram
    if "confidence" in detection_df.columns:
        st.subheader("Detection Confidence Histogram")
        hist_fig = px.histogram(
            detection_df,
            x="confidence",
            nbins=20,
            title="Confidence Score Distribution Histogram"
        )
        st.plotly_chart(hist_fig, use_container_width=True)

    # New Feature: Scatter Plot - Frame vs Confidence
    if "frame" in detection_df.columns and "confidence" in detection_df.columns:
        st.subheader("Frame vs Confidence Scatter Plot")
        scatter_fig = px.scatter(
            detection_df,
            x="frame",
            y="confidence",
            color="label",
            title="Frame vs Confidence",
            labels={"frame": "Frame Number", "confidence": "Confidence Score", "label": "Object"}
        )
        st.plotly_chart(scatter_fig, use_container_width=True)

    # New Feature: Top 5 Highest Confidence Detections
    st.subheader("Top 5 Highest Confidence Detections")
    if "confidence" in detection_df.columns:
        top_detections = detection_df.sort_values(by="confidence", ascending=False).head(5)
        st.dataframe(top_detections)
    else:
        st.info("Confidence data not available for top detections.")

# =============================================
# Activity Alerts Tab
# =============================================
def activity_alerts():
    st.title("System Alerts & Anomalies")
    
    # Check for detection data
    if "detection_data" not in st.session_state or not st.session_state["detection_data"]:
        st.warning("No activity data available")
        return

    # Convert detection data to a DataFrame
    df = pd.DataFrame(st.session_state["detection_data"])

    st.subheader("Anomaly Settings")
    # Allow user to adjust the anomaly (low-confidence) threshold
    anomaly_threshold = st.slider("Set anomaly confidence threshold", 0.0, 1.0, 0.4)

    # If detection data contains labels, let the user filter anomalies by waste type
    if "label" in df.columns:
        available_labels = df["label"].unique().tolist()
        selected_labels = st.multiselect("Filter anomalies by label", available_labels, default=available_labels)
    else:
        selected_labels = None

    # Filter anomalies based on the confidence threshold and selected labels
    anomalies = df[df["confidence"] < anomaly_threshold]
    if selected_labels:
        anomalies = anomalies[anomalies["label"].isin(selected_labels)]
    
    # Display summary metrics
    st.subheader("Summary")
    st.metric("Total Detections", len(df))
    st.metric("Anomaly Count", len(anomalies))
    
    # Show anomaly details if any exist
    if not anomalies.empty:
        st.error(f"⚠ Low-confidence detections ({len(anomalies)}) detected!")
        st.dataframe(anomalies)
    else:
        st.success("No anomalies detected in recent activity")
    
    # (Optional) Plot a time-series chart if frame data is available
    if "frame" in df.columns and not anomalies.empty:
        st.subheader("Anomaly Trend Over Frames")
        # Group anomalies by frame number and count them
        anomaly_trend = anomalies.groupby("frame").size().reset_index(name="count")
        # Display a line chart (you can also use Plotly or Altair for more customization)
        st.line_chart(anomaly_trend.set_index("frame"))
# =============================================
# Settings Tab
# =============================================
def settings():
    st.title("System Configuration")
    
    with st.form("settings_form"):
        st.subheader("Visual Settings")
        theme = st.selectbox("Interface Theme", ["Dark", "Light", "High Contrast"])
        anim = st.checkbox("Enable Animations", True)
        
        st.subheader("Detection Parameters")
        default_conf = st.slider("Default Confidence Threshold", 0.0, 1.0, 0.6)
        max_fps = st.slider("Maximum Processing FPS", 1, 30, 24)
        
        if st.form_submit_button("💾 Save Settings"):
            st.session_state.theme = theme
            st.session_state.animations = anim
            st.session_state.conf_thresh = default_conf
            st.success("Settings saved successfully!")

# =============================================
# Main App
# =============================================
def main():
    # Display the welcome modal only once.
    if "welcome_shown" not in st.session_state:
        st.session_state.welcome_shown = True
        components.html(
            """
            <style>
                .welcome-modal {
                    position: fixed;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%);
                    background: #2E3440;
                    padding: 2rem;
                    border-radius: 15px;
                    color: white;
                    z-index: 1000;
                    box-shadow: 0 0 20px rgba(0,0,0,0.5);
                    text-align: center;
                }
            </style>
            <div class="welcome-modal" id="welcomeModal">
                <h1>🚀 Welcome to AI Waste Sorting System</h1>
                <h3>Smart Waste Management Solution by ZAMM</h3>
            </div>
            <script>
                // Hide the welcome modal after 3 seconds (3000 milliseconds)
                setTimeout(function(){
                    var modal = document.getElementById("welcomeModal");
                    if(modal) {
                        modal.style.display = 'none';
                    }
                }, 3000);
            </script>
            """,
            height=200,
        )
    selected_tab = render_sidebar()
    
    tab_mapping = {
        "Sorting Class": sorting_class,
        "COM Info": com_info,
        "Dashboard": dashboard,
        "Data Analysis": data_analysis,
        "Activity Alerts": activity_alerts,
        "Settings": settings
    }
    
    if selected_tab in tab_mapping:
        tab_mapping[selected_tab]()

if __name__ == "__main__":
    main()
import json
from pathlib import Path

import streamlit as st

# My Farm profile: retain values during the current Streamlit session.
if "farm_profile" not in st.session_state:
    st.session_state["farm_profile"] = {}
from datetime import date

st.set_page_config(
    page_title="DesertCrop Navigator",
    page_icon="🌾",
    layout="wide",
)

# DESERTCROP_THEME_CSS
st.markdown("""
<style>
<style>
/* DesertCrop Navigator — clean, agricultural dashboard */
.block-container {
    padding-top: 1.6rem;
    padding-bottom: 3rem;
    max-width: 1450px;
}
[data-testid="stSidebar"] {
    border-right: 1px solid rgba(120, 140, 120, 0.25);
}
div[data-testid="stMetric"] {
    background: rgba(100, 145, 90, 0.08);
    border: 1px solid rgba(100, 145, 90, 0.18);
    padding: 14px;
    border-radius: 12px;
}
div[data-testid="stExpander"] {
    border-radius: 10px;
}
div.stButton > button,
div.stDownloadButton > button {
    border-radius: 9px;
    min-height: 2.6rem;
}
</style>

</style>
""", unsafe_allow_html=True)


# Prototype crop options are grounded in broad Rajasthan agro-climatic-zone guidance.
# They are not field-specific recommendations and must be validated by local agronomists.

def show_crop_details(crop):
    """Display crop information and clearly identify missing data."""

    def show_value(label, value):
        if value is None or value == "" or value == []:
            st.write(f"**{label}:** Not yet documented")
        elif isinstance(value, dict):
            st.write(f"**{label}:**")
            for key, item in value.items():
                readable_key = key.replace("_", " ").capitalize()
                show_value(readable_key, item)
        elif isinstance(value, list):
            st.write(f"**{label}:** " + ", ".join(map(str, value)))
        else:
            st.write(f"**{label}:** {value}")

    st.markdown("#### Farming information")
    for key, label in [
        ("farming_systems", "Farming systems"),
        ("growing_seasons", "Growing seasons"),
        ("suitable_districts", "Suitable districts"),
        ("soil_requirements", "Soil requirements"),
        ("water_requirements", "Water requirements"),
        ("climate_requirements", "Climate requirements"),
        ("cultivation", "Cultivation guidance"),
        ("production", "Production information"),
        ("economics", "Economics"),
        ("crop_rotation", "Crop rotation"),
    ]:
        show_value(label, crop.get(key))

    evidence = crop.get("evidence") or {}
    st.markdown("#### Evidence and validation")
    show_value("Evidence confidence", evidence.get("confidence"))
    show_value("Last reviewed", evidence.get("last_reviewed"))
    show_value("Validation notes", evidence.get("validation_notes"))

    sources = evidence.get("sources") or []
    if sources:
        st.write("**Sources:**")
        for source in sources:
            title = source.get("title", "Unnamed source")
            url = source.get("url")
            organisation = source.get("organization", "")
            if url:
                st.markdown(f"- [{title}]({url}) — {organisation}")
            else:
                st.write(f"- {title} — {organisation}")
    else:
        st.info("No source references have been recorded for this crop.")


DISTRICT_CROPS = {
    "Jodhpur": {
        "zone": "Arid Western Plain / Transitional Plain of Luni Basin (district spans more than one zone)",
        "kharif": ["Pearl millet (bajra)", "Moth bean", "Sesame", "Cluster bean (guar)"],
        "rabi": ["Mustard", "Wheat (only where water and soil conditions support it)", "Cumin (requires careful local suitability checks)", "Gram"],
        "notes": "Jodhpur spans agro-climatic settings; local soil, rainfall and irrigation can change suitability substantially."
    },
    "Barmer": {
        "zone": "Arid Western Plain",
        "kharif": ["Pearl millet (bajra)", "Moth bean", "Sesame", "Cluster bean (guar)"],
        "rabi": ["Mustard", "Cumin (requires careful local suitability checks)", "Wheat (only where water and soil conditions support it)", "Gram"],
        "notes": "In the arid western plain, water availability and rainfall timing are key constraints. Do not assume irrigation is available."
    },
    "Sikar": {
        "zone": "Internal Drainage Dry Zone / north-eastern arid-semi-arid transition",
        "kharif": ["Pearl millet (bajra)", "Cluster bean (guar)", "Pulses (locally suitable types)"],
        "rabi": ["Mustard", "Gram", "Wheat (where irrigation and soil conditions support it)"],
        "notes": "Local conditions vary; confirm crop choice with the nearest Krishi Vigyan Kendra (KVK) or agriculture office."
    },
}

SEASON_LABELS = {"Kharif (monsoon)": "kharif", "Rabi (winter)": "rabi"}

st.title("🌾 DesertCrop Navigator")
st.caption("Field Shift • Evidence-informed crop planning for Rajasthan")
st.subheader("Rajasthan crop-planning assistant")
st.write(
    "A prototype for comparing locally plausible crop options, checking prerequisites, "
    "and planning a more resilient crop sequence using agricultural evidence and NASA Earth-observation context."
)

st.info(
    "Prototype notice: This version uses broad agro-climatic crop lists and transparent rules. "
    "It does not yet automatically retrieve live satellite, forecast, soil-test, groundwater or mandi data. "
    "Treat results as options to investigate—not a guaranteed crop prescription."
)

with st.sidebar:
    st.header("My Farm")
    st.caption("Enter what you know. Unknown details can be left at their default values.")

    st.markdown("#### Restore a saved farm profile")
    profile_file = st.file_uploader(
        "Upload your My Farm JSON file",
        type=["json"],
        key="profile_upload"
    )

    if st.button("Restore My Farm Profile", key="restore_farm_profile"):
        if profile_file is None:
            st.warning("Please upload a saved JSON profile first.")
        else:
            try:
                saved_profile = json.loads(profile_file.getvalue().decode("utf-8"))
                required_keys = [
                    "farm_name", "district", "farm_area", "area_unit",
                    "season_label", "water", "soil_test", "previous_crop",
                    "priority", "satellite_date", "ndvi_value", "ndvi_available"
                ]

                if not isinstance(saved_profile, dict) or any(
                    key not in saved_profile for key in required_keys
                ):
                    st.error("This file does not contain all required farm-profile fields.")
                else:
                    valid_options = {
                        "district": list(DISTRICT_CROPS.keys()),
                        "area_unit": ["Acres", "Hectares"],
                        "season_label": list(SEASON_LABELS.keys()),
                        "water": [
                            "Rainfed / rainfall-dependent",
                            "Limited irrigation",
                            "Reliable irrigation"
                        ],
                        "soil_test": ["No / not sure", "Yes"],
                        "previous_crop": [
                            "Not sure", "Pearl millet (bajra)", "Moth bean",
                            "Cluster bean (guar)", "Sesame", "Mustard",
                            "Wheat", "Gram", "Cumin", "Other"
                        ],
                        "priority": [
                            "Reduce water risk", "Improve soil and rotation",
                            "Balance risk and income",
                            "Explore market-oriented options"
                        ]
                    }

                    invalid = [
                        key for key, options in valid_options.items()
                        if saved_profile[key] not in options
                    ]

                    if invalid:
                        st.error("The profile contains unsupported choices: " + ", ".join(invalid))
                    else:
                        try:
                            area = float(saved_profile["farm_area"])
                            ndvi = float(saved_profile["ndvi_value"])
                            if area < 0 or not (-1 <= ndvi <= 1):
                                raise ValueError("Farm size or NDVI is outside the allowed range.")

                            from datetime import date
                            date_value = saved_profile["satellite_date"]
                            parsed_date = date.fromisoformat(date_value) if date_value else None

                            if not isinstance(saved_profile["farm_name"], str):
                                raise ValueError("Farm name must be text.")
                            if not isinstance(saved_profile["ndvi_available"], bool):
                                raise ValueError("NDVI availability must be true or false.")

                            restored_values = {
                                "farm_name": saved_profile["farm_name"],
                                "district": saved_profile["district"],
                                "farm_area": area,
                                "area_unit": saved_profile["area_unit"],
                                "season_label": saved_profile["season_label"],
                                "water": saved_profile["water"],
                                "soil_test": saved_profile["soil_test"],
                                "previous_crop": saved_profile["previous_crop"],
                                "priority": saved_profile["priority"],
                                "satellite_date": parsed_date,
                                "ndvi_value": ndvi,
                                "ndvi_available": saved_profile["ndvi_available"]
                            }

                            # Apply only after validation; the widgets below use these keys.
                            for key, value in restored_values.items():
                                st.session_state[key] = value

                            st.success("Farm profile restored.")
                            st.rerun()

                        except (ValueError, TypeError) as e:
                            st.error(f"Invalid farm-profile value: {e}")

            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                st.error(f"Could not read this JSON file: {e}")

    farm_name = st.text_input("Farm name (optional)", key="farm_name")
    district = st.selectbox("District", list(DISTRICT_CROPS.keys()), key="district")

    farm_area = st.number_input(
        "Farm size",
        min_value=0.0,
        value=0.0,
        step=0.5,
        help="Enter 0 if you prefer not to specify the size yet.",
        key="farm_area"
    )
    area_unit = st.selectbox("Area unit", ["Acres", "Hectares"], key="area_unit")

    season_label = st.selectbox("Season you are planning for", list(SEASON_LABELS.keys()))
    water = st.radio(
        "Water access",
        ["Rainfed / rainfall-dependent", "Limited irrigation", "Reliable irrigation"],
        help="Choose the situation for the field being planned."
    )
    soil_test = st.radio("Recent soil test available?", ["No / not sure", "Yes"], key="soil_test")
    previous_crop = st.selectbox(
        "Previous crop (if known)",
        ["Not sure", "Pearl millet (bajra)", "Moth bean", "Cluster bean (guar)",
         "Sesame", "Mustard", "Wheat", "Gram", "Cumin", "Other"],
        key="previous_crop"
    )
    priority = st.selectbox(
        "Main priority",
        ["Reduce water risk", "Improve soil and rotation", "Balance risk and income", "Explore market-oriented options"]
    )
    satellite_date = st.date_input("NASA satellite observation date (optional)", value=None, key="satellite_date")
    ndvi_value = st.number_input(
        "NDVI for the field/area (optional)",
        min_value=-1.0, max_value=1.0, value=0.0, step=0.01, format="%.2f",
        help="Enter only if you already calculated a valid, cloud-screened NDVI. Leave at 0 if unavailable.",
        key="ndvi_value"
    )
    ndvi_available = st.checkbox("I have a valid NDVI value to interpret", value=False, key="ndvi_available")

farm_profile_export = {
    "profile_version": 1,
    "farm_name": farm_name,
    "district": district,
    "farm_area": farm_area,
    "area_unit": area_unit,
    "season_label": season_label,
    "water": water,
    "soil_test": soil_test,
    "previous_crop": previous_crop,
    "priority": priority,
    "satellite_date": satellite_date.isoformat() if satellite_date else None,
    "ndvi_value": ndvi_value,
    "ndvi_available": ndvi_available
}

st.sidebar.download_button(
    label="Download My Farm Profile (.json)",
    data=json.dumps(farm_profile_export, indent=2, ensure_ascii=False),
    file_name="DesertCrop_Navigator_My_Farm_Profile.json",
    mime="application/json",
    key="download_farm_profile"
)

profile = DISTRICT_CROPS[district]
season_key = SEASON_LABELS[season_label]
candidates = list(profile[season_key])

# Conservative prototype rules: prioritize water-conservative options for rainfed conditions.
if water == "Rainfed / rainfall-dependent":
    if season_key == "kharif":
        candidates = [c for c in candidates if c in [
            "Pearl millet (bajra)", "Moth bean", "Sesame", "Cluster bean (guar)",
            "Pulses (locally suitable types)"
        ]]
    else:
        candidates = [c for c in candidates if c not in [
            "Wheat (only where water and soil conditions support it)",
            "Wheat (where irrigation and soil conditions support it)"
        ]]
elif water == "Limited irrigation":
    candidates = [c for c in candidates if not c.startswith("Wheat")]

st.header("Your preliminary crop-planning results")
left, right = st.columns([1.2, 1])

with left:
    st.markdown("### 1. Crop options to investigate")
    st.caption(f"Area: {district}, Rajasthan · Season: {season_label}")
    st.write(f"**Broad agro-climatic context:** {profile['zone']}")
    crop_reasons = {
        "bajra": (
            "Pearl millet is an important dryland crop. Check local rainfall timing, "
            "soil conditions and the recommended variety before sowing."
        ),
        "moth bean": (
            "Moth bean is a pulse grown in dry regions. Check the local sowing window, "
            "seed availability and risks from dry spells or pests."
        ),
        "sesame": (
            "Sesame may suit some warm-season settings, but establishment can be "
            "sensitive to rainfall and waterlogging. Confirm local suitability first."
        ),
        "guar": (
            "Cluster bean is an important crop in parts of arid Rajasthan. Check soil "
            "conditions, rainfall outlook, variety duration and local market access."
        ),
        "mustard": (
            "Mustard is a winter oilseed option in Rajasthan. Check sowing dates, "
            "temperature conditions, soil salinity and available soil moisture."
        ),
        "wheat": (
            "Wheat generally needs dependable moisture and suitable temperatures. "
            "Confirm irrigation availability, soil suitability and local recommendations."
        ),
        "cumin": (
            "Cumin needs careful local suitability checks, including drainage, soil "
            "conditions, disease risk and the locally recommended sowing window."
        ),
        "gram": (
            "Gram is a pulse crop. Check stored soil moisture, soil conditions, "
            "sowing timing and local disease-management advice."
        ),
        "pulses": (
            "Pulse suitability depends on the specific crop and variety. Confirm the "
            "locally recommended species, season, soil and rainfall requirements."
        ),
    }

    st.info(
        "These are options to investigate, not final prescriptions. The app has not "
        "yet checked your field's live weather, soil-test results, groundwater "
        "conditions or current official crop advisories."
    )

    for i, crop in enumerate(candidates, start=1):
        crop_lower = crop.lower()
        reason = next(
            (text for key, text in crop_reasons.items() if key in crop_lower),
            "Confirm this crop's local soil, water, seasonal and variety requirements "
            "with an agricultural expert before deciding."
        )

        with st.expander(f"{i}. {crop} — why consider it?"):
            st.write(reason)
            st.markdown("**Before choosing, check:**")
            st.markdown(
                "- Soil-test results and any salinity or drainage constraints.\n"
                "- Expected rainfall, sowing window and moisture availability.\n"
                "- Seed or variety availability and expected crop duration.\n"
                "- Local pest risks, costs, market access and farmer preferences."
            )

    st.caption(
        "The order is not a validated ranking. A crop should not be selected until "
        "its local suitability and the farmer's constraints have been checked."
    )

    st.markdown("### 2. Before sowing")
    checks = [
        "Check the latest local rainfall outlook and soil moisture; do not rely on historical averages alone.",
        "Use a recent soil test for pH, salinity/electrical conductivity, organic carbon and available nutrients where possible.",
        "Confirm seed/variety availability, sowing window and local pest/disease advice with the agriculture department or KVK.",
        "For irrigated crops, confirm sustainable water availability, water quality and the likely number of irrigations.",
        "Compare expected input costs, local procurement/market access and downside risk before choosing."
    ]
    if soil_test == "No / not sure":
        checks.insert(0, "Priority: arrange a soil test through a local soil-testing laboratory/KVK before final fertilizer decisions.")
    for item in checks:
        st.markdown(f"- {item}")

with right:
    st.markdown("### 3. Risk flags")
    if water == "Rainfed / rainfall-dependent":
        st.warning("Rainfall timing and dry spells are major decision factors. Prefer locally validated drought-tolerant options and keep a contingency plan.")
    elif water == "Limited irrigation":
        st.warning("Avoid assuming a water-intensive crop is viable. Check irrigation scheduling, groundwater trend and water quality.")
    else:
        st.info("Reliable irrigation helps but does not remove soil, salinity, groundwater sustainability or market risks.")

    if season_key == "rabi" and water != "Reliable irrigation":
        st.warning("Winter crop choice needs extra caution where stored soil moisture and irrigation are limited.")
    if previous_crop != "Not sure":
        st.write(f"**Previous crop entered:** {previous_crop}")
        if previous_crop in ["Moth bean", "Cluster bean (guar)", "Gram"]:
            st.write("A legume was selected. Rotation decisions should consider disease carryover, residue management and nutrient removal—not nitrogen fixation alone.")
        else:
            st.write("Check whether repeating the same crop could increase pest, disease or weed pressure, and compare a locally suitable rotation.")
    else:
        st.write("Previous crop is unknown; rotation advice will remain general until the crop history is added.")

    st.markdown("### 4. NASA satellite context")
    if ndvi_available:
        st.write(f"Entered NDVI: **{ndvi_value:.2f}**")
        if ndvi_value < 0.1:
            st.write("This value is low, but may reflect bare soil, sparse vegetation, water, cloud contamination or timing. Check image quality and season before interpreting.")
        elif ndvi_value < 0.35:
            st.write("This may indicate sparse to moderate greenness depending on crop, season, soil background and image quality.")
        else:
            st.write("This may indicate stronger vegetation greenness, but cannot identify a crop, prove soil fertility, or estimate yield by itself.")
        if satellite_date:
            st.caption(f"Observation date entered: {satellite_date.isoformat()}")
        st.caption("NDVI is context only; it is not used as a standalone crop-selection rule.")
    else:
        st.write("No NDVI value entered. That is fine for this first prototype.")
        st.caption("NASA HLS can provide harmonized Landsat/Sentinel observations at 30 m resolution. Cloud/shadow screening and multi-date comparison are required.")

st.divider()
st.header("A possible next-crop sequence")
if season_key == "kharif":
    next_season = "Rabi (winter)"
    next_options = profile["rabi"]
else:
    next_season = "Kharif (monsoon)"
    next_options = profile["kharif"]

if priority == "Reduce water risk":
    next_options = [c for c in next_options if "Wheat" not in c]
if water == "Rainfed / rainfall-dependent":
    next_options = [c for c in next_options if "Wheat" not in c]

st.write(f"After the current {season_label.lower()} crop, compare these options for **{next_season}**:")
st.write(" · ".join(next_options) if next_options else "No safe shortlist can be generated from the current limited rules; seek local agronomic advice.")
st.caption(
    "A rotation cannot be recommended from crop names alone. It must also account for the actual sowing/harvest dates, "
    "soil, water availability, variety duration, disease/weed history, residue and market constraints."
)

st.divider()
st.header("6. Explore the Crop Catalogue")
st.write(
    "Search crops by English or Hindi name. A catalogue entry alone "
    "does not confirm that a crop is suitable for your farm."
)

try:
    with open(str(Path(__file__).resolve().parent / "crop_knowledge.json"), "r", encoding="utf-8") as f:
        crop_db = json.load(f)

    combined = {}

    for item in crop_db.get("crop_catalogue", []):
        combined[item["crop_id"]] = {
            "crop_id": item["crop_id"],
            "name_en": item.get("name_en", item["crop_id"]),
            "name_hi": item.get("name_hi", ""),
            "category": item.get("category", "Uncategorised"),
            "has_detail": False,
            "confidence": "insufficient_evidence"
        }

    for item in crop_db.get("crops", []):
        crop_id = item["crop_id"]
        combined[crop_id] = {
            **item,
            "crop_id": crop_id,
            "name_en": item.get("crop_name_english", crop_id),
            "name_hi": item.get("crop_name_hindi", ""),
            "category": item.get("crop_category", "Uncategorised"),
            "has_detail": True,
            "confidence": item.get("evidence", {}).get(
                "confidence", "insufficient_evidence"
            )
        }

    crops = sorted(
        combined.values(),
        key=lambda item: item["name_en"].casefold()
    )

    search_text = st.text_input(
        "Search crop name (English or Hindi)",
        placeholder="Try cumin, जीरा, cotton or कपास"
    )

    categories = sorted({
        item["category"] for item in crops
    })

    category_filter = st.selectbox(
        "Crop category",
        ["All categories"] + categories
    )

    results = []
    for item in crops:
        searchable = " ".join([
            item["name_en"],
            item["name_hi"],
            item["crop_id"],
            item["category"]
        ]).casefold()

        search_match = search_text.strip().casefold() in searchable
        category_match = (
            category_filter == "All categories"
            or item["category"] == category_filter
        )

        if search_match and category_match:
            results.append(item)

    st.caption(f"{len(results)} crop(s) found.")

    if not results:
        st.info("No matching crop found in the current catalogue.")

    for item in results:
        display_name = item["name_en"]
        if item["name_hi"]:
            display_name += " (" + item["name_hi"] + ")"

        with st.expander(display_name):
            st.write("**Category:** " + item["category"])

            if item["has_detail"]:
                st.write("**Detailed record:** Available")
                st.write("**Evidence status:** " + item["confidence"])
                st.caption(
                    "Review the source information and local suitability "
                    "before relying on this record."
                )

                show_crop_details(item)

            else:
                st.write("**Detailed record:** Not yet available")
                st.info(
                    "This crop is listed for discovery, but the available "
                    "database does not yet support a reliable farm-specific "
                    "recommendation."
                )

except (OSError, json.JSONDecodeError, KeyError) as error:
    st.error("Unable to load the crop catalogue. Please check the database.")

st.header("What this prototype still needs")
st.markdown(
    "- Live NASA HLS observations and cloud-screened seasonal NDVI/NDMI summaries for a defined area.\n"
    "- Current IMD rainfall/forecast data and official crop calendars/advisories.\n"
    "- Soil-test and groundwater depth/quality data, with dates and spatial coverage shown.\n"
    "- Verified district crop statistics, local crop durations, economics and farmer/KVK validation.\n"
    "- Hindi-friendly farmer explanations and an option to save or print the farm plan."
)

st.caption("Data principle: Never treat missing data as zero. Satellite greenness does not directly measure soil nutrients, groundwater level or guaranteed crop yield.")


st.divider()
st.header("5. Download your preliminary farm plan")

report_lines = [
    "DESERTCROP NAVIGATOR",
    "Preliminary Farmer Crop-Planning Report",
    "=" * 42,
    f"District: {district}, Rajasthan",
    f"Season: {season_label}",
    f"Water availability: {water}",
    f"Soil test status: {soil_test}",
    f"Previous crop: {previous_crop}",
    f"Planning priority: {priority}",
    "",
    "CROP OPTIONS TO INVESTIGATE",
    "-" * 30,
]

report_lines.extend(f"{i}. {crop}" for i, crop in enumerate(candidates, 1))
report_lines.extend([
    "",
    "PRE-SOWING CHECKLIST",
    "-" * 30,
])
report_lines.extend(f"- {item}" for item in checks)

report_lines.extend([
    "",
    "POSSIBLE NEXT-CROP OPTIONS",
    "-" * 30,
    f"Next season: {next_season}",
    ", ".join(next_options) if next_options else
        "No shortlist available; seek local agronomic advice.",
    "",
    "NASA SATELLITE CONTEXT",
    "-" * 30,
    (
        f"Entered NDVI: {ndvi_value:.2f}"
        if ndvi_available else "No NDVI value entered."
    ),
    (
        f"Observation date: {satellite_date.isoformat()}"
        if ndvi_available and satellite_date else ""
    ),
    "",
    "IMPORTANT LIMITATIONS",
    "-" * 30,
    "This is a preliminary planning aid, not a final crop prescription.",
    "Crop options are not a scientifically validated ranking.",
    "Live weather, soil, groundwater and official advisories may not have been checked.",
    "Confirm suitability with the local agriculture department or KVK.",
])

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import cm
from io import BytesIO
from xml.sax.saxutils import escape

report_text = "\n".join(report_lines)

pdf_buffer = BytesIO()
pdf_doc = SimpleDocTemplate(
    pdf_buffer,
    pagesize=A4,
    rightMargin=1.8 * cm,
    leftMargin=1.8 * cm,
    topMargin=1.8 * cm,
    bottomMargin=1.8 * cm,
)

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(
    name="ReportTitle",
    parent=styles["Title"],
    textColor=colors.HexColor("#174A6E"),
    spaceAfter=12,
))
styles.add(ParagraphStyle(
    name="ReportBody",
    parent=styles["BodyText"],
    leading=14,
    spaceAfter=5,
))

story = []
for index, line in enumerate(report_lines):
    safe_line = escape(line)
    if index == 0:
        story.append(Paragraph(safe_line, styles["ReportTitle"]))
    elif line and set(line) == {"="}:
        story.append(Spacer(1, 4))
    elif line and set(line) == {"-"}:
        story.append(Spacer(1, 3))
    elif line in [
        "Preliminary Farmer Crop-Planning Report",
        "CROP OPTIONS TO INVESTIGATE",
        "PRE-SOWING CHECKLIST",
        "POSSIBLE NEXT-CROP OPTIONS",
        "NASA SATELLITE CONTEXT",
        "IMPORTANT LIMITATIONS",
    ]:
        story.append(Paragraph(f"<b>{safe_line}</b>", styles["Heading2"]))
    elif line:
        story.append(Paragraph(safe_line, styles["ReportBody"]))
    else:
        story.append(Spacer(1, 5))

pdf_doc.build(story)
pdf_bytes = pdf_buffer.getvalue()

st.download_button(
    label="Download farm plan (.txt)",
    data=report_text,
    file_name="DesertCrop_Navigator_Farm_Plan.txt",
    mime="text/plain",
)

hindi_report_lines = [
    "डेजर्टक्रॉप नेविगेटर",
    "किसान के लिए प्रारंभिक फसल-योजना",
    "=" * 35,
    f"जिला: {district}, राजस्थान",
    f"फसल का मौसम: {'खरीफ (मानसून)' if season_key == 'kharif' else 'रबी (सर्दी)'}",
    f"पानी की उपलब्धता: {water if str(water).strip() not in ("", "/", "-") else "जानकारी उपलब्ध नहीं"}",
    f"मिट्टी की जाँच: {soil_test if str(soil_test).strip() not in ("", "/", "-") else "जानकारी उपलब्ध नहीं"}",
    f"पिछली फसल: {previous_crop}",
    f"फसल चयन की प्राथमिकता: {priority}",
    "",
    "विचार के लिए फसल विकल्प:",
]
hindi_crop_names = {
    "Pearl millet (bajra)": "बाजरा",
    "Moth bean": "मोठ",
    "Sesame": "तिल",
    "Cluster bean (guar)": "ग्वार",
    "Mustard": "सरसों",
    "Cumin (requires careful local suitability checks)": "जीरा",
    "Gram": "चना",
    "Wheat": "गेहूँ",
}
hindi_report_lines.extend(
    f"{i}. {hindi_crop_names.get(crop, crop)}"
    for i, crop in enumerate(candidates, 1)
)
hindi_report_lines.extend([
    "",
    "बुवाई से पहले की जाँच-सूची:",
    "• मिट्टी की जाँच कराएँ और लवणता, पीएच तथा पोषक तत्वों की जानकारी लें।",
    "• स्थानीय वर्षा पूर्वानुमान, मिट्टी की नमी और बुवाई का सही समय जाँचें।",
    "• बीज की उपलब्धता तथा स्थानीय कृषि विभाग या कृषि विज्ञान केंद्र (KVK) की सलाह लें।",
    "• पानी की उपलब्धता, गुणवत्ता और सिंचाई की आवश्यकता की जाँच करें।",
    "• लागत, बाजार और फसल के जोखिम पर विचार करें।",
    "",
    "अगली फसल के संभावित विकल्प:",
    f"अगला मौसम: {'रबी (सर्दी)' if season_key == 'kharif' else 'खरीफ (मानसून)'}",
    ", ".join(hindi_crop_names.get(crop, crop) for crop in next_options),
    "",
    "महत्वपूर्ण सूचना:",
    "यह प्रारंभिक मार्गदर्शन है, अंतिम कृषि सलाह नहीं।",
    "फसल विकल्पों की वैज्ञानिक रूप से प्रमाणित रैंकिंग नहीं की गई है।",
    "वास्तविक मौसम, मिट्टी, भूजल और सरकारी सलाह की जाँच आवश्यक हो सकती है।",
    "फसल चुनने से पहले स्थानीय कृषि विभाग या KVK से पुष्टि करें।",
])

st.download_button(
    label="हिंदी में किसान रिपोर्ट डाउनलोड करें (.txt)",
    data="\n".join(hindi_report_lines),
    file_name="DesertCrop_Navigator_Kisan_Report_Hindi.txt",
    mime="text/plain",
)

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

hindi_font_path = str(pathlib.Path(__file__).resolve().parent / "fonts" / "NotoSansDevanagari-Regular.ttf")
hindi_bold_font_path = str(pathlib.Path(__file__).resolve().parent / "fonts" / "NotoSansDevanagari-Regular.ttf")

pdfmetrics.registerFont(TTFont("HindiFont", hindi_font_path))
pdfmetrics.registerFont(TTFont("HindiFont-Bold", hindi_bold_font_path))

hindi_pdf_buffer = BytesIO()
hindi_pdf_doc = SimpleDocTemplate(
    hindi_pdf_buffer,
    pagesize=A4,
    rightMargin=1.8 * cm,
    leftMargin=1.8 * cm,
    topMargin=1.8 * cm,
    bottomMargin=1.8 * cm,
)

hindi_styles = getSampleStyleSheet()
hindi_styles.add(ParagraphStyle(
    name="HindiTitle",
    parent=hindi_styles["Title"],
    fontName="HindiFont-Bold",
    fontSize=18,
    leading=25,
    spaceAfter=12,
))
hindi_styles.add(ParagraphStyle(
    name="HindiBody",
    parent=hindi_styles["BodyText"],
    fontName="HindiFont",
    fontSize=10,
    leading=17,
    spaceAfter=6,
))
hindi_styles.add(ParagraphStyle(
    name="HindiHeading",
    parent=hindi_styles["Heading2"],
    fontName="HindiFont-Bold",
    fontSize=12,
    leading=19,
    spaceBefore=8,
    spaceAfter=6,
))

hindi_story = []
hindi_headings = {
    "विचार के लिए फसल विकल्प:",
    "बुवाई से पहले की जाँच-सूची:",
    "अगली फसल के संभावित विकल्प:",
    "महत्वपूर्ण सूचना:",
}

for index, line in enumerate(hindi_report_lines):
    safe_line = escape(line)
    if index == 0:
        hindi_story.append(Paragraph(safe_line, hindi_styles["HindiTitle"]))
    elif line in hindi_headings:
        hindi_story.append(Paragraph(safe_line, hindi_styles["HindiHeading"]))
    elif line:
        hindi_story.append(Paragraph(safe_line, hindi_styles["HindiBody"]))
    else:
        hindi_story.append(Spacer(1, 5))

hindi_pdf_doc.build(hindi_story)
hindi_pdf_bytes = hindi_pdf_buffer.getvalue()

st.download_button(
    label="हिंदी किसान रिपोर्ट डाउनलोड करें (.pdf)",
    data=hindi_pdf_bytes,
    file_name="DesertCrop_Navigator_Kisan_Report_Hindi.pdf",
    mime="application/pdf",
)



st.download_button(
    label="Download farm plan (.pdf)",
    data=pdf_bytes,
    file_name="DesertCrop_Navigator_Farm_Plan.pdf",
    mime="application/pdf",
)



# DESERTCROP DETAILED CROP PROFILES
st.markdown("---")
st.header("Crop Details | फसल की जानकारी")
st.caption("General educational guidance. Local suitability should be confirmed with agricultural experts.")

import json as _dc_json
from pathlib import Path as _dc_Path

_dc_db_path = _dc_Path(__file__).resolve().parent / "crop_knowledge.json"
with _dc_db_path.open("r", encoding="utf-8") as _dc_file:
    _dc_data = _dc_json.load(_dc_file)

_dc_crops = _dc_data.get("crop_catalogue", [])
_dc_search = st.text_input(
    "Find a crop | फसल खोजें",
    key="desertcrop_profile_search"
).strip().casefold()

for _dc_crop in _dc_crops:
    _dc_name = _dc_crop.get("name_en", _dc_crop.get("crop_id", "Crop"))
    _dc_name_hi = _dc_crop.get("name_hi", "")
    _dc_category = _dc_crop.get("category", "Category not specified")
    _dc_profile = _dc_crop.get("profile", {})

    _dc_search_text = " ".join([
        str(_dc_name), str(_dc_name_hi),
        str(_dc_category), str(_dc_crop.get("crop_id", ""))
    ]).casefold()

    if _dc_search and _dc_search not in _dc_search_text:
        continue

    with st.expander(f"{_dc_name} | {_dc_name_hi} — {_dc_category}"):
        if not _dc_profile:
            st.info("Detailed profile is not yet available for this crop.")
            continue

        if _dc_profile.get("overview_en"):
            st.markdown("**Overview**")
            st.write(_dc_profile["overview_en"])
        if _dc_profile.get("overview_hi"):
            st.markdown("**परिचय**")
            st.write(_dc_profile["overview_hi"])
        if _dc_profile.get("season"):
            st.markdown("**Growing season / फसल का मौसम**")
            st.write(_dc_profile["season"])
        if _dc_profile.get("water_en"):
            st.markdown("**Water and irrigation**")
            st.write(_dc_profile["water_en"])
        if _dc_profile.get("water_hi"):
            st.markdown("**पानी और सिंचाई**")
            st.write(_dc_profile["water_hi"])

        st.caption(
            "This is general guidance, not a verified recommendation for a particular farm or district."
        )

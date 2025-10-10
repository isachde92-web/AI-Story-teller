# app.py
import streamlit as st
from openai import OpenAI
from fpdf import FPDF

st.set_page_config(page_title="Kids Story Generator", page_icon="📖", layout="centered")

st.title("📚 Children's Story Generator")
st.caption("Enter a character name and a theme, then generate a short, age-appropriate story using OpenAI.")

# --- Fetch API key from Streamlit secrets ---
api_key = st.secrets.get("OPENAI_API_KEY", None)

if not api_key:
    st.error("No OpenAI API key found in st.secrets. Please add it in your Streamlit secrets configuration.")
    st.stop()

# Create the new OpenAI client (v1)
client = OpenAI(api_key=api_key)

# --- Inputs ---
with st.form("story_form"):
    name = st.text_input("Main character's name", value="Luna")
    theme = st.text_input("Theme (e.g., friendship, space adventure, courage)", value="space adventure")
    age_group = st.slider("Target age (years)", min_value=3, max_value=12, value=6)
    tone = st.selectbox("Tone", ["Playful", "Calm", "Adventurous", "Rhyming", "Educational"], index=0)
    length = st.selectbox("Length", ["Very short (2-4 paragraphs)", "Short (6-8 paragraphs)", "Medium (10-12 paragraphs)"], index=1)
    include_moral = st.checkbox("Include a short moral / lesson", value=True)
    generate_button = st.form_submit_button("Generate story ✨")

# Helper: prepare prompt
def build_prompt(name, theme, age_group, tone, length, include_moral):
    length_map = {
        "Very short (2-4 paragraphs)": "very short (about 150-250 words)",
        "Short (6-8 paragraphs)": "short (about 350-500 words)",
        "Medium (10-12 paragraphs)": "medium length (about 600-900 words)",
    }
    prompt = (
        f"Write a {length_map.get(length)} children's story for a {age_group}-year-old child. "
        f"Main character's name: {name}. Theme: {theme}. Tone: {tone}. "
        "Use simple sentences, vivid but age-appropriate imagery, and friendly language. "
        "Include short paragraphs and dialog where appropriate. "
    )
    if include_moral:
        prompt += "At the end, include a single-sentence moral or friendly takeaway. "
    prompt += ("Do NOT include any adult content, frightening descriptions, or complex vocabulary. "
               "Keep sentences short and easy to read.")
    return prompt

# Generate story
if generate_button:
    if not api_key:
        st.error("Please add your API key in Streamlit secrets (st.secrets['OPENAI_API_KEY']).")
    elif not name.strip() or not theme.strip():
        st.error("Please enter both a character name and a theme.")
    else:
        with st.spinner("Generating story..."):
            prompt = build_prompt(name.strip(), theme.strip(), age_group, tone, length, include_moral)
            try:
                # New v1 usage:
                resp = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=1000,
                    temperature=0.8,
                )
                # in v1 the text lives at resp.choices[0].message.content
                story = resp.choices[0].message["content"].strip()
            except Exception as e:
                st.exception(e)
                story = None

        if story:
            st.subheader("Your story")
            st.markdown(story)

            # Download as .txt
            st.download_button(
                label="Download .txt",
                data=story,
                file_name=f"{name}_story.txt",
                mime="text/plain",
            )

            # Create PDF for download
            def story_to_pdf(title, text, filename):
                pdf = FPDF()
                pdf.add_page()
                pdf.set_auto_page_break(auto=True, margin=15)
                pdf.set_font("Arial", 'B', 16)
                pdf.cell(0, 10, title, ln=True)
                pdf.ln(4)
                pdf.set_font("Arial", size=12)
                for line in text.split('\n'):
                    if line.strip() == "":
                        pdf.ln(4)
                    else:
                        pdf.multi_cell(0, 8, line)
                pdf.output(filename)

            pdf_path = f"{name}_story.pdf"
            try:
                story_to_pdf(f"{name}'s Story", story, pdf_path)
                with open(pdf_path, "rb") as f:
                    pdf_bytes = f.read()
                st.download_button("Download PDF", data=pdf_bytes, file_name=pdf_path, mime="application/pdf")
            except Exception as e:
                st.warning("Could not create PDF: " + str(e))

            # Shortened 1-minute reading
            with st.expander("Create a 1-minute reading (shortened)"):
                try:
                    mini_prompt = f"Shorten the following story to a 1-minute read (about 150 words), preserving characters and moral:\n\n{story}"
                    mini_resp = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": mini_prompt}],
                        max_tokens=400,
                        temperature=0.7,
                    )
                    mini_story = mini_resp.choices[0].message["content"].strip()
                    st.write(mini_story)
                except Exception as e:
                    st.info("Could not create 1-minute version: " + str(e))

st.markdown("---")
st.caption("Made with ❤️ using Streamlit and OpenAI.")

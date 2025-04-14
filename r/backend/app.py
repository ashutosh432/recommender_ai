from flask import Flask, request, render_template
from deepface import DeepFace
import os
import uuid
from werkzeug.utils import secure_filename

# ✅ Tell Flask where to find the templates
TEMPLATE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
app = Flask(__name__, template_folder=TEMPLATE_DIR)

# Folder to temporarily store uploaded images
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        print("📥 Received a POST / request")

        if 'file' not in request.files or request.files['file'].filename == '':
            return render_template('index.html', error="⚠️ No file uploaded")

        file = request.files['file']
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"{uuid.uuid4()}_{filename}")
        file.save(filepath)

        print(f"🔍 Analyzing: {filepath}")

        try:
            result = DeepFace.analyze(
                img_path=filepath,
                actions=['gender', 'age', 'race'],
                enforce_detection=False
            )

            # Choose best face if multiple
            if isinstance(result, list):
                best_match = max(result, key=lambda x: x.get('gender', {}).get('Woman', 0))
                analysis = best_match
            else:
                analysis = result

            gender_scores = analysis.get('gender', {})
            male_score = gender_scores.get('Man', 0)
            female_score = gender_scores.get('Woman', 0)

            print(f"🎯 Gender confidence - Man: {male_score:.2f}%, Woman: {female_score:.2f}%")

            gender = "Woman" if female_score > male_score else "Man"
            race = analysis.get('dominant_race', 'Unknown')
            age = analysis.get('age', -1)

            print(f"✅ Analysis complete: Gender={gender}, Age={age}, Race={race}")

            # --- Style Suggestion Logic ---
            if gender.lower() == "man":
                beard_style = "goatee" if age < 35 else "full beard"
                eyewear = "Oakley Rectangle Frame" if age > 30 else "Ray-Ban Round"
                hairstyle = "classic slick back" if race.lower() == "indian" else "side fade"
            else:
                beard_style = "clean shave"
                eyewear = "Prada Oversized" if age > 25 else "Kate Spade Cat-Eye"
                hairstyle = "side-swept waves" if race.lower() == "indian" else "loose curls"

            os.remove(filepath)

            return render_template('index.html', result={
                "gender": gender,
                "age": age,
                "race": race,
                "beard_style": beard_style,
                "eyewear": eyewear,
                "hairstyle": hairstyle,
                "gender_confidence": {"Man": male_score, "Woman": female_score}
            })

        except Exception as e:
            print(f"❌ Error during analysis: {e}")
            if os.path.exists(filepath):
                os.remove(filepath)
            return render_template('index.html', error=f"Error processing image: {e}")

    return render_template('index.html')


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

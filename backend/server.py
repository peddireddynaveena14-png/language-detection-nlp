
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

import joblib
import os
import time
import html
import requests
from io import BytesIO

from pypdf import PdfReader
from docx import Document

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4


# =========================================================
# PATHS
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

FRONTEND_DIR = os.path.join(
    BASE_DIR,
    "frontend"
)


# =========================================================
# FLASK APP
# =========================================================

app = Flask(
    __name__,
    static_folder=FRONTEND_DIR,
    static_url_path=""
)

CORS(app)


# =========================================================
# MODEL PATHS
# =========================================================

MODEL_PATH = os.path.join(
    BASE_DIR,
    "model.pkl"
)

VECTORIZER_PATH = os.path.join(
    BASE_DIR,
    "vectorizer.pkl"
)


# =========================================================
# LOAD MODEL
# =========================================================

print("======================================")
print("Loading language detection model...")
print("======================================")

model = joblib.load(
    MODEL_PATH
)

vectorizer = joblib.load(
    VECTORIZER_PATH
)

print("MODEL LOADED SUCCESSFULLY")


# =========================================================
# LANGUAGE CODES
# =========================================================

LANGUAGE_CODES = {

    "English": "en",
    "Hindi": "hi",
    "Telugu": "te",
    "Tamil": "ta",
    "Kannada": "kn",
    "Malayalam": "ml",

    "Spanish": "es",
    "French": "fr",
    "German": "de",
    "Portuguese": "pt",
    "Italian": "it",
    "Russian": "ru",
    "Dutch": "nl",

    "Arabic": "ar",
    "Turkish": "tr",
    "Danish": "da",
    "Greek": "el",
    "Swedish": "sv"
}


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    return app.send_static_file(
        "index.html"
    )


# =========================================================
# HEALTH
# =========================================================

@app.route("/health")
def health():

    return jsonify({

        "success": True,

        "status": "healthy",

        "message":
            "Language Detection Application is running"

    })


# =========================================================
# TEXT LANGUAGE DETECTION
# =========================================================

@app.route(
    "/predict",
    methods=["POST"]
)
def predict():

    try:

        data = request.get_json()

        if not data:

            return jsonify({

                "success": False,

                "message":
                    "No JSON data received."

            }), 400


        text = data.get(
            "text",
            ""
        ).strip()


        if not text:

            return jsonify({

                "success": False,

                "message":
                    "Please enter text."

            }), 400


        features = vectorizer.transform(
            [text]
        )


        prediction = model.predict(
            features
        )[0]


        if hasattr(
            model,
            "predict_proba"
        ):

            probabilities = (
                model.predict_proba(
                    features
                )[0]
            )

            confidence = (
                max(probabilities) * 100
            )

        else:

            confidence = 0


        return jsonify({

            "success": True,

            "language":
                str(prediction),

            "confidence":
                round(
                    confidence,
                    2
                ),

            "text":
                text

        })


    except Exception as error:

        print(
            "Prediction error:",
            repr(error)
        )

        return jsonify({

            "success": False,

            "message":
                str(error)

        }), 500


# =========================================================
# FILE TEXT EXTRACTION
# =========================================================

def extract_text_from_file(file):

    filename = (
        file.filename.lower()
    )


    # =====================================================
    # TXT
    # =====================================================

    if filename.endswith(".txt"):

        content = file.read()

        try:

            return content.decode(
                "utf-8"
            )

        except UnicodeDecodeError:

            return content.decode(
                "latin-1"
            )


    # =====================================================
    # PDF
    # =====================================================

    elif filename.endswith(".pdf"):

        reader = PdfReader(
            file
        )

        pages = []

        for page_number, page in enumerate(
            reader.pages,
            start=1
        ):

            try:

                page_text = (
                    page.extract_text()
                )

                if page_text:

                    pages.append(
                        page_text
                    )

            except Exception as error:

                print(
                    f"PDF page {page_number} "
                    f"reading error:",
                    repr(error)
                )


        return "\n".join(
            pages
        )


    # =====================================================
    # DOCX
    # =====================================================

    elif filename.endswith(".docx"):

        document = Document(
            file
        )

        paragraphs = []


        # Normal paragraphs
        for paragraph in (
            document.paragraphs
        ):

            text = (
                paragraph.text.strip()
            )

            if text:

                paragraphs.append(
                    text
                )


        # Tables inside DOCX
        for table in document.tables:

            for row in table.rows:

                row_text = []

                for cell in row.cells:

                    cell_text = (
                        cell.text.strip()
                    )

                    if cell_text:

                        row_text.append(
                            cell_text
                        )


                if row_text:

                    paragraphs.append(
                        " | ".join(row_text)
                    )


        return "\n".join(
            paragraphs
        )


    # =====================================================
    # INVALID FILE
    # =====================================================

    else:

        raise ValueError(

            "Only PDF, DOCX and TXT "
            "files are supported."

        )


# =========================================================
# FILE UPLOAD + LANGUAGE DETECTION
# =========================================================

@app.route(
    "/upload",
    methods=["POST"]
)
def upload_file():

    try:

        if "file" not in request.files:

            return jsonify({

                "success": False,

                "message":
                    "No file uploaded."

            }), 400


        file = request.files[
            "file"
        ]


        if not file.filename:

            return jsonify({

                "success": False,

                "message":
                    "Please select a file."

            }), 400


        print("======================================")
        print("FILE UPLOAD")
        print("Filename:", file.filename)
        print("======================================")


        # Extract text
        extracted_text = (
            extract_text_from_file(
                file
            )
        )


        extracted_text = (
            extracted_text.strip()
        )


        if not extracted_text:

            return jsonify({

                "success": False,

                "message":
                    "No readable text found "
                    "in the file. "
                    "If this is a scanned/image PDF, "
                    "OCR is required."

            }), 400


        # Use first 10000 characters
        # for language detection
        detection_text = (
            extracted_text[:10000]
        )


        features = (
            vectorizer.transform(
                [detection_text]
            )
        )


        prediction = (
            model.predict(
                features
            )[0]
        )


        if hasattr(
            model,
            "predict_proba"
        ):

            probabilities = (
                model.predict_proba(
                    features
                )[0]
            )

            confidence = (
                max(probabilities)
                * 100
            )

        else:

            confidence = 0


        print(
            "Detected language:",
            prediction
        )

        print(
            "Confidence:",
            round(
                confidence,
                2
            )
        )


        return jsonify({

            "success": True,

            "filename":
                file.filename,

            "extracted_text":
                extracted_text,

            "language":
                str(prediction),

            "confidence":
                round(
                    confidence,
                    2
                )

        })


    except Exception as error:

        print(
            "File error:",
            repr(error)
        )

        return jsonify({

            "success": False,

            "message":
                str(error)

        }), 500


# =========================================================
# TEXT CHUNKING
# =========================================================

def split_text_into_chunks(
    text,
    max_chars=350
):

    # Preserve text
    text = text.strip()

    if not text:

        return []


    words = text.split()

    chunks = []

    current = ""


    for word in words:

        test = (
            current
            + " "
            + word
        ).strip()


        if len(test) <= max_chars:

            current = test

        else:

            if current:

                chunks.append(
                    current
                )

            current = word


    if current:

        chunks.append(
            current
        )


    return chunks


# =========================================================
# GOOGLE TRANSLATE
# =========================================================

def translate_with_google(
    text,
    source_code,
    target_code
):

    url = (
        "https://translate.googleapis.com/"
        "translate_a/single"
    )


    params = {

        "client": "gtx",

        "sl": source_code,

        "tl": target_code,

        "dt": "t",

        "q": text

    }


    headers = {

        "User-Agent":
            "Mozilla/5.0"

    }


    print(
        "Trying Google translation..."
    )


    response = requests.get(

        url,

        params=params,

        headers=headers,

        timeout=30

    )


    print(
        "Google HTTP status:",
        response.status_code
    )


    response.raise_for_status()


    data = response.json()


    translated_parts = []


    if isinstance(data, list):

        translation_data = data[0]

        if isinstance(
            translation_data,
            list
        ):

            for item in translation_data:

                if (
                    isinstance(item, list)
                    and len(item) > 0
                    and item[0]
                ):

                    translated_parts.append(
                        item[0]
                    )


    translated = "".join(
        translated_parts
    ).strip()


    translated = html.unescape(
        translated
    )


    if not translated:

        raise Exception(
            "Google returned empty translation."
        )


    return translated


# =========================================================
# MYMEMORY TRANSLATE
# =========================================================

def translate_with_mymemory(
    text,
    source_code,
    target_code
):

    url = (
        "https://api.mymemory.translated.net/get"
    )


    params = {

        "q":
            text,

        "langpair":
            f"{source_code}|{target_code}"

    }


    headers = {

        "User-Agent":
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "LanguageDetectionAI/1.0"

    }


    print(
        "Trying MyMemory translation..."
    )


    response = requests.get(

        url,

        params=params,

        headers=headers,

        timeout=30

    )


    print(
        "MyMemory HTTP status:",
        response.status_code
    )


    response.raise_for_status()


    data = response.json()


    translated = (

        data
        .get(
            "responseData",
            {}
        )
        .get(
            "translatedText",
            ""
        )
        .strip()

    )


    translated = html.unescape(
        translated
    )


    if not translated:

        details = data.get(

            "responseDetails",

            "MyMemory returned empty translation."

        )

        raise Exception(
            str(details)
        )


    return translated


# =========================================================
# TRANSLATION CHUNK
# =========================================================

def translate_chunk(
    text,
    source_code,
    target_code
):

    # Same language
    if source_code == target_code:

        return text


    print(
        "--------------------------------------"
    )

    print(
        "Translation chunk"
    )

    print(
        "Source:",
        source_code
    )

    print(
        "Target:",
        target_code
    )

    print(
        "Text:",
        text[:200]
    )


    # =====================================================
    # METHOD 1 - GOOGLE
    # =====================================================

    try:

        translated = (
            translate_with_google(
                text,
                source_code,
                target_code
            )
        )

        print(
            "Google translation SUCCESS"
        )

        return translated


    except Exception as google_error:

        print(
            "Google translation failed:",
            repr(google_error)
        )


    # =====================================================
    # METHOD 2 - MYMEMORY
    # =====================================================

    try:

        translated = (
            translate_with_mymemory(
                text,
                source_code,
                target_code
            )
        )

        print(
            "MyMemory translation SUCCESS"
        )

        return translated


    except Exception as memory_error:

        print(
            "MyMemory translation failed:",
            repr(memory_error)
        )


    # =====================================================
    # BOTH FAILED
    # =====================================================

    raise Exception(

        "Both translation services failed. "
        "Please try again after a few seconds."

    )


# =========================================================
# TRANSLATE TEXT
# =========================================================

@app.route(
    "/translate",
    methods=["POST"]
)
def translate():

    try:

        data = request.get_json()


        if not data:

            return jsonify({

                "success": False,

                "message":
                    "No JSON data received."

            }), 400


        text = data.get(
            "text",
            ""
        ).strip()


        source_language = data.get(

            "source_language",

            "English"

        )


        target_language = data.get(

            "target_language",

            "English"

        )


        if not text:

            return jsonify({

                "success": False,

                "message":
                    "Please provide text."

            }), 400


        # =================================================
        # LANGUAGE CODES
        # =================================================

        source_code = (
            LANGUAGE_CODES.get(
                source_language
            )
        )


        target_code = (
            LANGUAGE_CODES.get(
                target_language
            )
        )


        if not source_code:

            return jsonify({

                "success": False,

                "message":
                    "Unsupported source language: "
                    + str(source_language)

            }), 400


        if not target_code:

            return jsonify({

                "success": False,

                "message":
                    "Unsupported target language: "
                    + str(target_language)

            }), 400


        print("")
        print("======================================")
        print("TRANSLATION REQUEST")
        print("Source language:", source_language)
        print("Source code:", source_code)
        print("Target language:", target_language)
        print("Target code:", target_code)
        print("Text length:", len(text))
        print("======================================")


        # =================================================
        # SAME LANGUAGE
        # =================================================

        if source_code == target_code:

            translated_text = text

            total_chunks = 1


        else:

            # =================================================
            # SPLIT TEXT
            # =================================================

            chunks = (
                split_text_into_chunks(
                    text,
                    350
                )
            )


            if not chunks:

                return jsonify({

                    "success": False,

                    "message":
                        "Unable to create translation chunks."

                }), 400


            translated_chunks = []


            total_chunks = len(
                chunks
            )


            print(
                "Total chunks:",
                total_chunks
            )


            # =================================================
            # TRANSLATE EVERY CHUNK
            # =================================================

            for index, chunk in enumerate(

                chunks,

                start=1

            ):

                print(
                    f"Translating chunk "
                    f"{index}/{total_chunks}"
                )


                translated = (
                    translate_chunk(

                        chunk,

                        source_code,

                        target_code

                    )
                )


                translated_chunks.append(
                    translated
                )


                # Small delay
                # between API requests

                if index < total_chunks:

                    time.sleep(
                        0.8
                    )


            translated_text = (
                "\n\n".join(
                    translated_chunks
                )
            )


        print(
            "TRANSLATION SUCCESS"
        )


        return jsonify({

            "success": True,

            "original_text":
                text,

            "translated_text":
                translated_text,

            "source_language":
                source_language,

            "target_language":
                target_language,

            "chunks":
                total_chunks

        })


    except Exception as error:

        print("")
        print(
            "======================================"
        )

        print(
            "TRANSLATION ERROR"
        )

        print(
            repr(error)
        )

        print(
            "======================================"
        )


        return jsonify({

            "success": False,

            "message":
                str(error)

        }), 502


# =========================================================
# DOWNLOAD TRANSLATED FILE
# =========================================================

@app.route(
    "/download",
    methods=["POST"]
)
def download_document():

    try:

        data = request.get_json()


        if not data:

            return jsonify({

                "success": False,

                "message":
                    "No JSON data received."

            }), 400


        text = data.get(
            "text",
            ""
        ).strip()


        file_format = data.get(
            "format",
            "txt"
        ).lower()


        if not text:

            return jsonify({

                "success": False,

                "message":
                    "No translated text available."

            }), 400


        # =================================================
        # TXT
        # =================================================

        if file_format == "txt":

            output = BytesIO()


            output.write(
                text.encode(
                    "utf-8"
                )
            )


            output.seek(0)


            return send_file(

                output,

                as_attachment=True,

                download_name=
                    "translated_text.txt",

                mimetype=
                    "text/plain"

            )


        # =================================================
        # DOCX
        # =================================================

        elif file_format == "docx":

            document = Document()


            for paragraph in (
                text.split("\n")
            ):

                document.add_paragraph(
                    paragraph
                )


            output = BytesIO()


            document.save(
                output
            )


            output.seek(0)


            return send_file(

                output,

                as_attachment=True,

                download_name=
                    "translated_document.docx",

                mimetype=
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

            )


        # =================================================
        # PDF
        # =================================================

        elif file_format == "pdf":

            output = BytesIO()


            pdf = canvas.Canvas(

                output,

                pagesize=A4

            )


            width, height = A4


            left_margin = 45

            top_margin = (
                height - 50
            )

            y = top_margin

            line_height = 16


            # =================================================
            # PDF FONT
            # =================================================

            font_name = "Helvetica"


            try:

                from reportlab.pdfbase import pdfmetrics
                from reportlab.pdfbase.ttfonts import TTFont


                possible_fonts = [

                    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",

                    "/usr/share/fonts/dejavu/DejaVuSans.ttf",

                    "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"

                ]


                for font_path in possible_fonts:

                    if os.path.exists(
                        font_path
                    ):

                        pdfmetrics.registerFont(

                            TTFont(
                                "UnicodeFont",
                                font_path
                            )

                        )

                        font_name = "UnicodeFont"

                        break


            except Exception as font_error:

                print(
                    "Unicode font loading failed:",
                    repr(font_error)
                )


            pdf.setFont(
                font_name,
                10
            )


            # =================================================
            # WRITE TEXT
            # =================================================

            for paragraph in (
                text.split("\n")
            ):

                words = paragraph.split()

                line = ""


                for word in words:

                    test_line = (

                        line
                        + " "
                        + word

                    ).strip()


                    if len(test_line) > 85:

                        pdf.drawString(

                            left_margin,

                            y,

                            line

                        )


                        y -= line_height

                        line = word


                        if y < 50:

                            pdf.showPage()

                            pdf.setFont(
                                font_name,
                                10
                            )

                            y = top_margin


                    else:

                        line = test_line


                if line:

                    pdf.drawString(

                        left_margin,

                        y,

                        line

                    )

                    y -= line_height


                y -= 8


                if y < 50:

                    pdf.showPage()

                    pdf.setFont(
                        font_name,
                        10
                    )

                    y = top_margin


            pdf.save()


            output.seek(0)


            return send_file(

                output,

                as_attachment=True,

                download_name=
                    "translated_document.pdf",

                mimetype=
                    "application/pdf"

            )


        # =================================================
        # INVALID FORMAT
        # =================================================

        else:

            return jsonify({

                "success": False,

                "message":
                    "Unsupported download format."

            }), 400


    except Exception as error:

        print(
            "Download error:",
            repr(error)
        )


        return jsonify({

            "success": False,

            "message":
                str(error)

        }), 500


# =========================================================
# ERROR HANDLERS
# =========================================================

@app.errorhandler(404)
def not_found(error):

    return jsonify({

        "success": False,

        "message":
            "Endpoint not found."

    }), 404


@app.errorhandler(413)
def file_too_large(error):

    return jsonify({

        "success": False,

        "message":
            "Uploaded file is too large."

    }), 413


# =========================================================
# RUN SERVER
# =========================================================

if __name__ == "__main__":

    print("")
    print("======================================")
    print(" LANGUAGE DETECTION FULL STACK APP")
    print("======================================")
    print("Frontend + Backend running together")
    print("======================================")
    print("Local URL:")
    print("http://127.0.0.1:5000")
    print("======================================")


    app.run(

        host="0.0.0.0",

        port=5000,

        debug=True

    )


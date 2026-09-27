
// =====================================================
// BACKEND URL
// =====================================================
// Frontend and backend are running from the SAME URL.
// So no separate backend URL is required.

const BACKEND_URL = "";


// =====================================================
// LANGUAGE DETECTION
// =====================================================

async function detectLanguage() {

    const text =
        document.getElementById("textInput").value.trim();

    const result =
        document.getElementById("language");

    const confidence =
        document.getElementById("confidence");

    const resultBox =
        document.getElementById("result");


    if (!text) {

        alert("Please enter some text.");

        return;
    }


    resultBox.classList.remove("hidden");

    result.innerText = "Detecting...";
    confidence.innerText = "Please wait...";


    try {

        const response =
            await fetch(
                `${BACKEND_URL}/predict`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        text: text
                    })
                }
            );


        if (!response.ok) {

            throw new Error(
                `Server error: ${response.status}`
            );
        }


        const data =
            await response.json();


        if (!data.success) {

            throw new Error(
                data.message ||
                "Detection failed."
            );
        }


        result.innerText =
            data.language;

        confidence.innerText =
            data.confidence + "%";


    } catch (error) {

        console.error(error);

        result.innerText =
            "Error";

        confidence.innerText =
            error.message;
    }
}


// =====================================================
// FILE UPLOAD + DETECTION + TRANSLATION
// =====================================================

async function uploadFile() {

    const fileInput =
        document.getElementById("fileInput");

    const file =
        fileInput.files[0];


    if (!file) {

        alert(
            "Please select a PDF, DOCX or TXT file."
        );

        return;
    }


    const fileResult =
        document.getElementById("fileResult");

    const fileName =
        document.getElementById("fileName");

    const fileLanguage =
        document.getElementById("fileLanguage");

    const fileConfidence =
        document.getElementById("fileConfidence");

    const resultBox =
        document.getElementById(
            "translationResult"
        );

    const translatedText =
        document.getElementById(
            "translatedText"
        );


    fileResult.classList.remove("hidden");


    fileName.innerText =
        file.name;

    fileLanguage.innerText =
        "Reading file...";

    fileConfidence.innerText =
        "Please wait...";


    try {

        // =================================================
        // STEP 1: UPLOAD FILE
        // =================================================

        const formData =
            new FormData();

        formData.append(
            "file",
            file
        );


        const uploadResponse =
            await fetch(
                `${BACKEND_URL}/upload`,
                {
                    method: "POST",
                    body: formData
                }
            );


        if (!uploadResponse.ok) {

            throw new Error(
                `Upload server error: ${uploadResponse.status}`
            );
        }


        const uploadData =
            await uploadResponse.json();


        if (!uploadData.success) {

            throw new Error(
                uploadData.message ||
                "File processing failed."
            );
        }


        // =================================================
        // STEP 2: SHOW DETECTED LANGUAGE
        // =================================================

        fileLanguage.innerText =
            uploadData.language;

        fileConfidence.innerText =
            uploadData.confidence + "%";


        // =================================================
        // STEP 3: GET EXTRACTED TEXT
        // =================================================

        const extractedText =
            uploadData.extracted_text;


        if (
            !extractedText ||
            extractedText.trim() === ""
        ) {

            throw new Error(
                "No readable text found in this file."
            );
        }


        // =================================================
        // STEP 4: GET TARGET LANGUAGE
        // =================================================

        const targetLanguage =
            document.getElementById(
                "targetLanguage"
            ).value;


        // =================================================
        // STEP 5: SHOW TRANSLATING
        // =================================================

        resultBox.classList.remove(
            "hidden"
        );

        translatedText.value =
            "Translating document...";


        // =================================================
        // STEP 6: TRANSLATE DOCUMENT
        // =================================================

        const translationResponse =
            await fetch(
                `${BACKEND_URL}/translate`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        text:
                            extractedText,

                        source_language:
                            uploadData.language,

                        target_language:
                            targetLanguage
                    })
                }
            );


        if (!translationResponse.ok) {

            throw new Error(
                `Translation server error: ${translationResponse.status}`
            );
        }


        const translationData =
            await translationResponse.json();


        if (!translationData.success) {

            throw new Error(
                translationData.message ||
                "Translation failed."
            );
        }


        // =================================================
        // STEP 7: DISPLAY TRANSLATION
        // =================================================

        translatedText.value =
            translationData.translated_text;


    } catch (error) {

        console.error(
            "Document translation error:",
            error
        );


        translatedText.value =
            "Translation failed: " +
            error.message;
    }
}


// =====================================================
// TEXT TRANSLATION
// =====================================================

async function translateText() {

    const text =
        document.getElementById(
            "textInput"
        ).value.trim();


    const targetLanguage =
        document.getElementById(
            "targetLanguage"
        ).value;


    const resultBox =
        document.getElementById(
            "translationResult"
        );


    const translatedText =
        document.getElementById(
            "translatedText"
        );


    if (!text) {

        alert(
            "Please enter text first."
        );

        return;
    }


    translatedText.value =
        "Translating...";


    resultBox.classList.remove(
        "hidden"
    );


    try {

        // =================================================
        // STEP 1: DETECT SOURCE LANGUAGE
        // =================================================

        const detectResponse =
            await fetch(
                `${BACKEND_URL}/predict`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        text: text
                    })
                }
            );


        if (!detectResponse.ok) {

            throw new Error(
                `Detection server error: ${detectResponse.status}`
            );
        }


        const detectData =
            await detectResponse.json();


        if (!detectData.success) {

            throw new Error(
                detectData.message ||
                "Language detection failed."
            );
        }


        const sourceLanguage =
            detectData.language;


        // =================================================
        // STEP 2: TRANSLATE
        // =================================================

        const response =
            await fetch(
                `${BACKEND_URL}/translate`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        text:
                            text,

                        source_language:
                            sourceLanguage,

                        target_language:
                            targetLanguage
                    })
                }
            );


        if (!response.ok) {

            throw new Error(
                `Translation server error: ${response.status}`
            );
        }


        const data =
            await response.json();


        if (!data.success) {

            throw new Error(
                data.message ||
                "Translation failed."
            );
        }


        // =================================================
        // STEP 3: DISPLAY RESULT
        // =================================================

        translatedText.value =
            data.translated_text;


    } catch (error) {

        console.error(error);

        translatedText.value =
            "Translation failed: " +
            error.message;
    }
}


// =====================================================
// DOWNLOAD TRANSLATION
// =====================================================

async function downloadTranslation() {

    const translatedText =
        document.getElementById(
            "translatedText"
        ).value.trim();


    if (!translatedText) {

        alert(
            "No translated text available."
        );

        return;
    }


    try {

        // =================================================
        // DOWNLOAD TXT FROM FLASK BACKEND
        // =================================================

        const response =
            await fetch(
                `${BACKEND_URL}/download`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        text:
                            translatedText,

                        format:
                            "txt"
                    })
                }
            );


        if (!response.ok) {

            throw new Error(
                `Download server error: ${response.status}`
            );
        }


        const blob =
            await response.blob();


        const url =
            window.URL.createObjectURL(
                blob
            );


        const link =
            document.createElement(
                "a"
            );


        link.href =
            url;


        link.download =
            "translated_text.txt";


        document.body.appendChild(
            link
        );


        link.click();


        document.body.removeChild(
            link
        );


        window.URL.revokeObjectURL(
            url
        );


    } catch (error) {

        console.error(
            "Download error:",
            error
        );


        alert(
            "Download failed: " +
            error.message
        );
    }
}


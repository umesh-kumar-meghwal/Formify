/* =========================================================
   FORMIFY - TRANSFORM PAGE
   File: transform.js

   Responsibilities:
   - Output selection
   - File handling
   - Validation
   - Profile menu
   - Generate button state
   - Generated output rendering
   - Copy / download / regenerate UI
   ========================================================= */


/* =========================================================
   DOM ELEMENTS
   ========================================================= */

const sourceText = document.getElementById("sourceText");
const sourceFile = document.getElementById("sourceFile");
const fileName = document.getElementById("fileName");

const sourceError = document.getElementById("sourceError");
const outputError = document.getElementById("outputError");
const generalError = document.getElementById("generalError");

const outputTypesContainer = document.getElementById("outputTypes");
const outputPills = document.querySelectorAll(".output-pill");
const selectedCount = document.getElementById("selectedCount");

const generateButton = document.getElementById("generateButton");

const generatedSection = document.getElementById("generatedSection");
const generatedOutputs = document.getElementById("generatedOutputs");

const additionalInstructions =
  document.getElementById("additionalInstructions");

const audience = document.getElementById("audience");
const tone = document.getElementById("tone");
const language = document.getElementById("language");
const detailLevel = document.getElementById("detailLevel");
const objective = document.getElementById("objective");
const style = document.getElementById("style");

const profileButton = document.getElementById("profileButton");
const profileMenu = document.getElementById("profileMenu");


/* =========================================================
   CONFIGURATION
   ========================================================= */

const CONFIG = {
  maxFileSizeMB: 25,

  allowedExtensions: [
    ".pdf",
    ".doc",
    ".docx",
    ".txt",
    ".md",
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".gif"
  ]
};


/* =========================================================
   STATE
   ========================================================= */

let selectedOutputs = new Set();

let isGenerating = false;


/* =========================================================
   OUTPUT SELECTION
   ========================================================= */

outputPills.forEach((pill) => {

  pill.addEventListener("click", () => {

    const outputType = pill.dataset.output;

    if (!outputType) {
      return;
    }

    if (selectedOutputs.has(outputType)) {
      selectedOutputs.delete(outputType);
    } else {
      selectedOutputs.add(outputType);
    }

    updateOutputPillUI();
    updateSelectedCount();
    clearOutputError();

  });

});


function updateOutputPillUI() {

  outputPills.forEach((pill) => {

    const outputType = pill.dataset.output;

    const isSelected = selectedOutputs.has(outputType);

    pill.setAttribute(
      "aria-pressed",
      String(isSelected)
    );

    if (isSelected) {

      pill.classList.remove(
        "border-[#D0D5DD]",
        "bg-white",
        "text-[#344054]"
      );

      pill.classList.add(
        "border-[#4F46E5]",
        "bg-[#4F46E5]",
        "text-white"
      );

    } else {

      pill.classList.remove(
        "border-[#4F46E5]",
        "bg-[#4F46E5]",
        "text-white"
      );

      pill.classList.add(
        "border-[#D0D5DD]",
        "bg-white",
        "text-[#344054]"
      );

    }

  });

}


function updateSelectedCount() {

  const count = selectedOutputs.size;

  selectedCount.textContent =
    `${count} selected`;

}


/* =========================================================
   FILE HANDLING
   ========================================================= */

sourceFile.addEventListener("change", () => {

  clearSourceError();

  const file = sourceFile.files[0];

  if (!file) {

    fileName.textContent = "";
    fileName.classList.add("hidden");

    return;
  }

  const validationError = validateFile(file);

  if (validationError) {

    sourceFile.value = "";

    fileName.textContent = "";
    fileName.classList.add("hidden");

    showSourceError(validationError);

    return;
  }

  fileName.textContent =
    `Selected file: ${file.name}`;

  fileName.classList.remove("hidden");

});


function validateFile(file) {

  const fileNameLower = file.name.toLowerCase();

  const extension = "." + fileNameLower.split(".").pop();

  if (!CONFIG.allowedExtensions.includes(extension)) {

    return "This file type is not supported.";

  }

  const maxBytes =
    CONFIG.maxFileSizeMB * 1024 * 1024;

  if (file.size > maxBytes) {

    return `File size must be ${CONFIG.maxFileSizeMB} MB or less.`;

  }

  return null;

}


/* =========================================================
   SOURCE VALIDATION
   ========================================================= */

function hasSource() {

  const text =
    sourceText.value.trim();

  const hasText =
    text.length > 0;

  const hasFile =
    sourceFile.files &&
    sourceFile.files.length > 0;

  return hasText || hasFile;

}


function validateSource() {

  clearSourceError();

  const text =
    sourceText.value.trim();

  const hasText =
    text.length > 0;

  const hasFile =
    sourceFile.files &&
    sourceFile.files.length > 0;

  if (!hasText && !hasFile) {

    showSourceError(
      "Please paste source content or upload a source file."
    );

    return false;

  }

  if (hasFile) {

    const fileError =
      validateFile(sourceFile.files[0]);

    if (fileError) {

      showSourceError(fileError);

      return false;

    }

  }

  return true;

}


/* =========================================================
   OUTPUT VALIDATION
   ========================================================= */

function validateOutputs() {

  clearOutputError();

  if (selectedOutputs.size === 0) {

    showOutputError(
      "Please select at least one output type."
    );

    return false;

  }

  return true;

}


/* =========================================================
   COMPLETE FORM VALIDATION
   ========================================================= */

function validateForm() {

  const sourceValid =
    validateSource();

  const outputsValid =
    validateOutputs();

  if (!sourceValid) {
    return false;
  }

  if (!outputsValid) {
    return false;
  }

  return true;

}


/* =========================================================
   ERROR HELPERS
   ========================================================= */

function showSourceError(message) {

  sourceError.textContent = message;

  sourceError.classList.remove("hidden");

}


function clearSourceError() {

  sourceError.textContent = "";

  sourceError.classList.add("hidden");

}


function showOutputError(message) {

  outputError.textContent = message;

  outputError.classList.remove("hidden");

}


function clearOutputError() {

  outputError.textContent = "";

  outputError.classList.add("hidden");

}


function showGeneralError(message) {

  generalError.textContent = message;

  generalError.classList.remove("hidden");

}


function clearGeneralError() {

  generalError.textContent = "";

  generalError.classList.add("hidden");

}


/* =========================================================
   GENERATE BUTTON
   ========================================================= */

generateButton.addEventListener("click", async () => {

  clearGeneralError();

  if (isGenerating) {
    return;
  }

  const valid =
    validateForm();

  if (!valid) {
    return;
  }

  /*
   * IMPORTANT:
   * The actual fetch/AJAX request will be connected
   * from transform.html as planned.
   *
   * This function dispatches a custom event so the HTML
   * can collect the current Formify data and call the backend.
   */

  const requestData =
    collectFormData();

  setGeneratingState(true);

  try {

    const event =
      new CustomEvent(
        "formify:generate",
        {
          detail: requestData
        }
      );

    document.dispatchEvent(event);

  } catch (error) {

    console.error(
      "Generation error:",
      error
    );

    showGeneralError(
      "Something went wrong while preparing the request."
    );

    setGeneratingState(false);

  }

});


/* =========================================================
   COLLECT FORM DATA
   ========================================================= */

function collectFormData() {

  const file =
    sourceFile.files &&
    sourceFile.files.length > 0
      ? sourceFile.files[0]
      : null;

  return {

    sourceText:
      sourceText.value.trim(),

    file,

    outputTypes:
      Array.from(selectedOutputs),

    settings: {

      audience:
        audience.value,

      tone:
        tone.value,

      language:
        language.value,

      detailLevel:
        detailLevel.value,

      objective:
        objective.value,

      style:
        style.value

    },

    additionalInstructions:
      additionalInstructions.value.trim()

  };

}


/* =========================================================
   GENERATION STATE
   ========================================================= */

function setGeneratingState(generating) {

  isGenerating =
    generating;

  generateButton.disabled =
    generating;

  if (generating) {

    generateButton.textContent =
      "Generating...";

  } else {

    generateButton.textContent =
      "Generate outputs";

  }

}


/* =========================================================
   BACKEND RESPONSE HANDLER
   =========================================================
   
   The HTML AJAX code can call:

       handleGenerationResponse(data)

   after receiving the backend response.
   ========================================================= */

function handleGenerationResponse(data) {

  setGeneratingState(false);

  clearGeneralError();

  if (!data) {

    showGeneralError(
      "The server returned an empty response."
    );

    return;

  }


  if (data.error) {

    showGeneralError(
      data.error
    );

    return;

  }


  const outputs =
    normalizeOutputs(data);

  if (outputs.length === 0) {

    showGeneralError(
      "No generated outputs were returned."
    );

    return;

  }


  renderGeneratedOutputs(outputs);

}


/* =========================================================
   NORMALIZE BACKEND OUTPUT
   ========================================================= */

function normalizeOutputs(data) {

  /*
   * Expected response can eventually look like:

   {
     "outputs": [
       {
         "type": "executive-summary",
         "title": "Executive Summary",
         "content": "...",
         "grounded": true,
         "matchedFacts": 12,
         "unsupportedClaims": 0
       }
     ]
   }

   The function also accepts an object-based
   output structure for flexibility.
  */


  if (Array.isArray(data.outputs)) {

    return data.outputs;

  }


  if (
    data.outputs &&
    typeof data.outputs === "object"
  ) {

    return Object.entries(data.outputs)
      .map(([type, value]) => {

        if (typeof value === "string") {

          return {
            type,
            title: formatOutputTitle(type),
            content: value
          };

        }

        return {
          type,
          ...(value || {}),
          title:
            value?.title ||
            formatOutputTitle(type)
        };

      });

  }


  return [];

}


/* =========================================================
   RENDER GENERATED OUTPUTS
   ========================================================= */

function renderGeneratedOutputs(outputs) {

  generatedOutputs.innerHTML = "";

  const selectedOutputArray =
    Array.from(selectedOutputs);

  /*
   * Only render outputs that were selected.
   */

  const selectedResults =
    outputs.filter((output) => {

      return selectedOutputArray.includes(
        output.type
      );

    });


  if (selectedResults.length === 0) {

    generatedSection.classList.remove("hidden");

    generatedOutputs.innerHTML = `
      <div class="rounded-xl border border-[#FECACA] bg-[#FEF2F2] p-4 text-[13px] text-[#B42318]">
        The backend did not return any of the selected output types.
      </div>
    `;

    return;

  }


  selectedResults.forEach((output) => {

    const card =
      createOutputCard(output);

    generatedOutputs.appendChild(card);

  });


  generatedSection.classList.remove("hidden");

  generatedSection.scrollIntoView({
    behavior: "smooth",
    block: "start"
  });

}


/* =========================================================
   CREATE OUTPUT CARD
   ========================================================= */

function createOutputCard(output) {

  const card =
    document.createElement("article");

  card.className =
    "overflow-hidden rounded-2xl border border-[#E4E7EC] bg-white shadow-[0_2px_8px_rgba(16,24,40,0.03)]";


  const title =
    output.title ||
    formatOutputTitle(output.type);


  const content =
    output.content ||
    output.text ||
    "";


  card.innerHTML = `

    <div class="flex flex-col gap-3 border-b border-[#EAECF0] px-5 py-4 sm:flex-row sm:items-center sm:justify-between">

      <div>

        <h3 class="text-[15px] font-semibold text-[#172033]">
          ${escapeHTML(title)}
        </h3>

        <div class="mt-1 flex items-center gap-2 text-[11px] text-[#667085]">

          ${
            output.grounded
              ? `
                <span class="inline-flex items-center gap-1 font-medium text-[#027A48]">
                  <span>✓</span>
                  Source grounded
                </span>
              `
              : ""
          }

          ${
            typeof output.matchedFacts === "number"
              ? `
                <span>
                  ${output.matchedFacts} facts matched
                </span>
              `
              : ""
          }

          ${
            typeof output.unsupportedClaims === "number"
              ? `
                <span>
                  · ${output.unsupportedClaims} unsupported claims
                </span>
              `
              : ""
          }

        </div>

      </div>


      <div class="flex flex-wrap items-center gap-2">

        <button
          type="button"
          class="copy-output rounded-lg border border-[#D0D5DD] bg-white px-3 py-1.5 text-[12px] font-medium text-[#344054] transition hover:bg-[#F9FAFB]"
          data-action="copy">

          Copy

        </button>


        <button
          type="button"
          class="download-output rounded-lg border border-[#D0D5DD] bg-white px-3 py-1.5 text-[12px] font-medium text-[#344054] transition hover:bg-[#F9FAFB]"
          data-action="download">

          Download .md

        </button>


        <button
          type="button"
          class="regenerate-output rounded-lg border border-[#D0D5DD] bg-white px-3 py-1.5 text-[12px] font-medium text-[#344054] transition hover:bg-[#F9FAFB]"
          data-action="regenerate">

          Regenerate

        </button>

      </div>

    </div>


    <div class="px-5 py-5">

      <div
        class="output-content whitespace-pre-wrap text-[14px] leading-7 text-[#344054]">
        ${escapeHTML(content)}
      </div>

    </div>


    ${
      output.evidence
        ? `
          <details class="border-t border-[#EAECF0] px-5 py-4">

            <summary class="cursor-pointer text-[12px] font-semibold text-[#344054]">
              View evidence
            </summary>

            <div class="mt-3 rounded-lg bg-[#F9FAFB] p-3 text-[12px] leading-5 text-[#667085]">
              ${escapeHTML(output.evidence)}
            </div>

          </details>
        `
        : ""
    }

  `;


  /* Copy */

  const copyButton =
    card.querySelector(".copy-output");

  copyButton.addEventListener(
    "click",
    async () => {

      await copyText(
        content,
        copyButton
      );

    }
  );


  /* Download */

  const downloadButton =
    card.querySelector(".download-output");

  downloadButton.addEventListener(
    "click",
    () => {

      downloadMarkdown(
        title,
        content
      );

    }
  );


  /* Regenerate */

  const regenerateButton =
    card.querySelector(".regenerate-output");

  regenerateButton.addEventListener(
    "click",
    () => {

      regenerateOutput(
        output.type
      );

    }
  );


  return card;

}


/* =========================================================
   COPY OUTPUT
   ========================================================= */

async function copyText(text, button) {

  try {

    await navigator.clipboard.writeText(
      text
    );

    const originalText =
      button.textContent;

    button.textContent =
      "Copied";

    setTimeout(() => {

      button.textContent =
        originalText;

    }, 1500);

  } catch (error) {

    console.error(
      "Copy failed:",
      error
    );

    button.textContent =
      "Copy failed";

    setTimeout(() => {

      button.textContent =
        "Copy";

    }, 1500);

  }

}


/* =========================================================
   DOWNLOAD MARKDOWN
   ========================================================= */

function downloadMarkdown(title, content) {

  const markdown =
    `# ${title}\n\n${content}\n`;

  const blob =
    new Blob(
      [markdown],
      {
        type: "text/markdown;charset=utf-8"
      }
    );

  const url =
    URL.createObjectURL(blob);

  const link =
    document.createElement("a");

  link.href =
    url;

  link.download =
    `${slugify(title)}.md`;

  document.body.appendChild(link);

  link.click();

  link.remove();

  URL.revokeObjectURL(url);

}


/* =========================================================
   REGENERATE ONE OUTPUT
   ========================================================= */

function regenerateOutput(outputType) {

  if (!outputType) {
    return;
  }

  /*
   * Temporarily select only this output.
   *
   * The actual AJAX request will be triggered
   * through the same Formify generation flow.
   */

  const wasSelected =
    selectedOutputs.has(outputType);

  if (!wasSelected) {

    selectedOutputs.add(outputType);

    updateOutputPillUI();
    updateSelectedCount();

  }


  document.dispatchEvent(
    new CustomEvent(
      "formify:regenerate",
      {
        detail: {
          outputType,
          formData: collectFormData()
        }
      }
    )
  );

}


/* =========================================================
   PROFILE MENU
   ========================================================= */

if (profileButton && profileMenu) {

  profileButton.addEventListener(
    "click",
    (event) => {

      event.stopPropagation();

      const isHidden =
        profileMenu.classList.contains("hidden");

      if (isHidden) {

        profileMenu.classList.remove("hidden");

        profileButton.setAttribute(
          "aria-expanded",
          "true"
        );

      } else {

        profileMenu.classList.add("hidden");

        profileButton.setAttribute(
          "aria-expanded",
          "false"
        );

      }

    }
  );


  document.addEventListener(
    "click",
    (event) => {

      if (
        !profileMenu.contains(event.target) &&
        !profileButton.contains(event.target)
      ) {

        profileMenu.classList.add("hidden");

        profileButton.setAttribute(
          "aria-expanded",
          "false"
        );

      }

    }
  );

}


/* =========================================================
   UTILITY FUNCTIONS
   ========================================================= */

function formatOutputTitle(type) {

  if (!type) {
    return "Generated Output";
  }

  return type
    .replace(/[-_]/g, " ")
    .replace(/\b\w/g, (char) =>
      char.toUpperCase()
    );

}


function slugify(text) {

  return String(text)
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");

}


function escapeHTML(value) {

  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");

}


/* =========================================================
   INITIAL STATE
   ========================================================= */

updateOutputPillUI();

updateSelectedCount();
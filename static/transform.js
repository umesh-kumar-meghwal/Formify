const sourceText = document.getElementById("source_content_raw");
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



const CONFIG = {
  maxFileSizeMB: 25,
  allowedExtensions: [
    ".pdf", ".doc", ".docx", ".txt", ".md",
    ".png", ".jpg", ".jpeg", ".webp", ".gif"
  ]
};



let selectedOutputs = new Set();
let isGenerating = false;



outputPills.forEach((pill) => {
  pill.addEventListener("click", () => {
    const outputType = pill.dataset.output;
    if (!outputType) return;

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

    pill.setAttribute("aria-pressed", String(isSelected));

    if (isSelected) {
      pill.classList.remove("border-[#D0D5DD]", "bg-white", "text-[#344054]");
      pill.classList.add("border-[#4F46E5]", "bg-[#4F46E5]", "text-white");
    } else {
      pill.classList.remove("border-[#4F46E5]", "bg-[#4F46E5]", "text-white");
      pill.classList.add("border-[#D0D5DD]", "bg-white", "text-[#344054]");
    }
  });
}

function updateSelectedCount() {
  const count = selectedOutputs.size;
  selectedCount.textContent = `${count} selected`;
}




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

  fileName.textContent = `Selected file: ${file.name}`;
  fileName.classList.remove("hidden");
});

function validateFile(file) {
  const fileNameLower = file.name.toLowerCase();
  const extension = "." + fileNameLower.split(".").pop();

  if (!CONFIG.allowedExtensions.includes(extension)) {
    return "This file type is not supported.";
  }

  const maxBytes = CONFIG.maxFileSizeMB * 1024 * 1024;
  if (file.size > maxBytes) {
    return `File size must be ${CONFIG.maxFileSizeMB} MB or less.`;
  }

  return null;
}



function validateSource() {
  clearSourceError();

  const text = sourceText.value.trim();
  const hasText = text.length > 0;
  const hasFile = sourceFile.files && sourceFile.files.length > 0;

  if (!hasText && !hasFile) {
    showSourceError("Please paste source content or upload a source file.");
    return false;
  }

  if (hasFile) {
    const fileError = validateFile(sourceFile.files[0]);
    if (fileError) {
      showSourceError(fileError);
      return false;
    }
  }

  return true;
}

function validateOutputs() {
  clearOutputError();

  if (selectedOutputs.size === 0) {
    showOutputError("Please select at least one output type.");
    return false;
  }

  return true;
}

function validateForm() {
  const sourceValid = validateSource();
  const outputsValid = validateOutputs();
  return sourceValid && outputsValid;
}




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




generateButton.addEventListener("click", async () => {
  clearGeneralError();

  if (isGenerating) return;

  const valid = validateForm();
  if (!valid) return;

  const requestData = collectFormData();

  setGeneratingState(true);

  try {
    const event = new CustomEvent("formify:generate", { detail: requestData });
    document.dispatchEvent(event);
  } catch (error) {
    console.error("Generation error:", error);
    showGeneralError("Something went wrong while preparing the request.");
    setGeneratingState(false);
  }
});




function collectFormData() {
  const file =
    sourceFile.files && sourceFile.files.length > 0
      ? sourceFile.files[0]
      : null;

  return {
    sourceText: sourceText.value.trim(),
    file,
    outputTypes: Array.from(selectedOutputs),
    settings: {
      audience: audience.value,
      tone: tone.value,
      language: language.value,
      detailLevel: detailLevel.value,
      objective: objective.value,
      style: style.value
    },
    additionalInstructions: additionalInstructions.value.trim()
  };
}


function setGeneratingState(generating) {
  isGenerating = generating;
  generateButton.disabled = generating;
  generateButton.textContent = generating ? "Generating..." : "Generate outputs";
}



function handleGenerationResponse(data) {
  setGeneratingState(false);
  clearGeneralError();

  if (!data) {
    showGeneralError("The server returned an empty response.");
    return;
  }

  if (data.error) {
    showGeneralError(data.error);
    return;
  }

  const outputs = normalizeOutputs(data);

  if (outputs.length === 0) {
    showGeneralError("No generated outputs were returned.");
    return;
  }

  renderGeneratedOutputs(outputs);
}




function normalizeOutputs(data) {
  if (Array.isArray(data.outputs)) {
    return data.outputs;
  }

  if (data.outputs && typeof data.outputs === "object") {
    return Object.entries(data.outputs).map(([type, value]) => {
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
        title: value?.title || formatOutputTitle(type),
        content: JSON.stringify(value, null, 2)
      };
    });
  }

  return [];
}




function renderGeneratedOutputs(outputs) {
  generatedOutputs.innerHTML = "";

  const selectedOutputArray = Array.from(selectedOutputs);

  const selectedResults = outputs.filter((output) =>
    selectedOutputArray.includes(output.type)
  );

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
    const card = createOutputCard(output);
    generatedOutputs.appendChild(card);
  });

  generatedSection.classList.remove("hidden");
  generatedSection.scrollIntoView({ behavior: "smooth", block: "start" });
}



function createOutputCard(output) {
  const card = document.createElement("article");
  card.className =
    "overflow-hidden rounded-2xl border border-[#E4E7EC] bg-white shadow-[0_2px_8px_rgba(16,24,40,0.03)]";

  const title = output.title || formatOutputTitle(output.type);
  const content = output.content || output.text || "";
  const isPresentation = output.type === "presentation" && output.data;
  const isInfographic = output.type === "infographic" && output.data;
  const isReport =
    (output.type === "executive-summary" || output.type === "technical-advisory") &&
    output.data;
  const isSocialPost =
    (output.type === "linkedin-post" || output.type === "x-post") && output.data;

  const downloadLabel = isPresentation
    ? "Download .pptx"
    : isInfographic
    ? "Download .html"
    : isReport
    ? "Download .docx"
    : isSocialPost
    ? "Download .txt"
    : "Download .md";

  card.innerHTML = `
    <div class="flex flex-col gap-3 border-b border-[#EAECF0] px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h3 class="text-[15px] font-semibold text-[#172033]">
          ${escapeHTML(title)}
        </h3>
        <div class="mt-1 flex items-center gap-2 text-[11px] text-[#667085]">
          ${
            output.grounded
              ? `<span class="inline-flex items-center gap-1 font-medium text-[#027A48]"><span>✓</span> Source grounded</span>`
              : ""
          }
          ${
            typeof output.matchedFacts === "number"
              ? `<span>${output.matchedFacts} facts matched</span>`
              : ""
          }
          ${
            typeof output.unsupportedClaims === "number"
              ? `<span>· ${output.unsupportedClaims} unsupported claims</span>`
              : ""
          }
        </div>
      </div>
      <div class="flex flex-wrap items-center gap-2">
        <button type="button" class="copy-output rounded-lg border border-[#D0D5DD] bg-white px-3 py-1.5 text-[12px] font-medium text-[#344054] transition hover:bg-[#F9FAFB]" data-action="copy">Copy</button>
        <button type="button" class="download-output rounded-lg border border-[#D0D5DD] bg-white px-3 py-1.5 text-[12px] font-medium text-[#344054] transition hover:bg-[#F9FAFB]" data-action="download">${downloadLabel}</button>
        <button type="button" class="regenerate-output rounded-lg border border-[#D0D5DD] bg-white px-3 py-1.5 text-[12px] font-medium text-[#344054] transition hover:bg-[#F9FAFB]" data-action="regenerate">Regenerate</button>
      </div>
    </div>
    <div class="px-5 py-5">
      <div class="output-content whitespace-pre-wrap text-[14px] leading-7 text-[#344054]">${escapeHTML(content)}</div>
    </div>
    ${
      output.evidence
        ? `<details class="border-t border-[#EAECF0] px-5 py-4">
             <summary class="cursor-pointer text-[12px] font-semibold text-[#344054]">View evidence</summary>
             <div class="mt-3 rounded-lg bg-[#F9FAFB] p-3 text-[12px] leading-5 text-[#667085]">${escapeHTML(output.evidence)}</div>
           </details>`
        : ""
    }
  `;

  const copyButton = card.querySelector(".copy-output");
  copyButton.addEventListener("click", async () => {
    await copyText(content, copyButton);
  });

  const downloadButton = card.querySelector(".download-output");

  if (isPresentation) {
    downloadButton.addEventListener("click", async () => {
      const originalText = downloadButton.textContent;
      downloadButton.textContent = "Preparing...";
      downloadButton.disabled = true;

      try {
        await downloadPptx(title, output.data);
      } catch (error) {
        console.error("PPTX download failed:", error);
        alert("Could not download the PowerPoint file. Please try again.");
      } finally {
        downloadButton.textContent = originalText;
        downloadButton.disabled = false;
      }
    });
  } else if (isInfographic) {
    downloadButton.addEventListener("click", async () => {
      const originalText = downloadButton.textContent;
      downloadButton.textContent = "Preparing...";
      downloadButton.disabled = true;

      try {
        await downloadInfographic(title, output.data);
      } catch (error) {
        console.error("Infographic download failed:", error);
        alert("Could not download the infographic. Please try again.");
      } finally {
        downloadButton.textContent = originalText;
        downloadButton.disabled = false;
      }
    });
  } else if (isReport) {
    downloadButton.addEventListener("click", async () => {
      const originalText = downloadButton.textContent;
      downloadButton.textContent = "Preparing...";
      downloadButton.disabled = true;

      try {
        await downloadReportDocx(title, output.data);
      } catch (error) {
        console.error("DOCX download failed:", error);
        alert("Could not download the Word document. Please try again.");
      } finally {
        downloadButton.textContent = originalText;
        downloadButton.disabled = false;
      }
    });
  } else if (isSocialPost) {
    downloadButton.addEventListener("click", () => {
      downloadSocialText(title, output.type, output.data);
    });
  } else {
    downloadButton.addEventListener("click", () => {
      downloadMarkdown(title, content);
    });
  }

  const regenerateButton = card.querySelector(".regenerate-output");
  regenerateButton.addEventListener("click", () => {
    regenerateOutput(output.type);
  });

  return card;
}




async function copyText(text, button) {
  try {
    await navigator.clipboard.writeText(text);
    const originalText = button.textContent;
    button.textContent = "Copied";
    setTimeout(() => { button.textContent = originalText; }, 1500);
  } catch (error) {
    console.error("Copy failed:", error);
    button.textContent = "Copy failed";
    setTimeout(() => { button.textContent = "Copy"; }, 1500);
  }
}

function downloadMarkdown(title, content) {
  const markdown = `# ${title}\n\n${content}\n`;
  const blob = new Blob([markdown], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `${slugify(title)}.md`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

async function downloadPptx(title, presentationData) {
  const response = await fetch("/download/presentation", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(presentationData)
  });

  if (!response.ok) {
    let message = "Could not generate the PowerPoint file.";
    try {
      const errorData = await response.json();
      if (errorData && errorData.error) message = errorData.error;
    } catch (_) {}
    throw new Error(message);
  }

  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `${slugify(title)}.pptx`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

async function downloadReportDocx(title, reportData) {
  const response = await fetch("/download/report", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(reportData)
  });

  if (!response.ok) {
    let message = "Could not generate the Word document.";
    try {
      const errorData = await response.json();
      if (errorData && errorData.error) message = errorData.error;
    } catch (_) {}
    throw new Error(message);
  }

  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `${slugify(title)}.docx`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

function buildSocialPlainText(outputType, data) {
  if (outputType === "linkedin-post") {
    const parts = [];
    if (data.opening) parts.push(data.opening);
    if (Array.isArray(data.body_sections)) {
      data.body_sections.forEach((section) => parts.push(section));
    }
    if (data.call_to_action) parts.push(data.call_to_action);

    let text = parts.join("\n\n");

    if (Array.isArray(data.hashtags) && data.hashtags.length > 0) {
      const tags = data.hashtags
        .map((tag) => (String(tag).startsWith("#") ? tag : `#${tag}`))
        .join(" ");
      text += `\n\n${tags}`;
    }

    return text;
  }

  if (outputType === "x-post") {
    const posts = Array.isArray(data.posts) ? data.posts : [];
    let text = posts
      .slice()
      .sort((a, b) => (a.position || 0) - (b.position || 0))
      .map((post) =>
        data.format === "thread"
          ? `${post.position}/ ${post.content}`
          : post.content
      )
      .join("\n\n---\n\n");

    if (Array.isArray(data.hashtags) && data.hashtags.length > 0) {
      const tags = data.hashtags
        .map((tag) => (String(tag).startsWith("#") ? tag : `#${tag}`))
        .join(" ");
      text += `\n\n${tags}`;
    }

    return text;
  }

  return "";
}

function downloadSocialText(title, outputType, data) {
  const text = buildSocialPlainText(outputType, data);
  const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `${slugify(title)}.txt`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

async function downloadInfographic(title, infographicData) {
  const response = await fetch("/download/infographic", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(infographicData)
  });

  if (!response.ok) {
    let message = "Could not generate the infographic file.";
    try {
      const errorData = await response.json();
      if (errorData && errorData.error) message = errorData.error;
    } catch (_) {}
    throw new Error(message);
  }

  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `${slugify(title)}.html`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

function regenerateOutput(outputType) {
  if (!outputType) return;

  const wasSelected = selectedOutputs.has(outputType);
  if (!wasSelected) {
    selectedOutputs.add(outputType);
    updateOutputPillUI();
    updateSelectedCount();
  }

  document.dispatchEvent(
    new CustomEvent("formify:regenerate", {
      detail: { outputType, formData: collectFormData() }
    })
  );
}


/* =========================================================
   PROFILE MENU
   ========================================================= */

if (profileButton && profileMenu) {
  profileButton.addEventListener("click", (event) => {
    event.stopPropagation();
    const isHidden = profileMenu.classList.contains("hidden");

    if (isHidden) {
      profileMenu.classList.remove("hidden");
      profileButton.setAttribute("aria-expanded", "true");
    } else {
      profileMenu.classList.add("hidden");
      profileButton.setAttribute("aria-expanded", "false");
    }
  });

  document.addEventListener("click", (event) => {
    if (!profileMenu.contains(event.target) && !profileButton.contains(event.target)) {
      profileMenu.classList.add("hidden");
      profileButton.setAttribute("aria-expanded", "false");
    }
  });
}




function formatOutputTitle(type) {
  if (!type) return "Generated Output";
  return type.replace(/[-_]/g, " ").replace(/\b\w/g, (char) => char.toUpperCase());
}

function slugify(text) {
  return String(text).toLowerCase().trim().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
}

function escapeHTML(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}




updateOutputPillUI();
updateSelectedCount();
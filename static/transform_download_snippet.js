const downloadButton = card.querySelector(".download-output");

if (output.type === "presentation" && output.data) {
  downloadButton.textContent = "Download .pptx";
  downloadButton.addEventListener("click", async () => {
    const originalText = downloadButton.textContent;
    downloadButton.textContent = "Preparing...";
    downloadButton.disabled = true;

    try {
      const response = await fetch("/download/presentation", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(output.data)
      });

      if (!response.ok) {
        throw new Error("Could not generate the PowerPoint file.");
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
    } catch (error) {
      console.error("PPTX download failed:", error);
      alert("Could not download the PowerPoint file. Please try again.");
    } finally {
      downloadButton.textContent = originalText;
      downloadButton.disabled = false;
    }
  });
} else {
  downloadButton.addEventListener("click", () => {
    downloadMarkdown(title, content);
  });
}
import os
import uuid
import html


GENERATED_DIR = "generated_files"


def _esc(value):
    return html.escape(str(value)) if value not in (None, "") else ""


def _render_visual_data(visual_data):
    """
    visual_data items can be plain strings/numbers or dicts like
    {"label": "...", "value": "..."}. Render generically either way.
    """
    if not visual_data:
        return ""

    items_html = []
    for item in visual_data:
        if isinstance(item, dict):
            label = item.get("label") or item.get("name") or ""
            value = item.get("value") or item.get("amount") or ""
            items_html.append(
                f'<div class="stat"><div class="stat-value">{_esc(value)}</div>'
                f'<div class="stat-label">{_esc(label)}</div></div>'
            )
        else:
            items_html.append(f'<div class="stat"><div class="stat-value">{_esc(item)}</div></div>')

    return f'<div class="stat-grid">{"".join(items_html)}</div>'


def _render_content_list(content, visual_type):
    if not content:
        return ""

    vtype = (visual_type or "").lower()

    if "checklist" in vtype:
        items = "".join(f'<li class="check-item">{_esc(c)}</li>' for c in content)
        return f'<ul class="checklist">{items}</ul>'

    if "timeline" in vtype:
        items = "".join(
            f'<div class="timeline-item"><span class="timeline-dot"></span>'
            f'<div class="timeline-text">{_esc(c)}</div></div>'
            for c in content
        )
        return f'<div class="timeline">{items}</div>'

    if "process" in vtype or "flow" in vtype:
        items = "".join(
            f'<div class="step"><div class="step-number">{i + 1}</div>'
            f'<div class="step-text">{_esc(c)}</div></div>'
            + ("<div class=\"step-arrow\">&#8594;</div>" if i < len(content) - 1 else "")
            for i, c in enumerate(content)
        )
        return f'<div class="process">{items}</div>'

    if "comparison" in vtype or "cards" in vtype:
        items = "".join(f'<div class="mini-card">{_esc(c)}</div>' for c in content)
        return f'<div class="card-grid">{items}</div>'

    if "callout" in vtype:
        items = "".join(f'<p class="callout-text">{_esc(c)}</p>' for c in content)
        return f'<div class="callout">{items}</div>'

    # default: clean bullet list (covers diagram, hierarchy, icon-supported, etc.)
    items = "".join(f'<li>{_esc(c)}</li>' for c in content)
    return f'<ul class="bullet-list">{items}</ul>'


def build_infographic_html(data):
    """
    Convert the Formify 'infographic' JSON (from INFOGRAPHIC_PROMPT) into a
    single self-contained, styled HTML file and return its path.
    """

    os.makedirs(GENERATED_DIR, exist_ok=True)

    title = data.get("title") or "Infographic"
    subtitle = data.get("subtitle") or ""
    key_messages = data.get("key_messages") or []
    sections = data.get("sections") or []
    footer = data.get("footer") or ""

    key_messages_html = ""
    if key_messages:
        pills = "".join(f'<span class="pill">{_esc(m)}</span>' for m in key_messages)
        key_messages_html = f'<div class="key-messages">{pills}</div>'

    sections_html = ""
    for section in sections:
        heading = section.get("heading") or ""
        key_message = section.get("key_message") or ""
        content = section.get("content") or []
        visual_type = section.get("visual_type") or ""
        visual_data = section.get("visual_data") or []

        body = _render_visual_data(visual_data) or _render_content_list(content, visual_type)

        key_msg_html = f'<p class="section-key-message">{_esc(key_message)}</p>' if key_message else ""

        sections_html += f"""
        <section class="info-section">
          <h2>{_esc(heading)}</h2>
          {key_msg_html}
          {body}
        </section>
        """

    footer_html = f'<footer>{_esc(footer)}</footer>' if footer else ""

    html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{_esc(title)}</title>
<style>
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    padding: 40px 24px;
    background: #F7F8FA;
    font-family: -apple-system, "Segoe UI", Roboto, Arial, sans-serif;
    color: #172033;
  }}
  .page {{
    max-width: 760px;
    margin: 0 auto;
    background: #FFFFFF;
    border-radius: 20px;
    padding: 48px 40px;
    box-shadow: 0 2px 20px rgba(16,24,40,0.06);
  }}
  h1 {{
    font-size: 30px;
    font-weight: 700;
    letter-spacing: -0.02em;
    margin: 0 0 8px;
  }}
  .subtitle {{
    font-size: 15px;
    color: #667085;
    margin: 0 0 24px;
  }}
  .key-messages {{
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 36px;
  }}
  .pill {{
    background: #EEF2FF;
    color: #4338CA;
    font-size: 13px;
    font-weight: 600;
    padding: 6px 14px;
    border-radius: 999px;
  }}
  .info-section {{
    margin-bottom: 34px;
    padding-bottom: 30px;
    border-bottom: 1px solid #EAECF0;
  }}
  .info-section:last-of-type {{
    border-bottom: none;
  }}
  .info-section h2 {{
    font-size: 18px;
    font-weight: 600;
    margin: 0 0 10px;
  }}
  .section-key-message {{
    font-size: 14px;
    font-weight: 600;
    color: #4338CA;
    margin: 0 0 14px;
  }}
  .bullet-list, .checklist {{
    margin: 0;
    padding-left: 20px;
    font-size: 14px;
    line-height: 1.7;
    color: #344054;
  }}
  .checklist {{
    list-style: none;
    padding-left: 0;
  }}
  .check-item {{
    padding-left: 26px;
    position: relative;
    margin-bottom: 6px;
  }}
  .check-item::before {{
    content: "✓";
    position: absolute;
    left: 0;
    color: #027A48;
    font-weight: 700;
  }}
  .stat-grid {{
    display: flex;
    flex-wrap: wrap;
    gap: 16px;
  }}
  .stat {{
    background: #F9FAFB;
    border-radius: 14px;
    padding: 18px 22px;
    min-width: 130px;
    text-align: center;
  }}
  .stat-value {{
    font-size: 24px;
    font-weight: 700;
    color: #4338CA;
  }}
  .stat-label {{
    font-size: 12px;
    color: #667085;
    margin-top: 4px;
  }}
  .card-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 12px;
  }}
  .mini-card {{
    background: #F9FAFB;
    border-radius: 12px;
    padding: 14px 16px;
    font-size: 13.5px;
    color: #344054;
  }}
  .timeline {{
    border-left: 2px solid #E0E7FF;
    padding-left: 20px;
  }}
  .timeline-item {{
    position: relative;
    margin-bottom: 16px;
    font-size: 14px;
    color: #344054;
  }}
  .timeline-dot {{
    position: absolute;
    left: -26px;
    top: 4px;
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: #4F46E5;
  }}
  .process {{
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 10px;
  }}
  .step {{
    background: #F9FAFB;
    border-radius: 12px;
    padding: 12px 16px;
    font-size: 13.5px;
    display: flex;
    align-items: center;
    gap: 10px;
  }}
  .step-number {{
    background: #4F46E5;
    color: white;
    width: 22px;
    height: 22px;
    border-radius: 50%;
    font-size: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }}
  .step-arrow {{
    color: #98A2B3;
    font-size: 16px;
  }}
  .callout {{
    background: #EEF2FF;
    border-radius: 14px;
    padding: 16px 20px;
  }}
  .callout-text {{
    margin: 0;
    font-size: 14px;
    color: #4338CA;
    font-weight: 500;
  }}
  footer {{
    margin-top: 20px;
    font-size: 12px;
    color: #98A2B3;
    text-align: center;
  }}
  @media print {{
    body {{ background: white; padding: 0; }}
    .page {{ box-shadow: none; border-radius: 0; }}
  }}
</style>
</head>
<body>
  <div class="page">
    <h1>{_esc(title)}</h1>
    {f'<p class="subtitle">{_esc(subtitle)}</p>' if subtitle else ''}
    {key_messages_html}
    {sections_html}
    {footer_html}
  </div>
</body>
</html>"""

    filename = f"{uuid.uuid4().hex}.html"
    output_path = os.path.join(GENERATED_DIR, filename)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_doc)

    return output_path
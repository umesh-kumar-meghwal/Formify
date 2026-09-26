import os
import uuid
import html

from ai.image_gen import generate_icon_image

GENERATED_DIR = "generated_files"

MAX_IMAGES_PER_INFOGRAPHIC = 4


def _esc(value):
    return html.escape(str(value)) if value not in (None, "") else ""


def _to_number(value):
    """Try to parse a value like '45%', '1,234', '3.5', 42 into a float."""
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = value.strip().replace(",", "").replace("%", "")
        try:
            return float(cleaned)
        except ValueError:
            return None
    return None


def _render_bar_chart(items, width=620, bar_area_height=200):
    """
    items = [(label, numeric_value, raw_display_value), ...]
    Renders a simple, dependency-free inline SVG bar chart.
    """
    n = len(items)
    if n == 0:
        return ""

    max_value = max(v for _, v, _ in items) or 1
    gap = 16
    bar_width = min(70, (width - gap * (n + 1)) / n)
    total_w = bar_width * n + gap * (n + 1)

    label_h = 20
    value_h = 20
    svg_h = bar_area_height + label_h + value_h + 10

    bars = []
    x = gap
    palette = ["#4F46E5", "#6366F1", "#818CF8", "#4338CA", "#A5B4FC", "#312E81"]

    for i, (label, value, display) in enumerate(items):
        bar_h = (value / max_value) * bar_area_height if max_value else 0
        y = value_h + (bar_area_height - bar_h)
        color = palette[i % len(palette)]

        bars.append(f'''
          <rect x="{x:.1f}" y="{y:.1f}" width="{bar_width:.1f}" height="{bar_h:.1f}"
                rx="6" fill="{color}" />
          <text x="{x + bar_width / 2:.1f}" y="{y - 6:.1f}" text-anchor="middle"
                font-size="13" font-weight="700" fill="#172033">{_esc(display)}</text>
          <text x="{x + bar_width / 2:.1f}" y="{value_h + bar_area_height + 18:.1f}"
                text-anchor="middle" font-size="11" fill="#667085">{_esc(label)}</text>
        ''')
        x += bar_width + gap

    total_w = max(total_w, width)

    return f'''
    <div class="chart-wrap">
      <svg viewBox="0 0 {total_w:.0f} {svg_h:.0f}" xmlns="http://www.w3.org/2000/svg"
           style="width:100%; max-width:{total_w:.0f}px; height:auto;">
        <line x1="0" y1="{value_h + bar_area_height:.1f}" x2="{total_w:.0f}" y2="{value_h + bar_area_height:.1f}"
              stroke="#EAECF0" stroke-width="1" />
        {"".join(bars)}
      </svg>
    </div>
    '''


def _render_visual_data(visual_data):
    """
    visual_data items can be plain strings/numbers or dicts like
    {"label": "...", "value": "..."}. When 2+ items have a numeric
    value, render a real SVG bar chart; otherwise fall back to
    simple stat cards.
    """
    if not visual_data:
        return ""

    parsed = []
    for item in visual_data:
        if isinstance(item, dict):
            label = item.get("label") or item.get("name") or ""
            raw_value = item.get("value") or item.get("amount") or ""
        else:
            label = ""
            raw_value = item

        number = _to_number(raw_value)
        parsed.append((label, number, raw_value))

    numeric_items = [(l, n, r) for (l, n, r) in parsed if n is not None]

    if len(numeric_items) >= 2:
        return _render_bar_chart(numeric_items)

    # fallback: plain stat cards (single stat, or non-numeric values)
    items_html = []
    for label, number, raw_value in parsed:
        items_html.append(
            f'<div class="stat"><div class="stat-value">{_esc(raw_value)}</div>'
            + (f'<div class="stat-label">{_esc(label)}</div>' if label else "")
            + '</div>'
        )

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


def build_infographic_html(data, generate_images=True):
    """
    Convert the Formify 'infographic' JSON (from INFOGRAPHIC_PROMPT) into a
    single self-contained, styled HTML file and return its path.

    generate_images: when True, calls OpenRouter's Image API to create a
    small AI icon per section (capped at MAX_IMAGES_PER_INFOGRAPHIC, since
    this is slow ~10-90s per image and costs credits). Any failure just
    skips that section's image rather than breaking the whole export.
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
    images_used = 0

    for section in sections:
        heading = section.get("heading") or ""
        key_message = section.get("key_message") or ""
        content = section.get("content") or []
        visual_type = section.get("visual_type") or ""
        visual_data = section.get("visual_data") or []

        body = _render_visual_data(visual_data) or _render_content_list(content, visual_type)

        key_msg_html = f'<p class="section-key-message">{_esc(key_message)}</p>' if key_message else ""

        image_html = ""
        if generate_images and images_used < MAX_IMAGES_PER_INFOGRAPHIC and heading:
            prompt_text = f"{heading}. {key_message}".strip()
            b64_data, media_type = generate_icon_image(prompt_text)

            if b64_data:
                images_used += 1
                image_html = (
                    f'<img class="section-icon" '
                    f'src="data:{media_type};base64,{b64_data}" alt="{_esc(heading)}" />'
                )

        sections_html += f"""
        <section class="info-section">
          <div class="section-head">
            {image_html}
            <div class="section-head-text">
              <h2>{_esc(heading)}</h2>
              {key_msg_html}
            </div>
          </div>
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
  .section-head {{
    display: flex;
    align-items: flex-start;
    gap: 16px;
    margin-bottom: 6px;
  }}
  .section-head-text {{
    flex: 1;
    min-width: 0;
  }}
  .section-head h2 {{
    margin: 0 0 6px;
  }}
  .section-icon {{
    width: 64px;
    height: 64px;
    border-radius: 14px;
    object-fit: cover;
    flex-shrink: 0;
    background: #F9FAFB;
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
  .chart-wrap {{
    width: 100%;
    overflow-x: auto;
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
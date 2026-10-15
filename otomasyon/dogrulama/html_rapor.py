"""Mevcut CANRAT-UI-002 JSON/XML koşu kanıtlarından bağımsız HTML rapor üretir.

Kayıtlı test sonucu ile kanıt doğrulama durumunu ayrı değerlendirir;
tutarlı KALDI, HATA ve ATLANDI kayıtları kanıtları eksiksizse doğrulanmış kabul edilir;
eksik veya çelişkili kanıtlarda kesinlikle doğrulanmış başarı rozeti gösterilmez.
"""
import argparse
import html
import json
import os
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from ortak import evaluate_run_evidence


def evaluate_run(folder_path):
    """Koşu klasöründeki kanıtları ortak kanıt değerlendirme fonksiyonuyla denetler."""
    return evaluate_run_evidence(folder_path, root=ROOT)



def render_html(info):
    """Tamamen bağımsız, harici kaynak gerektirmeyen HTML rapor üretir."""
    is_verified = (info["verification_status"] == "DOGRULANDI")
    badge_text = info["badge_text"]
    badge_class = info["badge_class"]
    recorded_result = info["recorded_result"]

    color_theme = {
        "pass": {"bg": "#e6f4ea", "text": "#137333", "border": "#34a853"},
        "fail": {"bg": "#fce8e6", "text": "#c5221f", "border": "#ea4335"},
        "warn": {"bg": "#fef7e0", "text": "#b06000", "border": "#f9ab00"},
    }
    c = color_theme.get(badge_class, color_theme["fail"])

    # Göreli linkler oluştur
    links_html = []
    folder = info["folder"]
    for item in info["links"]:
        name = html.escape(item["name"])
        desc = html.escape(item["desc"])
        exists = item["exists"]
        if exists:
            try:
                rel = os.path.relpath(item["path"], folder).replace("\\", "/")
                link_tag = f'<a href="{html.escape(rel)}">{name}</a>'
                status_badge = '<span class="status-pill pass">Mevcut</span>'
            except Exception:
                link_tag = name
                status_badge = '<span class="status-pill warn">Yol Hatası</span>'
        else:
            link_tag = name
            status_badge = '<span class="status-pill fail">Eksik Dosya</span>'

        links_html.append(f"""
        <tr>
            <td><strong>{link_tag}</strong></td>
            <td>{desc}</td>
            <td style="text-align: center;">{status_badge}</td>
        </tr>
        """)

    states = info["states"]
    restored_label = "Evet (Başlangıca Döndü)" if states["restored"] else "Hayır"
    restored_class = "pass" if states["restored"] else "fail"

    guard_start_label = "Boşta / Pasif (Start)" if info["guard_start_idle"] else "Aktif / Belirsiz"
    guard_start_class = "pass" if info["guard_start_idle"] else "fail"
    guard_end_label = "Boşta / Pasif (Start)" if info["guard_end_idle"] else "Aktif / Belirsiz"
    guard_end_class = "pass" if info["guard_end_idle"] else "fail"

    close_expected = "KAPANDI" if info["branch"] == "Closed" else ("ACIK_BIRAKILDI" if info["branch"] == "Existing" else "-")
    close_ok = (info["close_status"] == close_expected and close_expected != "-")
    close_class = "pass" if close_ok else "fail"

    error_items = "".join(f"<li>{html.escape(err)}</li>" for err in info["verification_reasons"])

    html_content = f"""<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(info['test_id'])} - Test Raporu ({html.escape(info['run_id'])})</title>
    <style>
        :root {{
            --bg-color: #f8f9fa;
            --card-bg: #ffffff;
            --text-primary: #202124;
            --text-secondary: #5f6368;
            --border-color: #dadce0;
        }}
        body {{
            font-family: system-ui, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-primary);
            line-height: 1.5;
            margin: 0;
            padding: 24px;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
        }}
        .header-card {{
            background: var(--card-bg);
            border-radius: 8px;
            border: 1px solid var(--border-color);
            padding: 24px;
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }}
        .header-title h1 {{
            margin: 0 0 6px 0;
            font-size: 24px;
            font-weight: 600;
        }}
        .header-title p {{
            margin: 0;
            color: var(--text-secondary);
            font-size: 14px;
        }}
        .verdict-badge {{
            background-color: {c['bg']};
            color: {c['text']};
            border: 2px solid {c['border']};
            padding: 10px 24px;
            border-radius: 24px;
            font-size: 18px;
            font-weight: 700;
            letter-spacing: 0.5px;
            text-align: center;
            white-space: nowrap;
        }}
        .card {{
            background: var(--card-bg);
            border-radius: 8px;
            border: 1px solid var(--border-color);
            padding: 20px 24px;
            margin-bottom: 20px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }}
        .card h2 {{
            margin: 0 0 16px 0;
            font-size: 16px;
            font-weight: 600;
            color: var(--text-primary);
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 8px;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
        }}
        .meta-item {{
            margin-bottom: 8px;
        }}
        .meta-item .label {{
            font-size: 12px;
            color: var(--text-secondary);
            text-transform: uppercase;
            font-weight: 600;
            margin-bottom: 2px;
        }}
        .meta-item .value {{
            font-size: 14px;
            font-weight: 500;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
            margin-top: 8px;
        }}
        th, td {{
            text-align: left;
            padding: 10px 12px;
            border-bottom: 1px solid var(--border-color);
        }}
        th {{
            background-color: #f8f9fa;
            color: var(--text-secondary);
            font-weight: 600;
            font-size: 13px;
        }}
        .status-pill {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
        }}
        .status-pill.pass {{
            background-color: #e6f4ea;
            color: #137333;
        }}
        .status-pill.fail {{
            background-color: #fce8e6;
            color: #c5221f;
        }}
        .status-pill.warn {{
            background-color: #fef7e0;
            color: #b06000;
        }}
        .alert-box {{
            padding: 14px 16px;
            border-radius: 6px;
            font-size: 14px;
            margin-top: 10px;
        }}
        .alert-box.info {{
            background-color: #e8f0fe;
            color: #1a73e8;
            border: 1px solid #d2e3fc;
        }}
        .alert-box.danger {{
            background-color: #fce8e6;
            color: #c5221f;
            border: 1px solid #fad2cf;
        }}
        .alert-box.warn {{
            background-color: #fef7e0;
            color: #b06000;
            border: 1px solid #ffe7a0;
        }}
        .alert-box ul {{
            margin: 8px 0 0 0;
            padding-left: 20px;
        }}
        a {{
            color: #1a73e8;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        .footer {{
            text-align: center;
            font-size: 12px;
            color: var(--text-secondary);
            margin-top: 30px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Başlık ve Rozet -->
        <div class="header-card">
            <div class="header-title">
                <h1>{html.escape(info['test_id'])} Raporu</h1>
                <p>Koşu ID: <code>{html.escape(info['run_id'])}</code> &bull; Tarih: {html.escape(info['time_str'])}</p>
            </div>
            <div class="verdict-badge">
                {html.escape(badge_text)}
            </div>
        </div>

        <!-- Özet / Sonuç Açıklaması -->
        <div class="card">
            <h2>Kayıtlı Test Sonucu ve Kanıt Doğrulama Durumu</h2>
            {f'''
            <div class="alert-box {'info' if recorded_result == 'GECTI' else ('warn' if recorded_result == 'ATLANDI' else 'danger')}">
                <strong>Kayıtlı Test Sonucu: {html.escape(recorded_result)} &bull; Kanıt Doğrulama: DOĞRULANDI</strong><br>
                {html.escape("Tüm durum geçişleri, süreç sahipliği ve güvenlik kontrolleri bağımsız kanıtlarla eksiksiz doğrulandı." if recorded_result == "GECTI" else f"Testin {recorded_result} sonucu mevcut kanıt kayıtlarıyla tutarlı biçimde doğrulanmıştır.")}
            </div>
            ''' if is_verified else f'''
            <div class="alert-box danger">
                <strong>KANIT DOĞRULANAMADI (Kayıtlı Sonuç: {html.escape(recorded_result)})</strong><br>
                Aşağıdaki eksiklik veya çelişkiler nedeniyle kanıt doğrulanamamıştır:
                <ul>{error_items}</ul>
            </div>
            '''}
        </div>

        <!-- Koşu Bilgileri -->
        <div class="card">
            <h2>Koşu Parametreleri ve Kayıtlar</h2>
            <div class="grid">
                <div class="meta-item">
                    <div class="label">Kayıtlı Test Sonucu</div>
                    <div class="value"><code>{html.escape(recorded_result)}</code></div>
                </div>
                <div class="meta-item">
                    <div class="label">Kanıt Doğrulama</div>
                    <div class="value"><span class="status-pill {'pass' if is_verified else 'fail'}">{html.escape(info['verification_status'])}</span></div>
                </div>
                <div class="meta-item">
                    <div class="label">Başlangıç Modu</div>
                    <div class="value"><code>{html.escape(info['branch'])}</code></div>
                </div>
                <div class="meta-item">
                    <div class="label">Koşu Süresi</div>
                    <div class="value">{html.escape(info['duration_str'])}</div>
                </div>
                <div class="meta-item">
                    <div class="label">Hedef PID</div>
                    <div class="value"><code>{html.escape(info['process_id'])}</code></div>
                </div>
                <div class="meta-item">
                    <div class="label">Süreç Start Ticks</div>
                    <div class="value"><small>{html.escape(info['process_start_ticks'])}</small></div>
                </div>
            </div>
        </div>

        <!-- Kaynak Bazında Test Sonuçları -->
        <div class="card">
            <h2>Kaynak Bazında Test Sonuçları</h2>
            <div class="grid">
                <div class="meta-item">
                    <div class="label">Pytest XML Sonucu</div>
                    <div class="value"><code>{html.escape(str(info.get('source_results', {}).get('xml', '-')))}</code></div>
                </div>
                <div class="meta-item">
                    <div class="label">Pytest Köprü Durumu</div>
                    <div class="value"><code>{html.escape(str(info.get('source_results', {}).get('link', '-')))}</code></div>
                </div>
                <div class="meta-item">
                    <div class="label">UI (UIA) Sonucu</div>
                    <div class="value"><code>{html.escape(str(info.get('source_results', {}).get('ui', '-')))}</code></div>
                </div>
                <div class="meta-item">
                    <div class="label">Yaşam Döngüsü Sonucu</div>
                    <div class="value"><code>{html.escape(str(info.get('source_results', {}).get('lifecycle', '-')))}</code></div>
                </div>
            </div>
        </div>

        <!-- Durum Geçişleri -->
        <div class="card">
            <h2>Onay Kutusu Durum Geçişleri (CANRAT-UI-002)</h2>
            <table>
                <thead>
                    <tr>
                        <th>Aşama</th>
                        <th>Beklenen Değer</th>
                        <th>Gerçekleşen Değer</th>
                        <th>Durum</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><strong>1. Başlangıç Durumu</strong></td>
                        <td>{html.escape(states['initial_expected'])}</td>
                        <td>{html.escape(states['initial_observed'])}</td>
                        <td><span class="status-pill {'pass' if states['initial_observed'] != '-' else 'fail'}">Okundu</span></td>
                    </tr>
                    <tr>
                        <td><strong>2. Karşıt Değere Geçiş</strong></td>
                        <td>{html.escape(states['changed_expected'])}</td>
                        <td>{html.escape(states['changed_observed'])}</td>
                        <td><span class="status-pill {'pass' if states['changed_observed'] == states['changed_expected'] and states['changed_observed'] != '-' and states['changed_observed'] != states['initial_observed'] else 'fail'}">{'Uyumlu' if states['changed_observed'] == states['changed_expected'] and states['changed_observed'] != states['initial_observed'] else 'Uyumsuz'}</span></td>
                    </tr>
                    <tr>
                        <td><strong>3. Başlangıç Durumuna Dönüş</strong></td>
                        <td>{html.escape(states['final_expected'])}</td>
                        <td>{html.escape(states['final_observed'])}</td>
                        <td><span class="status-pill {'pass' if states['final_observed'] == states['final_expected'] and states['final_observed'] != '-' and states['restored'] else 'fail'}">{'Geri Yüklendi' if states['final_observed'] == states['final_expected'] and states['restored'] else 'Kaldı'}</span></td>
                    </tr>
                </tbody>
            </table>
        </div>

        <!-- Güvenlik ve Yaşam Döngüsü -->
        <div class="card">
            <h2>Güvenlik ve Yaşam Döngüsü Denetimi</h2>
            <table>
                <thead>
                    <tr>
                        <th>Kontrol</th>
                        <th>Açıklama / Gözlem</th>
                        <th>Sonuç</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><strong>Start Butonu Güvenliği (Başlangıç)</strong></td>
                        <td>{html.escape(info['guard_start_text'])}</td>
                        <td><span class="status-pill {guard_start_class}">{guard_start_label}</span></td>
                    </tr>
                    <tr>
                        <td><strong>Start Butonu Güvenliği (Bitiş)</strong></td>
                        <td>{html.escape(info['guard_end_text'])}</td>
                        <td><span class="status-pill {guard_end_class}">{guard_end_label}</span></td>
                    </tr>
                    <tr>
                        <td><strong>Başlangıç Durumuna Geri Yükleme</strong></td>
                        <td>Kutunun test öncesi değerine döndürülmesi</td>
                        <td><span class="status-pill {restored_class}">{restored_label}</span></td>
                    </tr>
                    <tr>
                        <td><strong>Süreç Yaşam Döngüsü / Temizlik</strong></td>
                        <td>Beklenen: <code>{html.escape(close_expected)}</code> &bull; Gerçekleşen: <code>{html.escape(info['close_status'])}</code></td>
                        <td><span class="status-pill {close_class}">{html.escape(info['close_status'])}</span></td>
                    </tr>
                </tbody>
            </table>
        </div>

        <!-- Kaynak Kanıt Dosyaları -->
        <div class="card">
            <h2>Kaynak JSON ve XML Kanıtları</h2>
            <table>
                <thead>
                    <tr>
                        <th>Dosya</th>
                        <th>Açıklama</th>
                        <th style="text-align: center;">Durum</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(links_html)}
                </tbody>
            </table>
        </div>

        <div class="footer">
            CanRat Test Otomasyonu &bull; CANRAT-UI-002 Bağımsız HTML Raporu &bull; Ağ bağlantısı gerektirmez.
        </div>
    </div>
</body>
</html>
"""
    return html_content


def generate_report(folder_path, output_path=None):
    folder = Path(folder_path).resolve()
    if not folder.is_dir():
        raise FileNotFoundError(f"Koşu klasörü bulunamadı: {folder}")

    info = evaluate_run(folder)
    target = (folder / "rapor.html") if output_path is None else Path(output_path).resolve()
    content = render_html(info)
    target.write_text(content, encoding="utf-8")
    return target, info


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--folder", type=Path, required=True, help="Pytest koşu klasörü yolu")
    parser.add_argument("--output", type=Path, default=None, help="Çıktı HTML dosya yolu (varsayılan: <folder>/rapor.html)")
    args = parser.parse_args()

    try:
        report_path, info = generate_report(args.folder, args.output)
        status_label = "DOGRULANDI" if info["verification_status"] == "DOGRULANDI" else "DOGRULANAMADI"
        print(f"HTML_RAPOR_URETILDI: {status_label} (Kayıtlı: {info['recorded_result']}) -> {report_path}")
        return 0
    except Exception as exc:
        print(f"HATA: Rapor üretilemedi: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())

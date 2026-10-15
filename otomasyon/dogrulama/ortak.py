"""Görev kanıt doğrulayıcılarının ortak dosya, koşul ve kanıt değerlendirme işlemleri."""
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def project_path(root, reference):
    root = Path(root).resolve()
    path = (root / reference).resolve()
    path.relative_to(root)
    return path


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require_versions(root, versions, expected_files, message):
    normalized = {name.replace('\\', '/'): value for name, value in versions.items()}
    require(set(normalized) == set(expected_files), message)
    for name, value in normalized.items():
        require(digest(project_path(root, name)) == value, 'Eski surume ait kanit: ' + name)


# Ortak kanıt tutarlılık ve şema denetleyicileri

def check_xml_cases(xml_root):
    """testsuite ve testcase öğelerinin varlığını ve sayaç tutarlılığını denetler."""
    suites = list(xml_root.iter('testsuite'))
    cases = list(xml_root.iter('testcase'))
    suite = suites[0] if suites else None
    if suite is None:
        return False, "pytest.xml içinde geçerli <testsuite> öğesi yok.", 0, 0, 0, 0, 0, cases

    tests = int(suite.attrib.get('tests', 0))
    failures = int(suite.attrib.get('failures', 0))
    errors = int(suite.attrib.get('errors', 0))
    skipped = int(suite.attrib.get('skipped', 0))

    actual_failures = len([c for c in cases if any(child.tag == 'failure' for child in c)])
    actual_errors = len([c for c in cases if any(child.tag == 'error' for child in c)])
    actual_skipped = len([c for c in cases if any(child.tag == 'skipped' for child in c)])
    actual_cases = len(cases)

    # Sayaç - öğe tutarlılığı
    if tests > 0 and actual_cases == 0:
        return False, f"XML tests={tests} fakat testcase öğesi yok.", tests, actual_failures, actual_errors, actual_skipped, actual_cases, cases
    if actual_failures != failures:
        return False, f"XML failures sayacı ({failures}) gerçek failure öğeleriyle ({actual_failures}) çelişiyor.", tests, actual_failures, actual_errors, actual_skipped, actual_cases, cases
    if actual_errors != errors:
        return False, f"XML errors sayacı ({errors}) gerçek error öğeleriyle ({actual_errors}) çelişiyor.", tests, actual_failures, actual_errors, actual_skipped, actual_cases, cases
    if actual_skipped != skipped:
        return False, f"XML skipped sayacı ({skipped}) gerçek skipped öğeleriyle ({actual_skipped}) çelişiyor.", tests, actual_failures, actual_errors, actual_skipped, actual_cases, cases
    if tests != actual_cases:
        return False, f"XML tests sayacı ({tests}) gerçek testcase sayısı ({actual_cases}) ile çelişiyor.", tests, actual_failures, actual_errors, actual_skipped, actual_cases, cases

    return True, None, tests, actual_failures, actual_errors, actual_skipped, actual_cases, cases


def check_guard_consistency(guard):
    """Start guard alanlarının iç çelişkilerini denetler."""
    if not isinstance(guard, dict):
        return False, "Guard verisi sözlük tipinde değil."
    active = guard.get('active')
    toggle = guard.get('toggle_state')
    name = guard.get('name')
    idle = guard.get('idle')
    if (active is True or toggle == 'On' or name == 'Stop') and idle is True:
        return False, "Start butonu çelişkili: active=True veya toggle_state=On iken idle=True olamaz."
    if idle is True and (active is not False or toggle != 'Off' or name != 'Start'):
        return False, "Start butonu çelişkili: idle=True iken active=False, toggle_state=Off, name=Start olmalıdır."
    return True, None


def check_ticks_validity(ticks):
    """process_start_ticks varlığını ve sayısal geçerliliğini denetler."""
    if ticks is None:
        return False, "process_start_ticks eksik (None)."
    s = str(ticks).strip()
    if not s or not s.isdigit():
        return False, f"process_start_ticks eksik veya geçersiz rakam dizisi değil: {ticks!r}."
    return True, None


def check_states_match(link_states, ui_states):
    """Köprü observed_states ile UI gözlemlerinin uyumunu denetler."""
    if link_states != ui_states:
        return False, f"pytest-link observed_states ({link_states}) UI gözlemleriyle ({ui_states}) çelişiyor."
    return True, None


def resolve_linked_path(folder, reference, root=None):
    """Koşu klasörüne göre göreli veya köke göre dosya yolunu çözer."""
    if not reference:
        return None
    root = (ROOT if root is None else Path(root)).resolve()
    ref = Path(str(reference).replace('\\', '/'))
    if ref.is_absolute():
        return ref
    cand_root = (root / ref).resolve()
    if cand_root.exists():
        return cand_root
    cand_parent = (folder.parent / ref).resolve()
    if cand_parent.exists():
        return cand_parent
    cand_folder = (folder / ref).resolve()
    if cand_folder.exists():
        return cand_folder
    return cand_root


def evaluate_run_evidence(folder_path, root=None, expected_branch=None):
    """Tüm kanıt kaynaklarını (XML, link, UI, yaşam döngüsü) değerlendiren tekil ortak fonksiyon.

    Kayıtlı sonuç, kanıt tutarlılığı ve eksiklikleri ayrı ayrı tespit eder.
    """
    root = (ROOT if root is None else Path(root)).resolve()
    folder = Path(folder_path).resolve()
    contradictions = []
    missing_evidence = []

    info = {
        "folder": folder,
        "test_id": "CANRAT-UI-002",
        "run_id": folder.name,
        "branch": expected_branch or "-",
        "time_raw": "-",
        "time_str": "-",
        "duration_str": "-",
        "recorded_result": "BILINMIYOR",
        "verification_status": "DOGRULANAMADI",
        "source_results": {},
        "contradictions": contradictions,
        "missing_evidence": missing_evidence,
        "reasons": [],
        "verification_reasons": [],
        "badge_text": "KANIT DOĞRULANAMADI",
        "badge_class": "fail",
        "process_id": "-",
        "process_start_ticks": "-",
        "start_status": "-",
        "close_status": "-",
        "states": {
            "initial_expected": "Off",
            "initial_observed": "-",
            "changed_expected": "On",
            "changed_observed": "-",
            "final_expected": "Off",
            "final_observed": "-",
            "restored": False,
        },
        "guard_start_idle": False,
        "guard_start_text": "-",
        "guard_end_idle": False,
        "guard_end_text": "-",
        "links": [],
    }

    link_file = folder / "pytest-link.json"
    xml_file = folder / "pytest.xml"
    cmd_file = folder / "pytest-komut.json"

    # --- 1. XML İncelemesi ---
    xml_result = None
    if xml_file.is_file():
        info["links"].append({"name": "pytest.xml", "path": xml_file, "desc": "Pytest JUnit XML test sonucu", "exists": True})
        try:
            tree = ET.parse(xml_file)
            root_el = tree.getroot()
            valid_xml, xml_err, tests, act_fail, act_err, act_skip, act_cases, cases = check_xml_cases(root_el)
            if not valid_xml:
                contradictions.append(xml_err)

            if act_fail > 0:
                xml_result = "KALDI"
            elif act_err > 0:
                xml_result = "HATA"
            elif act_skip > 0:
                xml_result = "ATLANDI"
            elif act_cases == 1 and tests == 1:
                xml_result = "GECTI"
            elif tests == 0:
                xml_result = "HATA"
                contradictions.append("pytest XML test sayısı 0")
            else:
                xml_result = "HATA"
        except Exception as exc:
            contradictions.append(f"pytest.xml okuma hatası: {exc}")
            xml_result = "HATA"
    else:
        info["links"].append({"name": "pytest.xml", "path": xml_file, "desc": "Pytest JUnit XML test sonucu", "exists": False})
        missing_evidence.append("pytest.xml dosyası bulunamadı")
        xml_result = "HATA"

    # --- 2. Pytest-Link İncelemesi ---
    link_data = None
    link_pid = None
    link_ticks = None

    if link_file.is_file():
        info["links"].append({"name": "pytest-link.json", "path": link_file, "desc": "Pytest ve JSON kanıt köprü kaydı", "exists": True})
        try:
            raw_text = link_file.read_text(encoding="utf-8").strip()
            if not raw_text or raw_text == "{}":
                missing_evidence.append("pytest-link.json dosyası boş")
            else:
                link_data = json.loads(raw_text)
                for req_key in ("test_id", "run_id", "status", "exit_code"):
                    val = link_data.get(req_key)
                    if val is None or (isinstance(val, str) and not val.strip()):
                        missing_evidence.append(f"pytest-link.json zorunlu alan eksik: '{req_key}'")

                link_test_id = link_data.get("test_id")
                if link_test_id and link_test_id != "CANRAT-UI-002":
                    contradictions.append(f"Köprü test_id ('{link_test_id}') beklenen senaryoyla ('CANRAT-UI-002') eşleşmiyor.")

                info["test_id"] = link_data.get("test_id", info["test_id"])
                info["run_id"] = link_data.get("run_id", info["run_id"])
                branch_in_link = link_data.get("expected_branch")
                if branch_in_link:
                    info["branch"] = branch_in_link
                else:
                    missing_evidence.append("pytest-link.json expected_branch eksik veya boş.")
                if expected_branch and branch_in_link and branch_in_link != expected_branch:
                    contradictions.append(f"Başlangıç modu uyumsuz: beklenen {expected_branch}, köprüde {branch_in_link}")

                info["time_raw"] = link_data.get("time_utc", "-")
                if info["time_raw"] != "-":
                    info["time_str"] = str(info["time_raw"]).replace("T", " ").split(".")[0] + " UTC"
                if link_data.get("duration_seconds") is not None:
                    info["duration_str"] = f"{link_data['duration_seconds']} saniye"

                link_pid = link_data.get("process_id")
                link_ticks = str(link_data.get("process_start_ticks", ""))
                info["process_id"] = str(link_pid if link_pid is not None else "-")
                info["process_start_ticks"] = link_ticks or "-"
                info["start_status"] = str(link_data.get("start", "-"))
                info["close_status"] = str(link_data.get("close", "-"))

                link_status = link_data.get("status")
                exit_code = link_data.get("exit_code", 0)

                ALLOWED_LINK_STATUSES = {"DOGRULANDI", "KALDI", "HATA", "ATLANDI"}
                if not link_status or link_status not in ALLOWED_LINK_STATUSES:
                    contradictions.append(f"Bilinmeyen veya geçersiz pytest-link status değeri: '{link_status}' (İzin verilenler: DOGRULANDI, KALDI, HATA, ATLANDI)")

                link_run_id = link_data.get("run_id")
                if link_run_id is not None and link_run_id != folder.name:
                    contradictions.append(f"Köprü run_id ({link_run_id}) koşu klasörünün adıyla ({folder.name}) eşleşmiyor.")

                # Link çıkış kodu ve status tutarlılığı
                if link_status == "DOGRULANDI":
                    if exit_code != 0:
                        contradictions.append(f"pytest-link status 'DOGRULANDI' fakat exit_code={exit_code}")
                    if link_data.get("error"):
                        contradictions.append(f"pytest-link status 'DOGRULANDI' fakat error alanı dolu: '{link_data.get('error')}'")
                    if link_pid is None:
                        missing_evidence.append("pytest-link.json process_id eksik")
                    v_lticks, err_lticks = check_ticks_validity(link_data.get("process_start_ticks"))
                    if not v_lticks:
                        missing_evidence.append(f"pytest-link {err_lticks}")

                exp_states = link_data.get("expected_states")
                obs_states = link_data.get("observed_states")
                if exp_states is not None:
                    if not isinstance(exp_states, list) or len(exp_states) != 3 or any(s not in ("Off", "On") for s in exp_states):
                        contradictions.append(f"pytest-link.json expected_states ({exp_states}) geçersiz; 3 elemanlı 'Off'/'On' dizisi olmalıdır.")
                    else:
                        if exp_states[0] == exp_states[1]:
                            contradictions.append(f"pytest-link.json expected_states ({exp_states}) başlangıç ile karşıt durum aynı olamaz.")
                        if exp_states[0] != exp_states[2]:
                            contradictions.append(f"pytest-link.json expected_states ({exp_states}) başlangıç durumuna geri dönüş içermelidir.")

                if link_status == "DOGRULANDI":
                    if not exp_states or not isinstance(exp_states, list) or len(exp_states) != 3:
                        missing_evidence.append("pytest-link.json beklenen durumlar (expected_states) eksik veya geçersiz")
                    if not obs_states or not isinstance(obs_states, list) or len(obs_states) != 3:
                        missing_evidence.append("pytest-link.json gözlemlenen durumlar (observed_states) eksik veya geçersiz")

                if exp_states:
                    info["states"]["initial_expected"] = exp_states[0]
                    if len(exp_states) > 1:
                        info["states"]["changed_expected"] = exp_states[1]
                    if len(exp_states) > 2:
                        info["states"]["final_expected"] = exp_states[2]
                if obs_states:
                    info["states"]["initial_observed"] = obs_states[0]
                    if len(obs_states) > 1:
                        info["states"]["changed_observed"] = obs_states[1]
                    if len(obs_states) > 2:
                        info["states"]["final_observed"] = obs_states[2]

        except Exception as exc:
            contradictions.append(f"pytest-link.json okunamadı: {exc}")
    else:
        info["links"].append({"name": "pytest-link.json", "path": link_file, "desc": "Pytest ve JSON kanıt köprü kaydı", "exists": False})
        missing_evidence.append("pytest-link.json dosyası bulunamadı")

    if cmd_file.exists():
        info["links"].append({"name": "pytest-komut.json", "path": cmd_file, "desc": "Çalıştırılan pytest komutu ve çıkış kodu", "exists": True})

    # Başlangıç modu geçerlilik kontrolü
    if info["branch"] not in ("Existing", "Closed"):
        contradictions.append(f"Geçersiz veya eksik başlangıç modu: '{info['branch']}' (Yalnızca 'Existing' veya 'Closed' kabul edilir)")

    # --- 3. UI Sonuç Raporu İncelemesi ---
    ui_data = None
    ui_result = None
    ui_hata = None
    obs = None
    ui_path = resolve_linked_path(folder, link_data.get("ui_report") if link_data else None, root)
    if ui_path and ui_path.is_file():
        info["links"].append({"name": "UI sonuc.json", "path": ui_path, "desc": "CANRAT-UI-002 UIA işlem kanıtı", "exists": True})
        try:
            raw_ui = ui_path.read_text(encoding="utf-8").strip()
            if not raw_ui or raw_ui == "{}":
                missing_evidence.append("UI sonuc.json dosyası boş")
            else:
                ui_data = json.loads(raw_ui)
                ui_result = ui_data.get("test_sonucu")
                ui_hata = ui_data.get("hata") or ui_data.get("error") or ui_data.get("geri_yukleme_hatasi") or ui_data.get("kurtarma")

                # UI test_id ve calistirma_id doğrulaması
                ui_test_id = ui_data.get("test_id")
                if ui_test_id is None or not str(ui_test_id).strip():
                    missing_evidence.append("UI test_id eksik veya boş.")
                elif ui_test_id != "CANRAT-UI-002":
                    contradictions.append(f"UI test_id ('{ui_test_id}') beklenen senaryoyla ('CANRAT-UI-002') eşleşmiyor.")

                if link_data and link_data.get("test_id") and ui_test_id and link_data["test_id"] != ui_test_id:
                    contradictions.append(f"Köprü test_id ('{link_data['test_id']}') ile UI test_id ('{ui_test_id}') eşleşmiyor.")

                ui_calistirma_id = ui_data.get("calistirma_id")
                if ui_calistirma_id is None or not str(ui_calistirma_id).strip():
                    missing_evidence.append("UI calistirma_id eksik veya boş.")
                elif ui_calistirma_id != ui_path.parent.name:
                    contradictions.append(f"UI calistirma_id ('{ui_calistirma_id}') kendi kayıt klasörünün adıyla ('{ui_path.parent.name}') eşleşmiyor.")

                # UI hata alanı dolu mu? (Yalnızca GECTI iddiası varken çelişkidir; HATA kaydında açıklayıcı bilgidir)
                if ui_hata and ui_result == "GECTI":
                    contradictions.append(f"UI test_sonucu 'GECTI' fakat hata alanı dolu: '{ui_hata}'")

                obs = ui_data.get("gozlem")
                if not isinstance(obs, dict) or not obs:
                    missing_evidence.append("UI raporunda gozlem alanı eksik veya boş")
                else:
                    obs_error = obs.get("error")
                    obs_cleanup_error = obs.get("cleanup_error")
                    obs_cleanup_journal_error = obs.get("cleanup_journal_error")
                    if obs_error and ui_result == "GECTI":
                        contradictions.append(f"UI gözlem hata alanı dolu iken test GECTI olamaz: '{obs_error}'")
                    if obs_cleanup_error and ui_result == "GECTI":
                        contradictions.append(f"UI temizleme/geri yükleme hata alanı dolu iken test GECTI olamaz: '{obs_cleanup_error}'")
                    if obs_cleanup_journal_error and ui_result == "GECTI":
                        contradictions.append(f"UI temizleme günlüğü hatası mevcut iken test GECTI olamaz: '{obs_cleanup_journal_error}'")

                    if ui_result == "GECTI":
                        if obs.get("schema_version") != 1:
                            contradictions.append(f"Geçersiz veya eksik UI şema sürümü: {obs.get('schema_version')}")
                        if obs.get("mode") != "Exercise":
                            contradictions.append(f"Geçersiz UI modu: '{obs.get('mode')}' (beklenen: 'Exercise')")
                        if obs.get("phase") != "completed":
                            contradictions.append(f"UI aşaması tamamlanmamış (phase: '{obs.get('phase')}')")

                        events = obs.get("events")
                        if isinstance(events, list):
                            phases = [e.get("phase") for e in events if isinstance(e, dict)]
                            expected_phases = ['initial_saved', 'toggle_attempt', 'change_observed', 'restoring', 'completed']
                            if phases != expected_phases:
                                contradictions.append(f"UI işlem adımları eksik veya sırası bozuk: {phases}")
                        else:
                            missing_evidence.append("UI gözlem olayları (events) eksik")

                        if obs.get("mutation_attempted") is not True:
                            contradictions.append("UI kutu değiştirme denemesi yapılmadı (mutation_attempted=True değil)")
                        if obs.get("cleanup_attempted") is not True:
                            contradictions.append("UI temizleme denemesi yapılmadı (cleanup_attempted=True değil)")
                        if obs.get("changed_verified") is not True:
                            contradictions.append("UI kutu değişimi doğrulanmadı (changed_verified=True değil)")
                        if obs.get("restored") is not True:
                            contradictions.append("UI kutusunun geri yüklendiği doğrulanmadı (restored=True değil)")

                    initial = obs.get("initial")
                    exp_changed = obs.get("expected_changed")
                    changed = obs.get("changed")
                    final = obs.get("final")
                    restored = obs.get("restored")

                    info["states"]["initial_observed"] = initial if initial is not None else "-"
                    info["states"]["changed_observed"] = changed if changed is not None else "-"
                    info["states"]["final_observed"] = final if final is not None else "-"
                    info["states"]["restored"] = bool(restored)

                    # Link ile UI observed_states uyumu
                    ui_states_list = [initial, changed, final]
                    if link_data and "observed_states" in link_data:
                        v_match, err_match = check_states_match(link_data["observed_states"], ui_states_list)
                        if not v_match:
                            contradictions.append(err_match)

                    # UI process_start_ticks varlığı
                    v_ticks, err_ticks = check_ticks_validity(obs.get("process_start_ticks"))
                    if not v_ticks:
                        missing_evidence.append(f"UI {err_ticks}")

                    # Guard tutarlılığı
                    guards_before = obs.get("guard_before") or []
                    for g in guards_before:
                        vg, eg = check_guard_consistency(g)
                        if not vg:
                            contradictions.append(eg)
                    if guards_before and isinstance(guards_before, list):
                        last_guard = guards_before[-1]
                        info["guard_start_idle"] = bool(last_guard.get("idle"))
                        info["guard_start_text"] = f"Başlangıç: {last_guard.get('name', '-')}, Toggle={last_guard.get('toggle_state', '-')}, Boşta={last_guard.get('idle', False)}"

                    guard_after = obs.get("guard_after") or {}
                    if isinstance(guard_after, dict):
                        vg, eg = check_guard_consistency(guard_after)
                        if not vg:
                            contradictions.append(eg)
                        info["guard_end_idle"] = bool(guard_after.get("idle"))
                        info["guard_end_text"] = f"Bitiş: {guard_after.get('name', '-')}, Toggle={guard_after.get('toggle_state', '-')}, Boşta={guard_after.get('idle', False)}"

                    # PID / StartTicks eşleşmesi
                    ui_pid = obs.get("process_id")
                    ui_ticks = str(obs.get("process_start_ticks", ""))
                    if link_pid is not None and ui_pid != link_pid:
                        contradictions.append(f"UI süreç PID'si köprü PID'sinden farklı (UI: {ui_pid}, Köprü: {link_pid})")
                    if link_ticks and ui_ticks and ui_ticks != link_ticks:
                        contradictions.append("UI süreç start_ticks değeri köprü ile uyuşmuyor")

                # UI Journal (uia-adimlari.json) kontrolü
                uij_ref = link_data.get("ui_journal") if link_data else None
                uij_path = resolve_linked_path(folder, uij_ref, root) if uij_ref else (ui_path.parent / "uia-adimlari.json")
                if not uij_path or not uij_path.is_file():
                    missing_evidence.append("UI işlem günlüğü dosyası (uia-adimlari.json) bulunamadı")
                else:
                    try:
                        raw_uij = uij_path.read_text(encoding="utf-8").strip()
                        if not raw_uij or raw_uij == "{}":
                            missing_evidence.append("UI işlem günlüğü (uia-adimlari.json) dosyası boş ({})")
                        else:
                            uij_json = json.loads(raw_uij)
                            if obs is not None and uij_json != obs:
                                contradictions.append("UI işlem günlüğü (uia-adimlari.json) ile sonuc.json gözlemi çelişiyor.")
                    except Exception as exc:
                        contradictions.append(f"UI işlem günlüğü okuma hatası: {exc}")

        except Exception as exc:
            contradictions.append(f"UI raporu okuma hatası: {exc}")
    else:
        # Test runner seviyesinde ATLANDI veya HATA ise ve link'te ui_report yoksa aranmaz
        l_stat = link_data.get("status") if link_data else None
        if xml_result not in ("ATLANDI", "HATA") and l_stat not in ("ATLANDI", "HATA"):
            missing_evidence.append(f"Bağlı UI raporu bulunamadı: {link_data.get('ui_report') if link_data else 'kayıt yok'}")

    # --- 4. Yaşam Döngüsü Raporu İncelemesi ---
    life_data = None
    life_result = None
    life_obs = None
    life_path = resolve_linked_path(folder, link_data.get("lifecycle_report") if link_data else None, root)
    if life_path and life_path.is_file():
        info["links"].append({"name": "Yaşam Döngüsü sonuc.json", "path": life_path, "desc": "Süreç yaşam döngüsü kanıtı", "exists": True})
        try:
            raw_life = life_path.read_text(encoding="utf-8").strip()
            if not raw_life or raw_life == "{}":
                missing_evidence.append("Yaşam döngüsü raporu boş ({})")
            else:
                life_data = json.loads(raw_life)
                life_result = life_data.get("result")
                life_obs = life_data.get("observed")
                if not isinstance(life_obs, dict) or not life_obs:
                    missing_evidence.append("Yaşam döngüsü gözlem kaydı (observed) eksik veya boş")
                else:
                    life_run_id = life_data.get("run_id")
                    if life_run_id is None or not str(life_run_id).strip():
                        missing_evidence.append("Yaşam döngüsü run_id eksik veya boş.")
                    elif life_run_id != life_path.parent.name:
                        contradictions.append(f"Yaşam döngüsü run_id ('{life_run_id}') kendi kayıt klasörünün adıyla ('{life_path.parent.name}') eşleşmiyor.")

                    # Üst expected, observed.expected ve köprü expected_branch üçlü kontrolü
                    top_expected = life_data.get("expected")
                    obs_expected = life_obs.get("expected")
                    link_expected = link_data.get("expected_branch") if link_data else None

                    if top_expected is None or not str(top_expected).strip():
                        missing_evidence.append("Yaşam döngüsü üst expected değeri eksik veya boş.")
                    if obs_expected is None or not str(obs_expected).strip():
                        missing_evidence.append("Yaşam döngüsü observed.expected değeri eksik veya boş.")

                    if top_expected and obs_expected and top_expected != obs_expected:
                        contradictions.append(f"Yaşam döngüsü üst expected başlangıç modu ('{top_expected}') ile observed.expected ('{obs_expected}') eşleşmiyor.")
                    if top_expected and link_expected and top_expected != link_expected:
                        contradictions.append(f"Yaşam döngüsü üst expected başlangıç modu ('{top_expected}') köprü başlangıç moduyla ('{link_expected}') eşleşmiyor.")
                    if obs_expected and link_expected and obs_expected != link_expected:
                        contradictions.append(f"Yaşam döngüsü observed.expected başlangıç modu ('{obs_expected}') köprü başlangıç moduyla ('{link_expected}') eşleşmiyor.")

                    life_start = life_obs.get("start", {}).get("status") if isinstance(life_obs.get("start"), dict) else None
                    life_identity = life_obs.get("identity") if isinstance(life_obs.get("identity"), dict) else None
                    life_pid = life_identity.get("pid") if life_identity else None
                    life_ticks = str(life_identity.get("start_ticks", "")) if life_identity else ""

                    close_info = life_obs.get("close") or {}
                    close_status = close_info.get("status")
                    info["close_status"] = str(close_status if close_status is not None else "-")

                    # Süreç başladı mı yoksa başlamadan erken hata mı oluştu?
                    process_started = bool(
                        life_identity
                        or (life_start in ("BASLATILDI", "MEVCUDA_BAGLANILDI", "BASLATILIYOR"))
                        or (link_pid is not None)
                    )

                    # Alt test (observed.test) kontrolü
                    life_test = life_obs.get("test") or {}
                    life_test_result = life_test.get("status")

                    # Alt test report_path ile köprü ui_report uyumu
                    alt_report_raw = life_test.get("report_path")
                    if process_started or ui_path:
                        if alt_report_raw is None or not str(alt_report_raw).strip():
                            missing_evidence.append("Yaşam döngüsü alt test report_path eksik veya boş.")
                        else:
                            resolved_alt = resolve_linked_path(folder, alt_report_raw, root)
                            if resolved_alt and ui_path and resolved_alt.resolve() != ui_path.resolve():
                                contradictions.append(f"Yaşam döngüsü alt test report_path ({resolved_alt}) köprünün ui_report kaydıyla ({ui_path}) eşleşmiyor.")

                    # Başlatma durumu kontrolü
                    link_start = link_data.get("start") if link_data else None
                    if link_start and life_start and link_start != life_start:
                        contradictions.append(f"Köprü start durumu ({link_start}) yaşam döngüsü start durumu ({life_start}) ile çelişiyor.")

                    # Kapatma durumu kontrolü
                    link_close = link_data.get("close") if link_data else None
                    if link_close and close_status and link_close != close_status:
                        contradictions.append(f"Köprü close durumu ({link_close}) yaşam döngüsü close durumu ({close_status}) ile çelişiyor.")

                    life_err = life_data.get("error") or life_obs.get("error") or close_info.get("error") or life_data.get("cleanup_uncertain")
                    life_cleanup_err = life_obs.get("cleanup_error")
                    if life_err and life_result == "GECTI":
                        contradictions.append(f"Yaşam döngüsü sonucu 'GECTI' fakat hata alanı dolu: '{life_err}'")
                    if life_cleanup_err and life_result == "GECTI":
                        contradictions.append(f"Yaşam döngüsü temizleme hatası mevcut (cleanup_error): '{life_cleanup_err}'")

                    if not process_started:
                        # Erken hata durumu (süreç başlamadan önce hata oluştu):
                        # Olmayan kimlik veya başarılı kapanış şart koşulmaz, ulaşılan aşamayla tutarlı kayıt incelenir.
                        if life_result == "GECTI":
                            contradictions.append("Süreç başlatılmadığı halde yaşam döngüsü sonucu 'GECTI' olamaz.")
                        if not life_err and not (link_data and link_data.get("error")):
                            missing_evidence.append("Süreç başlatılamadı hatasında hata açıklaması (error) eksik.")
                        if life_obs.get("owned") is not False:
                            contradictions.append(f"Süreç başlatılamadığında owned=False olmalıdır (bulunan: {life_obs.get('owned')})")
                        if life_start != "BASLATILMADI":
                            contradictions.append(f"Süreç başlatılamadığında start.status 'BASLATILMADI' olmalıdır (bulunan: '{life_start}')")
                        if life_test_result != "CALISTIRILMADI":
                            contradictions.append(f"Süreç başlatılamadığında test.status 'CALISTIRILMADI' olmalıdır (bulunan: '{life_test_result}')")
                        if close_status != "DENENMEDI":
                            contradictions.append(f"Süreç başlatılamadığında close.status 'DENENMEDI' olmalıdır (bulunan: '{close_status}')")
                    else:
                        # Süreç başladı: Tüm süreç kimliği, sahiplik ve kapanış kontrolleri zorunludur!
                        if life_identity is None:
                            missing_evidence.append("Başlatılmış süreçte yaşam döngüsü identity eksik.")
                        else:
                            if life_pid is None:
                                missing_evidence.append("Başlatılmış süreçte PID eksik.")
                            v_pid_ticks, err_pid_ticks = check_ticks_validity(life_ticks)
                            if not v_pid_ticks:
                                missing_evidence.append(f"Yaşam döngüsü {err_pid_ticks}")

                        if link_pid is not None and life_pid != link_pid:
                            contradictions.append(f"Yaşam döngüsü PID'si köprü PID'sinden farklı (Yaşam: {life_pid}, Köprü: {link_pid})")
                        if link_ticks and life_ticks and life_ticks != link_ticks:
                            contradictions.append("Yaşam döngüsü start_ticks değeri köprü ile uyuşmuyor")

                        if ui_result and life_test_result and life_test_result != ui_result:
                            contradictions.append(f"Yaşam döngüsü alt test sonucu ({life_test_result}) UI sonucuyla ({ui_result}) çelişiyor.")
                        if link_data and link_data.get("test") and life_test_result and link_data["test"] != life_test_result:
                            contradictions.append(f"Köprü test durumu ({link_data['test']}) yaşam döngüsü alt test sonucuyla ({life_test_result}) çelişiyor.")

                        lt_id = life_test.get("observed_identity") or {}
                        lt_pid = lt_id.get("pid")
                        lt_ticks = str(lt_id.get("start_ticks", ""))
                        if lt_pid is not None and life_pid is not None and lt_pid != life_pid:
                            contradictions.append(f"Yaşam döngüsü alt test PID'si ({lt_pid}) yaşam döngüsü PID'sinden ({life_pid}) farklı")
                        if lt_ticks and life_ticks and lt_ticks != life_ticks:
                            contradictions.append("Yaşam döngüsü alt test start_ticks değeri yaşam döngüsü ile uyuşmuyor")

                        if close_status not in ("KAPANDI", "ACIK_BIRAKILDI"):
                            contradictions.append(f"Yaşam döngüsü kapanış durumu geçersiz: '{close_status}'")
                        if close_info.get("exited") is False and close_info.get("still_running") is not True:
                            contradictions.append(f"Süreç kapanışı başarısız (exited=False ve still_running={close_info.get('still_running')})")

                        expected_branch = info["branch"]
                        owned = life_obs.get("owned")
                        if expected_branch == "Closed":
                            if owned is not True:
                                contradictions.append(f"Kapalı başlangıçta (Closed) süreç sahipliği zorunludur (owned=True bekleniyor, bulunan: {owned})")
                            if life_obs.get("before") != []:
                                contradictions.append("Kapalı başlangıçta test öncesi çalışan süreç listesi boş olmalıdır (before=[])")
                            if close_status != "KAPANDI":
                                contradictions.append(f"Kapalı başlangıçta sürecin KAPANDI durumu doğrulanamadı (durum: '{close_status}')")
                            if close_info.get("method") != "CloseMainWindow":
                                contradictions.append(f"Kapatma yöntemi CloseMainWindow değil: '{close_info.get('method')}'")
                            if close_info.get("exited") is not True:
                                contradictions.append("Sürecin kapandığı (exited=True) teyit edilemedi")
                            if close_info.get("request_sent") is not True:
                                contradictions.append("Kapalı başlangıçta kapatma isteği gönderildiği (request_sent=True) teyit edilemedi")
                        elif expected_branch == "Existing":
                            if owned is not False:
                                contradictions.append(f"Önceden açık uygulamada (Existing) süreç sahiplenilemez (owned=False bekleniyor, bulunan: {owned})")
                            if close_status != "ACIK_BIRAKILDI":
                                contradictions.append(f"Önceden açık uygulamada close.status 'ACIK_BIRAKILDI' olmalıdır (durum: '{close_status}')")
                            if close_info.get("request_sent") is not False:
                                contradictions.append("Önceden açık uygulamada kapatma isteği gönderilmemelidir (request_sent=False olmalıdır)")
                            if close_info.get("still_running") is not True:
                                contradictions.append("Önceden açık uygulamanın çalışmaya devam ettiği (still_running=True) teyit edilemedi")

                    # Yaşam döngüsü günlüğü (yasam-adimlari.json) kontrolü
                    lj_ref = link_data.get("lifecycle_journal") if link_data else None
                    lj_path = resolve_linked_path(folder, lj_ref, root) if lj_ref else (life_path.parent / "yasam-adimlari.json")
                    if not lj_path or not lj_path.is_file():
                        missing_evidence.append("Yaşam döngüsü günlüğü dosyası (yasam-adimlari.json) bulunamadı")
                    else:
                        try:
                            raw_lj = lj_path.read_text(encoding="utf-8").strip()
                            if not raw_lj or raw_lj == "{}":
                                missing_evidence.append("Yaşam döngüsü günlüğü (yasam-adimlari.json) dosyası boş ({})")
                            else:
                                lj_json = json.loads(raw_lj)
                                if life_obs is not None and lj_json != life_obs:
                                    contradictions.append("Yaşam döngüsü günlüğü (yasam-adimlari.json) ile sonuc.json gözlemi çelişiyor.")
                        except Exception as exc:
                            contradictions.append(f"Yaşam döngüsü günlüğü okuma hatası: {exc}")

        except Exception as exc:
            contradictions.append(f"Yaşam döngüsü raporu okuma hatası: {exc}")
    else:
        l_stat = link_data.get("status") if link_data else None
        if xml_result not in ("ATLANDI", "HATA") and l_stat not in ("ATLANDI", "HATA"):
            missing_evidence.append(f"Bağlı yaşam döngüsü raporu bulunamadı: {link_data.get('lifecycle_report') if link_data else 'kayıt yok'}")

    # Günlük dosyalarını bağlantılara ekle
    if link_data and link_data.get("ui_journal"):
        uij_path = resolve_linked_path(folder, link_data["ui_journal"], root)
        if uij_path:
            info["links"].append({"name": "uia-adimlari.json", "path": uij_path, "desc": "UIA işlem günlüğü", "exists": uij_path.exists()})

    if link_data and link_data.get("lifecycle_journal"):
        lj_path = resolve_linked_path(folder, link_data["lifecycle_journal"], root)
        if lj_path:
            info["links"].append({"name": "yasam-adimlari.json", "path": lj_path, "desc": "Süreç adımları günlüğü", "exists": lj_path.exists()})

    # --- 5. Çapraz Kaynak Çelişki ve Tutarlılık Değerlendirmesi ---

    # UI vs XML tutarlılığı: UI başarısız iken XML PASS diyemez!
    if ui_data and ui_result in ("HATA", "KALDI") and xml_result == "GECTI":
        contradictions.append(f"UI test sonucu '{ui_result}' iken pytest XML test sonucu 'GECTI' (çelişki).")
    if ui_data and ui_result == "GECTI" and xml_result in ("HATA", "KALDI", "ATLANDI"):
        contradictions.append(f"UI test sonucu 'GECTI' iken pytest XML test sonucu '{xml_result}' (çelişki).")

    # Yaşam döngüsü vs XML/UI tutarlılığı: Yaşam döngüsü başarısız iken test GECTI diyemez!
    if life_data and life_result in ("HATA", "KALDI") and (xml_result == "GECTI" or ui_result == "GECTI"):
        contradictions.append(f"Yaşam döngüsü sonucu '{life_result}' iken test sonucu 'GECTI' (çelişki).")

    # XML skipped iken UI veya yaşam döngüsü çalışıp GECTI diyemez!
    if xml_result == "ATLANDI":
        if ui_data and ui_result == "GECTI":
            contradictions.append("pytest XML testin atlandığını (skipped) gösterirken UI raporu GECTI çalıştırma kanıtı içeriyor.")
        if life_data and life_result == "GECTI":
            contradictions.append("pytest XML testin atlandığını (skipped) gösterirken yaşam döngüsü GECTI çalıştırma kanıtı içeriyor.")

    # Link status / exit_code vs XML/UI tutarlılığı
    l_stat = link_data.get("status") if link_data else None
    l_exit = link_data.get("exit_code", 0) if link_data else 0
    l_err = link_data.get("error") if link_data else None

    life_test = (life_obs or {}).get("test") if life_obs else None
    life_test_result = life_test.get("status") if isinstance(life_test, dict) else None
    life_test_exit = life_test.get("exit_code") if isinstance(life_test, dict) else None

    if (l_stat in ("HATA", "KALDI") or l_exit != 0) and (xml_result == "GECTI" or ui_result == "GECTI"):
        contradictions.append(f"pytest-link durumu {l_stat} (exit={l_exit}) iken test sonucu GECTI olamaz.")
    if l_stat == "DOGRULANDI" and (
        xml_result in ("HATA", "KALDI")
        or (ui_data and ui_result in ("HATA", "KALDI"))
        or (life_data and life_result in ("HATA", "KALDI"))
        or (isinstance(life_test, dict) and (life_test_exit != 0 or life_test_result in ("HATA", "KALDI")))
    ):
        contradictions.append("pytest-link durumu 'DOGRULANDI' fakat test sonucu başarısız.")
    if (ui_result == "GECTI" or (life_data and life_result == "GECTI") or l_stat == "DOGRULANDI") and not isinstance(life_test, dict):
        missing_evidence.append("Yaşam döngüsü alt test kaydı (observed.test) eksik.")
    if (ui_result == "GECTI" or (life_data and life_result == "GECTI")) and (isinstance(life_test, dict) and (life_test_exit != 0 or life_test_result in ("HATA", "KALDI"))):
        contradictions.append(f"Alt test başarısız (çıkış kodu={life_test_exit}, durum='{life_test_result}') iken test sonucu GECTI olamaz.")

    # UI veya yaşam döngüsünde hata alanları doluyken GECTI veya DOGRULANDI olunamaz!
    has_any_error = bool(
        ui_hata or
        (obs and (obs.get("error") or obs.get("cleanup_error") or obs.get("cleanup_journal_error"))) or
        (life_data and (life_data.get("error") or life_data.get("cleanup_uncertain") or (life_obs and (life_obs.get("error") or life_obs.get("cleanup_error") or (life_obs.get("close") or {}).get("error")))))
    )
    if has_any_error and (xml_result == "GECTI" or ui_result == "GECTI" or (life_data and life_result == "GECTI") or l_stat == "DOGRULANDI"):
        contradictions.append("Hata veya temizleme hatası mevcutken başarılı test sonucu (GECTI) gösterilemez.")

    # Kayıtlı sonuç belirleme:
    # Pytest XML failure (KALDI) otomasyon hatasından (pytest.fail) kaynaklanıyorsa HATA korunmalı!
    if xml_result == "ATLANDI" or l_stat == "ATLANDI":
        recorded_result = "ATLANDI"
    elif (
        ui_result == "HATA"
        or (life_data and life_result == "HATA")
        or l_stat == "HATA"
        or l_err
        or has_any_error
        or xml_result == "HATA"
        or (life_data and not isinstance(life_test, dict))
        or (isinstance(life_test, dict) and (life_test_exit != 0 or life_test_result == "HATA"))
    ):
        recorded_result = "HATA"
    elif (
        ui_result == "KALDI"
        or xml_result == "KALDI"
        or (life_data and life_result == "KALDI")
        or l_stat == "KALDI"
        or (isinstance(life_test, dict) and life_test_result == "KALDI")
    ):
        recorded_result = "KALDI"
    elif (
        xml_result == "GECTI"
        and ui_result == "GECTI"
        and (life_result == "GECTI" or life_result is None)
        and l_stat == "DOGRULANDI"
        and isinstance(life_test, dict)
        and life_test_result == "GECTI"
        and life_test_exit == 0
    ):
        recorded_result = "GECTI"
    else:
        recorded_result = ui_result or (life_result if life_data else None) or xml_result or "BILINMIYOR"

    info["recorded_result"] = recorded_result

    # Kaynak bazında sonuçlar
    info["source_results"] = {
        "xml": xml_result or "-",
        "link": l_stat or "-",
        "ui": ui_result or "-",
        "lifecycle": life_result or "-",
    }

    # Eğer kaydedilmiş sonuç GECTI ise, TÜM GECTI gereksinimleri eksiksiz sağlanmalıdır:
    if recorded_result == "GECTI":
        if l_stat != "DOGRULANDI":
            contradictions.append(f"Başarılı koşuda köprü durumu 'DOGRULANDI' olmalıdır (bulunan: '{l_stat}')")
        if link_pid is None:
            missing_evidence.append("Başarılı koşuda köprü process_id eksik.")
        v_lticks, err_lticks = check_ticks_validity(link_data.get("process_start_ticks") if link_data else None)
        if not v_lticks:
            missing_evidence.append(f"Başarılı koşuda köprü {err_lticks}")
        exp_states = link_data.get("expected_states") if link_data else None
        obs_states = link_data.get("observed_states") if link_data else None
        if not exp_states or not isinstance(exp_states, list) or len(exp_states) != 3:
            missing_evidence.append("Başarılı koşuda köprü beklenen durumlar (expected_states) eksik veya geçersiz")
        if not obs_states or not isinstance(obs_states, list) or len(obs_states) != 3:
            missing_evidence.append("Başarılı koşuda köprü gözlemlenen durumlar (observed_states) eksik veya geçersiz")
        if exp_states and obs_states and exp_states != obs_states:
            contradictions.append(f"Başarılı koşuda beklenen durumlar ({exp_states}) gözlemlenen durumlarla ({obs_states}) uyuşmalıdır.")

        if not ui_data:
            missing_evidence.append("GECTI koşusu için UI raporu bulunamadı.")
        else:
            if ui_result != "GECTI":
                contradictions.append(f"GECTI koşusunda UI test_sonucu GECTI değil: '{ui_result}'")
            ui_obs = obs or {}
            if ui_obs.get("schema_version") != 1:
                contradictions.append(f"Başarılı koşuda UI şema sürümü 1 olmalıdır (bulunan: {ui_obs.get('schema_version')})")
            if ui_obs.get("mode") != "Exercise":
                contradictions.append(f"Başarılı koşuda UI modu 'Exercise' olmalıdır (bulunan: '{ui_obs.get('mode')}')")
            if ui_obs.get("phase") != "completed":
                contradictions.append(f"Başarılı koşuda UI aşaması 'completed' olmalıdır (bulunan: '{ui_obs.get('phase')}')")
            if ui_obs.get("mutation_attempted") is not True:
                contradictions.append("Başarılı koşuda mutation_attempted=True olmalıdır")
            if ui_obs.get("cleanup_attempted") is not True:
                contradictions.append("Başarılı koşuda cleanup_attempted=True olmalıdır")
            if ui_obs.get("changed_verified") is not True:
                contradictions.append("Başarılı koşuda changed_verified=True olmalıdır")
            if ui_obs.get("restored") is not True:
                contradictions.append("Başarılı koşuda restored=True olmalıdır")

            init = ui_obs.get("initial")
            chg = ui_obs.get("changed")
            fnl = ui_obs.get("final")
            exp_chg = ui_obs.get("expected_changed")

            if init is None or init not in ("Off", "On"):
                contradictions.append(f"Geçersiz UI başlangıç durumu: '{init}'")
            if chg is None or chg not in ("Off", "On"):
                contradictions.append(f"Geçersiz UI değişen durumu: '{chg}'")
            if fnl is None or fnl not in ("Off", "On"):
                contradictions.append(f"Geçersiz UI bitiş durumu: '{fnl}'")

            if init is not None and chg is not None and init == chg:
                contradictions.append(f"UI kutu değeri karşıt duruma geçmedi (başlangıç: {init}, değişim: {chg})")
            if exp_chg is not None and chg != exp_chg:
                contradictions.append(f"UI değişen değeri beklenen karşıt değerle uyuşmuyor (beklenen: {exp_chg}, gerçekleşen: {chg})")
            if init is not None and fnl is not None and init != fnl:
                contradictions.append(f"UI kutu değeri başlangıç durumuna dönmedi (başlangıç: {init}, son: {fnl})")
            if not info["guard_start_idle"] or not info["guard_end_idle"]:
                contradictions.append("Start butonu başlangıçta veya bitişte boşta/pasif değil")

        if not life_data:
            missing_evidence.append("GECTI koşusu için yaşam döngüsü raporu bulunamadı.")
        else:
            if life_data.get("result") != "GECTI":
                contradictions.append(f"Yaşam döngüsü sonucu GECTI değil: '{life_data.get('result')}'")
            if life_data.get("exit_code") != 0:
                contradictions.append(f"Yaşam döngüsü çıkış kodu 0 değil: {life_data.get('exit_code')}")

            # Alt test (observed.test) kontrolü: varlığı, sonucu, çıkış kodu ve kimliği eksiksiz olmalı
            life_test = (life_data.get("observed") or {}).get("test")
            if not life_test or not isinstance(life_test, dict):
                missing_evidence.append("Başarılı koşuda yaşam döngüsü alt test (observed.test) kaydı eksik.")
            else:
                if life_test.get("status") != "GECTI":
                    contradictions.append(f"Başarılı koşuda alt test sonucu GECTI değil: '{life_test.get('status')}'")
                if life_test.get("exit_code") != 0:
                    contradictions.append(f"Başarılı koşuda alt test çıkış kodu sıfır değil: {life_test.get('exit_code')}")
                alt_identity = life_test.get("observed_identity")
                if not alt_identity or not isinstance(alt_identity, dict):
                    missing_evidence.append("Alt testte gözlemlenen süreç kimliği (observed_identity) eksik.")
                else:
                    alt_pid = alt_identity.get("pid")
                    alt_ticks = str(alt_identity.get("start_ticks", ""))
                    if alt_pid is None or (life_pid is not None and alt_pid != life_pid):
                        contradictions.append(f"Alt test PID'si ({alt_pid}) hedef süreç PID'sinden ({life_pid}) farklı.")
                    v_aticks, err_aticks = check_ticks_validity(alt_ticks)
                    if not v_aticks:
                        missing_evidence.append(f"Alt test {err_aticks}")
                    elif life_ticks and alt_ticks != life_ticks:
                        contradictions.append("Alt test start_ticks değeri hedef süreç start_ticks ile uyuşmuyor.")

    # --- 6. Nihai Doğrulama Durumu ve Rozet ---
    all_reasons = contradictions + missing_evidence
    info["reasons"] = all_reasons
    info["verification_reasons"] = all_reasons

    if all_reasons:
        info["verification_status"] = "DOGRULANAMADI"
        info["badge_text"] = "KANIT DOĞRULANAMADI"
        info["badge_class"] = "fail"
    else:
        info["verification_status"] = "DOGRULANDI"
        if recorded_result == "GECTI":
            info["badge_text"] = "GECTI (DOĞRULANDI)"
            info["badge_class"] = "pass"
        elif recorded_result == "KALDI":
            info["badge_text"] = "KALDI (DOĞRULANDI)"
            info["badge_class"] = "fail"
        elif recorded_result == "ATLANDI":
            info["badge_text"] = "ATLANDI (DOĞRULANDI)"
            info["badge_class"] = "warn"
        elif recorded_result == "HATA":
            info["badge_text"] = "HATA (DOĞRULANDI)"
            info["badge_class"] = "fail"
        else:
            info["badge_text"] = f"{recorded_result} (DOĞRULANDI)"
            info["badge_class"] = "warn"

    return info

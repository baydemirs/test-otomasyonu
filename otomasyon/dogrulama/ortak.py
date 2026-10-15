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
                info["test_id"] = link_data.get("test_id", info["test_id"])
                branch_in_link = link_data.get("expected_branch")
                if branch_in_link:
                    info["branch"] = branch_in_link
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

                # Link çıkış kodu ve status tutarlılığı
                if link_status == "DOGRULANDI" and exit_code != 0:
                    contradictions.append(f"pytest-link status 'DOGRULANDI' fakat exit_code={exit_code}")
                if link_status == "DOGRULANDI" and link_data.get("error"):
                    contradictions.append(f"pytest-link status 'DOGRULANDI' fakat error alanı dolu: '{link_data.get('error')}'")
                if exit_code != 0 and link_status == "DOGRULANDI":
                    contradictions.append(f"pytest çıkış kodu {exit_code} iken köprü durumu DOGRULANDI olamaz")

                exp_states = link_data.get("expected_states") or []
                obs_states = link_data.get("observed_states") or []
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
                ui_hata = ui_data.get("hata") or ui_data.get("error")

                # UI hata alanı dolu mu?
                if ui_hata:
                    contradictions.append(f"UI hata alanı dolu: '{ui_hata}'")

                obs = ui_data.get("gozlem")
                if not isinstance(obs, dict) or not obs:
                    missing_evidence.append("UI raporunda gozlem alanı eksik veya boş")
                else:
                    obs_error = obs.get("error")
                    obs_cleanup_error = obs.get("cleanup_error")
                    if obs_error:
                        contradictions.append(f"UI gözlem hata alanı dolu: '{obs_error}'")
                    if obs_cleanup_error:
                        contradictions.append(f"UI temizleme/geri yükleme hata alanı dolu: '{obs_cleanup_error}'")

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

        except Exception as exc:
            contradictions.append(f"UI raporu okuma hatası: {exc}")
    else:
        # Test runner seviyesinde ATLANDI veya HATA ise UI raporu olmaması normaldir
        if xml_result not in ("ATLANDI", "HATA"):
            missing_evidence.append(f"Bağlı UI raporu bulunamadı: {link_data.get('ui_report') if link_data else 'kayıt yok'}")

    # --- 4. Yaşam Döngüsü Raporu İncelemesi ---
    life_data = None
    life_result = None
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
                    life_pid = life_obs.get("identity", {}).get("pid")
                    life_ticks = str(life_obs.get("identity", {}).get("start_ticks", ""))
                    if link_pid is not None and life_pid != link_pid:
                        contradictions.append(f"Yaşam döngüsü PID'si köprü PID'sinden farklı (Yaşam: {life_pid}, Köprü: {link_pid})")
                    if link_ticks and life_ticks and life_ticks != link_ticks:
                        contradictions.append("Yaşam döngüsü start_ticks değeri köprü ile uyuşmuyor")

                    close_info = life_obs.get("close") or {}
                    close_status = close_info.get("status")
                    info["close_status"] = str(close_status if close_status is not None else "-")

                    life_err = life_data.get("error") or life_obs.get("error") or close_info.get("error")
                    if life_err:
                        contradictions.append(f"Yaşam döngüsü hata alanı dolu: '{life_err}'")

                    if close_status not in ("KAPANDI", "ACIK_BIRAKILDI"):
                        contradictions.append(f"Yaşam döngüsü kapanış durumu geçersiz: '{close_status}'")
                    if close_info.get("exited") is False and close_info.get("still_running") is not True:
                        contradictions.append(f"Süreç kapanışı başarısız (exited=False ve still_running={close_info.get('still_running')})")

        except Exception as exc:
            contradictions.append(f"Yaşam döngüsü raporu okuma hatası: {exc}")
    else:
        if xml_result not in ("ATLANDI", "HATA"):
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

    # REGRESYON 4: XML skipped iken UI veya yaşam döngüsü çalışıp GECTI diyemez!
    if xml_result == "ATLANDI":
        if ui_data and ui_result == "GECTI":
            contradictions.append("pytest XML testin atlandığını (skipped) gösterirken UI raporu GECTI çalıştırma kanıtı içeriyor.")
        if life_data and life_result == "GECTI":
            contradictions.append("pytest XML testin atlandığını (skipped) gösterirken yaşam döngüsü GECTI çalıştırma kanıtı içeriyor.")

    # REGRESYON 1: Link status=HATA/KALDI veya exit_code!=0 iken test GECTI olunamaz!
    if link_data:
        l_stat = link_data.get("status")
        l_exit = link_data.get("exit_code", 0)
        if (l_stat in ("HATA", "KALDI") or l_exit != 0) and (xml_result == "GECTI" or ui_result == "GECTI"):
            contradictions.append(f"pytest-link durumu {l_stat} (exit={l_exit}) iken test sonucu GECTI olamaz.")
        if l_stat == "DOGRULANDI" and xml_result in ("HATA", "KALDI"):
            contradictions.append(f"pytest-link durumu 'DOGRULANDI' fakat test sonucu '{xml_result}'.")

    # REGRESYON 2 & 3: UI veya yaşam döngüsünde hata alanları doluyken GECTI olunamaz!
    has_any_error = bool(
        ui_hata or
        (ui_data and isinstance(ui_data.get("gozlem"), dict) and (ui_data["gozlem"].get("error") or ui_data["gozlem"].get("cleanup_error"))) or
        (life_data and (life_data.get("error") or (isinstance(life_data.get("observed"), dict) and (life_data["observed"].get("error") or (life_data["observed"].get("close") or {}).get("error")))))
    )
    if has_any_error and (xml_result == "GECTI" or ui_result == "GECTI"):
        contradictions.append("Hata veya temizleme hatası mevcutken başarılı test sonucu (GECTI) gösterilemez.")

    # Kayıtlı sonuç belirleme
    if xml_result == "ATLANDI":
        recorded_result = "ATLANDI"
    elif ui_result == "KALDI" or xml_result == "KALDI" or (life_data and life_result == "KALDI"):
        recorded_result = "KALDI"
    elif ui_result == "HATA" or (link_data and (link_data.get("status") == "HATA" or link_data.get("exit_code", 0) != 0)) or has_any_error or xml_result == "HATA":
        recorded_result = "HATA"
    elif xml_result == "GECTI" and ui_result == "GECTI" and life_result == "GECTI":
        recorded_result = "GECTI"
    else:
        # Çelişkili veya beklenmeyen durum: XML'e geri dönüp doğrulanmış başarı gösterme!
        if ui_result:
            recorded_result = ui_result
        elif life_result:
            recorded_result = life_result
        else:
            recorded_result = xml_result or "BILINMIYOR"

    info["recorded_result"] = recorded_result

    # Kaynak bazında sonuçlar
    info["source_results"] = {
        "xml": xml_result or "-",
        "link": (link_data.get("status") if link_data else None) or "-",
        "ui": ui_result or "-",
        "lifecycle": life_result or "-",
    }

    # Eğer kaydedilmiş sonuç GECTI ise, TÜM GECTI gereksinimleri eksiksiz sağlanmalıdır:
    if recorded_result == "GECTI":
        if not ui_data:
            missing_evidence.append("GECTI koşusu için UI raporu bulunamadı.")
        else:
            if ui_result != "GECTI":
                contradictions.append(f"GECTI koşusunda UI test_sonucu GECTI değil: '{ui_result}'")
            obs = ui_data.get("gozlem") or {}
            init = obs.get("initial")
            chg = obs.get("changed")
            fnl = obs.get("final")
            exp_chg = obs.get("expected_changed")
            rest = obs.get("restored")

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
            if not rest:
                contradictions.append("UI kutusunun geri yüklendiği doğrulanmadı (restored=False)")
            if not info["guard_start_idle"] or not info["guard_end_idle"]:
                contradictions.append("Start butonu başlangıçta veya bitişte boşta/pasif değil")

        if not life_data:
            missing_evidence.append("GECTI koşusu için yaşam döngüsü raporu bulunamadı.")
        else:
            if life_data.get("result") != "GECTI":
                contradictions.append(f"Yaşam döngüsü sonucu GECTI değil: '{life_data.get('result')}'")
            if life_data.get("exit_code") != 0:
                contradictions.append(f"Yaşam döngüsü çıkış kodu 0 değil: {life_data.get('exit_code')}")

            expected_branch = info["branch"]
            close_info = (life_data.get("observed") or {}).get("close") or {}
            c_stat = close_info.get("status")
            if expected_branch not in ("Existing", "Closed"):
                contradictions.append(f"Geçersiz başlangıç modu: '{expected_branch}'")
            elif expected_branch == "Closed":
                if c_stat != "KAPANDI":
                    contradictions.append(f"Kapalı başlangıçta sürecin KAPANDI durumu doğrulanamadı (durum: '{c_stat}')")
                if close_info.get("method") != "CloseMainWindow":
                    contradictions.append(f"Kapatma yöntemi CloseMainWindow değil: '{close_info.get('method')}'")
                if close_info.get("exited") is not True:
                    contradictions.append("Sürecin kapandığı (exited=True) teyit edilemedi")
            elif expected_branch == "Existing":
                if c_stat != "ACIK_BIRAKILDI":
                    contradictions.append(f"Açık başlangıçta sürecin ACIK_BIRAKILDI durumu doğrulanamadı (durum: '{c_stat}')")
                if close_info.get("still_running") is not True:
                    contradictions.append("Önceden açık sürecin çalışmaya devam ettiği (still_running=True) teyit edilemedi")

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

"""
Unitalk web-interface Selenium parser.

URL: https://my.unitalk.cloud
Верифіковано через реальний DOM-інспектинг 2026-03-19.

Алгоритм:
  1. Логін на https://my.unitalk.cloud/enter.html#auth
  2. Перехід на /calls/call-history
  3. Застосування фільтру дат (сьогодні або весь діапазон)
  4. Для кожного рядка з активною кнопкою "Voice analytics":
     - Витягуємо from_number / to_number / time з TD
     - Клікаємо Voice analytics → чекаємо модалку
     - Клікаємо "Show all" → витягуємо всі поля через JS
  5. Повертаємо список CallAnalyticData
"""
from __future__ import annotations

import os
import re
import time
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from core.logging import get_logger

try:
    from pyvirtualdisplay import Display as _VirtualDisplay
    _HAS_PYVD = True
except ImportError:
    _HAS_PYVD = False

logger = get_logger(__name__)

# ── Константи сайту ────────────────────────────────────────────────────────────

BASE_URL   = "https://my.unitalk.cloud"
LOGIN_PATH = "/enter.html#auth"
HISTORY_PATH = "/calls/call-history"

# Назви секцій аналітики (мовою Unitalk) → поля БД
# Увага: Unitalk використовує латинську "i" замість кириличної "і" у деяких словах!
SECTION_FIELD_MAP: Dict[str, str] = {
    "Тема":             "conversation_topic",         # "Тема дiалогу"
    "Ключовi моменти":  "key_points_of_the_dialogue", # "Ключовi моменти дiалогу"
    "Подальшi":         "next_steps",                 # "Подальшi кроки"
    "Помилки":          "operator_errors",            # "Помилки оператора"
    "Ключовi слова":    "keywords",                   # "Ключовi слова"
    "Слова-паразити":   "badwords",                   # "Слова-паразити"
    "Чи потр":          "attention_to_the_call",      # "Чи потрiбно звернути увагу..."
    "Аналiз настрою к": "clients_mood",               # "Аналiз настрою клієнта"
    "Аналіз настрою к": "clients_mood",               # варіант з кириличною і
    "Аналiз настрою о": "operators_mood",             # "Аналiз настрою оператора"
    "Аналіз настрою о": "operators_mood",
    "Аналiз настрою":   "clients_mood",               # загальний настрій (fallback)
    "Аналіз настрою":   "clients_mood",
    "Загальна вдовол":  "customer_satisfaction",      # "Загальна вдоволенiсть клiєнта"
    "Рiвень емпат":     "empathy",                    # "Рiвень емпатiї"
    "Яснiсть":          "clarity_of_communication",   # "Яснiсть спiлкування"
    "Iдентифiк":        "problem_identification",     # "Iдентифiкацiя проблеми"
    "Рiвень залучен":   "involvement",                # "Рiвень залученостi"
    "Здатнiсть":        "ability_to_adapt",           # "Здатнiсть адаптуватися"
    "Ефективнiсть":     "problem_solving_efficiency", # "Ефективнiсть вирiшення проблеми"
    "Професiоналiзм":   "operator_professionalism",  # "Професiоналiзм оператора"
}

# JS що витягує всю аналітику з відкритого модального вікна одним викликом.
# ВАЖЛИВО: скрипт має починатись з "return" — інакше execute_script поверне None.
_JS_EXTRACT_ANALYTICS = """
try {
    var allH6 = Array.prototype.slice.call(document.querySelectorAll('h6'));
    var metricsH6 = null;
    for (var _i = 0; _i < allH6.length; _i++) {
        if (allH6[_i].textContent.trim() === 'Analytics metrics') {
            metricsH6 = allH6[_i];
            break;
        }
    }
    if (!metricsH6) return {_error: 'no_analytics_header'};

    var headerBox = metricsH6.parentElement;
    var depth = 0;
    while (headerBox && headerBox.children.length < 2 && depth < 15) {
        headerBox = headerBox.parentElement;
        depth++;
    }
    if (!headerBox) return {_error: 'no_header_box'};

    var sectionsContainer = headerBox.nextElementSibling;
    if (!sectionsContainer) return {_error: 'no_sections_container'};

    var result = {_ok: true};
    var sections = Array.prototype.slice.call(sectionsContainer.children);
    for (var _s = 0; _s < sections.length; _s++) {
        var section = sections[_s];
        var h6el = section.querySelector('h6');
        if (!h6el) continue;
        var title = h6el.textContent.trim();
        var fullText = section.textContent.trim();
        var idx = fullText.indexOf(title);
        var content = idx >= 0 ? fullText.slice(idx + title.length).trim() : '';
        if (content) result['__sec__' + title] = content;
    }
    return result;
} catch(e) {
    return {_error: 'js_exception', _msg: String(e)};
}
"""

# JS що витягує from/to/time з рядка таблиці по його DOM-індексу
_JS_EXTRACT_ROW = """
(function(rowIndex) {
  const rows = [...document.querySelectorAll('tr.MuiTableRow-hover')];
  const row = rows[rowIndex];
  if (!row) return null;
  const tds = [...row.querySelectorAll('td')];
  const getText = i => tds[i]?.textContent?.trim() || '';
  const extractPhone = t => {
    const m = t.match(/\\+?\\d{10,13}/);
    return m ? m[0].replace('+','') : '';
  };
  return {
    callerRaw: getText(1),
    sourceRaw: getText(2),
    timeRaw:   getText(10),           // "15:25:50Today" або "15:25:50Вчора" тощо
    fromPhone: extractPhone(getText(1)),
    toPhone:   extractPhone(getText(2)),
    hasAnalytics: !row.querySelector('[aria-label="Voice analytics"].Mui-disabled'),
    analyticsEnabled: !!row.querySelector('[aria-label="Voice analytics"]:not(.Mui-disabled)'),
  };
})(arguments[0])
"""


# ── Data classes ───────────────────────────────────────────────────────────────

@dataclass
class CallAnalyticData:
    """Один результат парсингу: ідентифікатори + аналітичні поля."""
    from_number: str = ""
    to_number: str = ""
    call_date: Optional[str] = None   # "YYYY-MM-DD" або "today"

    # Аналітичні поля (назви відповідають CallAiAnalytic у БД)
    conversation_topic: Optional[str] = None
    key_points_of_the_dialogue: Optional[str] = None
    next_steps: Optional[str] = None
    operator_errors: Optional[str] = None
    keywords: Optional[str] = None
    badwords: Optional[str] = None
    attention_to_the_call: Optional[str] = None
    clients_mood: Optional[str] = None
    operators_mood: Optional[str] = None
    customer_satisfaction: Optional[str] = None
    operator_professionalism: Optional[str] = None
    empathy: Optional[str] = None
    clarity_of_communication: Optional[str] = None
    problem_identification: Optional[str] = None
    involvement: Optional[str] = None
    ability_to_adapt: Optional[str] = None
    problem_solving_efficiency: Optional[str] = None

    parse_error: Optional[str] = None   # None = успіх


@dataclass
class ParseStats:
    total: int = 0
    success: int = 0
    skipped_no_analytics: int = 0
    errors: int = 0
    results: List[CallAnalyticData] = field(default_factory=list)


# ── Parser ─────────────────────────────────────────────────────────────────────

class UnitalkParser:
    """
    Selenium-парсер для my.unitalk.cloud.

    Використання:
        parser = UnitalkParser(username=..., password=...)
        try:
            parser.login()
            stats = parser.get_analytics(today=True)
        finally:
            parser.quit()
    """

    def __init__(
        self,
        username: str,
        password: str,
        headless: bool = True,
        page_load_timeout: int = 30,
        element_wait_timeout: int = 15,
    ) -> None:
        self.username = username
        self.password = password
        self.headless = headless
        self.page_load_timeout = page_load_timeout
        self.wait_timeout = element_wait_timeout
        self._driver: Optional[webdriver.Chrome] = None
        self._vdisplay = None  # pyvirtualdisplay.Display instance (non-headless Docker)

    # ── Driver ─────────────────────────────────────────────────────────────────

    @staticmethod
    def _display_is_usable() -> bool:
        """Повертає True тільки якщо DISPLAY вказує на справжній X11-сервер."""
        display = os.environ.get("DISPLAY", "")
        if not display:
            return False
        try:
            import subprocess
            result = subprocess.run(
                ["xdpyinfo", "-display", display],
                capture_output=True, timeout=2,
            )
            return result.returncode == 0
        except Exception:
            return False

    def _ensure_display(self) -> None:
        """
        Якщо headless=False і реального X11 немає — запускає Xvfb через
        pyvirtualdisplay, щоб Chrome міг відкрити вікно без фізичного монітора.

        Важливо: перевіряємо реальну доступність дисплею через xdpyinfo,
        бо в Docker DISPLAY може бути встановлений (напр. :0) але неробочим.
        """
        if self.headless:
            return
        if self._vdisplay is not None:
            return  # вже запущений
        if self._display_is_usable():
            logger.info("unitalk_parser.display.real_x11_found",
                        display=os.environ.get("DISPLAY"))
            return
        if not _HAS_PYVD:
            logger.warning("unitalk_parser.display.pyvirtualdisplay_missing",
                           hint="pip install pyvirtualdisplay + apt install xvfb")
            return
        try:
            self._vdisplay = _VirtualDisplay(visible=False, size=(1920, 1080), color_depth=24)
            self._vdisplay.start()
            logger.info("unitalk_parser.display.xvfb_started",
                        display=os.environ.get("DISPLAY", "unknown"))
        except Exception as exc:
            logger.warning("unitalk_parser.display.xvfb_failed", error=str(exc))
            self._vdisplay = None

    def _build_driver(self) -> webdriver.Chrome:
        options = Options()
        if self.headless:
            options.add_argument("--headless=new")

        # ── Обов'язково для Docker (будь-який режим) ────────────────────────────
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-setuid-sandbox")
        options.add_argument("--disable-dev-shm-usage")   # уникаємо OOM в /dev/shm
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-software-rasterizer")
        options.add_argument("--window-size=1920,1080")

        # ── Стабільність (НЕ використовуємо --single-process: він викликає SIGSEGV
        #    в Chromium 120+ і є офіційно deprecated) ────────────────────────────
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-background-networking")
        options.add_argument("--disable-background-timer-throttling")
        options.add_argument("--disable-backgrounding-occluded-windows")
        options.add_argument("--disable-renderer-backgrounding")
        options.add_argument("--disable-ipc-flooding-protection")
        options.add_argument("--disable-hang-monitor")
        options.add_argument("--disable-prompt-on-repost")
        options.add_argument("--metrics-recording-only")
        options.add_argument("--no-first-run")
        options.add_argument("--safebrowsing-disable-auto-update")

        # ── Anti-bot (тільки в non-headless, в headless → несумісно з деякими версіями)
        if not self.headless:
            options.add_argument("--disable-blink-features=AutomationControlled")
            try:
                options.add_experimental_option("excludeSwitches", ["enable-automation"])
                options.add_experimental_option("useAutomationExtension", False)
            except Exception:
                pass

        chrome_binary = os.getenv("CHROME_BINARY", "")
        chromedriver_path = os.getenv("CHROMEDRIVER_PATH", "")

        if chrome_binary:
            options.binary_location = chrome_binary

        if chromedriver_path:
            service = ChromeService(executable_path=chromedriver_path)
        else:
            try:
                from webdriver_manager.chrome import ChromeDriverManager
                service = ChromeService(ChromeDriverManager().install())
            except ImportError:
                service = ChromeService()

        driver = webdriver.Chrome(service=service, options=options)
        driver.set_page_load_timeout(self.page_load_timeout)
        try:
            driver.execute_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )
        except Exception:
            pass
        return driver

    def _driver_js(self, script: str, *args):
        return self._driver.execute_script(script, *args)

    def quit(self) -> None:
        if self._driver:
            try:
                self._driver.quit()
            except Exception:
                pass
            self._driver = None
        if self._vdisplay is not None:
            try:
                self._vdisplay.stop()
            except Exception:
                pass
            self._vdisplay = None

    def _screenshot(self, name: str) -> None:
        try:
            path = f"/tmp/unitalk_{name}_{int(time.time())}.png"
            self._driver.save_screenshot(path)
            logger.info("unitalk_parser.screenshot", path=path)
        except Exception:
            pass

    # ── Login ──────────────────────────────────────────────────────────────────

    def login(self) -> None:
        """Авторизується на my.unitalk.cloud."""
        if self._driver is None:
            self._ensure_display()
            self._driver = self._build_driver()

        logger.info("unitalk_parser.login.start")
        self._driver.get(BASE_URL + LOGIN_PATH)
        time.sleep(2)

        # Якщо вже залогінено — редіректить на /calls/call-history
        if HISTORY_PATH in self._driver.current_url:
            logger.info("unitalk_parser.login.already_authenticated")
            return

        # Заповнюємо форму
        try:
            email_inp = WebDriverWait(self._driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']"))
            )
            email_inp.clear()
            email_inp.send_keys(self.username)

            pwd_inp = self._driver.find_element(By.CSS_SELECTOR, "input[type='password']")
            pwd_inp.clear()
            pwd_inp.send_keys(self.password)

            # Submit button — шукаємо по тексту або type=submit
            submit = None
            for sel in ["button[type='submit']", "input[type='submit']", "button.btn"]:
                els = self._driver.find_elements(By.CSS_SELECTOR, sel)
                if els:
                    submit = els[0]
                    break
            if submit is None:
                # Fallback: перша кнопка на сторінці
                submit = self._driver.find_element(By.TAG_NAME, "button")

            self._driver.execute_script("arguments[0].click();", submit)
        except Exception as exc:
            self._screenshot("login_form_error")
            raise RuntimeError(f"Не вдалось заповнити форму логіну: {exc}")

        # Чекаємо редіректу на call-history
        try:
            WebDriverWait(self._driver, 20).until(
                EC.url_contains(HISTORY_PATH)
            )
            logger.info("unitalk_parser.login.success")
        except TimeoutException:
            self._screenshot("login_failed")
            raise RuntimeError(
                f"Логін не вдався. Сторінка: {self._driver.current_url}. "
                "Перевір credentials або chекни скриншот у /tmp/"
            )

    # ── Navigate & filter ──────────────────────────────────────────────────────

    def _go_to_history(self) -> None:
        if HISTORY_PATH not in self._driver.current_url:
            self._driver.get(BASE_URL + HISTORY_PATH)
            time.sleep(3)

    def _click_all_tab(self) -> None:
        """Клікає вкладку 'All' щоб показувати всі типи дзвінків."""
        from selenium.webdriver.common.action_chains import ActionChains
        tabs = self._driver.find_elements(By.CSS_SELECTOR, '[role="tab"]')
        all_tab = next((t for t in tabs if t.text.strip() == "All"), None)
        if all_tab:
            ActionChains(self._driver).move_to_element(all_tab).click().perform()
            time.sleep(1.5)
            logger.info("unitalk_parser.filter.all_tab_clicked")

    # Набір відомих пресетів дати (англійська + українська)
    _DATE_PRESETS = {
        "Today", "Yesterday", "This week", "Last week",
        "This month", "Last month", "This year", "Last year",
        "Last 7 days", "Last 30 days", "All time",
        # Українська
        "Сьогодні", "Вчора", "Цей тиждень", "Минулий тиждень",
        "Цей місяць", "Минулий місяць", "Цей рік", "Минулий рік",
        "Останні 7 днів", "Останні 30 днів", "Весь час",
    }

    def _set_date_filter(self, preset: str) -> bool:
        """
        Встановлює датовий фільтр через picker.
        preset: 'All time' / 'Весь час', 'Last 30 days', 'Today' тощо
        Повертає True якщо фільтр успішно застосовано.

        Структура DOM: є два Chip-елементи поруч:
          1. MuiChip-sizeMedium (outline) — "DateToday" — НЕ відкриває пікер
          2. MuiChip-sizeSmall MuiChip-colorInfo (filled) — "Today" — відкриває пікер пресетів

        ВАЖЛИВО: для відкриття picker треба Selenium .click() (не ActionChains, не JS).
        Для кліку на li пресет — ActionChains.
        """
        from selenium.webdriver.common.action_chains import ActionChains

        # Знаходимо активний period chip (сma chip що містить поточний пресет)
        chips = self._driver.find_elements(By.CSS_SELECTOR, ".MuiChip-root")
        period_chip = next(
            (c for c in chips if c.text.strip() in self._DATE_PRESETS),
            None
        )
        if not period_chip:
            logger.warning("unitalk_parser.filter.date_chip_not_found", preset=preset)
            return False

        # Selenium native .click() відкриває picker (ActionChains/JS не підходять)
        period_chip.click()
        time.sleep(1.5)

        # Чекаємо поки пікер відкриється
        picker_visible = False
        for _ in range(10):
            vis = self._driver_js(
                "var p = document.querySelector('.MuiPickersLayout-root'); "
                "return p ? window.getComputedStyle(p).visibility : null;"
            )
            if vis == "visible":
                picker_visible = True
                break
            time.sleep(0.3)

        if not picker_visible:
            logger.warning("unitalk_parser.filter.picker_not_opened", preset=preset)
            return False

        # Знаходимо li пресет і клікаємо через ActionChains
        lis = self._driver.find_elements(By.TAG_NAME, "li")
        target_li = next((li for li in lis if li.text.strip() == preset), None)
        if not target_li:
            logger.warning("unitalk_parser.filter.preset_not_found", preset=preset)
            from selenium.webdriver.common.keys import Keys
            self._driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
            return False

        ActionChains(self._driver).move_to_element(target_li).click().perform()
        time.sleep(2)

        # Перевіряємо чи фільтр застосовано
        chips_after = self._driver.find_elements(By.CSS_SELECTOR, ".MuiChip-root")
        period_chip_after = next(
            (c for c in chips_after if c.text.strip() in self._DATE_PRESETS),
            None
        )
        chip_text = (period_chip_after.text.strip() if period_chip_after else "")
        applied = chip_text == preset
        logger.info("unitalk_parser.filter.date_set", preset=preset, chip=chip_text, applied=applied)
        return applied

    def _open_picker(self) -> bool:
        """Клікає chip дати і чекає поки MuiPickersLayout стане visible."""
        chips = self._driver.find_elements(By.CSS_SELECTOR, ".MuiChip-root")
        period_chip = next(
            (c for c in chips if c.text.strip() in self._DATE_PRESETS), None
        )
        if not period_chip:
            logger.warning("unitalk_parser.filter.date_chip_not_found")
            return False

        period_chip.click()
        time.sleep(1.5)

        for _ in range(10):
            vis = self._driver_js(
                "var p = document.querySelector('.MuiPickersLayout-root'); "
                "return p ? window.getComputedStyle(p).visibility : null;"
            )
            if vis == "visible":
                return True
            time.sleep(0.3)

        logger.warning("unitalk_parser.filter.picker_not_opened")
        return False

    def _set_custom_date_range(self, from_date: str, to_date: str) -> bool:
        """
        Встановлює кастомний діапазон дат у picker.
        from_date / to_date: "YYYY-MM-DD".

        Стратегії (по порядку):
          1. Знаходить пресет "Власний"/"Custom" у списку li і клікає
          2. Шукає input[type=text] всередині picker і заповнює через React setter
          3. Заповнює посегментно (MUI v6 segmented inputs: day/month/year)
        """
        from selenium.webdriver.common.action_chains import ActionChains
        from selenium.webdriver.common.keys import Keys

        try:
            from_dt = datetime.strptime(from_date, "%Y-%m-%d")
            to_dt = datetime.strptime(to_date, "%Y-%m-%d")
        except ValueError as e:
            logger.error("unitalk_parser.filter.date_range_parse_error", error=str(e))
            return False

        if not self._open_picker():
            return False

        # ── Крок 1: якщо є пресет "Custom/Власний" — клікаємо ──────────────────
        lis = self._driver.find_elements(By.TAG_NAME, "li")
        custom_li = next(
            (li for li in lis if any(
                kw in li.text for kw in ("Custom", "Власний", "Свій", "Довільн")
            )),
            None
        )
        if custom_li:
            ActionChains(self._driver).move_to_element(custom_li).click().perform()
            time.sleep(2.5)  # чекаємо перехід від списку пресетів до date-input view
            logger.info("unitalk_parser.filter.custom_preset_clicked", text=custom_li.text.strip())

        # Формати дати для Unitalk: "DD.MM.YYYY" (укр.) або "MM/DD/YYYY" (англ.)
        from_ua = from_dt.strftime("%d.%m.%Y")
        to_ua = to_dt.strftime("%d.%m.%Y")
        from_us = from_dt.strftime("%m/%d/%Y")
        to_us = to_dt.strftime("%m/%d/%Y")

        # ── Крок 2: шукаємо text inputs у picker або на сторінці (React setter) ──
        filled = self._driver_js("""
            // Шукаємо спочатку всередині picker, потім по всій сторінці
            var picker = document.querySelector('.MuiPickersLayout-root');
            var inputs = picker
                ? Array.prototype.slice.call(picker.querySelectorAll('input[type="text"], input:not([type])'))
                : [];
            if (!inputs.length) {
                // Широкий пошук: date-range inputs можуть бути за межами MuiPickersLayout
                inputs = Array.prototype.slice.call(
                    document.querySelectorAll(
                        '.MuiDateRangePickerToolbar-root input, ' +
                        '.MuiMultiInputDateRangeField-root input, ' +
                        '.MuiDateField-root input'
                    )
                );
            }
            if (!inputs.length) return 'no_inputs';

            function setReact(inp, val) {
                var setter = Object.getOwnPropertyDescriptor(
                    window.HTMLInputElement.prototype, 'value'
                ).set;
                if (setter) {
                    setter.call(inp, val);
                    inp.dispatchEvent(new Event('input',  {bubbles: true}));
                    inp.dispatchEvent(new Event('change', {bubbles: true}));
                }
            }
            if (inputs.length >= 2) {
                setReact(inputs[0], arguments[0]);
                setReact(inputs[1], arguments[1]);
                return 'ok:2inputs';
            }
            setReact(inputs[0], arguments[0] + ' - ' + arguments[1]);
            return 'ok:1input';
        """, from_ua, to_ua)

        logger.info("unitalk_parser.filter.date_range_fill", result=filled,
                    from_date=from_ua, to_date=to_ua)

        if filled and filled.startswith("ok"):
            time.sleep(1)
            # Підтверджуємо Enter або кнопкою Apply
            confirmed = self._driver_js("""
                var picker = document.querySelector('.MuiPickersLayout-root');
                if (!picker) return null;
                var btns = Array.prototype.slice.call(picker.querySelectorAll('button'));
                var applyBtn = btns.find(function(b) {
                    var t = (b.textContent || '').trim().toLowerCase();
                    return t === 'apply' || t === 'застосувати' || t === 'ok' || t === 'підтвердити';
                });
                if (applyBtn) { applyBtn.click(); return 'apply_btn'; }
                return null;
            """)
            if not confirmed:
                self._driver.find_element(By.TAG_NAME, "body").send_keys(Keys.RETURN)
                logger.info("unitalk_parser.filter.date_range_enter")
            else:
                logger.info("unitalk_parser.filter.date_range_apply", method=confirmed)
            time.sleep(2)

        elif "no_inputs" in (filled or ""):
            # ── Крок 3: segmented input (MUI v6 — окремі span/section per сегмент) ─
            logger.info("unitalk_parser.filter.segmented_input_fallback")
            self._fill_segmented_date_range(from_dt, to_dt)

        else:
            # Не вдалось — закриваємо picker
            self._driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
            time.sleep(0.5)
            logger.warning("unitalk_parser.filter.date_range_failed", result=filled)
            return False

        # ── Перевірка: picker закрився і chip оновився ──────────────────────────
        vis = self._driver_js(
            "var p = document.querySelector('.MuiPickersLayout-root'); "
            "return p ? window.getComputedStyle(p).visibility : null;"
        )
        if vis == "visible":
            self._driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
            time.sleep(0.5)

        chips_after = self._driver.find_elements(By.CSS_SELECTOR, ".MuiChip-root")
        chip_text = next(
            (c.text.strip() for c in chips_after if c.text.strip() in self._DATE_PRESETS), ""
        )
        logger.info("unitalk_parser.filter.date_range_result",
                    chip=chip_text, from_date=from_ua, to_date=to_ua)
        return True  # повертаємо True — намагались, результат в логах

    def _fill_segmented_date_range(self, from_dt, to_dt) -> None:
        """
        Заповнює MUI X date range picker (v5/v6/v7) через клавіатуру.

        MUI X v6/v7: сегменти = <span role="spinbutton"> або <span data-sectiontype>
        MUI X v5:    сегменти = <input type="text"> або [data-segment]

        Після введення year стартового поля фокус автоматично переходить
        на day-сегмент кінцевого поля — набираємо обидві дати як один потік.
        """
        from selenium.webdriver.common.keys import Keys
        from selenium.webdriver.common.action_chains import ActionChains

        # Чекаємо трохи — "Custom" може ще рендеритись
        time.sleep(0.8)

        # Пробуємо селектори від найновішого MUI X до найстарішого.
        # Спочатку ищемо всередині picker, якщо не знайшли — по всій сторінці.
        SELECTORS = [
            # MUI X v6/v7 — spinbutton spans
            (".MuiPickersLayout-root span[role='spinbutton']",   "picker_spinbutton_v6"),
            # MUI X v6 — data-sectiontype attribute
            (".MuiPickersLayout-root [data-sectiontype]",        "picker_sectiontype_v6"),
            # Широкий пошук по всій сторінці (якщо picker виходить за межі layout)
            ("span[role='spinbutton']",                          "page_spinbutton"),
            ("[data-sectiontype]",                               "page_sectiontype"),
            # MUI X v5 / старі версії
            (".MuiPickersLayout-root [data-segment]",            "picker_segment_v5"),
            (".MuiPickersLayout-root [contenteditable='true']",  "picker_contenteditable"),
        ]

        first_seg = None
        found_label = None
        for sel, label in SELECTORS:
            segs = self._driver.find_elements(By.CSS_SELECTOR, sel)
            if segs:
                first_seg = segs[0]
                found_label = label
                logger.info("unitalk_parser.filter.segmented_found",
                            selector=label, count=len(segs))
                break

        if first_seg is None:
            # Скріншот для діагностики + логування поточного HTML picker
            self._screenshot("segmented_no_segs")
            picker_html = self._driver_js(
                "var p=document.querySelector('.MuiPickersLayout-root');"
                "return p ? p.innerHTML.substring(0,2000) : 'NO_PICKER';"
            )
            logger.warning("unitalk_parser.filter.segmented_no_segments",
                           picker_html_preview=str(picker_html)[:500])
            return

        try:
            first_seg.click()
            time.sleep(0.4)
        except Exception as exc:
            logger.warning("unitalk_parser.filter.segmented_click_error", error=str(exc))
            return

        # Набираємо обидві дати в один ActionChains:
        # from: DD → TAB → MM → TAB → YYYY
        # to:   DD → TAB → MM → TAB → YYYY
        # (після YYYY from-поля MUI X автоматично переводить фокус на to-поле)
        ac = ActionChains(self._driver)
        ac.send_keys(from_dt.strftime("%d"))
        ac.send_keys(Keys.TAB)
        ac.send_keys(from_dt.strftime("%m"))
        ac.send_keys(Keys.TAB)
        ac.send_keys(from_dt.strftime("%Y"))
        ac.send_keys(to_dt.strftime("%d"))
        ac.send_keys(Keys.TAB)
        ac.send_keys(to_dt.strftime("%m"))
        ac.send_keys(Keys.TAB)
        ac.send_keys(to_dt.strftime("%Y"))
        ac.perform()
        time.sleep(1)

        logger.info("unitalk_parser.filter.segmented_typed",
                    selector=found_label,
                    from_date=from_dt.strftime("%d.%m.%Y"),
                    to_date=to_dt.strftime("%d.%m.%Y"))

        # Підтверджуємо кнопкою Apply або Enter
        confirmed = self._driver_js("""
            var picker = document.querySelector('.MuiPickersLayout-root');
            if (!picker) return null;
            var btns = Array.prototype.slice.call(picker.querySelectorAll('button'));
            var applyBtn = btns.find(function(b) {
                var t = (b.textContent || '').trim().toLowerCase();
                return t === 'apply' || t === 'застосувати' || t === 'ok' || t === 'підтвердити';
            });
            if (applyBtn) { applyBtn.click(); return 'apply_btn'; }
            return null;
        """)
        if not confirmed:
            self._driver.find_element(By.TAG_NAME, "body").send_keys(Keys.RETURN)
            logger.info("unitalk_parser.filter.segmented_enter")
        else:
            logger.info("unitalk_parser.filter.segmented_applied", method=confirmed)
        time.sleep(2)

    def _remove_new_leads_filter(self) -> None:
        """Знімає фільтр 'Only new leads' щоб бачити всі дзвінки."""
        try:
            chip_x = self._driver.find_element(
                By.XPATH,
                "//*[contains(@class,'MuiChip') and contains(.,'new lead')]"
                "//*[contains(@class,'deleteIcon') or @data-testid='CancelIcon']"
            )
            self._driver.execute_script("arguments[0].click();", chip_x)
            time.sleep(1)
            logger.info("unitalk_parser.filter.new_leads_removed")
        except Exception:
            pass

    def _wait_for_table(self, timeout: int = 30) -> bool:
        """Чекає завантаження таблиці дзвінків. Повертає True якщо є рядки."""
        try:
            WebDriverWait(self._driver, timeout).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "tr.MuiTableRow-hover")
                )
            )
            return True
        except TimeoutException:
            return False

    # ── Single call analytics ──────────────────────────────────────────────────

    def _get_next_analytics_row(self) -> Optional[dict]:
        """
        Знаходить першу необроблену активну кнопку Voice analytics,
        позначає її і клікає. Повертає row_data або None якщо більше немає.

        Використовує data-proc атрибут щоб не залежати від індексу рядка
        (таблиця може оновлюватись в реальному часі).
        """
        return self._driver_js("""
            const btn = document.querySelector(
                '[aria-label="Voice analytics"]:not(.Mui-disabled):not([data-proc])'
            );
            if (!btn) return null;
            btn.setAttribute('data-proc', '1');
            const row = btn.closest('tr');
            if (!row) return null;
            const tds = [...row.querySelectorAll('td')];
            const getText = i => tds[i]?.textContent?.trim() || '';
            const extractPhone = t => {
                const m = t.match(/\\+?\\d{10,13}/);
                return m ? m[0].replace('+','') : '';
            };
            btn.click();
            return {
                fromPhone: extractPhone(getText(1)),
                toPhone:   extractPhone(getText(2)),
                timeRaw:   getText(10),
                clicked:   true,
            };
        """)

    def _get_analytics_for_row(self, row_index: int) -> Optional[CallAnalyticData]:
        """
        Обробляє один рядок таблиці: відкриває аналітику і витягує поля.
        Повертає CallAnalyticData або None якщо аналітики немає / помилка.
        """
        # Читаємо дані рядка
        row_data = self._driver_js(_JS_EXTRACT_ROW, row_index)
        if not row_data:
            return None

        if not row_data.get("analyticsEnabled"):
            return None  # Аналітика недоступна (не прорахована або немає запису)

        analytic = CallAnalyticData(
            from_number=row_data.get("fromPhone", ""),
            to_number=row_data.get("toPhone", ""),
        )

        # Визначаємо дату з часового поля (наприклад "15:25:50Today")
        time_raw = row_data.get("timeRaw", "")
        analytic.call_date = self._parse_call_date(time_raw)

        # Клікаємо кнопку Voice analytics через JS
        clicked = self._driver_js("""
            const rows = [...document.querySelectorAll('tr.MuiTableRow-hover')];
            const row = rows[arguments[0]];
            const btn = row?.querySelector('[aria-label="Voice analytics"]:not(.Mui-disabled)');
            if (btn) { btn.click(); return true; }
            return false;
        """, row_index)

        if not clicked:
            analytic.parse_error = "click_failed"
            return analytic

        # Чекаємо модального вікна
        try:
            WebDriverWait(self._driver, 20).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, ".MuiModal-root:not(.MuiModal-hidden) h6")
                )
            )
        except TimeoutException:
            analytic.parse_error = "modal_timeout"
            return analytic

        time.sleep(0.5)

        # Клікаємо "Show all" щоб розкрити всі секції
        self._driver_js("""
            const modal = document.querySelector('.MuiModal-root:not(.MuiModal-hidden)');
            const btn = [...modal.querySelectorAll('button')].find(b => b.textContent.trim() === 'Show all');
            if (btn) btn.click();
        """)
        time.sleep(0.8)

        # Витягуємо всі поля через JS
        raw = self._driver_js(_JS_EXTRACT_ANALYTICS)

        if not raw or raw.get("_error"):
            analytic.parse_error = raw.get("_error", "extract_failed") if raw else "no_data"
        else:
            self._map_sections_to_analytic(raw, analytic)

        # Закриваємо модалку (перша SVG-кнопка у header модалки)
        self._close_modal()
        return analytic

    def _map_sections_to_analytic(self, raw: dict, analytic: CallAnalyticData) -> None:
        """Маппить сирі секції (з JS) на поля CallAnalyticData."""
        for key, content in raw.items():
            if not key.startswith("__sec__"):
                continue
            title = key[7:]  # прибираємо "__sec__"
            # Шукаємо перший збіг у SECTION_FIELD_MAP
            matched_field = None
            for prefix, field_name in SECTION_FIELD_MAP.items():
                if title.startswith(prefix):
                    matched_field = field_name
                    break

            if matched_field and hasattr(analytic, matched_field):
                # Не перезаписуємо вже встановлене поле (перший збіг має пріоритет)
                if getattr(analytic, matched_field) is None:
                    setattr(analytic, matched_field, content or None)

    def _close_modal(self) -> None:
        """
        Закриває модальне вікно.
        Спочатку шукає кнопку X у header, потім Escape.
        Чекає поки модалка дійсно зникне.
        """
        from selenium.webdriver.common.keys import Keys

        # Спроба 1: клік по кнопці закриття (SVG close / aria-label="close")
        closed = self._driver_js("""
            var modal = document.querySelector('.MuiModal-root:not(.MuiModal-hidden)');
            if (!modal) return 'already_closed';
            // Шукаємо кнопку з aria-label close або першу кнопку в header модалки
            var selectors = [
                '[aria-label="close"]', '[aria-label="Close"]',
                '[aria-label="закрити"]', '[aria-label="Закрити"]',
            ];
            for (var i = 0; i < selectors.length; i++) {
                var btn = modal.querySelector(selectors[i]);
                if (btn) { btn.click(); return 'close_btn'; }
            }
            // Перша кнопка у header/top area модалки (зазвичай X)
            var headerBtn = modal.querySelector('button');
            if (headerBtn) { headerBtn.click(); return 'first_btn'; }
            return null;
        """)

        if not closed or closed == 'already_closed':
            # Спроба 2: Escape
            try:
                self._driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
            except Exception:
                pass

        # Чекаємо поки модалка дійсно зникне (макс 3 сек)
        for _ in range(12):
            is_open = self._driver_js(
                "return !!document.querySelector('.MuiModal-root:not(.MuiModal-hidden)');"
            )
            if not is_open:
                break
            time.sleep(0.25)
        else:
            # Ще раз Escape якщо досі відкрита
            try:
                self._driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
                time.sleep(0.5)
            except Exception:
                pass

    def _parse_call_date(self, time_raw: str) -> str:
        """
        Перетворює рядок типу "15:25:50Today" або "15:25:50Yesterday" у "YYYY-MM-DD".
        """
        today = date.today()
        if "Today" in time_raw or "Сьогодні" in time_raw:
            return today.strftime("%Y-%m-%d")
        if "Yesterday" in time_raw or "Вчора" in time_raw:
            return (today - timedelta(days=1)).strftime("%Y-%m-%d")
        # Якщо є пряма дата (DD.MM.YYYY)
        m = re.search(r"(\d{2})\.(\d{2})\.(\d{4})", time_raw)
        if m:
            return f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
        # Якщо просто час — вважаємо сьогодні
        return today.strftime("%Y-%m-%d")

    # ── Main entry ─────────────────────────────────────────────────────────────

    def get_analytics(
        self,
        today: bool = False,
        max_days: int = 30,
        from_date: Optional[str] = None,
    ) -> ParseStats:
        """
        Головний метод.

        Args:
            today:     True → тільки сьогодні (Date: Today)
            max_days:  ігнорується якщо передано from_date
            from_date: "YYYY-MM-DD" — початкова дата діапазону (включно).
                       Якщо None — використовує last {max_days} days.
        """
        if self._driver is None:
            raise RuntimeError("Спочатку виклич login()")

        logger.info("unitalk_parser.parse.start", today=today,
                    from_date=from_date, max_days=max_days)
        self._go_to_history()
        self._wait_for_table(timeout=20)
        time.sleep(1)
        self._remove_new_leads_filter()

        # ВАЖЛИВО: датовий фільтр ДО кліку All tab (після — ламає picker)
        if today:
            self._set_date_filter("Today")
            self._click_all_tab()
            return self._parse_pages(date_label="today")
        else:
            return self._parse_all_days(from_date=from_date)

    def _get_shown_total(self) -> tuple:
        """
        Читає лічильник "Showed N of M" / "Показано N з M".
        Повертає (shown, total) або (0, 0) якщо не знайдено.
        """
        result = self._driver_js("""
            var spans = Array.prototype.slice.call(document.querySelectorAll('span, div, p'));
            for (var i = 0; i < spans.length; i++) {
                var t = spans[i].childNodes.length === 1
                    ? spans[i].textContent.trim()
                    : '';
                if (!t) continue;
                var m = t.match(/(?:Showed|Показано)\\s+(\\d+)\\s+(?:of|з)\\s+(\\d[\\d\\s]*)/i);
                if (m) {
                    var total = parseInt(m[2].replace(/\\s/g, ''));
                    return [parseInt(m[1]), total];
                }
            }
            return null;
        """)
        if result and len(result) == 2:
            return (int(result[0]), int(result[1]))
        return (0, 0)

    def _try_max_rows_per_page(self) -> None:
        """
        Намагається збільшити кількість рядків на сторінці через <select>.
        Кнопки поруч з лічильником НЕ чіпаємо — там Download, не налаштування.
        """
        # Чекаємо зникнення Backdrop після закриття picker
        for _ in range(10):
            backdrop = self._driver_js(
                "return !!document.querySelector('.MuiBackdrop-root:not([style*=\"opacity: 0\"])');"
            )
            if not backdrop:
                break
            time.sleep(0.3)

        changed = self._driver_js("""
            var selects = Array.prototype.slice.call(document.querySelectorAll('select'));
            for (var i = 0; i < selects.length; i++) {
                var opts = Array.prototype.slice.call(selects[i].options);
                var maxVal = 0;
                for (var j = 0; j < opts.length; j++) {
                    var v = parseInt(opts[j].value);
                    // розумний розмір сторінки: 10..1000
                    if (!isNaN(v) && v >= 10 && v <= 1000 && v > maxVal) maxVal = v;
                }
                if (maxVal >= 100) {
                    selects[i].value = String(maxVal);
                    selects[i].dispatchEvent(new Event('change', {bubbles: true}));
                    return 'select:' + maxVal;
                }
            }
            return null;
        """)
        if changed:
            logger.info("unitalk_parser.pagination.rows_per_page", result=changed)
            time.sleep(2)

    def _click_show_more(self) -> bool:
        """
        Клікає кнопку НАСТУПНОЇ сторінки в MUI Pagination внизу таблиці.

        Unitalk використовує числову пагінацію (1, 2, 3, ...) внизу сторінки.
        Алгоритм:
          1. Скролимо вниз щоб pagination з'явився
          2. Шукаємо поточну активну сторінку (disabled / Mui-selected / aria-current)
          3. Клікаємо кнопку з номером currentPage+1
          4. Якщо наступний номер не видно — шукаємо ">" або "наступна" кнопку
        """
        self._driver_js("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(0.8)

        clicked = self._driver_js("""
            var btns = Array.prototype.slice.call(document.querySelectorAll('button'));

            // Нумерні кнопки пагінації
            var numBtns = btns.filter(function(b) {
                return /^\\d+$/.test((b.textContent || '').trim());
            });
            if (!numBtns.length) return null;

            // Визначаємо поточну сторінку
            var currentPage = 1;
            var activeBtn = numBtns.find(function(b) {
                return b.getAttribute('aria-current') === 'page'
                    || b.getAttribute('aria-current') === 'true'
                    || b.getAttribute('aria-selected') === 'true'
                    || b.classList.contains('Mui-selected')
                    || b.disabled;
            });
            if (activeBtn) {
                currentPage = parseInt((activeBtn.textContent || '').trim()) || 1;
            }

            var nextPage = currentPage + 1;

            // Шукаємо кнопку з текстом nextPage
            var nextBtn = numBtns.find(function(b) {
                return parseInt((b.textContent || '').trim()) === nextPage && !b.disabled;
            });
            if (nextBtn) {
                nextBtn.scrollIntoView();
                nextBtn.click();
                return 'page:' + nextPage;
            }

            // Fallback: кнопка ">" / "наступна" / aria-label next
            var nextArrow = btns.find(function(b) {
                if (b.disabled) return false;
                var lbl = (b.getAttribute('aria-label') || b.title || b.textContent || '').trim().toLowerCase();
                return lbl === '>' || lbl === '>>' || lbl.includes('next')
                    || lbl.includes('наступн') || lbl.includes('вперед');
            });
            if (nextArrow) {
                nextArrow.click();
                return 'arrow_next';
            }

            return null;
        """)

        if clicked:
            logger.info("unitalk_parser.show_more_clicked", result=clicked)
            self._driver_js("window.scrollTo(0, 0);")
            return True

        logger.info("unitalk_parser.show_more_not_found")
        self._driver_js("window.scrollTo(0, 0);")
        return False

    def _go_next_page(self) -> bool:
        """
        Клікає кнопку "Показати ще" / "Show more" внизу сторінки.
        Повертає True якщо кнопку знайдено і нові рядки з'явились.
        """
        before_rows = self._driver_js(
            "return document.querySelectorAll('tr.MuiTableRow-hover').length;"
        ) or 0

        found = self._click_show_more()
        if not found:
            return False

        time.sleep(2.5)

        after_rows = self._driver_js(
            "return document.querySelectorAll('tr.MuiTableRow-hover').length;"
        ) or 0

        logger.info("unitalk_parser.next_page",
                    before_rows=before_rows, after_rows=after_rows)
        return after_rows > before_rows

    def _parse_all_days(self, from_date: Optional[str] = None) -> ParseStats:
        """
        Встановлює кастомний датовий діапазон [from_date → сьогодні],
        потім ітерує по всіх сторінках таблиці.

        from_date: "YYYY-MM-DD". Якщо None — "2025-09-01" (fallback).
        """
        if not from_date:
            from_date = "2025-09-01"

        to_date = date.today().strftime("%Y-%m-%d")
        logger.info("unitalk_parser.parse.range_mode", from_date=from_date, to_date=to_date)

        # Фільтр → All tab (порядок важливий: спочатку фільтр, потім таб)
        applied = self._set_custom_date_range(from_date, to_date)
        if not applied:
            logger.warning("unitalk_parser.parse.date_range_failed",
                           from_date=from_date, to_date=to_date)

        self._click_all_tab()

        if not self._wait_for_table(timeout=15):
            logger.warning("unitalk_parser.parse.no_table_after_filter")
            return ParseStats()

        time.sleep(1.5)

        # Пробуємо збільшити rows-per-page (щоб менше сторінок гортати)
        self._try_max_rows_per_page()

        shown, total = self._get_shown_total()
        logger.info("unitalk_parser.pagination.counter", shown=shown, total=total)

        combined = self._parse_pages(date_label="range")

        logger.info(
            "unitalk_parser.parse.done",
            total=combined.total,
            success=combined.success,
            skipped=combined.skipped_no_analytics,
            errors=combined.errors,
        )
        return combined

    def _parse_pages(self, date_label: str = "") -> ParseStats:
        """
        Парсить всі записи таблиці з автоматичним прокручуванням.
        Метод _parse_current_page тепер сам обробляє прокрутку і завантаження нових рядків.
        """
        logger.info("unitalk_parser.pagination.start", label=date_label)
        result = self._parse_current_page(date_label=date_label)
        logger.info("unitalk_parser.pagination.done",
                    total=result.total,
                    success=result.success,
                    skipped=result.skipped_no_analytics,
                    errors=result.errors)
        return result

    def _parse_current_page(self, date_label: str = "") -> ParseStats:
        """
        Парсить аналітику всіх доступних рядків, прокручуючи таблицю
        для завантаження нових записів поки вони є.
        """
        stats = ParseStats()

        if not self._wait_for_table(timeout=10):
            return stats

        time.sleep(1)

        # Лічильник ітерацій без нових рядків
        no_new_rows_count = 0
        max_iterations_without_new_rows = 15
        
        while True:
            # Рахуємо необроблені рядки
            unprocessed = self._driver_js("""
                return document.querySelectorAll(
                    '[aria-label="Voice analytics"]:not(.Mui-disabled):not([data-proc])'
                ).length;
            """) or 0

            if unprocessed == 0:
                # Немає необроблених рядків — шукаємо кнопку "Показати ще"
                before_rows = self._driver_js(
                    "return document.querySelectorAll('tr.MuiTableRow-hover').length;"
                ) or 0

                found = self._click_show_more()
                if found:
                    time.sleep(2.5)  # чекаємо завантаження нових рядків
                    no_new_rows_count = 0
                else:
                    no_new_rows_count += 1

                after_rows = self._driver_js(
                    "return document.querySelectorAll('tr.MuiTableRow-hover').length;"
                ) or 0
                unprocessed_after_scroll = self._driver_js("""
                    return document.querySelectorAll(
                        '[aria-label="Voice analytics"]:not(.Mui-disabled):not([data-proc])'
                    ).length;
                """) or 0

                logger.info("unitalk_parser.scroll_attempt",
                           before_rows=before_rows,
                           after_rows=after_rows,
                           unprocessed=unprocessed_after_scroll,
                           show_more_found=found)

                if no_new_rows_count >= max_iterations_without_new_rows:
                    break

                if unprocessed_after_scroll == 0:
                    continue
            
            # Обробляємо один рядок
            try:
                row_data = self._get_next_analytics_row()
                if row_data is None:
                    no_new_rows_count += 1
                    if no_new_rows_count >= max_iterations_without_new_rows:
                        break
                    continue

                no_new_rows_count = 0
                stats.total += 1
                analytic = CallAnalyticData(
                    from_number=row_data.get("fromPhone", ""),
                    to_number=row_data.get("toPhone", ""),
                )
                
                if date_label in ("today", "range"):
                    analytic.call_date = self._parse_call_date(row_data.get("timeRaw", ""))
                else:
                    analytic.call_date = date_label

                # Чекаємо модального вікна (макс 8 сек — Unitalk іноді не прораховує
                # аналітику для конкретного дзвінка, в такому разі модалка не відкривається.
                # Таймаут 20 сек × 28 рядків на сторінці = 9 хвилин зависання)
                try:
                    WebDriverWait(self._driver, 8).until(
                        EC.presence_of_element_located(
                            (By.CSS_SELECTOR, ".MuiModal-root:not(.MuiModal-hidden) h6")
                        )
                    )
                except TimeoutException:
                    analytic.parse_error = "modal_timeout"
                    stats.skipped_no_analytics += 1
                    logger.debug("unitalk_parser.parse.modal_timeout",
                                 from_num=analytic.from_number, date=date_label)
                    # Переконуємось що модалка не зависла у фоні
                    self._close_modal()
                    stats.results.append(analytic)
                    continue

                time.sleep(0.5)

                # Клікаємо "Show all"
                self._driver_js("""
                    var btns = Array.prototype.slice.call(document.querySelectorAll('button'));
                    for (var i = 0; i < btns.length; i++) {
                        if (btns[i].textContent.trim() === 'Show all') {
                            btns[i].click(); break;
                        }
                    }
                """)
                time.sleep(1.5)

                raw = self._driver_js(_JS_EXTRACT_ANALYTICS)

                if not raw or raw.get("_error"):
                    analytic.parse_error = raw.get("_error", "no_data") if raw else "no_data"
                    stats.errors += 1
                    logger.warning("unitalk_parser.parse.extract_error",
                                   error=analytic.parse_error, from_num=analytic.from_number)
                else:
                    raw.pop("_ok", None)
                    self._map_sections_to_analytic(raw, analytic)
                    stats.success += 1
                    logger.info(
                        "unitalk_parser.parse.row_ok",
                        from_num=analytic.from_number,
                        date=date_label,
                        topic=(analytic.conversation_topic or "")[:50],
                    )

                self._close_modal()
                stats.results.append(analytic)

            except Exception as exc:
                logger.error("unitalk_parser.parse.row_exception", error=str(exc), date=date_label)
                stats.errors += 1
                try:
                    self._close_modal()
                except Exception:
                    pass

        # Рахуємо пропущені записи
        total_rows = self._driver_js(
            "return document.querySelectorAll('tr.MuiTableRow-hover').length;"
        ) or 0
        stats.skipped_no_analytics = total_rows - stats.total

        logger.info("unitalk_parser.page.complete",
                   total_processed=stats.total,
                   success=stats.success,
                   errors=stats.errors,
                   skipped=stats.skipped_no_analytics)

        return stats
